from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import List

from evolver.research import internet_research


BENCHMARKS = [
    {"prompt": "Explain gradient descent in one paragraph.", "must_have": ["gradient", "step"]},
    {"prompt": "What is overfitting? Give one mitigation.", "must_have": ["overfitting", "mitigation"]},
    {"prompt": "Compare supervised and unsupervised learning.", "must_have": ["supervised", "unsupervised"]},
]


@dataclass
class EvalResult:
    score: float
    details: List[str]


def _load_module_from_path(path: Path):
    spec = importlib.util.spec_from_file_location("mutable_brain_runtime", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load mutable module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def evaluate_brain(mutable_file: Path, use_research: bool = True) -> EvalResult:
    module = _load_module_from_path(mutable_file)
    details: List[str] = []
    total = 0.0
    per_item = 1.0 / len(BENCHMARKS)

    for item in BENCHMARKS:
        research = internet_research(item["prompt"], 2) if use_research else []
        output = str(module.answer(item["prompt"], research))
        low = output.lower()
        hits = sum(1 for k in item["must_have"] if k in low)
        earned = per_item * (hits / len(item["must_have"]))
        total += earned
        details.append(f"{item['prompt'][:28]}... => {earned:.2f}")

    return EvalResult(score=round(total, 4), details=details)

