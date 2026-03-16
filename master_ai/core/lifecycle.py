from __future__ import annotations

import shutil
from pathlib import Path


def snapshot(agent_dir: Path, snapshot_dir: Path) -> None:
    if snapshot_dir.exists():
        shutil.rmtree(snapshot_dir)
    shutil.copytree(agent_dir, snapshot_dir)


def restore(agent_dir: Path, snapshot_dir: Path) -> None:
    if not snapshot_dir.exists():
        return
    if agent_dir.exists():
        shutil.rmtree(agent_dir)
    shutil.copytree(snapshot_dir, agent_dir)

