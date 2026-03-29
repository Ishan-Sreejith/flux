from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

from .models import Agent, AgentMeta, Evaluation, EvolutionConfig, Gene, Genome, TrainingResult, TrainingSample
from .parameters import build_parameter_library, filter_param_ids, parameter_by_id
from .scoring import is_perfect_score, score_value


INHERITANCE_STRATEGIES = ("dominant", "recessive", "experimental")


@dataclass
class ExecutionResult:
    value: Any
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None and self.value is not None


class EvolutionRunner:
    def __init__(self, config: EvolutionConfig, rng: Optional[random.Random] = None) -> None:
        self.config = config
        self.rng = rng or random.Random(config.seed)
        self.params = build_parameter_library(config.library_size)
        self.allowed_param_ids = self._build_allowed_params()
        self._next_agent_id = 1

    def _build_allowed_params(self) -> List[int]:
        params = self.params
        allowed = filter_param_ids(params, self.config.mode)
        min_id = max(1, self.config.param_min)
        max_id = min(self.config.library_size, self.config.param_max)
        allowed = [pid for pid in allowed if min_id <= pid <= max_id]
        if not allowed:
            allowed = [pid for pid in filter_param_ids(params, "all") if min_id <= pid <= max_id]
        return sorted(set(allowed))

    def _clamp_param_id(self, param_id: int) -> int:
        if param_id in self.allowed_param_ids:
            return param_id
        closest = min(self.allowed_param_ids, key=lambda pid: abs(pid - param_id))
        return closest

    def _next_id(self) -> int:
        agent_id = self._next_agent_id
        self._next_agent_id += 1
        return agent_id

    def create_random_gene(self, inheritance: Optional[str] = None) -> Gene:
        strategy = inheritance or self.rng.choice(INHERITANCE_STRATEGIES)
        gene = Gene(
            param_id=self.rng.choice(self.allowed_param_ids),
            randomness=max(0.0, min(1.0, self.config.initial_randomness + self.rng.uniform(-0.1, 0.1))),
            intensity=self.rng.random(),
            inheritance=strategy,
        )
        gene.clamp()
        gene.param_id = self._clamp_param_id(gene.param_id)
        return gene

    def create_random_genome(self, length: Optional[int] = None, inheritance: Optional[str] = None) -> Genome:
        target = length or self.config.initial_genome_length
        genes = [self.create_random_gene(inheritance=inheritance) for _ in range(target)]
        genome = Genome(genes=genes, library_size=self.config.library_size)
        genome.clamp()
        return genome

    def create_random_meta(self) -> AgentMeta:
        meta = AgentMeta(
            speed_weight=self.rng.random(),
            inheritance_strategy=self.rng.choice(INHERITANCE_STRATEGIES),
        )
        meta.clamp()
        return meta

    def create_random_agent(self) -> Agent:
        meta = self.create_random_meta()
        genome = self.create_random_genome(inheritance=meta.inheritance_strategy)
        return Agent(id=self._next_id(), genome=genome, meta=meta)

    def execute_genome(self, key: Any, genome: Genome, agent_id: int, sample_index: int) -> ExecutionResult:
        local_seed = (self.config.seed + agent_id * 1000003 + sample_index * 101) & 0xFFFFFFFF
        local_rng = random.Random(local_seed)
        value: Any = key
        for gene in genome.genes:
            try:
                param = parameter_by_id(self.params, gene.param_id)
                value = param.apply(value, gene, local_rng)
                if value is None:
                    return ExecutionResult(value=None, error="null result")
            except Exception as exc:
                return ExecutionResult(value=None, error=str(exc))
        return ExecutionResult(value=value, error=None)

    def evaluate_agent(self, agent: Agent, samples: List[TrainingSample]) -> Evaluation:
        total_distance = 0.0
        for idx, sample in enumerate(samples):
            result = self.execute_genome(sample.key, agent.genome, agent.id, idx)
            if not result.ok:
                return Evaluation(score=float("inf"), distance=float("inf"), efficiency_penalty=0.0, zero=True, error=result.error)
            total_distance += score_value(result.value, sample.value)
        distance = total_distance / max(1, len(samples))
        efficiency_penalty = agent.meta.speed_weight * (len(agent.genome.genes) / max(1, self.config.max_genome_length))
        score = distance + efficiency_penalty
        return Evaluation(score=score, distance=distance, efficiency_penalty=efficiency_penalty, zero=False, error=None)

    def _inheritance_bias(self, meta_a: AgentMeta, meta_b: AgentMeta) -> float:
        score_map = {"dominant": 0.35, "experimental": 0.0, "recessive": -0.35}
        bias = 0.5 + (score_map.get(meta_a.inheritance_strategy, 0.0) - score_map.get(meta_b.inheritance_strategy, 0.0))
        return max(0.1, min(0.9, bias))

    def crossover(self, parent_a: Agent, parent_b: Agent) -> Genome:
        bias = self._inheritance_bias(parent_a.meta, parent_b.meta)
        min_len = min(len(parent_a.genome.genes), len(parent_b.genome.genes), self.config.max_genome_length)
        max_len = max(len(parent_a.genome.genes), len(parent_b.genome.genes), self.config.min_genome_length)
        if max_len < min_len:
            max_len = min_len
        target_len = self.rng.randint(self.config.min_genome_length, self.config.max_genome_length)
        target_len = max(min_len, min(max_len, target_len))
        genes: List[Gene] = []
        for idx in range(target_len):
            source = parent_a if self.rng.random() < bias else parent_b
            source_gene = source.genome.genes[idx % len(source.genome.genes)]
            genes.append(
                Gene(
                    param_id=source_gene.param_id,
                    randomness=source_gene.randomness,
                    intensity=source_gene.intensity,
                    inheritance=source_gene.inheritance,
                )
            )
        genome = Genome(genes=genes, library_size=self.config.library_size)
        genome.clamp()
        return genome

    def mutate_genome(self, genome: Genome) -> Genome:
        for gene in genome.genes:
            if self.rng.random() < self.config.mutation_rate:
                offset = int(round(self.rng.gauss(0, 1) * self.config.mutation_volatility * 5))
                gene.param_id = max(1, min(genome.library_size, gene.param_id + offset))
                gene.param_id = self._clamp_param_id(gene.param_id)
                gene.randomness += self.rng.gauss(0, 0.25) * self.config.mutation_volatility
                gene.intensity += self.rng.gauss(0, 0.25) * self.config.mutation_volatility
                if self.rng.random() < 0.1:
                    gene.inheritance = self.rng.choice(INHERITANCE_STRATEGIES)

        if self.rng.random() < self.config.mutation_rate * 0.5:
            if len(genome.genes) < self.config.max_genome_length:
                genome.genes.append(self.create_random_gene())
        if self.rng.random() < self.config.mutation_rate * 0.5:
            if len(genome.genes) > self.config.min_genome_length:
                drop_index = self.rng.randrange(len(genome.genes))
                genome.genes.pop(drop_index)

        genome.clamp()
        for gene in genome.genes:
            gene.param_id = self._clamp_param_id(gene.param_id)
        return genome

    def select_parent(self, population: List[Agent], evaluations: List[Evaluation]) -> Agent:
        candidates = self.rng.sample(list(zip(population, evaluations)), k=min(self.config.tournament_size, len(population)))
        candidates.sort(key=lambda pair: pair[1].score)
        return candidates[0][0]

    def _salvage_genes(self, zeros: List[Agent]) -> List[Gene]:
        salvage: List[Gene] = []
        for agent in zeros:
            if not agent.genome.genes:
                continue
            gene = self.rng.choice(agent.genome.genes)
            salvage.append(
                Gene(
                    param_id=gene.param_id,
                    randomness=gene.randomness,
                    intensity=gene.intensity,
                    inheritance="dominant",
                )
            )
        return salvage

    def _apply_salvage(self, offspring: List[Agent], salvage: List[Gene]) -> None:
        if not offspring:
            return
        for gene in salvage:
            target = self.rng.choice(offspring)
            if not target.genome.genes:
                continue
            slot = self.rng.randrange(len(target.genome.genes))
            target.genome.genes[slot] = Gene(
                param_id=gene.param_id,
                randomness=gene.randomness,
                intensity=gene.intensity,
                inheritance=gene.inheritance,
            )

    @dataclass
    class GenerationResult:
        next_population: List[Agent]
        evaluations: List[Evaluation]
        ranking: List[Tuple[Agent, Evaluation]]

    def step_generation(self, population: List[Agent], samples: List[TrainingSample]) -> "EvolutionRunner.GenerationResult":
        evaluations = [self.evaluate_agent(agent, samples) for agent in population]
        ranking = sorted(zip(population, evaluations), key=lambda pair: pair[1].score)

        survivors = [agent for agent, eval_ in ranking if not eval_.zero]
        zeros = [agent for agent, eval_ in ranking if eval_.zero]
        salvage = self._salvage_genes(zeros)

        if not survivors:
            fresh_population = [self.create_random_agent() for _ in range(self.config.population_size)]
            return self.GenerationResult(
                next_population=fresh_population,
                evaluations=evaluations,
                ranking=ranking,
            )

        elite_count = int(self.config.population_size * self.config.elite_fraction)
        if elite_count == 0:
            elite_count = 1
        elites = [agent for agent, _ in ranking[:elite_count]]

        offspring: List[Agent] = []
        while len(elites) + len(offspring) < self.config.population_size:
            parent_a = self.select_parent(survivors, evaluations)
            parent_b = self.select_parent(survivors, evaluations)
            child_genome = self.crossover(parent_a, parent_b)
            child_genome = self.mutate_genome(child_genome)
            child_meta = AgentMeta(
                speed_weight=self.rng.random(),
                inheritance_strategy=self.rng.choice(INHERITANCE_STRATEGIES),
            )
            child_meta.clamp()
            offspring.append(Agent(id=self._next_id(), genome=child_genome, meta=child_meta))

        self._apply_salvage(offspring, salvage)
        next_population = elites + offspring
        return self.GenerationResult(
            next_population=next_population,
            evaluations=evaluations,
            ranking=ranking,
        )

    def run(self, samples: List[TrainingSample], initial_population: Optional[List[Agent]] = None) -> TrainingResult:
        population = initial_population or [self.create_random_agent() for _ in range(self.config.population_size)]
        history: List[float] = []
        best_agent = population[0]
        best_score = float("inf")
        best_distance = float("inf")
        converged = False

        for generation in range(self.config.max_generations):
            result = self.step_generation(population, samples)
            best_agent, best_eval = result.ranking[0]
            history.append(best_eval.score)
            if best_eval.score < best_score:
                best_score = best_eval.score
                best_distance = best_eval.distance
            if self.config.log_every > 0 and generation % self.config.log_every == 0:
                print(f"Gen {generation:04d} | best={best_eval.score:.6f} | distance={best_eval.distance:.6f}")
            if is_perfect_score(best_eval.distance):
                converged = True
                return TrainingResult(
                    best_agent=best_agent,
                    best_score=best_eval.score,
                    generations=generation + 1,
                    converged=converged,
                    history=history,
                )
            population = result.next_population

        return TrainingResult(
            best_agent=best_agent,
            best_score=best_score,
            generations=self.config.max_generations,
            converged=converged,
            history=history,
        )


def format_algorithm_map(genome: Genome, params: Optional[List[Any]] = None) -> str:
    if params is None:
        params = build_parameter_library(genome.library_size)
    lines = ["Complete Algorithm Map:"]
    for idx, gene in enumerate(genome.genes, start=1):
        param = parameter_by_id(params, gene.param_id)
        lines.append(
            f"{idx:02d}. Param_{gene.param_id:03d} ({param.name}) "
            f"randomness={gene.randomness:.3f} intensity={gene.intensity:.3f} inheritance={gene.inheritance}"
        )
    return "\n".join(lines)
