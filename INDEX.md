# 📑 COMPLETE FILE INDEX & NAVIGATION GUIDE

## Welcome to the Flux Evolutionary Ecosystem! 🌍

Your complete, fully-functional ecosystem simulation is ready to run. Use this guide to find what you need.

---

## 🎯 START HERE (Pick Your Path)

### 👤 I'm New - Get Me Running ASAP
1. Read: **QUICKSTART.md** (5 min)
2. Run: `bash test.sh`
3. Explore: Check output and try other commands

### 📚 I Want to Understand the Architecture
1. Read: **QUICKSTART.md** (overview)
2. Read: **README.md** (full technical guide)
3. Explore: Source code in `src/eco_sim/`

### 🔧 I Want to Extend/Modify
1. Read: **QUICKSTART.md**
2. Study: **PROJECT_STRUCTURE.md**
3. Modify: Edit files in `src/eco_sim/`
4. Test: Run `python3 validate_build.py`

### ✅ I Need to Verify Everything Works
1. Run: `python3 validate_build.py`
2. Run: `bash test.sh`
3. Check: All tests pass

---

## 📁 FILE ORGANIZATION

### 📖 Documentation Files (Read These First)

| File | Purpose | Read Time | Best For |
|------|---------|-----------|----------|
| **QUICKSTART.md** | Fast getting-started guide | 5 min | 🚀 Getting running immediately |
| **README.md** | Full technical documentation | 20 min | 🧠 Understanding architecture |
| **BUILD_SUMMARY.md** | What was implemented | 10 min | ✅ Understanding scope |
| **PROJECT_STRUCTURE.md** | File-by-file breakdown | 5 min | 📂 Navigating code |
| **COMPLETION_SUMMARY.md** | This session's overview | 5 min | 📊 High-level summary |
| **FINAL_SUMMARY.txt** | Executive summary | 3 min | 🎯 Quick reference |
| **This File** | Navigation guide | 5 min | 🗺️ Finding things |

### 🔧 Executable Scripts

| File | Purpose | How to Run |
|------|---------|-----------|
| **test.sh** | Run all demos | `bash test.sh` |
| **validate_build.py** | Check setup | `python3 validate_build.py` |
| **EXECUTION_GUIDE.sh** | View commands | `bash EXECUTION_GUIDE.sh` |

### 📦 Source Code (src/eco_sim/)

```
src/eco_sim/
├── models.py                          # All dataclasses
├── world/
│   └── engine.py                      # Main simulation
├── agents/
│   ├── sensors.py                     # Input encoding
│   ├── brain.py                       # Neural network
│   ├── plasticity.py                  # Evolution genetics
│   └── policy.py                      # Decision making
├── awareness/
│   ├── state.py                       # Confidence/curiosity
│   └── causal.py                      # Learning buffer
├── evolution/
│   ├── pipeline.py                    # GA operators
│   └── social.py                      # Social learning
├── io/
│   ├── events.py                      # Event logging
│   └── replay.py                      # Replay system
└── demo/
    └── run_demo.py                    # Runnable demo
```

### 🧪 Test Suite (tests/)

```
tests/
├── test_world_engine.py               # World physics
├── test_agents.py                     # Agent systems
├── test_awareness.py                  # Awareness layer
└── test_evolution.py                  # Evolution
```

### ⚙️ Configuration

| File | Purpose |
|------|---------|
| **pyproject.toml** | Package configuration |

---

## 🚀 QUICK COMMANDS

### Run Everything
```bash
cd /Users/ishan/flux
bash test.sh
```

### Run Single Demo
```bash
cd /Users/ishan/flux
export PYTHONPATH="/Users/ishan/flux/src:$PYTHONPATH"
python3 src/eco_sim/demo/run_demo.py 100 42
```

### Validate Build
```bash
cd /Users/ishan/flux
python3 validate_build.py
```

### View Available Commands
```bash
bash /Users/ishan/flux/EXECUTION_GUIDE.sh
```

---

## 📚 READING PATHS (Choose One)

### Path 1: I Just Want to Run It (5 min)
1. **QUICKSTART.md** - Section "Quick Run"
2. Run: `bash test.sh`
3. Done! ✅

### Path 2: I Want to Understand It (30 min)
1. **QUICKSTART.md** - Full read
2. **README.md** - Architecture section
3. **PROJECT_STRUCTURE.md** - Full read
4. Run: `bash test.sh`
5. Explore source in `src/eco_sim/`

### Path 3: I Want to Extend It (1-2 hours)
1. **QUICKSTART.md** - Full read
2. **README.md** - Full read
3. **PROJECT_STRUCTURE.md** - Full read
4. Explore source: Start with `models.py`
5. Understand world engine: Read `world/engine.py`
6. Modify agents: Edit `agents/policy.py`
7. Test: Run `python3 validate_build.py`

### Path 4: I Want Everything (2-3 hours)
1. Read all documentation files in order
2. Run validation and tests
3. Study each source module
4. Create custom variants
5. Run long training runs

---

## 🎯 COMMON TASKS

### "I want to run the simulation"
→ **QUICKSTART.md** (Option 1 or 2) or `bash test.sh`

### "I want to understand what was built"
→ **BUILD_SUMMARY.md** or **README.md**

### "I want to modify agent behavior"
→ **src/eco_sim/agents/policy.py** (edit `decide_action()` function)

### "I want to add a new stressor"
→ **src/eco_sim/world/engine.py** (edit `_apply_stressors()` method)

### "I want to change simulation parameters"
→ **src/eco_sim/models.py** (edit `WorldConfig` class)

### "I want to understand the neural architecture"
→ **src/eco_sim/agents/brain.py** (simple feedforward)

### "I want to understand evolution"
→ **src/eco_sim/evolution/pipeline.py** (fitness, selection, breeding)

### "I want to understand metacognition"
→ **src/eco_sim/awareness/causal.py** (prediction error tracking)

### "I need to verify everything works"
→ Run `python3 validate_build.py` then `bash test.sh`

---

## 📊 WHAT EACH FILE DOES

### Core Implementation

**models.py** (659 lines)
- Defines all data structures: AgentState, WorldState, Genome, Event, etc.
- Contains WorldConfig with all configurable parameters
- Essential foundation for everything else

**world/engine.py** (213 lines)
- Main simulation loop (step method)
- Grid physics (movement, eating, mating, death)
- Plant regrowth with stressor modifiers
- Event generation and logging
- Deterministic tick-based updates

**agents/sensors.py** (47 lines)
- Encodes environment into 7-value sensor vector
- Detects: plants, predators, energy, peers, hormones
- Forms input to neural brain

**agents/brain.py** (45 lines)
- Defines neural network class
- Forward pass with tanh activation
- Genome creation and conversion

**agents/plasticity.py** (49 lines)
- Mutation operators (weight noise, structural changes)
- Crossover (genetic breeding)
- Sensor range adaptation

**agents/policy.py** (54 lines)
- Decision-making logic (heuristic rules)
- Maps sensors to actions
- Calculates confidence scores

**awareness/state.py** (8 lines)
- Updates confidence and curiosity mode
- Simple but critical for metacognition

**awareness/causal.py** (33 lines)
- Maintains rolling buffer of prediction errors
- Tracks expected vs. actual energy changes
- Enables learning from mistakes

**evolution/pipeline.py** (64 lines)
- Fitness evaluation
- Parent selection (elitism + tournament)
- Breeding via crossover and mutation

**evolution/social.py** (13 lines)
- Optional social learning (juvenile priming)
- Transfers knowledge from elites

**io/events.py** (30 lines)
- Event log storage and serialization
- JSON save/load for persistence

**io/replay.py** (44 lines)
- Frame snapshots (state at each tick)
- Enables replay and retrospective analysis

**demo/run_demo.py** (37 lines)
- Standalone executable demo
- Pretty-printed output
- Entry point for running simulations

### Testing

**test_world_engine.py** (34 lines)
- Tests world physics (regrowth, events, tick increment)
- Validates simulation basics

**test_agents.py** (67 lines)
- Tests sensors, brain, mutations, crossover
- Validates agent systems

**test_awareness.py** (42 lines)
- Tests confidence, curiosity, causal buffer
- Validates metacognition

**test_evolution.py** (46 lines)
- Tests fitness, selection, evolution
- Validates GA operators

### Scripts

**test.sh**
- Bash script that runs all demos
- Sets up environment and executes simulations
- Good for automated testing

**validate_build.py**
- Python script that checks all imports
- Verifies build integrity
- Good for debugging setup issues

---

## 💡 TIPS FOR SUCCESS

### Getting Started
1. Read QUICKSTART.md (not the README first!)
2. Run `bash test.sh` to see it working
3. Modify small things and re-run

### Understanding the Code
- Start with `models.py` (understand data structures)
- Then read `world/engine.py` (understand simulation)
- Then explore `agents/` (understand agents)
- Finally read `evolution/` (understand learning)

### Making Changes
- Edit source files in `src/eco_sim/`
- Delete any `__pycache__` directories if you get import errors
- Run `python3 validate_build.py` to check your changes
- Run `python3 src/eco_sim/demo/run_demo.py 50 42` to test quickly

### Common Issues
- "ModuleNotFoundError": Set `export PYTHONPATH="/Users/ishan/flux/src:$PYTHONPATH"`
- "stale .pyc files": `find src -type d -name __pycache__ -delete`
- "Want to see more output": Edit `demo/run_demo.py` to print more details

---

## 🎓 LEARNING ORDER

1. **Understand the Vision**
   - Read QUICKSTART.md introduction
   - Read README.md architecture section

2. **See It Running**
   - Run `bash test.sh`
   - Watch different seeds produce different results

3. **Understand the Code**
   - Read PROJECT_STRUCTURE.md
   - Review `models.py` (10 min)
   - Review `world/engine.py` (15 min)

4. **Understand Agents**
   - Read `agents/sensors.py`
   - Read `agents/brain.py`
   - Read `agents/policy.py`

5. **Understand Evolution**
   - Read `agents/plasticity.py`
   - Read `evolution/pipeline.py`

6. **Understand Awareness**
   - Read `awareness/causal.py`

7. **Make Changes**
   - Modify `WorldConfig` in `models.py`
   - Add stressors in `world/engine.py`
   - Change agent behavior in `agents/policy.py`
   - Run `python3 validate_build.py`
   - Test with `python3 src/eco_sim/demo/run_demo.py`

---

## ✅ VERIFICATION CHECKLIST

- [ ] Read QUICKSTART.md
- [ ] Run `python3 validate_build.py` (all imports work)
- [ ] Run `bash test.sh` (all demos run)
- [ ] Read README.md (understand architecture)
- [ ] Explore source files
- [ ] Make a small modification
- [ ] Run modified version

---

## 📞 NEED HELP?

### "How do I run the simulation?"
→ QUICKSTART.md or `bash test.sh`

### "How do I modify agent behavior?"
→ Edit `src/eco_sim/agents/policy.py`

### "How do I change world parameters?"
→ Edit `WorldConfig` in `src/eco_sim/models.py`

### "How do I understand the architecture?"
→ Read README.md, then Project Structure, then source

### "How do I add a new feature?"
→ Read relevant module, add code, run `validate_build.py`, test

### "Why is import failing?"
→ Set PYTHONPATH: `export PYTHONPATH="/Users/ishan/flux/src:$PYTHONPATH"`

### "Why are my changes not showing?"
→ Delete `__pycache__`: `find src -name __pycache__ -type d -delete`

---

## 🎯 FINAL STEPS

1. **Right now**: `cd /Users/ishan/flux && bash test.sh`
2. **Then**: Read QUICKSTART.md while watching the output
3. **Next**: Explore the source files mentioned above
4. **Finally**: Make your own modifications and extensions

---

## 📋 SUMMARY TABLE

| What | Where | How |
|------|-------|-----|
| **Get started** | QUICKSTART.md | `bash test.sh` |
| **Understand it** | README.md | Read full guide |
| **See the code** | src/eco_sim/ | Read source files |
| **Run tests** | tests/ | `bash test.sh` or `python3 -m pytest` |
| **Modify behavior** | agents/policy.py | Edit `decide_action()` |
| **Change world** | models.py | Edit `WorldConfig` |
| **Add stressors** | world/engine.py | Edit `_apply_stressors()` |
| **Validate** | validate_build.py | `python3 validate_build.py` |

---

**You're all set! Pick a task above and get started.** 🚀

Enjoy your evolving ecosystem! 🌍🐰🦁🌿

