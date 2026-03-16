from __future__ import annotations

import argparse
from pathlib import Path

from master_ai.core.internet_access import search, set_allow_sources, set_block_sources
from master_ai.sim import answer, breed_next_generation, run_simulation, _append_learned, _load_learned


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Master AI simulation (36 agents)")
    p.add_argument("--rounds", type=int, default=1000)
    p.add_argument("--population", type=int, default=36)
    p.add_argument("--forbidden-question", action="append", default=[])
    p.add_argument("--questions-file", type=str, default="")
    p.add_argument("--forbidden-phrase", action="append", default=[])
    p.add_argument("--generations", type=int, default=1)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--max-workers", type=int, default=4)
    p.add_argument("--search-quota", type=int, default=None)
    p.add_argument("--time-budget-sec", type=float, default=10.0)
    p.add_argument("--trust-threshold", type=float, default=0.5)
    p.add_argument("--allow-source", action="append", default=[])
    p.add_argument("--block-source", action="append", default=[])
    p.add_argument("--ask-agent", action="store_true")
    p.add_argument("--chat-agent", action="store_true", help="Start interactive chat (Ctrl+C to exit)")
    p.add_argument("--agent-id", type=int, default=1)
    p.add_argument("--gen", type=int, default=0)
    p.add_argument("--question", type=str, default="")
    p.add_argument("--refresh", action="store_true", help="Fetch web facts before answering")
    return p


def main() -> None:
    args = build_parser().parse_args()
    root = Path(__file__).resolve().parents[1] / "master_ai"
    if args.seed is not None:
        import random

        random.seed(args.seed)

    if args.ask_agent or args.chat_agent:
        set_allow_sources(args.allow_source or None)
        set_block_sources(args.block_source or [])
        gen_dir = root / "population" / f"gen_{args.gen}"
        agent_dir = gen_dir / f"agent_{args.agent_id:02d}"
        if not agent_dir.exists():
            raise SystemExit(f"Agent not found: {agent_dir}")
        if args.ask_agent:
            if not args.question.strip():
                raise SystemExit("Provide --question for --ask-agent")
            if args.refresh:
                items = search(args.question, max_results=5)
                _append_learned(agent_dir, args.question, items)
            _load_learned(agent_dir, max_items=200)
            print(answer(agent_dir, args.question))
            return
        # chat mode
        print("Chat mode. Press Ctrl+C to exit.")
        try:
            while True:
                q = input("You> ").strip()
                if not q:
                    continue
                if args.refresh:
                    items = search(q, max_results=5)
                    _append_learned(agent_dir, q, items)
                _load_learned(agent_dir, max_items=200)
                print(answer(agent_dir, q))
        except KeyboardInterrupt:
            print("\nChat ended.")
        return

    questions: list[str] = []
    if args.questions_file:
        qpath = Path(args.questions_file)
        if qpath.exists():
            questions.extend([l.strip() for l in qpath.read_text(encoding="utf-8").splitlines() if l.strip()])
    questions.extend(args.forbidden_question or [])
    if not questions:
        raise SystemExit("Provide --forbidden-question or --questions-file")

    winners = []
    try:
        for gen in range(1, args.generations + 1):
            print(f"=== Running generation {gen} ===")
            scored, run_dir = run_simulation(
                root=root,
                forbidden_phrases=args.forbidden_phrase or [],
                forbidden_questions=questions,
                rounds=args.rounds,
                population_size=args.population,
                seed=args.seed,
                max_workers=args.max_workers,
                search_quota=args.search_quota,
                time_budget_sec=args.time_budget_sec,
                trust_threshold=args.trust_threshold,
                allow_sources=args.allow_source or None,
                block_sources=args.block_source or [],
            )
            if not scored:
                print(f"Interrupted. Partial run report: {run_dir}")
                return
            winners = [p for p, _ in scored[:6]]
            print("Top 6 scores:")
            for p, s in scored[:6]:
                print(f"{p.name} score={s:.4f}")
            print(f"Run report: {run_dir}")
            if gen < args.generations:
                breed_next_generation(root, winners, generation_index=gen)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        return

    print("Done.")


if __name__ == "__main__":
    main()
