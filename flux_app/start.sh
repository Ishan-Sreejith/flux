#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
export PYTHONPATH="$ROOT"

"$PYTHON_BIN" -c "from pathlib import Path; (Path('$ROOT')/'flux_app'/'logs').mkdir(parents=True, exist_ok=True)"

"$PYTHON_BIN" -m flux_app.bridge > "$ROOT/flux_app/logs/bridge.log" 2>&1 &
BRIDGE_PID=$!
"$PYTHON_BIN" -m flux_app.backend > "$ROOT/flux_app/logs/backend.log" 2>&1 &
BACKEND_PID=$!
"$PYTHON_BIN" -m http.server 8080 --directory "$ROOT/flux_app/frontend" > "$ROOT/flux_app/logs/frontend.log" 2>&1 &
FRONTEND_PID=$!

printf "Services started. Backend: 3001, Bridge: 5002, Frontend: 8080\n"
printf "Press Ctrl+C to stop all services.\n"

trap "kill $BRIDGE_PID $BACKEND_PID $FRONTEND_PID" INT TERM
wait $BRIDGE_PID $BACKEND_PID $FRONTEND_PID
