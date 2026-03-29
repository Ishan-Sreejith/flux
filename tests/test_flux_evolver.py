import random
import unittest

from flux_evolver.evolution import EvolutionRunner, format_algorithm_map
from flux_evolver.models import Agent, AgentMeta, EvolutionConfig, Gene, Genome, TrainingSample
from flux_evolver.parameters import build_parameter_library
from flux_evolver.scoring import score_value


class TestFluxEvolver(unittest.TestCase):
    def test_parameter_library_size(self):
        params = build_parameter_library(300)
        self.assertEqual(len(params), 300)
        self.assertEqual(params[0].id, 1)
        self.assertEqual(params[-1].id, 300)

    def test_score_numeric(self):
        self.assertEqual(score_value(5, 7), 2.0)
        self.assertEqual(score_value(5.5, 5.5), 0.0)

    def test_score_string(self):
        self.assertEqual(score_value("abc", "abc"), 0.0)
        self.assertGreater(score_value("abc", "ab"), 0.0)

    def test_execute_identity(self):
        config = EvolutionConfig(population_size=1, library_size=10, min_genome_length=1, max_genome_length=1)
        runner = EvolutionRunner(config=config, rng=random.Random(1))
        genome = Genome(genes=[Gene(param_id=1, randomness=0.0, intensity=0.0, inheritance="dominant")], library_size=10)
        result = runner.execute_genome("hello", genome, agent_id=1, sample_index=0)
        self.assertTrue(result.ok)
        self.assertEqual(result.value, "hello")

    def test_zero_rule_salvage(self):
        config = EvolutionConfig(
            population_size=2,
            library_size=10,
            min_genome_length=1,
            max_genome_length=1,
            initial_genome_length=1,
            max_generations=1,
            elite_fraction=0.5,
            tournament_size=1,
            mutation_rate=0.0,
            mutation_volatility=0.0,
            seed=7,
            log_every=0,
        )
        runner = EvolutionRunner(config=config, rng=random.Random(7))
        good_agent = Agent(
            id=1,
            genome=Genome(genes=[Gene(1, 0.0, 0.0, "dominant")], library_size=10),
            meta=AgentMeta(speed_weight=0.0, inheritance_strategy="dominant"),
        )
        bad_agent = Agent(
            id=2,
            genome=Genome(genes=[Gene(2, 0.0, 0.0, "dominant")], library_size=10),
            meta=AgentMeta(speed_weight=0.0, inheritance_strategy="dominant"),
        )
        samples = [TrainingSample(key="abc", value="abc")]
        result = runner.step_generation([good_agent, bad_agent], samples)
        next_population = result.next_population
        self.assertTrue(any(agent.genome.genes[0].param_id == 2 for agent in next_population))

    def test_run_converges_with_seeded_population(self):
        config = EvolutionConfig(
            population_size=1,
            library_size=10,
            min_genome_length=1,
            max_genome_length=1,
            initial_genome_length=1,
            max_generations=3,
            elite_fraction=1.0,
            tournament_size=1,
            mutation_rate=0.0,
            mutation_volatility=0.0,
            seed=11,
            log_every=0,
        )
        runner = EvolutionRunner(config=config, rng=random.Random(11))
        genome = Genome(genes=[Gene(1, 0.0, 0.0, "dominant")], library_size=10)
        agent = Agent(id=1, genome=genome, meta=AgentMeta(speed_weight=0.0, inheritance_strategy="dominant"))
        samples = [TrainingSample(key="hello", value="hello")]
        result = runner.run(samples, initial_population=[agent])
        self.assertTrue(result.converged)
        self.assertEqual(result.best_score, 0.0)


if __name__ == "__main__":
    unittest.main()
