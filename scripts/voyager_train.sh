#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${ROOT_DIR}/src:${PYTHONPATH:-}"

DATASET="${ROOT_DIR}/examples/voyager_slingshot.json"
MODEL="/tmp/voyager_model.json"
BUNDLE="/tmp/voyager_bundle.json"

echo "Training on voyager_slingshot.json..."
python3 -m flux_evolver train \
  --dataset "${DATASET}" \
  --library 220 \
  --generations 250 \
  --population 70 \
  --verify 6 \
  --verify-retries 5 \
  --output-model "${MODEL}" \
  --save-bundle "${BUNDLE}"

echo ""
echo "Asking model questions (JSON key arrays)..."
python3 -m flux_evolver question --model "${MODEL}" --key "[45.0, 15000.0, 5.97, 750.0]" --key-json
python3 -m flux_evolver question --model "${MODEL}" --key "[55.0, 15800.0, 6.80, 680.0]" --key-json
python3 -m flux_evolver question --model "${MODEL}" --key "[75.0, 16800.0, 8.40, 580.0]" --key-json

echo ""
echo "Saved bundle: ${BUNDLE}"
