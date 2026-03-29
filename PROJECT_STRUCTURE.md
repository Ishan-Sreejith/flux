# Project Structure & File Overview

## Complete File Listing

```
/Users/ishan/flux/
│
├── 📄 pyproject.toml                    # Package configuration (setuptools)
├── 📄 README.md                         # Full architecture documentation
├── 📄 QUICKSTART.md                     # ← Start here! Quick run guide
├── 📄 BUILD_SUMMARY.md                  # Complete build summary
├── 📄 validate_build.py                 # Validate all imports work
├── 🔧 test.sh                           # Executable test runner
│
├── 📦 src/eco_sim/                      # Main package
│   │
│   ├── 📄 __init__.py                   # Package init
│   ├── 📄 models.py                     # [659 lines] Core dataclasses:
│   │                                    #   - AgentState, WorldState
│   │                                    #   - Genome, BrainGraph
│   │                                    #   - Event, ReplayFrame
│   │                                    #   - HormoneState, StressEvent
│   │                                    #   - WorldConfig
│   │
│   ├── 📁 world/
│   │   ├── 📄 __init__.py
│   │   └── 📄 engine.py                 # [213 lines] WorldEngine class:
│   │                                    #   - Step-by-step simulation
│   │                                    #   - Grid physics (movement, eating, mating, death)
│   │                                    #   - Plant regrowth with stressor modifiers
│   │                                    #   - Stochastic stressor generation
│   │                                    #   - Event emission (append-only log)
│   │                                    #   - run() method for batch execution
│   │
│   ├── 📁 agents/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 sensors.py                # [47 lines] build_sensor_vector():
│   │                                    #   - 7-value sensory encoding
│   │                                    #   - Plant, predator, energy, peers, hormones
│   │                                    #   - Distance/angle calculations
│   │
│   │   ├── 📄 brain.py                  # [45 lines] Neural network:
│   │                                    #   - Brain class (forward pass with tanh)
│   │                                    #   - random_genome() factory
│   │                                    #   - genome_to_brain() converter
│   │
│   │   ├── 📄 plasticity.py             # [49 lines] NEAT-style mutations:
│   │                                    #   - mutate_genome() with weight perturbation
│   │                                    #   - Structural: add hidden neurons
│   │                                    #   - Sensor range mutation (2-8)
│   │                                    #   - crossover() for breeding
│   │
│   │   └── 📄 policy.py                 # [54 lines] Action decision:
│   │                                    #   - decide_action() heuristic rules
│   │                                    #   - ActionDecision dataclass
│   │                                    #   - Curiosity mode handling
│   │                                    #   - Expected energy predictions
│   │
│   ├── 📁 awareness/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 state.py                  # [8 lines] update_confidence_and_curiosity():
│   │                                    #   - Confidence score from action
│   │                                    #   - Curiosity trigger (< 0.35 threshold)
│   │
│   │   └── 📄 causal.py                 # [33 lines] CausalBuffer class:
│   │                                    #   - Rolling 100-record FIFO buffer
│   │                                    #   - add(tick, expected, actual)
│   │                                    #   - mismatch_score() = avg |error|
│   │
│   ├── 📁 evolution/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 pipeline.py               # [64 lines] EvolutionPipeline:
│   │                                    #   - evaluate_fitness() ranking
│   │                                    #   - select_parents() elitism + tournament
│   │                                    #   - evolve_generation() breed offspring
│   │                                    #   - get_metrics() for reporting
│   │
│   │   └── 📄 social.py                 # [13 lines] SocialLearner:
│   │                                    #   - prime_juvenile() from elite
│   │                                    #   - Copy mentor dopamine & sensor range
│   │
│   ├── 📁 io/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 events.py                 # [30 lines] EventLog:
│   │                                    #   - Append-only event list
│   │                                    #   - save() / load() JSON serialization
│   │
│   │   └── 📄 replay.py                 # [44 lines] ReplayBuilder:
│   │                                    #   - Frame snapshots (tick, pops, energy)
│   │                                    #   - build_frame() from current state
│   │                                    #   - get_frame_at_tick() query
│   │
│   └── 📁 demo/
│       ├── 📄 __init__.py
│       └── 📄 run_demo.py               # [37 lines] Standalone demo:
│                                        #   - run_demo(ticks, seed) function
│                                        #   - Pretty-printed output
│                                        #   - Tick-by-tick progress
│
├── 📦 tests/                            # Test suite
│   ├── 📄 __init__.py
│   ├── 📄 test_world_engine.py          # [34 lines] World physics tests:
│   │                                    #   - Initial population
│   │                                    #   - Tick increment
│   │                                    #   - Event logging
│   │                                    #   - Plant regrowth
│   │                                    #   - Run completion
│   │
│   ├── 📄 test_agents.py                # [67 lines] Agent tests:
│   │                                    #   - Sensor vector generation
│   │                                    #   - Action decision
│   │                                    #   - Genome creation
│   │                                    #   - Mutation & crossover
│   │                                    #   - Brain forward pass
│   │
│   ├── 📄 test_awareness.py             # [42 lines] Awareness tests:
│   │                                    #   - Confidence update
│   │                                    #   - Curiosity trigger
│   │                                    #   - Causal buffer add
│   │                                    #   - Mismatch scoring
│   │
│   └── 📄 test_evolution.py             # [46 lines] Evolution tests:
│                                        #   - Fitness evaluation
│                                        #   - Dead agent fitness (0)
│                                        #   - Generation evolution
│                                        #   - Metrics reporting
```

---

## Module Dependencies

```
models.py
  ↓
world/engine.py ←─────────────────┐
  ↓                               │
agents/                           │
  ├── sensors.py ────────────┐    │
  ├── policy.py ──────┐      │    │
  ├── brain.py        │      │    │
  └── plasticity.py   │      │    │
                      ↓      ↓    │
awareness/            │      │    │
  ├── state.py ───────┤      │    │
  └── causal.py ──────┤      │    │
                      ↓      ↓    │
evolution/            │      │    │
  ├── pipeline.py ────┘      │    │
  └── social.py              │    │
                             ↓    │
io/                          │    │
  ├── events.py ─────────────┘    │
  └── replay.py ──────────────────┘

demo/run_demo.py
  └── imports from all above
```

---

## Line Count Summary

| Module | Lines | Purpose |
|--------|-------|---------|
| models.py | 659 | Data models |
| world/engine.py | 213 | Core simulation |
| agents/sensors.py | 47 | Input encoding |
| agents/brain.py | 45 | Neural network |
| agents/plasticity.py | 49 | Evolution genetics |
| agents/policy.py | 54 | Decision logic |
| awareness/state.py | 8 | Metacognition |
| awareness/causal.py | 33 | Learning buffer |
| evolution/pipeline.py | 64 | GA operators |
| evolution/social.py | 13 | Social learning |
| io/events.py | 30 | Event log |
| io/replay.py | 44 | Replay builder |
| demo/run_demo.py | 37 | Demo runner |
| **Total Source** | **1397** | **All modules** |
| tests/ (4 files) | 189 | Test coverage |
| **Grand Total** | **1586** | **Complete MVP** |

---

## Key Metrics

- **Modules**: 13 source + 4 tests
- **Functions**: ~40 public APIs
- **Classes**: ~15 main classes
- **Lines**: 1400 lines of implementation
- **Dependencies**: Standard library only (Python 3.9+)
- **Config**: Fully parameterizable via WorldConfig
- **Reproducibility**: Deterministic with seed control

---

## Quick Navigation

| Need | Go To |
|------|-------|
| **Getting Started** | `QUICKSTART.md` |
| **Full Architecture** | `README.md` |
| **Build Summary** | `BUILD_SUMMARY.md` |
| **Run Tests** | `test.sh` or `validate_build.py` |
| **Simulation Loop** | `src/eco_sim/world/engine.py` |
| **Agent Brain** | `src/eco_sim/agents/` |
| **Evolution** | `src/eco_sim/evolution/pipeline.py` |
| **Awareness** | `src/eco_sim/awareness/` |

---

## Usage Commands

```bash
# Navigate to project
cd /Users/ishan/flux

# Set Python path
export PYTHONPATH="/Users/ishan/flux/src:$PYTHONPATH"

# Validate build
python3 validate_build.py

# Run tests
bash test.sh

# Run single demo
python3 src/eco_sim/demo/run_demo.py 100 42

# Run custom simulation
python3 -c "
import sys; sys.path.insert(0, 'src')
from eco_sim.world.engine import WorldEngine
from eco_sim.models import WorldConfig

config = WorldConfig(width=15, height=15, initial_prey=10, initial_predators=3)
engine = WorldEngine(config=config, seed=42)
state = engine.run(ticks=100)
print(f'Events: {len(state.events)}')
"
```

---

## Architecture Highlights

✅ **Modular**: Each subsystem (world, agents, evolution, awareness) is independent
✅ **Testable**: Unit tests for each major component
✅ **Configurable**: All parameters in WorldConfig
✅ **Reproducible**: Seed-based deterministic RNG
✅ **Extensible**: Easy to add new behaviors, stressors, mutations
✅ **Observable**: Full event logging + replay capability
✅ **Lean**: No external dependencies, pure Python

---

**Build Status**: ✅ Complete & Ready to Run

See `QUICKSTART.md` to get started!

