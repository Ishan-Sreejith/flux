#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${ROOT_DIR}/src:${PYTHONPATH:-}"

MODEL_A="${1:-/tmp/flux_model_a.json}"
MODEL_B="${2:-/tmp/flux_model_b.json}"
KEY="${3:-11}"
TARGET="${4:-}"

echo "Comparing models..."
python3 - <<'PY'
import json
import os
import sys
from flux_evolver.evolution import EvolutionRunner
from flux_evolver.io import load_genome
from flux_evolver.models import Agent, AgentMeta, EvolutionConfig
from flux_evolver.scoring import score_value

model_a = sys.argv[1]
model_b = sys.argv[2]
key_raw = sys.argv[3]
target_raw = sys.argv[4] if len(sys.argv) > 4 else ""

def parse(val: str):
    val = val.strip()
    if not val:
        return None
    if val.startswith("[") or val.startswith("{"):
        return json.loads(val)
    try:
        return float(val)
    except Exception:
        return val

key = parse(key_raw)
target = parse(target_raw) if target_raw else None

def eval_model(path):
    genome = load_genome(path)
    config = EvolutionConfig(
        population_size=1,
        library_size=genome.library_size,
        min_genome_length=len(genome.genes),
        max_genome_length=len(genome.genes),
        initial_genome_length=len(genome.genes),
        seed=42,
        log_every=0,
    )
    runner = EvolutionRunner(config=config)
    agent = Agent(id=1, genome=genome, meta=AgentMeta(speed_weight=0.0, inheritance_strategy="dominant"))
    result = runner.execute_genome(key, genome, agent_id=agent.id, sample_index=0)
    if not result.ok:
        return float("inf"), result.value
    if target is None:
        return len(genome.genes), result.value
    return score_value(result.value, target) + (len(genome.genes) / 100.0), result.value

score_a, out_a = eval_model(model_a)
score_b, out_b = eval_model(model_b)

best = "A" if score_a <= score_b else "B"
print(f"Model A score: {score_a}")
print(f"Model B score: {score_b}")
print(f"Winner: {best}")
print(f"Output A: {out_a}")
print(f"Output B: {out_b}")
PY "$MODEL_A" "$MODEL_B" "$KEY" "$TARGET"
