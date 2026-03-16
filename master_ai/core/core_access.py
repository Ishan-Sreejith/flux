from __future__ import annotations

from pathlib import Path

from master_ai.core.rewrite_engine import IMMUTABLE_FILES


def is_immutable(path: Path) -> bool:
    return path.name in IMMUTABLE_FILES

