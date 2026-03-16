from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict


def new_run_dir(root: Path) -> Path:
    ts = time.strftime("%Y%m%d_%H%M%S")
    run_dir = root / "reports" / f"run_{ts}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def log_event(run_dir: Path, row: Dict) -> None:
    path = run_dir / "events.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def log_fitness(run_dir: Path, row: Dict) -> None:
    path = run_dir / "fitness.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def write_summary_csv(run_dir: Path, rows: list[Dict]) -> None:
    if not rows:
        return
    path = run_dir / "summary.csv"
    headers = sorted(rows[0].keys())
    with path.open("w", encoding="utf-8") as f:
        f.write(",".join(headers) + "\n")
        for row in rows:
            f.write(",".join(str(row.get(h, "")) for h in headers) + "\n")

