from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def compute_core_hashes(core_dir: Path) -> Dict[str, str]:
    hashes: Dict[str, str] = {}
    for file in core_dir.glob("*.py"):
        hashes[file.name] = _hash_file(file)
    return hashes


def load_hashes(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_hashes(path: Path, hashes: Dict[str, str]) -> None:
    path.write_text(json.dumps(hashes, indent=2), encoding="utf-8")


def verify_core_hashes(core_dir: Path, cache_path: Path) -> None:
    current = compute_core_hashes(core_dir)
    cached = load_hashes(cache_path)
    if not cached:
        save_hashes(cache_path, current)
        return
    for name, digest in current.items():
        if cached.get(name) != digest:
            raise RuntimeError(f"Immutable core file changed: {name}")
