from __future__ import annotations

from typing import Dict, List


def answer(prompt: str, learned: List[Dict[str, str]] | None = None) -> str:
    prompt = (prompt or "").strip()
    if not prompt:
        return "Please ask a specific question."

    facts = []
    if learned:
        tokens = {t for t in prompt.lower().split() if len(t) > 3}
        scored = []
        for row in learned:
            text = str(row.get("fact", "")).strip()
            if not text:
                continue
            low = text.lower()
            overlap = sum(1 for t in tokens if t in low)
            scored.append((overlap, text))
        scored.sort(key=lambda x: x[0], reverse=True)
        for score, text in scored:
            if score <= 0 and facts:
                break
            facts.append(text)
            if len(facts) >= 3:
                break

    parts = [f"Answer to: {prompt}"]
    if facts:
        parts.append("Learned facts: " + " | ".join(facts))
    else:

        parts.append(
            "Definition: describe the concept in one sentence, then add a simple example and a practical implication."
        )
        low = prompt.lower()
        if "overfitting" in low:
            parts.append(
                "Example: a model memorizes training data and fails on new data; use validation and regularization to reduce it."
            )
        elif "artificial intelligence" in low or "ai" in low:
            parts.append(
                "Example: a classifier that labels emails as spam vs. not spam based on patterns in past data."
            )
        elif "gradient descent" in low:
            parts.append(
                "Example: iteratively adjust parameters opposite the gradient to reduce the loss."
            )
        else:
            parts.append("Example: define a small real-world case that shows the concept in action.")
    return " ".join(parts)
