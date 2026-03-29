from __future__ import annotations

import json
from pathlib import Path
from typing import List

from .models import Gene, Genome, TrainingSample


def load_samples(path: str) -> List[TrainingSample]:
    file_path = Path(path)
    data = json.loads(file_path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [TrainingSample(key=item.get("Key", item.get("key")), value=item.get("Value", item.get("value"))) for item in data]
    if isinstance(data, dict):
        samples = []
        for _, v in data.items():
            if isinstance(v, dict) and "Key" in v and "Value" in v:
                samples.append(TrainingSample(key=v["Key"], value=v["Value"]))
            else:
                samples.append(TrainingSample(key=_, value=v))
        return samples
    raise ValueError("Unsupported dataset format")


def save_genome(genome: Genome, path: str) -> None:
    payload = {
        "genes": [{"param_id": gene.param_id, "strength": gene.strength} for gene in genome.genes],
    }
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_genome(path: str) -> Genome:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    genes = [Gene(param_id=item["param_id"], strength=item["strength"]) for item in payload["genes"]]
    return Genome(genes=genes)

