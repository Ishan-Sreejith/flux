from __future__ import annotations

import sys

from eco_sim.io.replay import ReplayBuilder
from eco_sim.models import WorldConfig
from eco_sim.world.engine import WorldEngine


def run_demo(ticks: int = 100, seed: int = 42) -> None:
    print(f"🌍 Ecosystem Simulation Demo | ticks={ticks}, seed={seed}")
    print("-" * 60)

    config = WorldConfig(
        width=20,
        height=20,
        initial_prey=20,
        initial_predators=6,
        max_ticks=ticks,
    )

    engine = WorldEngine(config=config, seed=seed)
    replay = ReplayBuilder(engine.state)

    for i in range(ticks):
        engine.step()
        replay.record_frame()
        if (i + 1) % 20 == 0:
            frame = replay.build_frame()
            living_prey = frame.living_prey
            living_predators = frame.living_predators
            plant_energy = frame.plant_total
            print(f"Tick {frame.tick:3d}: 🐰 {living_prey:2d} | 🦁 {living_predators:2d} | 🌿 {plant_energy:6.1f}")

    final_frame = replay.build_frame()
    print("-" * 60)
    print(f"Final: 🐰 {final_frame.living_prey} prey, 🦁 {final_frame.living_predators} predators")
    print(f"Total energy: {final_frame.energy_total:.1f}")
    print(f"Plant energy: {final_frame.plant_total:.1f}")
    print(f"Total events logged: {len(engine.state.events)}")
    print("✅ Demo complete!")


if __name__ == "__main__":
    ticks = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 42
    run_demo(ticks=ticks, seed=seed)

