from __future__ import annotations

from typing import Any


def score_value(predicted: Any, target: Any) -> float:
    if isinstance(target, list) and isinstance(predicted, list):
        if not target:
            return 0.0 if not predicted else float("inf")
        paired = zip(predicted, target)
        scores = [score_value(p, t) for p, t in paired]
        return sum(scores) / len(scores)
    if isinstance(target, (int, float)) and isinstance(predicted, (int, float)):
        return abs(float(predicted) - float(target))
    if isinstance(target, str) and isinstance(predicted, str):
        return 0.0 if predicted == target else 1.0
    return 0.0 if predicted == target else 1.0


def accuracy_from_scores(scores: list[float], tolerance: float) -> float:
    if not scores:
        return 0.0
    hits = sum(1 for s in scores if s <= tolerance)
    return hits / len(scores)

