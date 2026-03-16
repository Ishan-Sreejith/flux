from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from animal1010101.wikidata_lookup import category_entities

BASE_DIR = Path(__file__).resolve().parent

CATEGORY_QIDS = {
    "mammals": "Q7377",
    "birds": "Q5113",
    "reptiles": "Q10811",
    "amphibians": "Q10908",
    "fish": "Q152",
    "insects": "Q1390",
}

CARNIVORE = {
    "lion","tiger","leopard","cheetah","jaguar","wolf","fox","bear","hyena","shark","crocodile",
    "alligator","eagle","hawk","falcon","owl","snake","lizard","frog","toad","otter","seal","dolphin",
    "whale","puma","cougar","lynx","panther","weasel","badger","wolverine","raccoon","vulture",
}

DOMESTIC = {"dog","cat","cow","sheep","goat","pig","chicken","duck","goose","horse"}

AQUATIC = {"shark","dolphin","whale","otter","seal","hippo","crocodile","alligator","penguin"}

FLYING = {"eagle","hawk","falcon","owl","vulture","sparrow","pigeon","crow","raven","parrot"}


def _chunks(items: list[str], size: int) -> Iterable[list[str]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _path_for(label: str, category: str) -> list[str]:
    w = label.lower()
    mammal = "Mammal" if category == "mammals" else "Non-Mammal"
    domestic = "Domestic" if w in DOMESTIC else "Wild"
    diet = "Carnivore" if w in CARNIVORE else "Herbivore"
    return [mammal, domestic, diet]


def _overrides_for(label: str) -> dict:
    w = label.lower()
    overrides = {}
    if w in AQUATIC:
        overrides["p15"] = 0.9
    if w in FLYING:
        overrides["p16"] = 0.9
    if w in {"elephant","rhino","hippo"}:
        overrides["p1"] = 0.95
    if w in {"mouse","rat"}:
        overrides["p1"] = 0.15
    return overrides


def build_animals(limit_per_category: int = 120) -> dict:
    results: dict = {}
    for label, qid in CATEGORY_QIDS.items():
        items = category_entities(qid, limit=limit_per_category)
        for item in items:
            word = item.strip().lower()
            if not word:
                continue
            if word in results:
                continue
            path = _path_for(word, label)
            entry = {"prime": "Animal", "path": path}
            overrides = _overrides_for(word)
            if overrides:
                entry["overrides"] = overrides
            results[word] = entry
    return results


def save_animals(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
