from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from animal1010101.engine import LexicalEngine
from animal1010101.wikidata_lookup import category_entities


CATEGORY_QIDS = {
    "mammals": "Q7377",
    "reptiles": "Q10811",
    "birds": "Q5113",
    "fish": "Q3314483",
    "vehicles": "Q42889",
    "tools": "Q39546",
}

ANIMAL_HERBIVORES = {
    "deer",
    "horse",
    "cow",
    "sheep",
    "goat",
    "zebra",
    "rhino",
    "hippo",
    "kangaroo",
    "panda",
    "camel",
    "moose",
    "bison",
    "giraffe",
    "elephant",
    "rabbit",
}

ANIMAL_CARNIVORES = {
    "lion",
    "tiger",
    "wolf",
    "bear",
    "fox",
    "otter",
    "shark",
    "eagle",
    "owl",
    "falcon",
    "penguin",
    "snake",
    "lizard",
    "frog",
    "toad",
    "seal",
}

NON_MAMMALS = {"eagle", "owl", "falcon", "penguin", "snake", "lizard", "frog", "toad", "shark"}

FOOD_FRUITS = {
    "apple",
    "banana",
    "orange",
    "grape",
    "mango",
    "strawberry",
    "pear",
    "peach",
}

FOOD_OTHER = {
    "bread",
    "rice",
    "pasta",
    "cheese",
    "milk",
    "egg",
    "chicken",
    "beef",
    "fish",
    "carrot",
    "potato",
    "tomato",
}

EMOTIONS_NEG = {"fear", "anger", "sadness", "anxiety", "shame"}
EMOTIONS_POS = {"joy", "peace", "calm", "pride", "surprise"}

VERBS_VIOLENCE = {"fight", "attack"}
VERBS_COOP = {"hug", "help", "build", "learn", "teach", "travel", "cook", "run"}

AQUATIC = {"dolphin", "whale", "shark", "seal", "otter", "penguin"}
FLYING = {"eagle", "owl", "falcon"}
NOCTURNAL = {"owl"}
SOCIAL = {"dolphin", "chimpanzee", "gorilla", "monkey", "wolf"}


def _animal_path(word: str) -> list[str]:
    w = word.lower()
    if w in NON_MAMMALS:
        mammal = "Non-Mammal"
    else:
        mammal = "Mammal"
    if w in ANIMAL_HERBIVORES:
        diet = "Herbivore"
    else:
        diet = "Carnivore"
    return [mammal, "Wild", diet]


def _food_path(word: str) -> list[str]:
    w = word.lower()
    if w in FOOD_FRUITS:
        return ["Fruit", "Fresh"]
    return ["Non-Fruit", "Cooked"]


def _emotion_path(word: str) -> list[str]:
    w = word.lower()
    if w in EMOTIONS_NEG:
        return ["Arousal"]
    return ["Calm"]


def _verb_path(word: str) -> list[str]:
    w = word.lower()
    if w in VERBS_VIOLENCE:
        return ["Violence"]
    return ["Cooperation"]


def expand(limit: int = 100) -> Dict[str, dict]:
    base_dir = Path(__file__).resolve().parent
    engine = LexicalEngine(base_dir)
    results: Dict[str, dict] = {}

    for name, qid in CATEGORY_QIDS.items():
        items = category_entities(qid, limit=limit)
        for item in items:
            res = engine.learn(item)
            results[item.lower()] = {"prime": res.prime, "path": res.path}

    for w in ANIMAL_HERBIVORES | ANIMAL_CARNIVORES | NON_MAMMALS:
        overrides = {}
        if w in AQUATIC:
            overrides["p15"] = 0.9
        if w in FLYING:
            overrides["p16"] = 0.9
        if w in NOCTURNAL:
            overrides["p17"] = 0.9
        if w in SOCIAL:
            overrides["p18"] = 0.9
        results[w] = {"prime": "Animal", "path": _animal_path(w), "overrides": overrides}

    for w in FOOD_FRUITS | FOOD_OTHER:
        results[w] = {"prime": "Food", "path": _food_path(w)}

    for w in EMOTIONS_NEG | EMOTIONS_POS:
        results[w] = {"prime": "Feeling", "path": _emotion_path(w)}

    for w in VERBS_VIOLENCE | VERBS_COOP:
        results[w] = {"prime": "Action", "path": _verb_path(w)}

    return results


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    out = base_dir / "lexicon_auto_expanded.json"
    data = expand(limit=120)
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Expanded lexicon saved to {out}")
