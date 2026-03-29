#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${ROOT_DIR}/src:${PYTHONPATH:-}"

DATASET="${1:-${ROOT_DIR}/examples/market_share_linear.json}"
VERIFY_COUNT="${2:-10}"
SEED="${3:-42}"

python3 -m flux_evolver train \
  --dataset "${DATASET}" \
  --library 180 \
  --generations 200 \
  --population 60 \
  --verify "${VERIFY_COUNT}" \
  --verify-retries 5 \
  --seed "${SEED}" \
  --output-model /tmp/flux_model.json

python3 -m flux_evolver question --model /tmp/flux_model.json --key 11 --key-json
