from __future__ import annotations

import math
import random
from typing import List

from eco_sim.models import BrainGraph, Genome


class Brain:
    def __init__(self, graph: BrainGraph) -> None:
        self.graph = graph

    def forward(self, x: List[float]) -> List[float]:
        outputs: List[float] = []
        for row in self.graph.weights:
            s = 0.0
            for w, xi in zip(row, x):
                s += w * xi
            outputs.append(math.tanh(s))
        return outputs


def random_genome(input_size: int, output_size: int, rng: random.Random) -> Genome:
    weights = []
    for _ in range(output_size):
        row = [rng.uniform(-0.5, 0.5) for _ in range(input_size)]
        weights.append(row)
    return Genome(
        input_size=input_size,
        hidden_size=0,
        output_size=output_size,
        weights=weights,
        sensor_range=4,
    )


def genome_to_brain(genome: Genome) -> BrainGraph:
    return BrainGraph(
        input_size=genome.input_size,
        hidden_size=genome.hidden_size,
        output_size=genome.output_size,
        weights=[row[:] for row in genome.weights],
    )

