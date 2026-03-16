from __future__ import annotations

import argparse
import json
from pathlib import Path

from animal1010101.algorithm import simplify
from animal1010101.simple_qa import synthesize_answer
from animal1010101.weights import load_weights
from animal1010101.engine import LexicalEngine


def _ask(question: str) -> str:
    base_dir = Path(__file__).resolve().parent / "animal1010101"
    engine = LexicalEngine(base_dir)
    simplified = simplify(question, engine)
    weights = load_weights(base_dir / "model_weights.json")
    return synthesize_answer(simplified, weights or None)


def _train(question: str, prime: str | None, traits: list[str]) -> None:
    base_dir = Path(__file__).resolve().parent / "animal1010101"
    path = base_dir / "train_data.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if not prime:
        raise ValueError("--prime is required (Animal/Object/Action/Feeling/Food)")
    entry = {"question": question, "prime": prime, "traits": traits}
    data.append(entry)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description="noux: schema Q&A without internet access")
    sub = p.add_subparsers(dest="cmd")

    ask = sub.add_parser("ask")
    ask.add_argument("question", type=str)

    chat = sub.add_parser("chat")

    train = sub.add_parser("train")
    train.add_argument("question", type=str)
    train.add_argument("--prime", type=str, default=None)
    train.add_argument("--traits", type=str, default="")

    args = p.parse_args()

    if args.cmd is None:
        args.cmd = "chat"

    if args.cmd == "ask":
        print(_ask(args.question))
        return 0

    if args.cmd == "chat":
        try:
            while True:
                q = input("noux> ").strip()
                if not q:
                    continue
                if q.lower() in {"exit", "quit"}:
                    break
                print(_ask(q))
        except KeyboardInterrupt:
            print("")
        return 0

    if args.cmd == "train":
        traits = [t.strip() for t in args.traits.split(",") if t.strip()]
        _train(args.question, args.prime, traits)
        print("Added training example. Run: python3 -m animal1010101.cli train-weights")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
