import argparse
import json
import sys
import urllib.request
from typing import Dict

from .config import BACKEND_PORT


def _post(path: str, payload: Dict):
    url = f"http://127.0.0.1:{BACKEND_PORT}{path}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get(path: str):
    url = f"http://127.0.0.1:{BACKEND_PORT}{path}"
    with urllib.request.urlopen(url, timeout=15) as resp:
        return resp.read().decode("utf-8")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--session", default="default")
    sub = p.add_subparsers(dest="cmd")

    ask = sub.add_parser("ask")
    ask.add_argument("question")
    ask.add_argument("--grade", type=int, default=10)
    ask.add_argument("--refresh", action="store_true")

    train = sub.add_parser("train")
    train.add_argument("--file", default="")
    train.add_argument("--line", action="append", default=[])
    train.add_argument("--dim", type=int, default=200)
    train.add_argument("--max-sources", type=int, default=1)
    train.add_argument("--workers", type=int, default=6)
    train.add_argument("--full", action="store_true")
    train.add_argument("--word2vec", action="store_true")
    train.add_argument("--grade", type=int, default=10)

    cfg = sub.add_parser("config")
    cfg.add_argument("--params", default="{}")

    args = p.parse_args()

    if args.cmd == "ask":
        payload = {
            "question": args.question,
            "refresh": args.refresh,
            "grade_level": args.grade,
            "session_id": args.session,
        }
        res = _post("/ask", payload)
        print(res.get("answer", ""))
        return

    if args.cmd == "train":
        questions = []
        if args.file:
            with open(args.file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        questions.append(line)
        for line in args.line:
            line = line.strip()
            if line:
                questions.append(line)
        if not questions:
            print("Provide --file or --line for training.")
            sys.exit(1)
        payload = {
            "questions": questions,
            "dim": args.dim,
            "max_sources": args.max_sources,
            "workers": args.workers,
            "full": args.full,
            "use_word2vec": args.word2vec,
            "grade_level": args.grade,
            "session_id": args.session,
        }
        res = _post("/train", payload)
        print(json.dumps(res, indent=2))
        return

    if args.cmd == "config":
        try:
            params = json.loads(args.params)
        except json.JSONDecodeError:
            print("--params must be valid JSON")
            sys.exit(1)
        res = _post("/config", {"session_id": args.session, "nlp_params": params})
        print(json.dumps(res, indent=2))
        return

    p.print_help()


if __name__ == "__main__":
    main()
