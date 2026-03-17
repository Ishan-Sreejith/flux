from __future__ import annotations

from typing import List


RULES = [
    ("negative", "This is likely an unpleasant or adverse state."),
    ("domesticated", "Often lives alongside humans."),
    ("carnivorous", "Diet likely includes meat."),
    ("herbivorous", "Diet likely includes plants."),
    ("aquatic", "It typically lives in or around water."),
    ("flying", "It can travel through the air."),
    ("nocturnal", "It is more active at night."),
    ("social", "It tends to live or act in groups."),
    ("wild", "It is not domesticated and lives in natural habitats."),
    ("tool-like", "Typically used to perform tasks."),
    ("artificial", "Human-made rather than natural."),
    ("dangerous", "Use caution when interacting."),
    ("friendly", "Likely approachable or social."),
    ("intelligent", "Can learn or adapt over time."),
    ("edible", "Can be consumed as food."),
    ("large", "Its physical size is relatively large."),
    ("small", "Its physical size is relatively small."),
    ("agentic", "It can initiate actions or respond to goals."),
]

PRIME_RULES = {
    "Animal": "It is a living organism with biological needs.",
    "Food": "It is intended for consumption.",
    "Action": "It represents an action or process.",
    "Feeling": "It represents an internal emotional state.",
    "Object": "It represents a physical or conceptual object.",
}


def reason(traits: List[str], prime: str) -> List[str]:
    notes: List[str] = []
    if prime in PRIME_RULES:
        notes.append(PRIME_RULES[prime])
    if "artificial" in traits and "tool-like" in traits:
        notes.append("It is likely designed for a specific purpose.")
    if "domesticated" in traits and "friendly" in traits:
        notes.append("Human interaction is typically safe and encouraged.")
    for key, sentence in RULES:
        if key in traits:
            notes.append(sentence)

    seen = set()
    out: List[str] = []
    for n in notes:
        if n in seen:
            continue
        seen.add(n)
        out.append(n)
    return out
