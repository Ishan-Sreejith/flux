from __future__ import annotations

import hashlib
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TONE_DATA_PATH = BASE_DIR / "tone_data.json"

_TONE_DATA: dict | None = None


def _load() -> dict:
    global _TONE_DATA
    if _TONE_DATA is None:
        _TONE_DATA = json.loads(TONE_DATA_PATH.read_text(encoding="utf-8"))
    return _TONE_DATA


def _stable_choice(items: list[str], seed: str) -> str:
    if not items:
        return ""
    h = hashlib.md5(seed.encode("utf-8")).hexdigest()
    idx = int(h, 16) % len(items)
    return items[idx]


def tone_from_params(params: dict) -> str:
    if params.get("p2", 0) > 0.7 or params.get("p9", 0) > 0.7:
        return "intense"
    if params.get("p10", 0) < 0.4:
        return "somber"
    if params.get("p10", 0) >= 0.7:
        return "warm"
    if params.get("p18", 0) >= 0.7:
        return "curious"
    if params.get("p3", 0) >= 0.7:
        return "analytical"
    return "neutral"


def tone_from_tokens(tokens: list[str]) -> str | None:
    data = _load()
    tone_map = data.get("tone_map", {})
    for t in tokens:
        if t in tone_map:
            return str(tone_map[t])
    return None


def pick_tone(params: dict, tokens: list[str]) -> str:
    token_tone = tone_from_tokens(tokens)
    if token_tone:
        return token_tone
    return tone_from_params(params)


def render_with_tone(subject: str, prime: str, traits: list[str], tone: str) -> str:
    data = _load()
    styles = data.get("tone_styles", {})
    style = styles.get(tone, styles.get("neutral", {}))
    prefix = _stable_choice(style.get("prefixes", []), subject + tone)
    copula = _stable_choice(style.get("copulas", []), subject + prime)
    closer = _stable_choice(style.get("closers", []), subject)

    trait_text = ", ".join(traits[:5]) if traits else ""
    if trait_text:
        body = f"{subject} {copula} a {prime.lower()} that tends to be {trait_text}"
    else:
        body = f"{subject} {copula} a {prime.lower()} in this schema"

    parts = [p for p in [prefix, body, closer] if p]
    if prefix and prefix[-1].isalnum():
        parts[0] = prefix + ":"
    return " ".join(parts) + "."
