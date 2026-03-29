import unittest
from eco_sim.awareness.state import update_confidence_and_curiosity
from eco_sim.awareness.causal import CausalBuffer
from eco_sim.agents.policy import ActionDecision
from eco_sim.models import AgentState, AgentKind, ActionType


class TestAwareness(unittest.TestCase):
    def setUp(self):
        self.agent = AgentState(id=1, kind=AgentKind.PREY, pos=(5, 5), energy=10.0)

    def test_confidence_update(self):
        decision = ActionDecision(action_type=ActionType.MOVE, confidence=0.8)
        update_confidence_and_curiosity(self.agent, decision, threshold=0.35)
        self.assertEqual(self.agent.confidence, 0.8)
        self.assertFalse(self.agent.curiosity_mode)

    def test_curiosity_triggered(self):
        decision = ActionDecision(action_type=ActionType.MOVE, confidence=0.2)
        update_confidence_and_curiosity(self.agent, decision, threshold=0.35)
        self.assertTrue(self.agent.curiosity_mode)

    def test_causal_buffer_add(self):
        buffer = CausalBuffer(max_len=10)
        buffer.add(tick=1, expected_delta_energy=2.0, actual_delta_energy=1.8)
        self.assertEqual(len(buffer.buffer), 1)

    def test_causal_mismatch_score(self):
        buffer = CausalBuffer(max_len=10)
        buffer.add(tick=1, expected_delta_energy=2.0, actual_delta_energy=1.5)
        buffer.add(tick=2, expected_delta_energy=3.0, actual_delta_energy=3.0)
        score = buffer.mismatch_score()
        self.assertGreater(score, 0.0)


if __name__ == "__main__":
    unittest.main()

