from __future__ import annotations

import shutil
from pathlib import Path


def prepare_worker_sandbox(
    project_root: Path, sandbox_root: Path, worker_id: int, reset: bool = False
) -> Path:
    worker_dir = sandbox_root / f"worker_{worker_id}"
    if reset and worker_dir.exists():
        shutil.rmtree(worker_dir)
    if worker_dir.exists():
        return worker_dir

    worker_dir.mkdir(parents=True, exist_ok=True)
    for entry in project_root.iterdir():
        if entry.name in {".git", ".venv", "__pycache__", "sandboxes"}:
            continue
        target = worker_dir / entry.name
        if entry.is_dir():
            shutil.copytree(entry, target)
        else:
            shutil.copy2(entry, target)
    return worker_dir


def reset_worker_sandbox(project_root: Path, sandbox_root: Path, worker_id: int) -> Path:
    worker_dir = sandbox_root / f"worker_{worker_id}"
    if worker_dir.exists():
        shutil.rmtree(worker_dir)
    worker_dir.mkdir(parents=True, exist_ok=True)

    for entry in project_root.iterdir():
        if entry.name in {".git", ".venv", "__pycache__", "sandboxes"}:
            continue
        target = worker_dir / entry.name
        if entry.is_dir():
            shutil.copytree(entry, target)
        else:
            shutil.copy2(entry, target)
    return worker_dir


def checkpoint_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def restore_file(path: Path, snapshot: str) -> None:
    path.write_text(snapshot, encoding="utf-8")
