import unittest
import random
from eco_sim.agents.sensors import build_sensor_vector
from eco_sim.agents.policy import decide_action
from eco_sim.agents.brain import random_genome, genome_to_brain, Brain
from eco_sim.agents.plasticity import mutate_genome, crossover
from eco_sim.models import WorldConfig, AgentState, AgentKind
from eco_sim.world.engine import WorldEngine


class TestAgents(unittest.TestCase):
    def setUp(self):
        self.config = WorldConfig(width=10, height=10)
        self.engine = WorldEngine(config=self.config, seed=42)
        self.rng = random.Random(42)

    def test_sensor_vector(self):
        agent = list(self.engine.state.agents.values())[0]
        vec = build_sensor_vector(self.engine.state, agent)
        self.assertEqual(len(vec), 7)
        for val in vec:
            self.assertIsInstance(val, float)

    def test_action_decision(self):
        agent = list(self.engine.state.agents.values())[0]
        vec = build_sensor_vector(self.engine.state, agent)
        action = decide_action(agent, vec, self.rng)
        self.assertIsNotNone(action.action_type)
        self.assertGreaterEqual(action.confidence, 0.0)
        self.assertLessEqual(action.confidence, 1.0)

    def test_genome_creation(self):
        genome = random_genome(7, 4, self.rng)
        self.assertEqual(genome.input_size, 7)
        self.assertEqual(genome.output_size, 4)
        self.assertEqual(len(genome.weights), 4)
        self.assertEqual(len(genome.weights[0]), 7)

    def test_genome_mutation(self):
        genome = random_genome(7, 4, self.rng)
        original_sensor_range = genome.sensor_range
        mutated = mutate_genome(genome, self.rng)
        self.assertEqual(mutated.input_size, genome.input_size)
        self.assertGreaterEqual(mutated.sensor_range, 2)
        self.assertLessEqual(mutated.sensor_range, 8)

    def test_crossover(self):
        g1 = random_genome(7, 4, self.rng)
        g2 = random_genome(7, 4, self.rng)
        child = crossover(g1, g2, self.rng)
        self.assertEqual(child.input_size, 7)
        self.assertEqual(child.output_size, 4)

    def test_brain_forward(self):
        genome = random_genome(7, 4, self.rng)
        brain_graph = genome_to_brain(genome)
        brain = Brain(brain_graph)
        inputs = [1.0] * 7
        outputs = brain.forward(inputs)
        self.assertEqual(len(outputs), 4)


if __name__ == "__main__":
    unittest.main()


