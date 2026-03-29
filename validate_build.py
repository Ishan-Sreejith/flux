#!/usr/bin/env python3
"""
Quick validation script to verify all modules can be imported and basic structure is correct.
Run: python3 validate_build.py
"""

import sys
import os

# Add src to path
sys.path.insert(0, '/Users/ishan/flux/src')

def validate():
    print("🔍 Validating Ecosystem Simulation Build...")
    print("=" * 60)

    errors = []

    # Test core imports
    try:
        from eco_sim.models import (
            AgentState, WorldConfig, Genome, Event,
            AgentKind, ActionType, HormoneState
        )
        print("✅ models.py: All dataclasses imported")
    except Exception as e:
        errors.append(f"❌ models.py: {e}")

    # Test world engine
    try:
        from eco_sim.world.engine import WorldEngine, WorldState
        print("✅ world/engine.py: WorldEngine & WorldState imported")
    except Exception as e:
        errors.append(f"❌ world/engine.py: {e}")

    # Test agents
    try:
        from eco_sim.agents.sensors import build_sensor_vector
        from eco_sim.agents.brain import Brain, random_genome, genome_to_brain
        from eco_sim.agents.plasticity import mutate_genome, crossover
        from eco_sim.agents.policy import decide_action, ActionDecision
        print("✅ agents/*: All agent modules imported")
    except Exception as e:
        errors.append(f"❌ agents/: {e}")

    # Test awareness
    try:
        from eco_sim.awareness.state import update_confidence_and_curiosity
        from eco_sim.awareness.causal import CausalBuffer
        print("✅ awareness/*: Awareness modules imported")
    except Exception as e:
        errors.append(f"❌ awareness/: {e}")

    # Test evolution
    try:
        from eco_sim.evolution.pipeline import EvolutionPipeline
        from eco_sim.evolution.social import SocialLearner
        print("✅ evolution/*: Evolution modules imported")
    except Exception as e:
        errors.append(f"❌ evolution/: {e}")

    # Test io
    try:
        from eco_sim.io.events import EventLog
        from eco_sim.io.replay import ReplayBuilder
        print("✅ io/*: IO modules imported")
    except Exception as e:
        errors.append(f"❌ io/: {e}")

    # Test demo
    try:
        from eco_sim.demo.run_demo import run_demo
        print("✅ demo/run_demo.py: Demo imported")
    except Exception as e:
        errors.append(f"❌ demo/run_demo.py: {e}")

    print("=" * 60)

    if errors:
        print("\n⚠️  ERRORS FOUND:")
        for err in errors:
            print(err)
        return False

    print("\n✅ ALL MODULES VALIDATED SUCCESSFULLY!")
    print("\n🚀 Ready to run:")
    print("   python3 src/eco_sim/demo/run_demo.py 100 42")
    return True

if __name__ == "__main__":
    success = validate()
    sys.exit(0 if success else 1)

