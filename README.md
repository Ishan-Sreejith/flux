# Flux Evolver

Flux Evolver is a local, deterministic evolutionary engine for discovering simple transformation recipes from input/output pairs. It includes a CLI, an interactive ask mode, and a GitHub Pages demo.

## Quick Start

```bash
export PYTHONPATH="/Users/ishan/flux/src:$PYTHONPATH"
flux train --example market --verify 6 --verify-tolerance 0.5
flux question --model /tmp/flux_model.json --key 11
```

## Ask Mode

```bash
flux
```

Commands inside ask mode:

- `;train example:market`
- `;parameters library=180 generations=200 population=60 verify=6 verify_tolerance=0.5`
- `;exit`

## Built-in Examples

```bash
flux examples
flux demo --example voyager
```

Examples are stored in `/Users/ishan/flux/examples`.

## GitHub Pages Demo

The static demo lives in `/docs`. Publish it by setting GitHub Pages to the `/docs` folder on the main branch.

## Scripts

- `/Users/ishan/flux/scripts/run_all.sh`
- `/Users/ishan/flux/scripts/solar_train.sh`
- `/Users/ishan/flux/scripts/voyager_train.sh`
- `/Users/ishan/flux/scripts/ensemble_manager.sh`

