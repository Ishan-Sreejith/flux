from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from animal1010101.algorithm import simplify
from animal1010101.simple_qa import build_answer
from animal1010101.wikidata_lookup import describe
from animal1010101.weights import load_weights
from animal1010101.engine import LexicalEngine


def _wikipedia_summary(term: str) -> str:
    if not term:
        return ""
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(term)}"
    req = urllib.request.Request(url, headers={"User-Agent": "animal1010101/0.4"})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return ""
    if data.get("type", "").endswith("not_found"):
        return ""
    return str(data.get("extract", "") or "").strip()


def _ask(question: str, use_live: bool) -> str:
    base_dir = Path(__file__).resolve().parent / "animal1010101"
    engine = LexicalEngine(base_dir)
    simplified = simplify(question, engine)
    term = " ".join(simplified.tokens[:3]) if simplified.tokens else question
    live = _wikipedia_summary(term) if use_live else ""
    web_text = live or describe(term)
    weights = load_weights(base_dir / "model_weights.json")
    return build_answer(simplified.intent, web_text, simplified, weights or None)


def main() -> int:
    p = argparse.ArgumentParser(description="flux: schema Q&A with internet access")
    sub = p.add_subparsers(dest="cmd")

    ask = sub.add_parser("ask")
    ask.add_argument("question", type=str)
    ask.add_argument("--live", action="store_true", help="Use live Wikipedia override")

    chat = sub.add_parser("chat")
    chat.add_argument("--live", action="store_true", help="Use live Wikipedia override")

    args = p.parse_args()

    if args.cmd is None:
        args.cmd = "chat"

    if args.cmd == "ask":
        print(_ask(args.question, args.live))
        return 0

    if args.cmd == "chat":
        try:
            while True:
                q = input("flux> ").strip()
                if not q:
                    continue
                if q.lower() in {"exit", "quit"}:
                    break
                print(_ask(q, args.live))
        except KeyboardInterrupt:
            print("")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
