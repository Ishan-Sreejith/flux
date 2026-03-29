from __future__ import annotations

import argparse
import json
import sys
from typing import List

from .evolution import EvolutionEngine, format_algorithm
from .io import load_genome, load_samples, save_genome
from .models import EvolutionConfig


def run_train(args: argparse.Namespace) -> int:
    samples = load_samples(args.dataset)
    config = EvolutionConfig(
        population_size=args.population,
        genome_length=args.genome_length,
        param_count=args.param_count,
        numeric_param_count=args.numeric_params,
        text_param_count=args.text_params,
        domain=args.domain,
        mutation_rate=args.mutation_rate,
        mutation_strength=args.mutation_strength,
        elite_fraction=args.elite_fraction,
        top_k=args.top_k,
        selection_strategy=args.selection,
        mutation_pressure=not args.no_mutation_pressure,
        stagnation_generations=args.stagnation,
        accuracy_target=args.accuracy_target,
        max_generations=args.generations,
        tolerance=args.tolerance,
        seed=args.seed,
    )
    engine = EvolutionEngine(config)
    result = engine.train(samples)
    print(format_algorithm(result.best_agent.genome, engine.params))
    print(f"Accuracy: {result.best_agent.accuracy:.3f}")
    print(f"Generations: {result.generations}")
    print(f"Converged: {'yes' if result.converged else 'no'}")
    if args.output_model:
        save_genome(result.best_agent.genome, args.output_model)
        print(f"Saved genome to {args.output_model}")
    return 0


def run_question(args: argparse.Namespace) -> int:
    genome = load_genome(args.model)
    engine = EvolutionEngine(
        EvolutionConfig(
            population_size=1,
            genome_length=len(genome.genes),
            param_count=args.param_count,
            numeric_param_count=args.numeric_params,
            text_param_count=args.text_params,
            domain=args.domain,
            max_generations=1,
            tolerance=args.tolerance,
            seed=args.seed,
        )
    )
    try:
        key = json.loads(args.key)
    except json.JSONDecodeError:
        key = args.key
    if args.domain == "auto":
        if isinstance(key, str):
            engine.set_domain("text")
        else:
            engine.set_domain("numeric")
    result = engine.execute_genome(key, genome)
    if not result.ok:
        print("Error executing genome.")
        return 1
    print(result.value)
    return 0


def run_ask(_: argparse.Namespace) -> int:
    print("Flux Ask Mode. Use ;train to train, or ask a question.")
    model_path = "/tmp/flux_model.json"
    while True:
        try:
            raw = input("flux-ask> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not raw:
            continue
        if raw.startswith(";"):
            cmd = raw[1:].strip().split()
            if not cmd:
                continue
            if cmd[0] in ("exit", "quit"):
                return 0
            if cmd[0] == "train" and len(cmd) >= 2:
                dataset = cmd[1]
                args = build_parser().parse_args(["train", "--dataset", dataset, "--output-model", model_path])
                args.func(args)
                continue
            print("Commands: ;train <dataset>, ;exit")
            continue

        args = build_parser().parse_args(["question", "--model", model_path, "--key", raw])
        args.func(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Flux Evolver CLI")
    sub = parser.add_subparsers(dest="command", required=False)

    train = sub.add_parser("train", help="Train with dataset")
    train.add_argument("--dataset", required=True)
    train.add_argument("--population", type=int, default=200)
    train.add_argument("--genome-length", type=int, default=8)
    train.add_argument("--param-count", type=int, default=1000)
    train.add_argument("--numeric-params", type=int, default=500)
    train.add_argument("--text-params", type=int, default=500)
    train.add_argument("--domain", choices=["auto", "numeric", "text"], default="auto")
    train.add_argument("--mutation-rate", type=float, default=0.2)
    train.add_argument("--mutation-strength", type=float, default=0.35)
    train.add_argument("--elite-fraction", type=float, default=0.1)
    train.add_argument("--top-k", type=int, default=10)
    train.add_argument("--selection", choices=["roulette", "tournament"], default="roulette")
    train.add_argument("--no-mutation-pressure", action="store_true")
    train.add_argument("--stagnation", type=int, default=20)
    train.add_argument("--accuracy-target", type=float, default=1.0)
    train.add_argument("--generations", type=int, default=500)
    train.add_argument("--tolerance", type=float, default=0.0)
    train.add_argument("--seed", type=int, default=42)
    train.add_argument("--output-model")
    train.set_defaults(func=run_train)

    question = sub.add_parser("question", help="Ask the trained model")
    question.add_argument("--model", required=True)
    question.add_argument("--key", required=True)
    question.add_argument("--param-count", type=int, default=1000)
    question.add_argument("--numeric-params", type=int, default=500)
    question.add_argument("--text-params", type=int, default=500)
    question.add_argument("--domain", choices=["auto", "numeric", "text"], default="auto")
    question.add_argument("--tolerance", type=float, default=0.0)
    question.add_argument("--seed", type=int, default=42)
    question.set_defaults(func=run_question)

    ask = sub.add_parser("ask", help="Interactive mode")
    ask.set_defaults(func=run_ask)

    return parser


def main(argv: List[str] | None = None) -> int:
    if argv is None and len(sys.argv) == 1:
        return run_ask(argparse.Namespace())
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        return run_ask(argparse.Namespace())
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
