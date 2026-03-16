from __future__ import annotations

import json
from pathlib import Path
from typing import Dict


def load_weights(path: Path) -> Dict[str, Dict[str, float]]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_weights(path: Path, data: Dict[str, Dict[str, float]]) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
