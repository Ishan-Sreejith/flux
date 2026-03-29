#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${ROOT_DIR}/src:${PYTHONPATH:-}"

echo "Running unit tests..."
python3 -m unittest tests.test_flux_evolver -v

echo ""
echo "Training on market_share_linear.json with verification..."
python3 -m flux_evolver train \
  --dataset "${ROOT_DIR}/examples/market_share_linear.json" \
  --library 180 \
  --generations 200 \
  --population 60 \
  --verify 10 \
  --verify-retries 5 \
  --output-model /tmp/market_linear.json

echo ""
echo "Asking model with key=11..."
python3 -m flux_evolver question --model /tmp/market_linear.json --key 11 --key-json
