from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

from evolver.knowledge import append_items, load_items
from evolver.research import internet_research
from evolver.runner import run_parallel


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Self-evolving LLM sandbox runner")
    p.add_argument("--workers", type=int, default=2, help="Number of parallel worker sandboxes")
    p.add_argument("--generations", type=int, default=8, help="Mutation attempts per worker")
    p.add_argument(
        "--continuous",
        action="store_true",
        help="Run forever until stopped (Ctrl+C), persisting progress each generation",
    )
    p.add_argument(
        "--fresh",
        action="store_true",
        help="Reset worker sandboxes/state before running",
    )
    p.add_argument(
        "--ask",
        action="store_true",
        help="Open question-asking section (interactive chat with selected worker brain)",
    )
    p.add_argument(
        "--question",
        type=str,
        default="",
        help="Ask one question and exit (can be used with --ask)",
    )
    p.add_argument(
        "--worker-id",
        type=int,
        default=1,
        help="Worker id used by --ask (default: 1)",
    )
    p.add_argument(
        "--no-research",
        action="store_true",
        help="Disable internet research context in --ask mode",
    )
    p.add_argument(
        "--train",
        action="store_true",
        help="Train the worker by fetching internet facts for the provided topic",
    )
    p.add_argument(
        "--topic",
        type=str,
        default="",
        help="Topic to train on (used with --train)",
    )
    return p


def _load_answer_fn(path: Path):
    spec = importlib.util.spec_from_file_location(f"brain_worker_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load brain module from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.answer


def _print_outcomes(outcomes, title: str) -> None:
    print(title)
    for o in outcomes:
        improve_rate = (o.verification_improved / o.verification_runs) if o.verification_runs else 0.0
        cand = "n/a" if o.last_candidate_score is None else f"{o.last_candidate_score:.3f}"
        print(
            f"worker={o.worker_id} gen={o.generation} best={o.best_score:.3f} "
            f"acc/rej={o.accepted}/{o.rejected} verify={o.verification_improved}/{o.verification_runs} "
            f"improve_rate={improve_rate:.1%} last={o.last_status} cand={cand}"
        )


def _load_state(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(path: Path, state: dict) -> None:
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _record_ask_event(root: Path, worker_id: int, question: str, answer_text: str) -> None:
    state_file = root / "sandboxes" / f"worker_{worker_id}" / "evolver_state.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state = _load_state(state_file)
    history = state.get("ask_history", [])
    history.append(
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "question": question,
            "answer_preview": answer_text[:300],
        }
    )
    state["ask_history"] = history[-100:]
    state["ask_count"] = int(state.get("ask_count", 0)) + 1
    state["last_ask_question"] = question
    state["last_answer_preview"] = answer_text[:300]
    _save_state(state_file, state)


def _knowledge_path(root: Path, worker_id: int) -> Path:
    return root / "sandboxes" / f"worker_{worker_id}" / "evolver_knowledge.jsonl"


def _run_train_mode(root: Path, worker_id: int, topic: str, use_research: bool) -> None:
    if not topic.strip():
        print("Please provide --topic for training.")
        return
    research = internet_research(topic, 5) if use_research else []
    knowledge_file = _knowledge_path(root, worker_id)
    append_items(knowledge_file, topic, research)
    learned_memory = load_items(knowledge_file, max_items=300)
    print(f"Trained worker {worker_id} on '{topic}'. Learned entries: {len(learned_memory)}")


def _run_question_mode(root: Path, worker_id: int, question: str, use_research: bool) -> None:
    worker_brain = root / "sandboxes" / f"worker_{worker_id}" / "mutable" / "brain.py"
    brain_path = worker_brain if worker_brain.exists() else root / "mutable" / "brain.py"
    answer_fn = _load_answer_fn(brain_path)
    knowledge_file = _knowledge_path(root, worker_id)

    def ask_once(q: str) -> None:
        research = internet_research(q, 3) if use_research else []
        if research:
            append_items(knowledge_file, q, research)
        learned_memory = load_items(knowledge_file, max_items=300)
        try:
            ai_answer = answer_fn(q, None, learned_memory)
        except TypeError:
            ai_answer = answer_fn(q, None)
        print(str(ai_answer))
        _record_ask_event(root, worker_id, q, str(ai_answer))

    if question.strip():
        ask_once(question.strip())
        return

    while True:
        q = input("You> ").strip()
        if not q:
            continue
        if q.lower() in {"exit", "quit"}:
            break
        ask_once(q)


def main() -> None:
    args = build_parser().parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.train:
        _run_train_mode(root, worker_id=args.worker_id, topic=args.topic or args.question, use_research=not args.no_research)
        return
    if args.ask:
        _run_question_mode(
            root=root,
            worker_id=args.worker_id,
            question=args.question,
            use_research=not args.no_research,
        )
        return

    if args.continuous:
        print("Continuous mode enabled. Press Ctrl+C to stop.")
        try:
            while True:
                outcomes = run_parallel(
                    root,
                    workers=args.workers,
                    generations=max(1, args.generations),
                    fresh=args.fresh,
                )
                args.fresh = False
                _print_outcomes(outcomes, "=== Evolution Tick ===")
        except KeyboardInterrupt:
            print("\nStopped. Progress saved in sandboxes/worker_*/")
        return

    outcomes = run_parallel(root, workers=args.workers, generations=args.generations, fresh=args.fresh)

    _print_outcomes(outcomes, "=== Evolution Summary ===")


if __name__ == "__main__":
    main()
