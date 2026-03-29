#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${ROOT_DIR}/src:${PYTHONPATH:-}"

DATASET="${ROOT_DIR}/examples/solar_system_planets.json"
KEY_MAP="${ROOT_DIR}/examples/solar_system_planet_map.json"
MODEL="/tmp/solar_model.json"
BUNDLE="/tmp/solar_bundle.json"

echo "Training on solar_system_planets.json (synthetic linear data)..."
python3 -m flux_evolver train \
  --dataset "${DATASET}" \
  --key-map "${KEY_MAP}" \
  --library 180 \
  --generations 200 \
  --population 60 \
  --verify 8 \
  --verify-retries 5 \
  --output-model "${MODEL}" \
  --save-bundle "${BUNDLE}"

echo ""
echo "Asking model questions (planet name -> synthetic value)..."
python3 -m flux_evolver question --model "${MODEL}" --key mercury --key-map "${KEY_MAP}"
python3 -m flux_evolver question --model "${MODEL}" --key mars --key-map "${KEY_MAP}"
python3 -m flux_evolver question --model "${MODEL}" --key neptune --key-map "${KEY_MAP}"

echo ""
echo "Saved bundle: ${BUNDLE}"
