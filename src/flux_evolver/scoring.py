from __future__ import annotations

import json
from difflib import SequenceMatcher
from typing import Any


def _as_json(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True)
    except TypeError:
        return str(value)


def score_value(predicted: Any, target: Any) -> float:
    if predicted is None:
        return float("inf")

    if isinstance(target, (list, tuple)) and isinstance(predicted, (list, tuple)):
        if len(target) == 0:
            return 0.0 if len(predicted) == 0 else float("inf")
        length_penalty = abs(len(target) - len(predicted)) * 1.0
        paired = zip(predicted, target)
        distances = [score_value(p, t) for p, t in paired]
        if not distances:
            return length_penalty
        return (sum(distances) / len(distances)) + length_penalty
    if isinstance(target, (list, tuple)) or isinstance(predicted, (list, tuple)):
        return float("inf")

    if isinstance(target, (int, float)) and isinstance(predicted, (int, float)):
        return abs(float(predicted) - float(target))

    if isinstance(target, str) and isinstance(predicted, str):
        if target == predicted:
            return 0.0
        ratio = SequenceMatcher(a=predicted, b=target).ratio()
        return max(0.0, 1.0 - ratio)

    if isinstance(target, (int, float)) and isinstance(predicted, str):
        try:
            return abs(float(predicted) - float(target))
        except ValueError:
            return float("inf")

    if isinstance(target, str) and not isinstance(predicted, str):
        predicted_str = str(predicted)
        if predicted_str == target:
            return 0.0
        ratio = SequenceMatcher(a=predicted_str, b=target).ratio()
        return max(0.0, 1.0 - ratio)

    if predicted == target:
        return 0.0

    ratio = SequenceMatcher(a=_as_json(predicted), b=_as_json(target)).ratio()
    return max(0.0, 1.0 - ratio)


def is_perfect_score(score: float) -> bool:
    return score <= 1e-12
