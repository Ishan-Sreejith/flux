import json
from pathlib import Path
from typing import Dict, List

from master_ai.core.internet_access import search as master_search
from mutable import brain as mutable_brain

from .utils import tokenize

ROOT = Path(__file__).resolve().parents[1]
LEXICON_PATH = ROOT / "animal1010101" / "lexicon.json"
TAXONOMY_PATH = ROOT / "animal1010101" / "taxonomy.json"

_LEXICON: dict = {}
_TAXONOMY: dict = {}


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _ensure_loaded() -> None:
    global _LEXICON, _TAXONOMY
    if not _LEXICON:
        _LEXICON = _load_json(LEXICON_PATH)
    if not _TAXONOMY:
        _TAXONOMY = _load_json(TAXONOMY_PATH)


def _guess_prime(word: str) -> str:
    if any(k in word for k in ["dog", "cat", "wolf", "bird", "fish"]):
        return "Animal"
    if any(k in word for k in ["apple", "banana", "bread", "steak", "fruit", "food"]):
        return "Food"
    if any(k in word for k in ["feel", "happy", "sad", "fear"]):
        return "Feeling"
    if any(k in word for k in ["run", "fight", "hug", "move"]):
        return "Action"
    return "Object"


def _path_guess_from_tokens(text: str, prime: str) -> List[str]:
    low = text.lower()
    if prime == "Animal":
        mammal = "Mammal" if any(k in low for k in ["mammal", "dog", "cat", "cow", "wolf"]) else "Non-Mammal"
        domestic = "Domestic" if any(k in low for k in ["domestic", "pet", "tame"]) else "Wild"
        carn = "Carnivore" if any(k in low for k in ["carnivore", "predator", "meat"]) else "Herbivore"
        return [mammal, domestic, carn]
    if prime == "Object":
        tool = "Tool" if any(k in low for k in ["tool", "device", "instrument"]) else "Non-Tool"
        mech = "Mechanical" if any(k in low for k in ["mechanical", "engine", "machine"]) else "Natural"
        return [tool, mech]
    if prime == "Action":
        violence = "Violence" if any(k in low for k in ["attack", "violence", "fight", "harm"]) else "Cooperation"
        return [violence]
    if prime == "Feeling":
        positive = "Positive" if any(k in low for k in ["happy", "joy", "pleasure", "positive"]) else "Negative"
        calm = "Calm" if any(k in low for k in ["calm", "peace", "relax"]) else "Arousal"
        return [positive, calm]
    if prime == "Food":
        fruit = "Fruit" if any(k in low for k in ["fruit", "apple", "banana", "berry"]) else "Non-Fruit"
        fresh = "Fresh" if any(k in low for k in ["fresh", "raw"]) else "Cooked"
        return [fruit, fresh]
    return []


def _lexicon_entry(term: str) -> dict:
    _ensure_loaded()
    return _LEXICON.get(term.lower(), {})


def _traits_from_path(path: List[str]) -> str:
    if not path:
        return ""
    return " -> ".join(path)


def experimental_sources(question: str) -> List[Dict]:
    tokens = [t for t in tokenize(question) if len(t) > 2]
    main = tokens[0] if tokens else question.strip().split()[0] if question.strip() else ""
    entry = _lexicon_entry(main) if main else {}
    prime = entry.get("prime") or _guess_prime(question.lower())
    path = entry.get("path") or _path_guess_from_tokens(question, prime)
    trait_summary = _traits_from_path(path)
    exp_sources: List[Dict] = []

    if trait_summary:
        exp_sources.append(
            {
                "summary": f"Experimental traits: {prime} -> {trait_summary}",
                "url": "",
                "source": "animal1010101",
            }
        )

    try:
        items = master_search(question, max_results=3)
    except Exception:
        items = []
    for item in items:
        exp_sources.append(
            {
                "summary": item.get("snippet", ""),
                "url": item.get("url", ""),
                "source": item.get("source", "master_ai"),
            }
        )

    try:
        brain_text = mutable_brain.answer(question, items, None)
        if brain_text:
            exp_sources.append(
                {
                    "summary": brain_text,
                    "url": "",
                    "source": "mutable_brain",
                }
            )
    except Exception:
        pass

    return [s for s in exp_sources if s.get("summary")]
