import unittest
import random
from eco_sim.evolution.pipeline import EvolutionPipeline
from eco_sim.models import AgentState, AgentKind


class TestEvolution(unittest.TestCase):
    def setUp(self):
        self.rng = random.Random(42)
        self.pipeline = EvolutionPipeline(rng=self.rng)

    def test_fitness_evaluation(self):
        agent = AgentState(id=1, kind=AgentKind.PREY, pos=(5, 5), energy=20.0, age_ticks=10)
        agent.alive = True
        fitness = self.pipeline.evaluate_fitness(agent)
        self.assertGreater(fitness, 0.0)

    def test_dead_agent_fitness(self):
        agent = AgentState(id=1, kind=AgentKind.PREY, pos=(5, 5), energy=0.0)
        agent.alive = False
        fitness = self.pipeline.evaluate_fitness(agent)
        self.assertEqual(fitness, 0.0)

    def test_evolve_generation(self):
        agents = [
            AgentState(id=i, kind=AgentKind.PREY, pos=(5, 5), energy=15.0 + i, age_ticks=i)
            for i in range(5)
        ]
        for a in agents:
            a.alive = True
        genomes = self.pipeline.evolve_generation(agents)
        self.assertEqual(len(genomes), 5)

    def test_metrics(self):
        agents = [
            AgentState(id=i, kind=AgentKind.PREY, pos=(5, 5), energy=15.0 + i, age_ticks=i)
            for i in range(5)
        ]
        for a in agents:
            a.alive = True
        metrics = self.pipeline.get_metrics(agents)
        self.assertGreater(metrics.best_fitness, 0.0)
        self.assertGreater(metrics.mean_fitness, 0.0)
        self.assertEqual(metrics.survivor_count, 5)


if __name__ == "__main__":
    unittest.main()

