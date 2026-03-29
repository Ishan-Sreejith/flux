from __future__ import annotations

from typing import Any, List, Optional

from eco_sim.models import Event, ReplayFrame


class ReplayBuilder:
    def __init__(self, state: Any) -> None:
        self.state = state
        self.frames: List[ReplayFrame] = []

    def build_frame(self) -> ReplayFrame:
        plant_total = sum(
            cell.plant_energy
            for row in self.state.grid
            for cell in row
        )
        living_prey = sum(
            1 for a in self.state.agents.values()
            if a.alive and a.kind.value == "prey"
        )
        living_predators = sum(
            1 for a in self.state.agents.values()
            if a.alive and a.kind.value == "predator"
        )
        energy_total = sum(
            a.energy for a in self.state.agents.values()
            if a.alive
        )
        return ReplayFrame(
            tick=self.state.tick,
            plant_total=plant_total,
            living_prey=living_prey,
            living_predators=living_predators,
            energy_total=energy_total,
        )

    def record_frame(self) -> None:
        self.frames.append(self.build_frame())

    def get_frame_at_tick(self, tick: int) -> Optional[ReplayFrame]:
        for f in self.frames:
            if f.tick == tick:
                return f
        return None

