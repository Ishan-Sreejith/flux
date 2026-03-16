from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List


class LexiconStore:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.auto_path = base_dir / "lexicon_auto.json"
        self.snap_dir = base_dir / "lexicon_snapshots"
        self.snap_dir.mkdir(exist_ok=True)

    def snapshot(self, reason: str) -> Path:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snap_path = self.snap_dir / f"lexicon_auto_{stamp}.json"
        if self.auto_path.exists():
            shutil.copy2(self.auto_path, snap_path)
        else:
            snap_path.write_text("{}", encoding="utf-8")
        meta_path = self.snap_dir / f"lexicon_auto_{stamp}.meta.json"
        meta = {"reason": reason, "source": str(self.auto_path)}
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        return snap_path

    def list_snapshots(self) -> List[Path]:
        return sorted(self.snap_dir.glob("lexicon_auto_*.json"))

    def latest_snapshot(self) -> Path | None:
        snaps = self.list_snapshots()
        return snaps[-1] if snaps else None

    def rollback(self, snapshot: Path) -> dict:
        data = json.loads(snapshot.read_text(encoding="utf-8"))
        self.auto_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data
