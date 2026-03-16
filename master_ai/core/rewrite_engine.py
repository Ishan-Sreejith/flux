from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Dict, List


IMMUTABLE_FILES = {
    "lifecycle.py",
    "internet_access.py",
    "rewrite_engine.py",
    "core_access.py",
    "backup_manager.py",
}


def can_edit(path: Path) -> bool:
    return path.name not in IMMUTABLE_FILES


def mutate_config(config: Dict[str, float], mutation_rate: float = 0.05) -> Dict[str, float]:
    out = dict(config)
    for k in out:
        if random.random() < mutation_rate:
            out[k] = random.uniform(0.1, 2.0)
    return out


def adjust_config(config: Dict[str, float], deltas: Dict[str, float]) -> Dict[str, float]:
    out = dict(config)
    for k, v in deltas.items():
        if k in out:
            out[k] = min(2.0, max(0.1, out[k] + v))
    return out


def write_config(path: Path, config: Dict[str, float]) -> None:
    if not can_edit(path):
        raise PermissionError(f"Attempt to edit immutable file: {path}")
    path.write_text(json.dumps(config, indent=2), encoding="utf-8")


def crossover(parent_a: Dict[str, float], parent_b: Dict[str, float]) -> Dict[str, float]:
    keys = list(parent_a.keys())
    random.shuffle(keys)
    split = len(keys) // 2
    out = {}
    for k in keys[:split]:
        out[k] = parent_a[k]
    for k in keys[split:]:
        out[k] = parent_b[k]
    return out


def clamp_config(config: Dict[str, float]) -> Dict[str, float]:
    return {k: min(2.0, max(0.1, float(v))) for k, v in config.items()}

