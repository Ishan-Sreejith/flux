from __future__ import annotations

import math
from typing import List

from eco_sim.models import AgentKind, AgentState


def _distance(a: tuple[int, int], b: tuple[int, int]) -> float:
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return math.sqrt(dx * dx + dy * dy)


def build_sensor_vector(world_state, agent: AgentState) -> List[float]:
    x, y = agent.pos
    cell = world_state.grid[y][x]

    nearest_plant = cell.plant_energy
    nearest_predator_dist = 999.0
    nearest_predator_angle = 0.0
    peer_signal = 0.0

    for other in world_state.agents.values():
        if not other.alive or other.id == agent.id:
            continue
        d = _distance(agent.pos, other.pos)
        if d <= agent.sensor_range:
            if other.kind == agent.kind:
                peer_signal += 1.0
            if other.kind == AgentKind.PREDATOR:
                if d < nearest_predator_dist:
                    nearest_predator_dist = d
                    nearest_predator_angle = math.atan2(other.pos[1] - y, other.pos[0] - x)

    if nearest_predator_dist == 999.0:
        nearest_predator_dist = float(agent.sensor_range + 1)

    return [
        float(nearest_plant),
        float(nearest_predator_dist),
        float(nearest_predator_angle),
        float(agent.energy),
        float(peer_signal),
        float(agent.hormones.dopamine),
        float(agent.hormones.cortisol),
    ]

