from __future__ import annotations

from typing import Dict, List


SYSTEM_STYLE = "clear, concise, factual"
LEARNED_TERMS = ["gradient", "optimization", "generalization"]


def _pick_focus_terms(prompt: str) -> List[str]:
    low = prompt.lower()
    terms = []
    if "overfitting" in low:
        terms.extend(["overfitting", "validation", "regularization"])
    if "gradient" in low or "descent" in low:
        terms.extend(["gradient", "learning rate", "local minimum"])
    if "supervised" in low or "unsupervised" in low:
        terms.extend(["supervised", "unsupervised", "labels"])
    if not terms:
        terms.extend(LEARNED_TERMS[:3])
    # Preserve order while dropping duplicates.
    seen = set()
    out: List[str] = []
    for t in terms:
        if t not in seen:
            out.append(t)
            seen.add(t)
    return out


def _select_memory_facts(prompt: str, memory: List[Dict[str, str]] | None) -> List[str]:
    if not memory:
        return []
    tokens = {t for t in prompt.lower().split() if len(t) > 3}
    scored: List[tuple[int, str]] = []
    for row in memory:
        text = str(row.get("fact", "")).strip()
        if not text:
            continue
        low = text.lower()
        overlap = sum(1 for t in tokens if t in low)
        scored.append((overlap, text))
    scored.sort(key=lambda x: x[0], reverse=True)
    out: List[str] = []
    for score, text in scored:
        if score <= 0 and out:
            break
        out.append(text)
        if len(out) >= 2:
            break
    return out


def _example_for_terms(terms: List[str]) -> str:
    low = [t.lower() for t in terms]
    if any("overfitting" in t for t in low):
        return "For example, if a model memorizes the training set, hold out validation data and apply regularization to reduce overfitting."
    if any("gradient" in t for t in low):
        return "For example, in gradient descent you compute the gradient on a batch and step opposite to it with a tuned learning rate."
    if any("supervised" in t for t in low):
        return "For example, supervised learning uses labeled pairs (image, label), while unsupervised clusters unlabeled data."
    return "For example, start with the core definition, state one concrete scenario, and show what to do next."


def answer(
    prompt: str,
    research: List[Dict[str, str]] | None = None,
    learned_memory: List[Dict[str, str]] | None = None,
) -> str:
    """Return a natural-language answer using any learned memory facts."""
    prompt = (prompt or "").strip()
    if not prompt:
        return "Please ask a specific question so I can help."

    focus = _pick_focus_terms(prompt)
    memory_facts = _select_memory_facts(prompt, learned_memory)

    parts: List[str] = []
    parts.append(f"Here's a clear answer to \"{prompt}\":")

    if memory_facts:
        parts.append("Key points I've learned: " + " | ".join(memory_facts))
    else:
        parts.append("Key points: " + ", ".join(focus))

    parts.append(_example_for_terms(focus))
    parts.append("Practical next step: write it in your own words and test it on a small example to check understanding.")

    return " ".join(parts)
