from __future__ import annotations

import importlib.util
import json
import math
import os
import random
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Tuple

from master_ai.core.backup_manager import backup, recover
from master_ai.core.integrity import verify_core_hashes
from master_ai.core.internet_access import search, set_allow_sources, set_block_sources, set_forbidden_phrases
from master_ai.core.rewrite_engine import adjust_config, clamp_config, crossover, mutate_config, write_config
from master_ai.reporting import log_event, log_fitness, new_run_dir, write_summary_csv


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _load_answer_fn(path: Path):
    spec = importlib.util.spec_from_file_location(f"agent_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load agent logic from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.answer


def _tokenize(text: str) -> List[str]:
    return [t for t in "".join(ch if ch.isalnum() else " " for ch in text.lower()).split() if t]


def _cosine_similarity(a: str, b: str) -> float:
    ta = _tokenize(a)
    tb = _tokenize(b)
    if not ta or not tb:
        return 0.0
    vocab = {}
    for t in ta + tb:
        vocab.setdefault(t, len(vocab))
    va = [0.0] * len(vocab)
    vb = [0.0] * len(vocab)
    for t in ta:
        va[vocab[t]] += 1.0
    for t in tb:
        vb[vocab[t]] += 1.0
    dot = sum(x * y for x, y in zip(va, vb))
    na = math.sqrt(sum(x * x for x in va))
    nb = math.sqrt(sum(x * x for x in vb))
    return dot / (na * nb) if na and nb else 0.0


def _learned_path(agent_dir: Path) -> Path:
    return agent_dir / "learned.jsonl"


def _append_learned(agent_dir: Path, topic: str, items: List[Dict[str, str]]) -> None:
    if not items:
        return
    path = _learned_path(agent_dir)
    seen = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
                fact = str(row.get("fact", "")).strip().lower()
                if fact:
                    seen.add(fact)
            except Exception:
                continue
    with path.open("a", encoding="utf-8") as f:
        for item in items:
            title = str(item.get("title", "")).strip()
            snippet = str(item.get("snippet", "")).strip()
            if not snippet:
                continue
            trust = float(item.get("trust", 0.5))
            fact = f"{title}: {snippet}" if title else snippet
            if fact.lower() in seen:
                continue
            f.write(
                json.dumps(
                    {
                        "topic": topic[:160],
                        "fact": fact,
                        "source": item.get("source", ""),
                        "trust": trust,
                        "url": item.get("url", ""),
                    }
                )
                + "\n"
            )
            seen.add(fact.lower())


def _load_learned(agent_dir: Path, max_items: int = 200) -> List[Dict[str, str]]:
    path = _learned_path(agent_dir)
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
            if isinstance(row, dict):
                rows.append(row)
        except Exception:
            continue
    return rows[-max_items:]


def _curiosity_query(base_topics: List[str], curiosity_bias: float, round_idx: int) -> str:
    if random.random() < min(1.0, curiosity_bias / 2.0):
        return random.choice(base_topics)
    return base_topics[round_idx % len(base_topics)]


def create_population(root: Path, count: int = 36, seed: int | None = None) -> List[Path]:
    if seed is not None:
        random.seed(seed)
    template = _load_json(root / "agent" / "config_template.json")
    out = []
    pop_root = root / "population" / "gen_0"
    pop_root.mkdir(parents=True, exist_ok=True)
    for i in range(count):
        agent_dir = pop_root / f"agent_{i+1:02d}"
        agent_dir.mkdir(parents=True, exist_ok=True)
        config = {k: random.uniform(0.1, 2.0) for k in template.keys()}
        _write_json(agent_dir / "config.json", config)
        (agent_dir / "logic.py").write_text(
            (root / "agent" / "agent_logic.py").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        out.append(agent_dir)
    return out


def _load_state(agent_dir: Path) -> dict:
    path = agent_dir / "state.json"
    if not path.exists():
        return {"searches_used": 0}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"searches_used": 0}


def _save_state(agent_dir: Path, state: dict) -> None:
    (agent_dir / "state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")


def action_cycle(
    agent_dir: Path,
    round_idx: int,
    search_quota: int | None,
    trust_threshold: float,
    time_budget_sec: float,
) -> Tuple[bool, str]:
    config = _load_json(agent_dir / "config.json")
    base_topics = [
        "machine learning fundamentals",
        "overfitting and regularization",
        "supervised vs unsupervised learning",
        "gradient descent intuition",
        "bias variance tradeoff",
        "evaluation metrics",
    ]
    started = time.time()
    state = _load_state(agent_dir)
    if search_quota is not None and state.get("searches_used", 0) >= search_quota:
        return False, "quota_exceeded"
    query = _curiosity_query(base_topics, config.get("curiosity_bias", 1.0), round_idx)
    if time.time() - started > time_budget_sec:
        return False, "timeout"
    results = search(query, max_results=max(1, int(3 * config.get("search_breadth", 1.0))))
    results = [r for r in results if float(r.get("trust", 0.5)) >= trust_threshold]
    _append_learned(agent_dir, query, results)
    state["searches_used"] = int(state.get("searches_used", 0)) + 1
    _save_state(agent_dir, state)
    return True, query


def self_evolve(agent_dir: Path, success_signal: float) -> None:
    config = _load_json(agent_dir / "config.json")
    deltas = {
        "curiosity_bias": 0.05 if success_signal > 0.5 else -0.03,
        "search_breadth": 0.03 if success_signal > 0.5 else -0.02,
        "memory_weight": 0.02 if success_signal > 0.5 else -0.01,
    }
    updated = adjust_config(config, deltas)
    updated = clamp_config(updated)
    write_config(agent_dir / "config.json", updated)


def answer(agent_dir: Path, question: str) -> str:
    logic_path = agent_dir / "logic.py"
    answer_fn = _load_answer_fn(logic_path)
    learned = _load_learned(agent_dir, max_items=200)
    return str(answer_fn(question, learned))


def fitness(agent_dir: Path, question: str, golden_answer: str) -> float:
    response = answer(agent_dir, question)
    return _cosine_similarity(response, golden_answer)


def _cache_key(question: str, forbidden_phrases: List[str], allow_sources: List[str] | None, block_sources: List[str]) -> str:
    key = {
        "question": question,
        "forbidden": sorted([p.lower() for p in forbidden_phrases]),
        "allow": sorted([s.lower() for s in allow_sources]) if allow_sources else [],
        "block": sorted([s.lower() for s in block_sources]),
    }
    return json.dumps(key, sort_keys=True)


def _load_golden_cache(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_golden_cache(path: Path, cache: dict) -> None:
    path.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def _golden_answer(
    question: str,
    forbidden_phrases: List[str],
    allow_sources: List[str] | None,
    block_sources: List[str],
    cache_path: Path,
) -> str:
    cache = _load_golden_cache(cache_path)
    key = _cache_key(question, forbidden_phrases, allow_sources, block_sources)
    if key in cache:
        return cache[key]
    golden = search(question, max_results=3)
    text = " ".join(f"{x.get('title','')} {x.get('snippet','')}" for x in golden).strip()
    if not text:
        text = question
    cache[key] = text
    _save_golden_cache(cache_path, cache)
    return text


def _round_worker(
    agent_dir_str: str,
    round_idx: int,
    snapshot_every: int,
    search_quota: int | None,
    trust_threshold: float,
    time_budget_sec: float,
    seed: int | None,
) -> dict:
    agent_dir = Path(agent_dir_str)
    if seed is not None:
        random.seed(seed)
    snapshot_dir = agent_dir / ".snapshot"
    if round_idx % snapshot_every == 0:
        backup(agent_dir, snapshot_dir)
    status = "ok"
    query = ""
    try:
        ok, query = action_cycle(agent_dir, round_idx, search_quota, trust_threshold, time_budget_sec)
        self_evolve(agent_dir, success_signal=1.0 if ok else 0.0)
    except Exception as e:
        recover(agent_dir, snapshot_dir)
        status = f"error:{e}"
    return {
        "agent": agent_dir.name,
        "round": round_idx,
        "status": status,
        "query": query,
    }


def run_simulation(
    root: Path,
    forbidden_phrases: List[str],
    forbidden_questions: List[str],
    rounds: int = 1000,
    population_size: int = 36,
    snapshot_every: int = 50,
    seed: int | None = None,
    max_workers: int = 4,
    search_quota: int | None = None,
    time_budget_sec: float = 10.0,
    trust_threshold: float = 0.5,
    allow_sources: List[str] | None = None,
    block_sources: List[str] | None = None,
) -> Tuple[List[Tuple[Path, float]], Path]:
    block_sources = block_sources or []
    set_forbidden_phrases(forbidden_phrases)
    set_allow_sources(allow_sources)
    set_block_sources(block_sources)

    verify_core_hashes(root / "core", root / "core" / "core_hashes.json")
    agents = create_population(root, count=population_size, seed=seed)
    run_dir = new_run_dir(root)

    try:
        for r in range(1, rounds + 1):
            verify_core_hashes(root / "core", root / "core" / "core_hashes.json")
            futures = []
            ex = ProcessPoolExecutor(max_workers=max_workers)
            try:
                for idx, agent in enumerate(agents):
                    worker_seed = None if seed is None else (seed + r * 1000 + idx)
                    futures.append(
                        ex.submit(
                            _round_worker,
                            str(agent),
                            r,
                            snapshot_every,
                            search_quota,
                            trust_threshold,
                            time_budget_sec,
                            worker_seed,
                        )
                    )
                for fut in as_completed(futures):
                    log_event(run_dir, fut.result())
            except KeyboardInterrupt:
                ex.shutdown(wait=False, cancel_futures=True)
                raise
            finally:
                ex.shutdown(wait=True)
    except KeyboardInterrupt:

        return [], run_dir


    scored = []
    set_forbidden_phrases([p for p in forbidden_phrases if all(p.lower() not in q.lower() for q in forbidden_questions)])
    cache_path = root / "population" / "golden_cache.json"
    summary_rows = []
    for agent in agents:
        scores = []
        for q in forbidden_questions:
            golden_text = _golden_answer(q, forbidden_phrases, allow_sources, block_sources, cache_path)
            score = fitness(agent, q, golden_text)
            scores.append(score)
            log_fitness(run_dir, {"agent": agent.name, "question": q, "score": score})
        avg = sum(scores) / len(scores) if scores else 0.0
        scored.append((agent, avg))
        summary_rows.append({"agent": agent.name, "avg_score": round(avg, 4)})
    write_summary_csv(run_dir, summary_rows)
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored, run_dir


def breed_next_generation(root: Path, winners: List[Path], generation_index: int) -> List[Path]:
    next_root = root / "population" / f"gen_{generation_index}"
    next_root.mkdir(parents=True, exist_ok=True)
    children = []
    configs = [_load_json(w / "config.json") for w in winners]
    parent_names = [w.name for w in winners]
    lineage_rows = []

    for i in range(36):
        a_idx = random.randrange(len(configs))
        b_idx = random.randrange(len(configs))
        parent_a = configs[a_idx]
        parent_b = configs[b_idx]
        child = crossover(parent_a, parent_b)
        child = mutate_config(child, mutation_rate=0.05)
        child = clamp_config(child)
        agent_dir = next_root / f"agent_{i+1:02d}"
        agent_dir.mkdir(parents=True, exist_ok=True)
        _write_json(agent_dir / "config.json", child)
        (agent_dir / "logic.py").write_text(
            (root / "agent" / "agent_logic.py").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        lineage = {
            "child": agent_dir.name,
            "parent_a": parent_names[a_idx],
            "parent_b": parent_names[b_idx],
            "generation": generation_index,
            "mutation_rate": 0.05,
        }
        (agent_dir / "lineage.json").write_text(json.dumps(lineage, indent=2), encoding="utf-8")
        lineage_rows.append(lineage)
        children.append(agent_dir)
    (next_root / "lineage.csv").write_text(
        "child,parent_a,parent_b,generation,mutation_rate\n"
        + "".join(
            f"{r['child']},{r['parent_a']},{r['parent_b']},{r['generation']},{r['mutation_rate']}\n"
            for r in lineage_rows
        ),
        encoding="utf-8",
    )
    return children
