Flux Evolver
============

Flux Evolver is a small evolutionary system that learns simple input‑to‑output transformations from examples. It creates many agents with random “genes” (operations like add, subtract, first letter, etc.), scores them against a dataset, keeps the best half, and mixes genes from the top performers to create the next generation. Training stops when accuracy reaches a target or when the maximum number of generations is reached.

What it does
------------
- Reads a JSON dataset of key/value pairs.
- Evolves agents to match the values from the keys.
- Outputs an algorithm key (the ordered list of operations) for the best agent.
- Lets you reuse the saved genome to answer new questions.

Quick start
-----------
Install locally and run:

```
export PYTHONPATH="/Users/ishan/flux/src:$PYTHONPATH"
flux train --dataset /Users/ishan/flux/example_data.json --output-model /tmp/flux_model.json
flux question --model /tmp/flux_model.json --key 6
```

Dataset format
--------------
The dataset is JSON and supports either a list or a dictionary:

List form:
```
[
  {"Key": 1, "Value": 6},
  {"Key": 2, "Value": 7}
]
```

Dictionary form:
```
{
  "Sample_01": {"Key": 1, "Value": 6},
  "Sample_02": {"Key": 2, "Value": 7}
}
```

CLI commands
------------
Train:
```
flux train --dataset /path/to/data.json --population 200 --genome-length 8 --param-count 1000
```

Ask:
```
flux question --model /tmp/flux_model.json --key 10
```

Interactive:
```
flux
```

Web demo
--------
The GitHub Pages demo is in the `docs/` folder. Set Pages to the `master` branch and `/docs` folder.

