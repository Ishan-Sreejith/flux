from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from eco_sim.agents.policy import decide_action
from eco_sim.agents.sensors import build_sensor_vector
from eco_sim.awareness.causal import CausalBuffer
from eco_sim.awareness.state import update_confidence_and_curiosity
from eco_sim.models import (
    ActionType,
    AgentKind,
    AgentState,
    Event,
    GridCell,
    StressEvent,
    WorldConfig,
)


@dataclass
class WorldState:
    config: WorldConfig
    rng_seed: int
    tick: int = 0
    agents: Dict[int, AgentState] = field(default_factory=dict)
    grid: List[List[GridCell]] = field(default_factory=list)
    events: List[Event] = field(default_factory=list)
    stressors: List[StressEvent] = field(default_factory=list)
    next_agent_id: int = 1
    causal_buffer: CausalBuffer = field(default_factory=CausalBuffer)

    def __post_init__(self) -> None:
        if not self.grid:
            self.grid = [
                [GridCell() for _ in range(self.config.width)]
                for _ in range(self.config.height)
            ]


class WorldEngine:
    def __init__(self, config: Optional[WorldConfig] = None, seed: int = 7) -> None:
        self.config = config or WorldConfig()
        self.random = random.Random(seed)
        self.state = WorldState(config=self.config, rng_seed=seed)
        self._spawn_initial_population()
        self._seed_plants()

    def _seed_plants(self) -> None:
        for y in range(self.config.height):
            for x in range(self.config.width):
                if self.random.random() < self.config.plant_seed_density:
                    self.state.grid[y][x].plant_energy = self.random.uniform(1.0, 8.0)

    def _spawn_agent(self, kind: AgentKind) -> AgentState:
        x = self.random.randrange(self.config.width)
        y = self.random.randrange(self.config.height)
        agent = AgentState(
            id=self.state.next_agent_id,
            kind=kind,
            pos=(x, y),
            energy=self.config.initial_agent_energy,
        )
        self.state.next_agent_id += 1
        self.state.agents[agent.id] = agent
        self.state.events.append(Event(self.state.tick, "birth", agent.id, {"kind": kind.value}))
        return agent

    def _spawn_initial_population(self) -> None:
        for _ in range(self.config.initial_prey):
            self._spawn_agent(AgentKind.PREY)
        for _ in range(self.config.initial_predators):
            self._spawn_agent(AgentKind.PREDATOR)

    def _regrow_plants(self) -> None:
        modifier = 1.0
        for stress in self.state.stressors:
            if stress.kind == "drought":
                modifier -= 0.5 * stress.severity
        modifier = max(0.1, modifier)
        for row in self.state.grid:
            for cell in row:
                cell.plant_energy = min(
                    cell.max_plant_energy,
                    cell.plant_energy + self.config.base_plant_regrow * modifier,
                )

    def _apply_stressors(self) -> None:
        updated: List[StressEvent] = []
        for stress in self.state.stressors:
            stress.duration_ticks -= 1
            if stress.duration_ticks > 0:
                updated.append(stress)
        self.state.stressors = updated
        if self.random.random() < 0.02:
            stress = StressEvent(
                kind=self.random.choice(["drought", "winter", "predator_spike"]),
                duration_ticks=self.random.randint(20, 80),
                severity=self.random.uniform(0.4, 1.0),
            )
            self.state.stressors.append(stress)
            self.state.events.append(
                Event(
                    tick=self.state.tick,
                    kind="stressor_start",
                    agent_id=None,
                    payload={"kind": stress.kind, "duration": stress.duration_ticks, "severity": stress.severity},
                )
            )
            if stress.kind == "predator_spike":
                extra = max(1, int(stress.severity * 3))
                for _ in range(extra):
                    self._spawn_agent(AgentKind.PREDATOR)

    def _move(self, agent: AgentState, dx: int, dy: int) -> None:
        x, y = agent.pos
        nx = (x + dx) % self.config.width
        ny = (y + dy) % self.config.height
        agent.pos = (nx, ny)
        agent.energy -= self.config.movement_cost
        self.state.events.append(Event(self.state.tick, "move", agent.id, {"to": agent.pos}))

    def _eat(self, agent: AgentState) -> None:
        x, y = agent.pos
        cell = self.state.grid[y][x]
        if agent.kind == AgentKind.PREY:
            amount = min(self.config.eat_gain, cell.plant_energy)
            if amount > 0:
                cell.plant_energy -= amount
                agent.energy += amount
                agent.hormones.dopamine = min(1.0, agent.hormones.dopamine + 0.2)
                self.state.events.append(Event(self.state.tick, "eat", agent.id, {"amount": amount}))

    def _attack(self, predator: AgentState) -> None:
        prey_targets = [
            a
            for a in self.state.agents.values()
            if a.alive and a.kind == AgentKind.PREY and a.pos == predator.pos
        ]
        if not prey_targets:
            return
        prey = self.random.choice(prey_targets)
        prey.alive = False
        prey.energy = 0.0
        predator.energy += self.config.attack_gain
        predator.hormones.dopamine = min(1.0, predator.hormones.dopamine + 0.4)
        self.state.events.append(Event(self.state.tick, "attack", predator.id, {"target": prey.id}))
        self.state.events.append(Event(self.state.tick, "death", prey.id, {"reason": "predated"}))

    def _mate(self, agent: AgentState) -> None:
        if agent.energy < self.config.mate_cost:
            return
        partner = next(
            (
                a
                for a in self.state.agents.values()
                if a.alive and a.id != agent.id and a.kind == agent.kind and a.pos == agent.pos and a.energy >= self.config.mate_cost
            ),
            None,
        )
        if not partner:
            return
        agent.energy -= self.config.mate_cost
        partner.energy -= self.config.mate_cost
        child = self._spawn_agent(agent.kind)
        child.pos = agent.pos
        self.state.events.append(Event(self.state.tick, "mate", agent.id, {"partner": partner.id, "child": child.id}))

    def _decay_and_death(self, agent: AgentState) -> None:
        if agent.energy <= 0 and agent.alive:
            agent.alive = False
            self.state.events.append(Event(self.state.tick, "death", agent.id, {"reason": "starvation"}))

    def step(self) -> None:
        self.state.tick += 1
        self._apply_stressors()
        self._regrow_plants()

        for agent in list(self.state.agents.values()):
            if not agent.alive:
                continue
            before_energy = agent.energy
            vec = build_sensor_vector(self.state, agent)
            action = decide_action(agent, vec, self.random)
            update_confidence_and_curiosity(agent, action)

            if action.action_type == ActionType.MOVE:
                dx, dy = action.vector
                self._move(agent, dx, dy)
            elif action.action_type == ActionType.EAT:
                self._eat(agent)
            elif action.action_type == ActionType.ATTACK:
                self._attack(agent)
            elif action.action_type == ActionType.MATE:
                self._mate(agent)

            if action.predator_near:
                agent.hormones.cortisol = min(1.0, agent.hormones.cortisol + 0.15)
            else:
                agent.hormones.cortisol = max(0.0, agent.hormones.cortisol - 0.05)
            agent.hormones.dopamine = max(0.0, agent.hormones.dopamine - 0.02)

            self.state.causal_buffer.add(
                tick=self.state.tick,
                expected_delta_energy=action.expected_delta_energy,
                actual_delta_energy=agent.energy - before_energy,
            )

            agent.age_ticks += 1
            self._decay_and_death(agent)

    def run(self, ticks: Optional[int] = None) -> WorldState:
        limit = ticks if ticks is not None else self.config.max_ticks
        for _ in range(limit):
            self.step()
        return self.state

