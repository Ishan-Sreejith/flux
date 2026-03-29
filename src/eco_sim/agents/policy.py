from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Tuple

from eco_sim.models import ActionType, AgentState


@dataclass
class ActionDecision:
    action_type: ActionType
    vector: Tuple[int, int] = (0, 0)
    confidence: float = 1.0
    predator_near: bool = False
    expected_delta_energy: float = 0.0


def decide_action(agent: AgentState, vec: List[float], rng: random.Random) -> ActionDecision:
    predator_near = vec[1] <= 2.0
    plant_energy = vec[0]

    if agent.curiosity_mode:
        return ActionDecision(
            action_type=ActionType.MOVE,
            vector=rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)]),
            confidence=0.2,
            predator_near=predator_near,
            expected_delta_energy=-0.3,
        )

    if agent.kind.value == "prey":
        if plant_energy > 2.0:
            return ActionDecision(ActionType.EAT, confidence=0.9, predator_near=predator_near, expected_delta_energy=2.0)
        if predator_near:
            return ActionDecision(
                ActionType.MOVE,
                vector=rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)]),
                confidence=0.6,
                predator_near=True,
                expected_delta_energy=-0.3,
            )
        if agent.energy > 24.0:
            return ActionDecision(ActionType.MATE, confidence=0.7, predator_near=predator_near, expected_delta_energy=-6.0)
    else:
        if predator_near:
            return ActionDecision(ActionType.ATTACK, confidence=0.8, predator_near=predator_near, expected_delta_energy=4.0)
        if agent.energy > 26.0:
            return ActionDecision(ActionType.MATE, confidence=0.65, predator_near=predator_near, expected_delta_energy=-6.0)

    return ActionDecision(
        action_type=ActionType.MOVE,
        vector=rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)]),
        confidence=0.5,
        predator_near=predator_near,
        expected_delta_energy=-0.3,
    )

