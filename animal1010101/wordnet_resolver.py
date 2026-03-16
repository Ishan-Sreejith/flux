from __future__ import annotations

from typing import List, Tuple


def _load_wordnet():
    try:
        from nltk.corpus import wordnet as wn  # type: ignore

        # Touch data to trigger LookupError if missing.
        _ = wn.synsets("dog")
        return wn
    except Exception:
        try:
            import nltk  # type: ignore

            nltk.download("wordnet", quiet=True)
            nltk.download("omw-1.4", quiet=True)
            from nltk.corpus import wordnet as wn  # type: ignore

            _ = wn.synsets("dog")
            return wn
        except Exception:
            return None


def _lemma_set(synsets, max_depth: int = 5) -> set[str]:
    if synsets is None:
        return set()
    out: set[str] = set()
    for s in synsets:
        stack = [(s, 0)]
        while stack:
            node, depth = stack.pop()
            out.update(node.lemma_names())
            if depth >= max_depth:
                continue
            for h in node.hypernyms():
                stack.append((h, depth + 1))
    return {t.replace("_", " ").lower() for t in out}


def _prime_from_wordnet(wn, word: str) -> str | None:
    synsets = wn.synsets(word)
    if not synsets:
        return None
    lexnames = {s.lexname() for s in synsets}
    if any(x.startswith("animal.") for x in lexnames):
        return "Animal"
    if any(x.startswith("noun.animal") for x in lexnames):
        return "Animal"
    if any(x.startswith("noun.artifact") or x.startswith("noun.object") for x in lexnames):
        return "Object"
    if any(x.startswith("verb.") or x.startswith("noun.act") for x in lexnames):
        return "Action"
    if any(x.startswith("noun.feeling") or x.startswith("noun.emotion") for x in lexnames):
        return "Feeling"
    return None


def _animal_path(tokens: set[str]) -> List[str]:
    mammal = "Mammal" if any(t in tokens for t in ["mammal", "dog", "cat", "cow", "wolf"]) else "Non-Mammal"
    domestic = "Domestic" if any(t in tokens for t in ["domestic", "pet", "tame"]) else "Wild"
    carn = "Carnivore" if any(t in tokens for t in ["carnivore", "predator", "meat", "flesh"]) else "Herbivore"
    return [mammal, domestic, carn]


def _object_path(tokens: set[str]) -> List[str]:
    tool = "Tool" if any(t in tokens for t in ["tool", "device", "instrument", "implement"]) else "Non-Tool"
    mech = "Mechanical" if any(t in tokens for t in ["mechanical", "machine", "engine"]) else "Natural"
    return [tool, mech]


def _action_path(tokens: set[str]) -> List[str]:
    intent = "Intentional" if any(t in tokens for t in ["intentional", "deliberate", "purpose"]) else "Unintentional"
    violence = "Violence" if any(t in tokens for t in ["attack", "violence", "fight", "harm"]) else "Cooperation"
    return [intent, violence]


def _feeling_path(tokens: set[str]) -> List[str]:
    positive = "Positive" if any(t in tokens for t in ["happy", "joy", "pleasure", "positive"]) else "Negative"
    calm = "Calm" if any(t in tokens for t in ["calm", "peace", "relax"]) else "Arousal"
    return [positive, calm]


def resolve_wordnet(word: str) -> Tuple[str, List[str]] | None:
    wn = _load_wordnet()
    if wn is None:
        return None
    prime = _prime_from_wordnet(wn, word)
    if prime is None:
        return None
    synsets = wn.synsets(word)
    tokens = _lemma_set(synsets, max_depth=5)
    if prime == "Animal":
        return prime, _animal_path(tokens)
    if prime == "Object":
        return prime, _object_path(tokens)
    if prime == "Action":
        return prime, _action_path(tokens)
    if prime == "Feeling":
        return prime, _feeling_path(tokens)
    return None

