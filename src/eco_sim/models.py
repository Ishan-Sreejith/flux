from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


Vec2 = Tuple[int, int]


class AgentKind(str, Enum):
    PREY = "prey"
    PREDATOR = "predator"


class ActionType(str, Enum):
    MOVE = "move"
    EAT = "eat"
    MATE = "mate"
    ATTACK = "attack"
    IDLE = "idle"


@dataclass
class HormoneState:
    dopamine: float = 0.0
    cortisol: float = 0.0


@dataclass
class BrainGraph:
    input_size: int
    hidden_size: int
    output_size: int
    weights: List[List[float]]


@dataclass
class AgentState:
    id: int
    kind: AgentKind
    pos: Vec2
    energy: float
    age_ticks: int = 0
    alive: bool = True
    sensor_range: int = 4
    hormones: HormoneState = field(default_factory=HormoneState)
    brain: Optional[BrainGraph] = None
    confidence: float = 1.0
    curiosity_mode: bool = False


@dataclass
class GridCell:
    plant_energy: float = 0.0
    max_plant_energy: float = 12.0


@dataclass
class StressEvent:
    kind: str
    duration_ticks: int
    severity: float


@dataclass
class Event:
    tick: int
    kind: str
    agent_id: Optional[int]
    payload: Dict[str, object] = field(default_factory=dict)


@dataclass
class ReplayFrame:
    tick: int
    plant_total: float
    living_prey: int
    living_predators: int
    energy_total: float


@dataclass
class WorldConfig:
    width: int = 20
    height: int = 20
    initial_prey: int = 20
    initial_predators: int = 6
    initial_agent_energy: float = 20.0
    base_plant_regrow: float = 0.6
    movement_cost: float = 0.3
    eat_gain: float = 4.0
    attack_gain: float = 8.0
    mate_cost: float = 6.0
    plant_seed_density: float = 0.3
    max_ticks: int = 500


@dataclass
class CausalRecord:
    tick: int
    expected_delta_energy: float
    actual_delta_energy: float


@dataclass
class SimMetrics:
    generation: int
    best_fitness: float
    mean_fitness: float
    survivor_count: int


@dataclass
class Genome:
    input_size: int
    hidden_size: int
    output_size: int
    weights: List[List[float]]
    sensor_range: int

