from __future__ import annotations

import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import List

from evolver.config import default_config
from evolver.evaluator import evaluate_brain
from evolver.knowledge import append_items
from evolver.memory import FailureMemory
from evolver.mutator import Mutator
from evolver.sandbox import checkpoint_file, prepare_worker_sandbox, restore_file


@dataclass
class WorkerOutcome:
    worker_id: int
    generation: int
    best_score: float
    accepted: int
    rejected: int
    verification_runs: int
    verification_improved: int
    last_status: str
    last_candidate_score: float | None


def _load_worker_state(path: Path) -> dict:
    if not path.exists():
        return {
            "generation": 0,
            "best_score": 0.0,
            "accepted": 0,
            "rejected": 0,
            "verification_runs": 0,
            "verification_improved": 0,
            "last_status": "init",
            "last_candidate_score": None,
        }
    return json.loads(path.read_text(encoding="utf-8"))


def _save_worker_state(path: Path, state: dict) -> None:
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _ensure_state_defaults(state: dict) -> None:
    state.setdefault("generation", 0)
    state.setdefault("best_score", 0.0)
    state.setdefault("accepted", 0)
    state.setdefault("rejected", 0)
    state.setdefault("verification_runs", 0)
    state.setdefault("verification_improved", 0)
    state.setdefault("last_status", "init")
    state.setdefault("last_candidate_score", None)


def _append_verification_log(path: Path, row: dict) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def run_worker(project_root: Path, worker_id: int, generations: int, fresh: bool = False) -> WorkerOutcome:
    cfg = default_config(project_root)
    cfg.sandbox_root.mkdir(parents=True, exist_ok=True)

    worker_root = prepare_worker_sandbox(project_root, cfg.sandbox_root, worker_id, reset=fresh)
    mutable_file = worker_root / "mutable" / "brain.py"
    state_file = worker_root / "evolver_state.json"
    verification_file = worker_root / "evolver_verification.jsonl"
    knowledge_file = worker_root / "evolver_knowledge.jsonl"
    memory = FailureMemory(worker_root / "evolver_memory.json")
    mutator = Mutator()
    state = _load_worker_state(state_file)
    _ensure_state_defaults(state)

    if state["generation"] == 0:
        base_eval = evaluate_brain(mutable_file)
        state["best_score"] = base_eval.score
        _save_worker_state(state_file, state)

    for _ in range(generations):
        g = state["generation"] + 1
        current = mutable_file.read_text(encoding="utf-8")
        proposal = mutator.propose(current, g)
        append_items(knowledge_file, proposal.query, proposal.research_items)

        if memory.has_seen(proposal.new_source):
            state["generation"] = g
            state["rejected"] += 1
            state["verification_runs"] += 1
            state["last_status"] = "duplicate_rejected"
            state["last_candidate_score"] = None
            _append_verification_log(
                verification_file,
                {
                    "generation": g,
                    "status": state["last_status"],
                    "candidate_score": None,
                    "best_score": state["best_score"],
                },
            )
            _save_worker_state(state_file, state)
            continue

        snap = checkpoint_file(mutable_file)
        mutable_file.write_text(proposal.new_source, encoding="utf-8")

        try:
            candidate_eval = evaluate_brain(mutable_file)
        except Exception as e:
            restore_file(mutable_file, snap)
            memory.add(proposal.new_source, f"runtime error: {e}", g)
            state["generation"] = g
            state["rejected"] += 1
            state["verification_runs"] += 1
            state["last_status"] = "runtime_error_rejected"
            state["last_candidate_score"] = None
            _append_verification_log(
                verification_file,
                {
                    "generation": g,
                    "status": state["last_status"],
                    "candidate_score": None,
                    "best_score": state["best_score"],
                    "error": str(e),
                },
            )
            _save_worker_state(state_file, state)
            continue

        state["verification_runs"] += 1
        state["last_candidate_score"] = candidate_eval.score
        if candidate_eval.score > state["best_score"]:
            state["best_score"] = candidate_eval.score
            state["accepted"] += 1
            state["verification_improved"] += 1
            state["last_status"] = "accepted"
        else:
            restore_file(mutable_file, snap)
            memory.add(proposal.new_source, f"no improvement ({candidate_eval.score})", g)
            state["rejected"] += 1
            state["last_status"] = "score_rejected"

        _append_verification_log(
            verification_file,
            {
                "generation": g,
                "status": state["last_status"],
                "candidate_score": candidate_eval.score,
                "best_score": state["best_score"],
            },
        )

        state["generation"] = g
        _save_worker_state(state_file, state)

    return WorkerOutcome(
        worker_id=worker_id,
        generation=state["generation"],
        best_score=state["best_score"],
        accepted=state["accepted"],
        rejected=state["rejected"],
        verification_runs=state["verification_runs"],
        verification_improved=state["verification_improved"],
        last_status=state["last_status"],
        last_candidate_score=state["last_candidate_score"],
    )


def run_parallel(project_root: Path, workers: int, generations: int, fresh: bool = False) -> List[WorkerOutcome]:
    outcomes: List[WorkerOutcome] = []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futures = [
            ex.submit(run_worker, project_root, i + 1, generations, fresh) for i in range(workers)
        ]
        for fut in as_completed(futures):
            outcomes.append(fut.result())
    return sorted(outcomes, key=lambda x: x.worker_id)
