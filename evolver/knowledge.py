from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List


def _normalize_fact(item: Dict[str, str]) -> str:
    title = str(item.get("title", "")).strip()
    snippet = str(item.get("snippet", "")).strip()
    if not snippet:
        return ""
    return f"{title}: {snippet}" if title else snippet


def append_items(path: Path, topic: str, items: List[Dict[str, str]], max_items: int = 1000) -> None:
    if not items:
        return

    existing = load_items(path, max_items=max_items)
    seen = {str(x.get("fact", "")).strip().lower() for x in existing}

    new_rows = []
    for item in items:
        fact = _normalize_fact(item)
        if not fact:
            continue
        key = fact.lower()
        if key in seen:
            continue
        new_rows.append(
            {
                "ts": int(time.time()),
                "topic": topic[:160],
                "fact": fact,
                "source": str(item.get("source", "")),
                "url": str(item.get("url", "")),
            }
        )
        seen.add(key)

    if not new_rows:
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for row in new_rows:
            f.write(json.dumps(row) + "\n")


    trimmed = load_items(path, max_items=max_items)
    if len(trimmed) >= max_items:
        path.write_text(
            "".join(json.dumps(r) + "\n" for r in trimmed[-max_items:]),
            encoding="utf-8",
        )


def load_items(path: Path, max_items: int = 300) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    rows: List[Dict[str, str]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
                if isinstance(row, dict):
                    rows.append(row)
            except Exception:
                continue
    except Exception:
        return []
    return rows[-max_items:]

