from __future__ import annotations

import random

from eco_sim.models import Genome


def mutate_genome(genome: Genome, rng: random.Random, weight_rate: float = 0.15, structure_rate: float = 0.03) -> Genome:
    new_weights = [row[:] for row in genome.weights]

    for oi, row in enumerate(new_weights):
        for ii, _ in enumerate(row):
            if rng.random() < weight_rate:
                row[ii] += rng.uniform(-0.2, 0.2)

    hidden_size = genome.hidden_size
    if rng.random() < structure_rate:
        hidden_size += 1
        for row in new_weights:
            row.append(rng.uniform(-0.3, 0.3))

    sensor_range = max(2, min(8, genome.sensor_range + rng.choice([-1, 0, 1])))

    return Genome(
        input_size=genome.input_size,
        hidden_size=hidden_size,
        output_size=genome.output_size,
        weights=new_weights,
        sensor_range=sensor_range,
    )


def crossover(a: Genome, b: Genome, rng: random.Random) -> Genome:
    weights = []
    width = min(len(a.weights[0]), len(b.weights[0])) if a.weights and b.weights else 0
    for ra, rb in zip(a.weights, b.weights):
        row = []
        for i in range(width):
            row.append(ra[i] if rng.random() < 0.5 else rb[i])
        weights.append(row)

    return Genome(
        input_size=min(a.input_size, b.input_size),
        hidden_size=max(a.hidden_size, b.hidden_size),
        output_size=min(a.output_size, b.output_size),
        weights=weights,
        sensor_range=rng.choice([a.sensor_range, b.sensor_range]),
    )

