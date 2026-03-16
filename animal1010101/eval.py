from __future__ import annotations

import json
from pathlib import Path

from animal1010101.algorithm import simplify
from animal1010101.engine import LexicalEngine
from animal1010101.simple_qa import synthesize_answer


def load_questions(base_dir: Path) -> list[dict]:
    path = base_dir / "eval_questions.json"
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_one(question: dict, engine: LexicalEngine, auto_learn: bool) -> dict:
    q = question["question"]
    simplified = simplify(q, engine)
    if auto_learn and simplified.tokens:
        for t in simplified.tokens:
            engine.learn(t)
        simplified = simplify(q, engine)

    synthesized = synthesize_answer(simplified).lower()
    expect_any = [w.lower() for w in question.get("expect_any", [])]
    expect_prime = question.get("expect_prime")

    ok_any = True
    if expect_any:
        ok_any = any(w in synthesized for w in expect_any)

    ok_prime = True
    if expect_prime:
        ok_prime = any(enc.startswith(expect_prime) for enc in simplified.encodings)

    passed = ok_any and ok_prime
    return {
        "question": q,
        "synthesized": synthesized,
        "passed": passed,
        "ok_any": ok_any,
        "ok_prime": ok_prime,
    }


def run(auto_learn: bool = False) -> int:
    base_dir = Path(__file__).resolve().parent
    engine = LexicalEngine(base_dir)
    questions = load_questions(base_dir)
    results = [evaluate_one(q, engine, auto_learn) for q in questions]

    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"[{status}] {r['question']}")
        if not r["passed"]:
            print(f"  synthesized: {r['synthesized']}")
    print(f"\nScore: {passed}/{total}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(run())
