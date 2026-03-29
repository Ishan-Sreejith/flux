from __future__ import annotations

import random
from typing import List

from eco_sim.models import AgentState, Genome


class SocialLearner:
    def __init__(self, rng: random.Random) -> None:
        self.rng = rng

    def prime_juvenile(self, juvenile: AgentState, elite_trajectories: List[AgentState]) -> None:
        if not elite_trajectories:
            return
        mentor = self.rng.choice(elite_trajectories)
        juvenile.hormones.dopamine = mentor.hormones.dopamine * 0.8
        juvenile.sensor_range = max(2, mentor.sensor_range - 1)

