from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List


@dataclass(frozen=True)
class TrainingSample:
    key: Any
    value: Any


@dataclass
class Gene:
    param_id: int
    strength: float

    def clamp(self) -> None:
        self.strength = max(0.0, min(1.0, self.strength))


@dataclass
class Genome:
    genes: List[Gene]


@dataclass
class Agent:
    id: int
    genome: Genome
    score: float = 0.0
    accuracy: float = 0.0


@dataclass
class EvolutionConfig:
    population_size: int = 100
    genome_length: int = 8
    param_count: int = 1000
    numeric_param_count: int = 500
    text_param_count: int = 500
    domain: str = "auto"
    mutation_rate: float = 0.2
    mutation_strength: float = 0.35
    elite_fraction: float = 0.1
    top_k: int = 10
    selection_strategy: str = "roulette"
    mutation_pressure: bool = True
    stagnation_generations: int = 20
    accuracy_target: float = 1.0
    max_generations: int = 500
    tolerance: float = 0.0
    seed: int = 42


@dataclass
class TrainingResult:
    best_agent: Agent
    generations: int
    converged: bool
    history: List[float] = field(default_factory=list)
