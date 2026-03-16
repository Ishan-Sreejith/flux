from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, List

from animal1010101.algorithm import simplify
from animal1010101.engine import LexicalEngine
from animal1010101.weights import save_weights


TRAITS = [
    "negative",
    "edible",
    "sweet",
    "carnivorous",
    "herbivorous",
    "domesticated",
    "wild",
    "aquatic",
    "flying",
    "nocturnal",
    "social",
    "aggressive",
    "dangerous",
    "tool-like",
    "artificial",
    "natural",
    "friendly",
    "large",
    "small",
    "intelligent",
    "agentic",
]

PRIMES = ["Animal", "Object", "Action", "Feeling", "Food"]


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def dot(w: Dict[str, float], x: Dict[str, float]) -> float:
    return sum(w.get(k, 0.0) * x.get(k, 0.0) for k in x.keys()) + w.get("bias", 0.0)


def train(dataset_path: Path, out_path: Path, epochs: int = 20, lr: float = 0.4) -> None:
    base_dir = Path(__file__).resolve().parent
    engine = LexicalEngine(base_dir)
    data = json.loads(dataset_path.read_text(encoding="utf-8"))

    weights: Dict[str, Dict[str, float]] = {}
    for t in TRAITS + [f"prime:{p}" for p in PRIMES]:
        weights[t] = {"bias": 0.0}

    for _ in range(epochs):
        for row in data:
            q = row["question"]
            simplified = simplify(q, engine)
            x = simplified.parameters

            # Trait classification
            gold = set(row.get("traits", []))
            for t in TRAITS:
                y = 1.0 if t in gold else 0.0
                pred = sigmoid(dot(weights[t], x))
                err = y - pred
                for k, v in x.items():
                    weights[t][k] = weights[t].get(k, 0.0) + lr * err * v
                weights[t]["bias"] = weights[t].get("bias", 0.0) + lr * err

            # Prime classification (one-vs-rest)
            prime = row.get("prime")
            for p in PRIMES:
                key = f"prime:{p}"
                y = 1.0 if p == prime else 0.0
                pred = sigmoid(dot(weights[key], x))
                err = y - pred
                for k, v in x.items():
                    weights[key][k] = weights[key].get(k, 0.0) + lr * err * v
                weights[key]["bias"] = weights[key].get("bias", 0.0) + lr * err

    save_weights(out_path, weights)


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    train(base_dir / "train_data.json", base_dir / "model_weights.json")
