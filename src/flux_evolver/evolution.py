from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, List

from .models import Agent, EvolutionConfig, Gene, Genome, TrainingResult, TrainingSample
from .parameters import build_parameter_pools, parameter_by_id
from .scoring import accuracy_from_scores, score_value


@dataclass
class ExecutionResult:
    value: Any
    ok: bool


class EvolutionEngine:
    def __init__(self, config: EvolutionConfig) -> None:
        self.config = config
        self.rng = random.Random(config.seed)
        self.numeric_params, self.text_params = build_parameter_pools(
            config.numeric_param_count, config.text_param_count
        )
        self.params = self.numeric_params
        self.domain = "numeric"
        self._next_id = 1
        if config.domain in ("numeric", "text"):
            self.set_domain(config.domain)

    def _next_agent_id(self) -> int:
        agent_id = self._next_id
        self._next_id += 1
        return agent_id

    def create_random_gene(self) -> Gene:
        return Gene(
            param_id=self.rng.randint(1, len(self.params)),
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

    def _infer_domain(self, samples: List[TrainingSample]) -> str:
        def is_text(item: Any) -> bool:
            if isinstance(item, str):
                return True
            if isinstance(item, list) and any(isinstance(v, str) for v in item):
                return True
            if isinstance(item, dict):
                return any(isinstance(v, str) for v in item.values())
            return False

        for sample in samples:
            if is_text(sample.key) or is_text(sample.value):
                return "text"
        return "numeric"

    def set_domain(self, domain: str) -> None:
        if domain not in ("numeric", "text"):
            domain = "numeric"
        self.domain = domain
        self.params = self.text_params if domain == "text" else self.numeric_params

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

    def evolve_generation(self, agents: List[Agent], samples: List[TrainingSample], mutation_rate: float) -> List[Agent]:
        for agent in agents:
            self.evaluate_agent(agent, samples)
        agents.sort(key=lambda a: (a.score, len(a.genome.genes)))

        elite_count = max(1, int(len(agents) * self.config.elite_fraction))
        elites = agents[:elite_count]
        top_k = agents[: max(1, min(self.config.top_k, len(agents)))]
        gene_pool = [gene for agent in top_k for gene in agent.genome.genes]

        next_gen: List[Agent] = []
        for agent in elites:
            next_gen.append(Agent(id=self._next_agent_id(), genome=Genome(genes=[Gene(g.param_id, g.strength) for g in agent.genome.genes])))

        def select_parent() -> Agent:
            if self.config.selection_strategy == "tournament":
                contenders = self.rng.sample(agents, k=min(5, len(agents)))
                return min(contenders, key=lambda a: a.score)
            weights = [1.0 / (a.score + 1e-6) for a in agents]
            total = sum(weights)
            pick = self.rng.random() * total
            acc = 0.0
            for agent, weight in zip(agents, weights):
                acc += weight
                if acc >= pick:
                    return agent
            return agents[0]

        while len(next_gen) < self.config.population_size:
            parent_a = select_parent()
            parent_b = select_parent()
            new_genes: List[Gene] = []
            for idx, gene in enumerate(parent_a.genome.genes):
                donor = gene
                if idx < len(parent_b.genome.genes) and self.rng.random() < 0.5:
                    donor = parent_b.genome.genes[idx]
                if gene_pool and self.rng.random() < 0.4:
                    donor = self.rng.choice(gene_pool)
                gene = Gene(donor.param_id, donor.strength)
                if self.rng.random() < mutation_rate:
                    if self.rng.random() < 0.5:
                        gene.param_id = self.rng.randint(1, len(self.params))
                    gene.strength = min(1.0, max(0.0, gene.strength + self.rng.uniform(-self.config.mutation_strength, self.config.mutation_strength)))
                new_genes.append(gene)
            next_gen.append(Agent(id=self._next_agent_id(), genome=Genome(genes=new_genes)))

        return next_gen

    def train(self, samples: List[TrainingSample]) -> TrainingResult:
        domain = self.config.domain
        if domain == "auto":
            domain = self._infer_domain(samples)
        self.set_domain(domain)
        agents = self.create_population()
        history: List[float] = []
        best_agent = agents[0]
        mutation_rate = self.config.mutation_rate
        best_score = float("inf")
        stagnation = 0
        for generation in range(self.config.max_generations):
            agents = self.evolve_generation(agents, samples, mutation_rate)
            best_agent = min(agents, key=lambda a: (a.score, len(a.genome.genes)))
            history.append(best_agent.accuracy)
            if best_agent.score < best_score:
                best_score = best_agent.score
                stagnation = 0
                mutation_rate = max(0.05, mutation_rate * 0.9)
            else:
                stagnation += 1
                if self.config.mutation_pressure and stagnation >= self.config.stagnation_generations:
                    mutation_rate = min(0.6, mutation_rate * 1.25)
                    stagnation = 0
            if best_agent.accuracy >= self.config.accuracy_target:
                return TrainingResult(best_agent=best_agent, generations=generation + 1, converged=True, history=history)
        return TrainingResult(best_agent=best_agent, generations=self.config.max_generations, converged=False, history=history)


def format_algorithm(genome: Genome, params: List[Any]) -> str:
    lines = ["Algorithm Key:"]
    for idx, gene in enumerate(genome.genes, start=1):
        param = parameter_by_id(params, gene.param_id)
        lines.append(f"{idx:02d}. {param.name} (param={gene.param_id}) strength={gene.strength:.3f}")
    return "\n".join(lines)
