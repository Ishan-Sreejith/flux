from __future__ import annotations

import json
from pathlib import Path

from animal1010101.wikidata_lookup import get_entities, search_entities
from animal1010101.weights import load_weights, save_weights


FEATURES = [
    "label_exact",
    "label_contains",
    "desc_animal",
    "desc_tech",
    "desc_name",
    "type_positive",
    "type_negative",
]

POSITIVE_TYPES = {
    "Q16521",
    "Q7432",
    "Q7377",
    "Q729",
    "Q5113",
    "Q10811",
    "Q10908",
    "Q1390",
    "Q756",
}

NEGATIVE_TYPES = {
    "Q5",
    "Q202444",
    "Q101352",
    "Q41298",
    "Q571",
    "Q11424",
    "Q7366",
    "Q482994",
}


def _instance_of(entity: dict) -> set[str]:
    claims = entity.get("claims", {}).get("P31", [])
    ids: set[str] = set()
    for claim in claims:
        val = claim.get("mainsnak", {}).get("datavalue", {}).get("value", {})
        if isinstance(val, dict) and "id" in val:
            ids.add(val["id"])
    return ids


def features(term: str, hit: dict, entity: dict | None) -> dict:
    term_lower = term.lower()
    label = hit.get("label", "").lower()
    desc = (hit.get("description", "") or "").lower()
    feat = {
        "label_exact": 1.0 if label == term_lower else 0.0,
        "label_contains": 1.0 if term_lower in label else 0.0,
        "desc_animal": 1.0 if any(k in desc for k in ["animal", "mammal", "species", "bird", "fish"]) else 0.0,
        "desc_tech": 1.0 if any(k in desc for k in ["computer", "software", "technology", "intelligent"]) else 0.0,
        "desc_name": 1.0 if any(k in desc for k in ["given name", "family name"]) else 0.0,
        "type_positive": 0.0,
        "type_negative": 0.0,
    }
    if entity:
        types = _instance_of(entity)
        feat["type_positive"] = 1.0 if types & POSITIVE_TYPES else 0.0
        feat["type_negative"] = 1.0 if types & NEGATIVE_TYPES else 0.0
    return feat


def score(w: dict, feat: dict) -> float:
    return sum(w.get(k, 0.0) * feat.get(k, 0.0) for k in FEATURES) + w.get("bias", 0.0)


def train(dataset_path: Path, out_path: Path, epochs: int = 10, lr: float = 0.3) -> None:
    data = json.loads(dataset_path.read_text(encoding="utf-8"))
    weights = load_weights(out_path)
    if not weights:
        weights = {"bias": 0.0}
        for f in FEATURES:
            weights[f] = 0.0

    for _ in range(epochs):
        for row in data:
            term = row["term"]
            correct = row["correct_id"]
            hits = search_entities(term, limit=6)
            entities = get_entities([h.get("id", "") for h in hits])
            feat_map = []
            for h in hits:
                ent = entities.get(h.get("id", "")) if entities else None
                feat = features(term, h, ent)
                feat_map.append((h.get("id", ""), feat))

            correct_feat = None
            for hid, feat in feat_map:
                if hid == correct:
                    correct_feat = feat
                    break
            if not correct_feat:
                continue


            for hid, feat in feat_map:
                if hid == correct:
                    continue
                if score(weights, correct_feat) <= score(weights, feat):
                    for f in FEATURES:
                        weights[f] = weights.get(f, 0.0) + lr * (correct_feat.get(f, 0.0) - feat.get(f, 0.0))
                    weights["bias"] = weights.get("bias", 0.0) + lr * 0.1

    save_weights(out_path, weights)


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    train(base_dir / "disambig_data.json", base_dir / "disambig_weights.json")
