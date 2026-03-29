from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Optional

from .models import Gene, Genome, TrainingSample


def load_samples(path: str) -> List[TrainingSample]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(path)

    if file_path.suffix.lower() == ".json":
        data = json.loads(file_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            samples = []
            for k, v in data.items():
                if isinstance(v, dict) and "Key" in v and "Value" in v:
                    samples.append(TrainingSample(key=v["Key"], value=v["Value"]))
                else:
                    samples.append(TrainingSample(key=k, value=v))
            return samples
        if isinstance(data, list):
            samples = []
            for item in data:
                if isinstance(item, dict) and "Key" in item and "Value" in item:
                    samples.append(TrainingSample(key=item["Key"], value=item["Value"]))
                    continue
                if not isinstance(item, dict) or "key" not in item or "value" not in item:
                    raise ValueError("JSON list items must have key and value")
                samples.append(TrainingSample(key=item["key"], value=item["value"]))
            return samples
        raise ValueError("Unsupported JSON format for samples")

    samples: List[TrainingSample] = []
    for line in file_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "\t" in stripped:
            key, value = stripped.split("\t", 1)
        elif "=>" in stripped:
            key, value = stripped.split("=>", 1)
            key = key.strip()
            value = value.strip()
        else:
            raise ValueError("Unsupported line format; use tab or => separator")
        samples.append(TrainingSample(key=key, value=value))
    return samples


def summarize_samples(samples: List[TrainingSample]) -> dict[str, Any]:
    value_types = {type(sample.value).__name__ for sample in samples}
    key_types = {type(sample.key).__name__ for sample in samples}
    has_numeric_values = any(isinstance(sample.value, (int, float)) for sample in samples)
    has_string_values = any(isinstance(sample.value, str) for sample in samples)
    has_non_numeric_string_keys = any(
        isinstance(sample.key, str) and not _is_numeric_string(sample.key) for sample in samples
    )
    has_numeric_like_keys = any(_is_numeric_string(sample.key) or isinstance(sample.key, (int, float)) for sample in samples)
    return {
        "value_types": sorted(value_types),
        "key_types": sorted(key_types),
        "has_numeric_values": has_numeric_values,
        "has_string_values": has_string_values,
        "has_non_numeric_string_keys": has_non_numeric_string_keys,
        "has_numeric_like_keys": has_numeric_like_keys,
    }


def _is_numeric_string(value: str) -> bool:
    try:
        float(value.strip())
        return True
    except Exception:
        return False


def save_genome(genome: Genome, path: str) -> None:
    payload = {
        "library_size": genome.library_size,
        "genes": [
            {
                "param_id": gene.param_id,
                "randomness": gene.randomness,
                "intensity": gene.intensity,
                "inheritance": gene.inheritance,
            }
            for gene in genome.genes
        ],
    }
    Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def save_bundle(genome: Genome, samples: List[TrainingSample], path: str, metadata: Optional[dict[str, Any]] = None) -> None:
    payload = {
        "metadata": metadata or {},
        "dataset": [{"key": sample.key, "value": sample.value} for sample in samples],
        "genome": {
            "library_size": genome.library_size,
            "genes": [
                {
                    "param_id": gene.param_id,
                    "randomness": gene.randomness,
                    "intensity": gene.intensity,
                    "inheritance": gene.inheritance,
                }
                for gene in genome.genes
            ],
        },
    }
    Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def append_to_store(path: str, samples: List[TrainingSample]) -> None:
    store_path = Path(path)
    store_path.parent.mkdir(parents=True, exist_ok=True)
    existing: List[TrainingSample] = []
    if store_path.exists():
        data = json.loads(store_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and "key" in item and "value" in item:
                    existing.append(TrainingSample(key=item["key"], value=item["value"]))
        elif isinstance(data, dict):
            for k, v in data.items():
                existing.append(TrainingSample(key=k, value=v))
    combined = existing + samples
    payload = [{"key": sample.key, "value": sample.value} for sample in combined]
    store_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def load_store(path: str) -> List[TrainingSample]:
    if not Path(path).exists():
        return []
    return load_samples(path)


def load_genome(path: str) -> Genome:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Invalid genome file")
    library_size = int(payload.get("library_size", 0))
    genes_payload = payload.get("genes", [])
    if library_size < 1:
        raise ValueError("Genome file missing library_size")
    genes: List[Gene] = []
    for item in genes_payload:
        genes.append(
            Gene(
                param_id=int(item["param_id"]),
                randomness=float(item["randomness"]),
                intensity=float(item["intensity"]),
                inheritance=str(item.get("inheritance", "dominant")),
            )
        )
    genome = Genome(genes=genes, library_size=library_size)
    genome.clamp()
    return genome
