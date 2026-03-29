from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, List

from .models import Agent, EvolutionConfig, Gene, Genome, TrainingResult, TrainingSample
from .parameters import build_parameter_library, parameter_by_id
from .scoring import accuracy_from_scores, score_value


@dataclass
class ExecutionResult:
    value: Any
    ok: bool


class EvolutionEngine:
    def __init__(self, config: EvolutionConfig) -> None:
        self.config = config
        self.rng = random.Random(config.seed)
        self.params = build_parameter_library(config.param_count)
        self._next_id = 1

    def _next_agent_id(self) -> int:
        agent_id = self._next_id
        self._next_id += 1
        return agent_id

    def create_random_gene(self) -> Gene:
        return Gene(
            param_id=self.rng.randint(1, self.config.param_count),
            strength=self.rng.random(),
        )

    def create_random_genome(self) -> Genome:
        return Genome(genes=[self.create_random_gene() for _ in range(self.config.genome_length)])

    def create_population(self) -> List[Agent]:
        return [Agent(id=self._next_agent_id(), genome=self.create_random_genome()) for _ in range(self.config.population_size)]

    def execute_genome(self, key: Any, genome: Genome) -> ExecutionResult:
        value = key
        for gene in genome.genes:
            try:
                param = parameter_by_id(self.params, gene.param_id)
                value = param.apply(value, gene)
            except Exception:
                return ExecutionResult(value=None, ok=False)
        return ExecutionResult(value=value, ok=True)

    def evaluate_agent(self, agent: Agent, samples: List[TrainingSample]) -> None:
        scores: List[float] = []
        for sample in samples:
            result = self.execute_genome(sample.key, agent.genome)
            if not result.ok:
                scores.append(float("inf"))
                continue
            scores.append(score_value(result.value, sample.value))
        agent.score = sum(scores) / len(scores)
        agent.accuracy = accuracy_from_scores(scores, self.config.tolerance)

    def evolve_generation(self, agents: List[Agent], samples: List[TrainingSample]) -> List[Agent]:
        for agent in agents:
            self.evaluate_agent(agent, samples)
        agents.sort(key=lambda a: (a.score, len(a.genome.genes)))

        survivors = agents[: max(1, len(agents) // 2)]
        top10 = agents[: min(10, len(agents))]
        gene_pool = [gene for agent in top10 for gene in agent.genome.genes]

        next_gen: List[Agent] = []
        for agent in survivors:
            next_gen.append(Agent(id=self._next_agent_id(), genome=Genome(genes=[Gene(g.param_id, g.strength) for g in agent.genome.genes])))

        while len(next_gen) < self.config.population_size:
            parent = self.rng.choice(survivors)
            new_genes: List[Gene] = []
            for gene in parent.genome.genes:
                if gene_pool and self.rng.random() < 0.5:
                    donor = self.rng.choice(gene_pool)
                    gene = Gene(donor.param_id, donor.strength)
                if self.rng.random() < self.config.mutation_rate:
                    if self.rng.random() < 0.5:
                        gene.param_id = self.rng.randint(1, self.config.param_count)
                    gene.strength = min(1.0, max(0.0, gene.strength + self.rng.uniform(-self.config.mutation_strength, self.config.mutation_strength)))
                new_genes.append(gene)
            next_gen.append(Agent(id=self._next_agent_id(), genome=Genome(genes=new_genes)))

        return next_gen

    def train(self, samples: List[TrainingSample]) -> TrainingResult:
        agents = self.create_population()
        history: List[float] = []
        best_agent = agents[0]
        for generation in range(self.config.max_generations):
            agents = self.evolve_generation(agents, samples)
            best_agent = min(agents, key=lambda a: (a.score, len(a.genome.genes)))
            history.append(best_agent.accuracy)
            if best_agent.accuracy >= self.config.accuracy_target:
                return TrainingResult(best_agent=best_agent, generations=generation + 1, converged=True, history=history)
        return TrainingResult(best_agent=best_agent, generations=self.config.max_generations, converged=False, history=history)


def format_algorithm(genome: Genome, params: List[Any]) -> str:
    lines = ["Algorithm Key:"]
    for idx, gene in enumerate(genome.genes, start=1):
        param = parameter_by_id(params, gene.param_id)
        lines.append(f"{idx:02d}. {param.name} (param={gene.param_id}) strength={gene.strength:.3f}")
    return "\n".join(lines)

