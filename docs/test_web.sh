#!/usr/bin/env zsh
set -euo pipefail

ROOT="/Users/ishan/flux/docs"

echo "[1/3] Basic file checks"
[[ -f "$ROOT/index.html" ]] || { echo "Missing index.html"; exit 1; }
[[ -f "$ROOT/styles.css" ]] || { echo "Missing styles.css"; exit 1; }
[[ -f "$ROOT/app.js" ]] || { echo "Missing app.js"; exit 1; }

echo "[2/3] Feature hooks checks"
grep -q "theme-comfort" "$ROOT/index.html"
grep -q "btnAutoformat" "$ROOT/index.html"
grep -q "btnGenerateHuman" "$ROOT/index.html"
grep -q "guideCard" "$ROOT/index.html"
grep -q "appVersion" "$ROOT/app.js"
grep -q "generateHumanAlgorithm" "$ROOT/app.js"

echo "[3/3] Version badge check"
grep -q "buildVersion" "$ROOT/index.html"

echo "All web smoke checks passed."

