#!/bin/bash
# Simple push script for Flux Evolver project

echo "--- Committing changes ---"
git add .
git commit -m "Flux Evolver IDE v0.0.3: Improved stability and example presets"

echo "--- Pushing to master ---"
git push origin master

echo "--- Deployment trigger complete ---"
