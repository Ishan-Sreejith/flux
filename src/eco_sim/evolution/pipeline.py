from __future__ import annotations

import random
from typing import List, Tuple

from eco_sim.agents.plasticity import crossover, mutate_genome
from eco_sim.models import AgentKind, AgentState, Genome, SimMetrics


class EvolutionPipeline:
    def __init__(self, rng: random.Random) -> None:
        self.rng = rng
        self.generation: int = 0
        self.population: List[Genome] = []
        self.fitness_history: List[float] = []

    def evaluate_fitness(self, agent: AgentState) -> float:
        if not agent.alive:
            return 0.0
        base_fitness = agent.energy + agent.age_ticks * 0.1
        if agent.kind == AgentKind.PREDATOR:
            base_fitness *= 1.2
        return base_fitness

    def select_parents(self, genomes: List[Genome], fitness_scores: List[float], count: int) -> List[Genome]:
        indexed = list(zip(genomes, fitness_scores))
        indexed.sort(key=lambda x: x[1], reverse=True)
        elite = [g for g, _ in indexed[:max(1, count // 4)]]
        tournament_picks = []
        for _ in range(count - len(elite)):
            candidates = self.rng.sample(indexed, min(5, len(indexed)))
            winner = max(candidates, key=lambda x: x[1])
            tournament_picks.append(winner[0])
        return elite + tournament_picks

    def evolve_generation(self, agents: List[AgentState]) -> List[Genome]:
        fitness_scores = [self.evaluate_fitness(a) for a in agents]
        if not fitness_scores or max(fitness_scores) == 0:
            return [
                Genome(input_size=7, hidden_size=0, output_size=4, weights=[[0.0] * 7] * 4, sensor_range=4)
                for _ in agents
            ]

        parents = self.select_parents([], fitness_scores, len(agents))
        offspring = []
        for _ in range(len(agents)):
            p1, p2 = self.rng.sample(parents, 2) if len(parents) >= 2 else (parents[0], parents[0])
            child = crossover(p1, p2, self.rng)
            child = mutate_genome(child, self.rng)
            offspring.append(child)

        self.generation += 1
        best_fitness = max(fitness_scores) if fitness_scores else 0.0
        self.fitness_history.append(best_fitness)
        return offspring

    def get_metrics(self, agents: List[AgentState]) -> SimMetrics:
        fitness_scores = [self.evaluate_fitness(a) for a in agents if a.alive]
        best = max(fitness_scores) if fitness_scores else 0.0
        mean = sum(fitness_scores) / len(fitness_scores) if fitness_scores else 0.0
        return SimMetrics(
            generation=self.generation,
            best_fitness=best,
            mean_fitness=mean,
            survivor_count=len(fitness_scores),
        )

