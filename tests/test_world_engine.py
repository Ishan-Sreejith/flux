import unittest
from eco_sim.world.engine import WorldEngine
from eco_sim.models import WorldConfig, AgentKind


class TestWorldEngine(unittest.TestCase):
    def setUp(self):
        self.config = WorldConfig(width=10, height=10, initial_prey=5, initial_predators=2)
        self.engine = WorldEngine(config=self.config, seed=42)

    def test_initial_population(self):
        prey_count = sum(1 for a in self.engine.state.agents.values() if a.kind == AgentKind.PREY and a.alive)
        predator_count = sum(1 for a in self.engine.state.agents.values() if a.kind == AgentKind.PREDATOR and a.alive)
        self.assertEqual(prey_count, self.config.initial_prey)
        self.assertEqual(predator_count, self.config.initial_predators)

    def test_step_increments_tick(self):
        initial_tick = self.engine.state.tick
        self.engine.step()
        self.assertEqual(self.engine.state.tick, initial_tick + 1)

    def test_events_logged(self):
        initial_events = len(self.engine.state.events)
        self.engine.step()
        self.assertGreater(len(self.engine.state.events), initial_events)

    def test_plant_regrowth(self):
        initial_plant = sum(cell.plant_energy for row in self.engine.state.grid for cell in row)
        self.engine.step()
        current_plant = sum(cell.plant_energy for row in self.engine.state.grid for cell in row)
        self.assertGreater(current_plant, 0)

    def test_run_completes(self):
        state = self.engine.run(ticks=5)
        self.assertEqual(state.tick, 5)
        self.assertGreater(len(state.events), 0)


if __name__ == "__main__":
    unittest.main()

