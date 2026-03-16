from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
from typing import Callable


def load_answer_fn(path: Path) -> Callable[[str, list], str]:
    spec = importlib.util.spec_from_file_location(f"brain_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.answer


def main() -> None:
    p = argparse.ArgumentParser(description="Manual Turing-style A/B check")
    p.add_argument("--a", required=True, help="Path to variant A brain.py")
    p.add_argument("--b", required=True, help="Path to variant B brain.py")
    p.add_argument("--prompt", required=True, help="Prompt to compare")
    args = p.parse_args()

    fn_a = load_answer_fn(Path(args.a))
    fn_b = load_answer_fn(Path(args.b))
    prompt = args.prompt

    print("=== Variant X ===")
    print(fn_a(prompt, []))
    print("\n=== Variant Y ===")
    print(fn_b(prompt, []))
    print("\nHuman judge: decide which response is better / more human-like.")


if __name__ == "__main__":
    main()

