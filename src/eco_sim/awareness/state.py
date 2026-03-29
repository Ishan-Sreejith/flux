from __future__ import annotations

from eco_sim.agents.policy import ActionDecision
from eco_sim.models import AgentState


def update_confidence_and_curiosity(agent: AgentState, decision: ActionDecision, threshold: float = 0.35) -> None:
    agent.confidence = decision.confidence
    agent.curiosity_mode = decision.confidence < threshold

