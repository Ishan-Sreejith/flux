from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

PRESET_GROUPS = {
    "animals_common": [
        "lion","tiger","leopard","cheetah","jaguar","wolf","fox","bear","hyena","otter",
        "dolphin","whale","shark","eagle","owl","falcon","penguin","snake","lizard","frog",
        "toad","crocodile","alligator","horse","deer","elk","moose","bison","antelope","zebra",
        "giraffe","elephant","rhino","hippo","kangaroo","panda","rabbit","mouse","rat","monkey",
        "chimpanzee","gorilla","cow","sheep","goat","pig","dog","cat","chicken","duck","goose",
    ],
    "mammals": [
        "lion","tiger","leopard","cheetah","jaguar","wolf","fox","bear","hyena","otter",
        "dolphin","whale","horse","deer","elk","moose","bison","antelope","zebra","giraffe",
        "elephant","rhino","hippo","kangaroo","panda","rabbit","mouse","rat","monkey",
        "chimpanzee","gorilla","cow","sheep","goat","pig","dog","cat",
    ],
    "reptiles": [
        "snake","lizard","crocodile","alligator",
    ],
    "birds": [
        "eagle","owl","falcon","penguin","chicken","duck","goose",
    ],
    "fish": [
        "shark",
    ],
}


def load_group(name: str) -> dict:
    name = name.strip().lower()
    if name not in PRESET_GROUPS:
        raise ValueError(f"Unknown preset group: {name}")
    presets_path = BASE_DIR / "animal_presets.json"
    presets = json.loads(presets_path.read_text(encoding="utf-8"))
    return {k: presets[k] for k in PRESET_GROUPS[name] if k in presets}
