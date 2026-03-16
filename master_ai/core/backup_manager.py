from __future__ import annotations

from pathlib import Path

from master_ai.core.lifecycle import restore, snapshot


def backup(agent_dir: Path, snapshot_dir: Path) -> None:
    snapshot(agent_dir, snapshot_dir)


def recover(agent_dir: Path, snapshot_dir: Path) -> None:
    restore(agent_dir, snapshot_dir)

