from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional, Sequence


@dataclass(frozen=True)
class TrainingSample:
    key: Any
    value: Any


@dataclass
class Gene:
    param_id: int
    randomness: float
    intensity: float
    inheritance: str

    def clamp(self) -> None:
        self.randomness = max(0.0, min(1.0, self.randomness))
        self.intensity = max(0.0, min(1.0, self.intensity))


@dataclass
class Genome:
    genes: List[Gene]
    library_size: int

    def clamp(self) -> None:
        for gene in self.genes:
            gene.clamp()
            gene.param_id = max(1, min(self.library_size, gene.param_id))


@dataclass
class AgentMeta:
    speed_weight: float
    inheritance_strategy: str

    def clamp(self) -> None:
        self.speed_weight = max(0.0, min(1.0, self.speed_weight))


@dataclass
class Agent:
    id: int
    genome: Genome
    meta: AgentMeta


@dataclass
class Evaluation:
    score: float
    distance: float
    efficiency_penalty: float
    zero: bool
    error: Optional[str] = None


@dataclass
class EvolutionConfig:
    population_size: int = 40
    library_size: int = 120
    param_min: int = 1
    param_max: int = 300
    mode: str = "all"
    min_genome_length: int = 4
    max_genome_length: int = 12
    initial_genome_length: int = 8
    max_generations: int = 200
    elite_fraction: float = 0.2
    tournament_size: int = 5
    mutation_rate: float = 0.25
    mutation_volatility: float = 0.35
    initial_randomness: float = 0.25
    seed: int = 42
    log_every: int = 1


@dataclass
class TrainingResult:
    best_agent: Agent
    best_score: float
    generations: int
    converged: bool
    history: List[float] = field(default_factory=list)
