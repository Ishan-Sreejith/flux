#!/bin/bash

# Ecosystem Simulation Test Suite
export PYTHONPATH="/Users/ishan/flux/src:$PYTHONPATH"

echo "🧪 Ecosystem Simulation Test Suite"
echo "===================================="
echo ""
echo "PYTHONPATH=$PYTHONPATH"
echo ""

echo "✅ Test 1: World Engine (100 ticks, seed 42)..."
python3 /Users/ishan/flux/src/eco_sim/demo/run_demo.py 100 42

echo ""
echo "✅ Test 2: World Engine (50 ticks, seed 99)..."
python3 /Users/ishan/flux/src/eco_sim/demo/run_demo.py 50 99

echo ""
echo "✅ Test 3: World Engine (200 ticks, seed 123)..."
python3 /Users/ishan/flux/src/eco_sim/demo/run_demo.py 200 123

echo ""
echo "===================================="
echo "🎉 All demo tests completed!"
echo "===================================="



