from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EvolverConfig:
    root: Path
    mutable_file: Path
    memory_file: Path
    sandbox_root: Path
    max_research_results: int = 3
    mutation_timeout_sec: int = 25
    worker_generations: int = 10


def default_config(root: Path) -> EvolverConfig:
    return EvolverConfig(
        root=root,
        mutable_file=root / "mutable" / "brain.py",
        memory_file=root / "evolver_memory.json",
        sandbox_root=root / "sandboxes",
    )

