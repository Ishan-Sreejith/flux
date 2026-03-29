from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque

from eco_sim.models import CausalRecord


@dataclass
class CausalBuffer:
    buffer: Deque[CausalRecord] = None
    max_len: int = 100

    def __post_init__(self) -> None:
        if self.buffer is None:
            self.buffer = deque(maxlen=self.max_len)

    def add(self, tick: int, expected_delta_energy: float, actual_delta_energy: float) -> None:
        record = CausalRecord(
            tick=tick,
            expected_delta_energy=expected_delta_energy,
            actual_delta_energy=actual_delta_energy,
        )
        self.buffer.append(record)

    def mismatch_score(self) -> float:
        if not self.buffer:
            return 0.0
        total_error = sum(
            abs(r.actual_delta_energy - r.expected_delta_energy)
            for r in self.buffer
        )
        return total_error / len(self.buffer)

