from __future__ import annotations

import argparse
import json
import random
import shlex
import sys
from typing import Any, List
from pathlib import Path

from .evolution import EvolutionRunner, format_algorithm_map
from .io import append_to_store, load_genome, load_samples, save_bundle, save_genome, summarize_samples
from .models import Agent, AgentMeta, EvolutionConfig, Genome
from .scoring import score_value

DATA_STORE_DEFAULT = "/Users/ishan/flux/data/flux_training_data.json"
EXAMPLE_DATASETS = {
    "market": "/Users/ishan/flux/examples/market_share_linear.json",
    "solar": "/Users/ishan/flux/examples/solar_system_planets.json",
    "voyager": "/Users/ishan/flux/examples/voyager_slingshot.json",
}
EXAMPLE_QUESTIONS = {
    "market": ["11", "12"],
    "solar": ["1", "4", "8"],
    "voyager": ["[45.0, 15000.0, 5.97, 750.0]", "[75.0, 16800.0, 8.40, 580.0]"],
}


def _parse_key(value: str, as_json: bool) -> Any:
    if not as_json:
        return value
    return json.loads(value)


def _map_key(key: Any, map_path: str) -> Any:
    mapping = json.loads(Path(map_path).read_text(encoding="utf-8"))
    if not isinstance(mapping, dict):
        raise ValueError("key-map must be a JSON object")
    if key in mapping:
        return mapping[key]
    key_str = str(key)
    if key_str in mapping:
        return mapping[key_str]
    raise KeyError(f"key not found in map: {key}")


def _build_config(args: argparse.Namespace) -> EvolutionConfig:
    return EvolutionConfig(
        population_size=args.population,
        library_size=args.library,
        param_min=args.param_min,
        param_max=args.param_max,
        mode=args.mode,
        min_genome_length=args.min_length,
        max_genome_length=args.max_length,
        initial_genome_length=args.initial_length,
        max_generations=args.generations,
        elite_fraction=args.elite_fraction,
        tournament_size=args.tournament,
        mutation_rate=args.mutation_rate,
        mutation_volatility=args.mutation_volatility,
        initial_randomness=args.initial_randomness,
        seed=args.seed,
        log_every=args.log_every,
    )


def _resolve_dataset(args: argparse.Namespace) -> str:
    if args.example:
        if args.example not in EXAMPLE_DATASETS:
            raise ValueError(f"Unknown example: {args.example}")
        return EXAMPLE_DATASETS[args.example]
    if not args.dataset:
        raise ValueError("dataset required")
    return args.dataset


def run_train(args: argparse.Namespace) -> int:
    dataset_path = _resolve_dataset(args)
    samples = load_samples(dataset_path)
    if not args.no_store:
        append_to_store(args.data_store, samples)
    summary = summarize_samples(samples)
    if summary["has_numeric_values"] and summary["has_string_values"]:
        print("Warning: mixed value types detected (numeric + string). Convergence may be unlikely.")
    if summary["has_numeric_values"] and summary["has_non_numeric_string_keys"]:
        print("Warning: numeric targets with non-numeric string keys may be hard to learn.")
        print("Tip: for text keys with numeric targets, add a key-mapping file and use --key-map.")

    verify_samples = samples
    if args.verify_file:
        verify_samples = load_samples(args.verify_file)
    if args.verify and args.verify > len(verify_samples):
        print("Verification count exceeds available samples.")
        return 1

    success_target = args.success_rate
    trials = max(1, args.success_rate_trials)
    total_runs = args.verify_retries + 1
    if success_target > 0:
        total_runs = max(total_runs, trials)

    success_count = 0
    best_success = None
    best_success_score = float("inf")

    for attempt in range(total_runs):
        seed = args.seed + attempt
        config = _build_config(args)
        config.seed = seed
        runner = EvolutionRunner(config=config)
        result = runner.run(samples)
        print()
        print(format_algorithm_map(result.best_agent.genome, runner.params))
        print()
        print(f"Best score: {result.best_score:.6f}")
        print(f"Generations: {result.generations}")
        print(f"Converged: {'yes' if result.converged else 'no'}")

        verified = False
        if args.verify:
            rng = random.Random(args.verify_seed + attempt)
            used_keys = set()
            successes = 0
            attempts = 0
            while successes < args.verify and attempts < args.verify * 10:
                sample = rng.choice(verify_samples)
                key_input = sample.key
                if args.key_map:
                    key_input = _map_key(sample.key, args.key_map)
                key_id = json.dumps(key_input, sort_keys=True, default=str)
                attempts += 1
                if key_id in used_keys:
                    continue
                used_keys.add(key_id)
                exec_result = runner.execute_genome(
                    key_input, result.best_agent.genome, agent_id=1, sample_index=attempts
                )
                if exec_result.ok and score_value(exec_result.value, sample.value) <= args.verify_tolerance:
                    successes += 1
                else:
                    successes = 0
            if successes >= args.verify:
                print(f"Verification passed: {args.verify} consecutive unique matches.")
                verified = True
            print(f"Verification failed: {successes} consecutive matches (needed {args.verify}).")
        else:
            verified = True

        if verified:
            success_count += 1
            if result.best_score < best_success_score:
                best_success_score = result.best_score
                best_success = result

        if success_target > 0:
            current_rate = success_count / (attempt + 1)
            print(f"Success rate: {success_count}/{attempt + 1} = {current_rate:.2f}")
            if attempt + 1 >= trials:
                if current_rate >= success_target:
                    if best_success and args.output_model:
                        save_genome(best_success.best_agent.genome, args.output_model)
                        print(f"Saved genome to {args.output_model}")
                    if best_success and args.save_bundle:
                        save_bundle(
                            best_success.best_agent.genome,
                            samples,
                            args.save_bundle,
                            metadata={"seed": args.seed, "generations": best_success.generations},
                        )
                        print(f"Saved bundle to {args.save_bundle}")
                    return 0
        else:
            if verified:
                if args.output_model:
                    save_genome(result.best_agent.genome, args.output_model)
                    print(f"Saved genome to {args.output_model}")
                if args.save_bundle:
                    save_bundle(
                        result.best_agent.genome,
                        samples,
                        args.save_bundle,
                        metadata={"seed": seed, "generations": result.generations},
                    )
                    print(f"Saved bundle to {args.save_bundle}")
                return 0

        if attempt < args.verify_retries:
            print(f"Retrying training with seed {seed + 1}...")

    if success_target > 0:
        print(f"Failed to reach success rate {success_target:.2f} after {trials} trials.")
    return 1


def run_question(args: argparse.Namespace) -> int:
    try:
        genome = load_genome(args.model)
    except FileNotFoundError:
        print(f"Model not found: {args.model}. Train first with 'flux train' or ';train' in ask mode.")
        return 1
    config = EvolutionConfig(
        population_size=1,
        library_size=genome.library_size,
        min_genome_length=len(genome.genes),
        max_genome_length=len(genome.genes),
        initial_genome_length=len(genome.genes),
        seed=args.seed,
        log_every=0,
    )
    runner = EvolutionRunner(config=config)
    key = _parse_key(args.key, args.key_json)
    if args.key_map:
        key = _map_key(key, args.key_map)
    agent = Agent(id=1, genome=genome, meta=AgentMeta(speed_weight=0.0, inheritance_strategy="dominant"))
    result = runner.execute_genome(key, genome, agent_id=agent.id, sample_index=0)
    if not result.ok:
        print(f"Error: {result.error}")
        return 1
    print(result.value)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parameter evolution CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    train = subparsers.add_parser("train", help="Evolve parameters against a dataset")
    train.add_argument("--dataset", help="Path to dataset JSON/TSV")
    train.add_argument("--example", help="Built-in dataset: market | solar | voyager")
    train.add_argument("--library", type=int, default=120, help="Library slider (1-300)")
    train.add_argument("--param-min", type=int, default=1, help="Minimum parameter id")
    train.add_argument("--param-max", type=int, default=300, help="Maximum parameter id")
    train.add_argument("--mode", default="all", help="Parameter mode: all | math | text | list")
    train.add_argument("--population", type=int, default=40, help="Population size")
    train.add_argument("--min-length", type=int, default=4, help="Minimum genome length")
    train.add_argument("--max-length", type=int, default=12, help="Maximum genome length")
    train.add_argument("--initial-length", type=int, default=8, help="Initial genome length")
    train.add_argument("--generations", type=int, default=200, help="Max generations")
    train.add_argument("--elite-fraction", type=float, default=0.2, help="Elite fraction")
    train.add_argument("--tournament", type=int, default=5, help="Tournament size")
    train.add_argument("--mutation-rate", type=float, default=0.25, help="Mutation rate")
    train.add_argument("--mutation-volatility", type=float, default=0.35, help="Mutation volatility")
    train.add_argument("--initial-randomness", type=float, default=0.25, help="Initial gene randomness")
    train.add_argument("--seed", type=int, default=42, help="RNG seed")
    train.add_argument("--log-every", type=int, default=1, help="Log every N generations")
    train.add_argument("--output-model", help="Path to save the best genome JSON")
    train.add_argument("--save-bundle", help="Save genome + dataset bundle JSON")
    train.add_argument("--verify", type=int, default=0, help="Require N consecutive unique matches")
    train.add_argument("--verify-file", help="Optional dataset for verification")
    train.add_argument("--verify-seed", type=int, default=1337, help="RNG seed for verification samples")
    train.add_argument("--verify-tolerance", type=float, default=1e-6, help="Tolerance for verification success")
    train.add_argument("--verify-retries", type=int, default=0, help="Retry training N times on verify failure")
    train.add_argument("--key-map", help="Optional JSON mapping for text keys")
    train.add_argument("--data-store", default=DATA_STORE_DEFAULT, help="Training data store file")
    train.add_argument("--no-store", action="store_true", help="Do not append to data store")
    train.add_argument("--success-rate", type=float, default=0.0, help="Require minimum success rate (0-1)")
    train.add_argument("--success-rate-trials", type=int, default=5, help="Trials used for success rate")
    train.set_defaults(func=run_train)

    question = subparsers.add_parser("question", help="Run a trained genome on a key")
    question.add_argument("--model", required=True, help="Path to saved genome JSON")
    question.add_argument("--key", required=True, help="Key input (string or JSON)")
    question.add_argument("--key-json", action="store_true", help="Parse key as JSON")
    question.add_argument("--seed", type=int, default=42, help="RNG seed")
    question.add_argument("--key-map", help="Optional JSON mapping for text keys")
    question.set_defaults(func=run_question)

    ask = subparsers.add_parser("ask", help="Interactive Q&A shell")
    ask.add_argument("--model", default="/tmp/flux_model.json", help="Default model path")
    ask.add_argument("--data-store", default=DATA_STORE_DEFAULT, help="Training data store file")
    ask.set_defaults(func=run_ask)

    examples = subparsers.add_parser("examples", help="List built-in datasets")
    examples.set_defaults(func=run_examples)

    demo = subparsers.add_parser("demo", help="Run built-in example training and Q&A")
    demo.add_argument("--example", required=True, help="Example name: market | solar | voyager")
    demo.add_argument("--model", help="Output model path")
    demo.add_argument("--library", type=int, default=180, help="Library slider (1-300)")
    demo.add_argument("--generations", type=int, default=200, help="Max generations")
    demo.add_argument("--population", type=int, default=60, help="Population size")
    demo.add_argument("--verify", type=int, default=0, help="Require N consecutive unique matches")
    demo.add_argument("--verify-retries", type=int, default=0, help="Retry training N times on verify failure")
    demo.set_defaults(func=run_demo)

    shell = subparsers.add_parser("shell", help="Interactive shell")
    shell.set_defaults(func=run_shell)

    return parser



def _shell_help() -> str:
    return (
        "Commands:\n"
        "  train <dataset_path> [--library N] [--generations N] [--output MODEL] [--verify N] [--verify-retries N] [--key-map FILE]\n"
        "  ask <model_path> <key> [--key-map FILE]\n"
        "  ask-json <model_path> <json_key> [--key-map FILE]\n"
        "  examples\n"
        "  demo --example NAME\n"
        "  help\n"
        "  exit | quit\n"
    )


def run_shell(_: argparse.Namespace) -> int:
    print("Flux Evolver Shell. Type 'help' for commands.")
    while True:
        try:
            raw = input("flux> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not raw:
            continue
        if raw in ("exit", "quit"):
            return 0
        if raw == "help":
            print(_shell_help())
            continue

        parts = shlex.split(raw)
        if not parts:
            continue
        cmd = parts[0]
        if cmd == "train":
            dataset = parts[1] if len(parts) > 1 else None
            if not dataset:
                print("Usage: train <dataset_path> [--library N] [--generations N] [--output MODEL]")
                continue
            args_list = ["train", "--dataset", dataset]
            if dataset.startswith("example:"):
                example_name = dataset.split(":", 1)[1]
                args_list = ["train", "--example", example_name]
            i = 2
            while i < len(parts):
                token = parts[i]
                if token in (
                    "--library",
                    "--param-min",
                    "--param-max",
                    "--mode",
                    "--generations",
                    "--output",
                    "--verify",
                    "--verify-retries",
                    "--verify-tolerance",
                    "--success-rate",
                    "--success-rate-trials",
                    "--save-bundle",
                    "--key-map",
                ) and i + 1 < len(parts):
                    if token == "--output":
                        args_list.extend(["--output-model", parts[i + 1]])
                    elif token == "--verify":
                        args_list.extend(["--verify", parts[i + 1]])
                    elif token == "--verify-retries":
                        args_list.extend(["--verify-retries", parts[i + 1]])
                    elif token == "--verify-tolerance":
                        args_list.extend(["--verify-tolerance", parts[i + 1]])
                    elif token == "--save-bundle":
                        args_list.extend(["--save-bundle", parts[i + 1]])
                    elif token == "--key-map":
                        args_list.extend(["--key-map", parts[i + 1]])
                    elif token == "--success-rate":
                        args_list.extend(["--success-rate", parts[i + 1]])
                    elif token == "--success-rate-trials":
                        args_list.extend(["--success-rate-trials", parts[i + 1]])
                    else:
                        args_list.extend([token, parts[i + 1]])
                    i += 2
                    continue
                i += 1
            try:
                args = build_parser().parse_args(args_list)
                args.func(args)
            except SystemExit:
                continue
            continue

        if cmd in ("ask", "ask-json"):
            if len(parts) < 3:
                print("Usage: ask <model_path> <key> | ask-json <model_path> <json_key>")
                continue
            model_path = parts[1]
            key = " ".join(parts[2:])
            args_list = ["question", "--model", model_path, "--key", key]
            if "--key-map" in parts:
                idx = parts.index("--key-map")
                if idx + 1 < len(parts):
                    args_list.extend(["--key-map", parts[idx + 1]])
            if cmd == "ask-json":
                args_list.append("--key-json")
            try:
                args = build_parser().parse_args(args_list)
                args.func(args)
            except SystemExit:
                continue
            continue

        if cmd == "examples":
            for name, path in EXAMPLE_DATASETS.items():
                print(f"{name}: {path}")
            continue

        print("Unknown command. Type 'help' for commands.")
    return 0


def _ask_help() -> str:
    return (
        "Ask Mode Commands:\n"
        "  ;train [dataset_path|example:NAME] [--verify N] [--verify-retries N]\n"
        "  ;parameters [key=value ...] (library, generations, population, verify, verify_retries, verify_tolerance, model, mode, param_min, param_max, success_rate, success_rate_trials)\n"
        "  ;help\n"
        "  ;exit\n"
        "Otherwise, type a question to query the current model.\n"
    )


def run_ask(args: argparse.Namespace) -> int:
    params = {
        "library": 180,
        "generations": 200,
        "population": 60,
        "verify": 0,
        "verify_retries": 0,
        "verify_tolerance": 1e-6,
        "success_rate": 0.0,
        "success_rate_trials": 5,
        "mode": "all",
        "param_min": 1,
        "param_max": 300,
        "model": args.model,
    }
    data_store = args.data_store
    print("Flux Ask Mode. Type ;help for commands.")
    while True:
        try:
            raw = input("flux-ask> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not raw:
            continue
        if raw.startswith(";"):
            cmd_line = raw[1:].strip()
            if cmd_line in ("exit", "quit"):
                return 0
            if cmd_line == "help":
                print(_ask_help())
                continue
            if cmd_line.startswith("parameters"):
                parts = shlex.split(cmd_line)
                if len(parts) == 1:
                    for k, v in params.items():
                        print(f"{k}={v}")
                    continue
                for token in parts[1:]:
                    if "=" not in token:
                        continue
                    key, value = token.split("=", 1)
                    if key in ("library", "generations", "population", "verify", "verify_retries", "success_rate_trials"):
                        params[key] = int(value)
                    elif key == "success_rate":
                        params[key] = float(value)
                    elif key == "verify_tolerance":
                        params[key] = float(value)
                    elif key in ("param_min", "param_max"):
                        params[key] = int(value)
                    elif key == "mode":
                        params[key] = value
                    elif key == "model":
                        params[key] = value
                continue
            if cmd_line.startswith("train"):
                parts = shlex.split(cmd_line)
                dataset = None
                if len(parts) > 1:
                    dataset = parts[1]
                if not dataset:
                    dataset = data_store
                train_args = [
                    "train",
                    "--dataset",
                    dataset,
                    "--library",
                    str(params["library"]),
                    "--generations",
                    str(params["generations"]),
                    "--population",
                    str(params["population"]),
                    "--verify",
                    str(params["verify"]),
                    "--verify-retries",
                    str(params["verify_retries"]),
                    "--verify-tolerance",
                    str(params["verify_tolerance"]),
                    "--success-rate",
                    str(params["success_rate"]),
                    "--success-rate-trials",
                    str(params["success_rate_trials"]),
                    "--param-min",
                    str(params["param_min"]),
                    "--param-max",
                    str(params["param_max"]),
                    "--mode",
                    str(params["mode"]),
                    "--output-model",
                    params["model"],
                ]
                if dataset.startswith("example:"):
                    example_name = dataset.split(":", 1)[1]
                    train_args = [arg for arg in train_args if arg not in ("--dataset", dataset)]
                    train_args.extend(["--example", example_name])
                try:
                    train_ns = build_parser().parse_args(train_args)
                    train_ns.func(train_ns)
                except SystemExit:
                    continue
                continue
            print("Unknown command. Type ;help for commands.")
            continue

        question_args = ["question", "--model", params["model"], "--key", raw]
        try:
            q_ns = build_parser().parse_args(question_args)
            q_ns.func(q_ns)
        except SystemExit:
            continue
    return 0


def run_examples(_: argparse.Namespace) -> int:
    for name, path in EXAMPLE_DATASETS.items():
        print(f"{name}: {path}")
    return 0


def run_demo(args: argparse.Namespace) -> int:
    if args.example not in EXAMPLE_DATASETS:
        print(f"Unknown example: {args.example}")
        return 1
    model_path = args.model or f"/tmp/flux_{args.example}_model.json"
    train_args = [
        "train",
        "--example",
        args.example,
        "--library",
        str(args.library),
        "--param-min",
        "1",
        "--param-max",
        "300",
        "--mode",
        "all",
        "--generations",
        str(args.generations),
        "--population",
        str(args.population),
        "--verify",
        str(args.verify),
        "--verify-retries",
        str(args.verify_retries),
        "--output-model",
        model_path,
    ]
    train_ns = build_parser().parse_args(train_args)
    train_rc = train_ns.func(train_ns)
    if train_rc != 0:
        return train_rc
    questions = EXAMPLE_QUESTIONS.get(args.example, [])
    for q in questions:
        q_args = ["question", "--model", model_path, "--key", q]
        if q.startswith("[") or q.startswith("{"):
            q_args.append("--key-json")
        q_ns = build_parser().parse_args(q_args)
        q_ns.func(q_ns)
    return 0


def main(argv: List[str] | None = None) -> int:
    if argv is None and len(sys.argv) == 1:
        ask_args = build_parser().parse_args(["ask"])
        return run_ask(ask_args)
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "train" and not (1 <= args.library <= 300):
        parser.error("--library must be within 1..300")
    if args.command == "train" and not args.dataset and not args.example:
        parser.error("--dataset or --example is required")
    if args.command == "train" and not (0.0 <= args.success_rate <= 1.0):
        parser.error("--success-rate must be within 0..1")
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
