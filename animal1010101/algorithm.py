from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from animal1010101.engine import LexicalEngine
from animal1010101.grammar import (
    content_filter,
    detect_intent,
    merge_phrases,
    tag_tokens,
    tokenize,
)
from animal1010101.grammar import SHORT_KEEP


@dataclass
class SimplifiedResult:
    raw_tokens: List[str]
    tokens: List[str]
    encodings: List[str]
    parameters: Dict[str, float]
    intent: Tuple[str, str]
    pos_tags: List[Tuple[str, str]]
    primary_prime: str
    primary_path: List[str]
    primary_source: str


def content_tokens(text: str, engine: LexicalEngine | None = None) -> List[str]:
    tokens = tokenize(text)
    if engine:
        phrases = [k for k in list(engine.lexicon.keys()) + list(engine.lexicon_auto.keys()) if " " in k]
        tokens = merge_phrases(tokens, phrases)
    tagged = tag_tokens(tokens)
    content = content_filter(tagged)
    if engine:
        vocab = set(engine.lexicon.keys()) | set(engine.lexicon_auto.keys())
        return [resolve_token(t.lemma, vocab, t.pos) for t in content]
    return [t.lemma for t in content]


def _edit_distance(a: str, b: str, max_dist: int = 2) -> int:
    if abs(len(a) - len(b)) > max_dist:
        return max_dist + 1
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        best_row = i
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            cur_val = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
            cur.append(cur_val)
            best_row = min(best_row, cur_val)
        if best_row > max_dist:
            return max_dist + 1
        prev = cur
    return prev[-1]


def resolve_token(token: str, vocab: set[str], pos: str) -> str:
    if token in vocab or token in SHORT_KEEP:
        return token
    if not token:
        return token
    if pos == "verb":
        return token
    if len(token) < 5:
        return token
    candidates = [w for w in vocab if w and w[0] == token[0] and abs(len(w) - len(token)) <= 2]
    best = None
    best_dist = 3
    for w in candidates:
        dist = _edit_distance(token, w, max_dist=2)
        if dist < best_dist:
            best_dist = dist
            best = w
            if dist == 1:
                break
    if best_dist == 1:
        return best or token
    return token


def _weight_for_pos(pos: str) -> float:
    if pos == "noun":
        return 1.0
    if pos == "verb":
        return 0.8
    if pos == "adv":
        return 0.5
    return 0.6


def simplify(text: str, engine: LexicalEngine) -> SimplifiedResult:
    raw_tokens = tokenize(text)
    tokens = list(raw_tokens)
    phrases = [k for k in list(engine.lexicon.keys()) + list(engine.lexicon_auto.keys()) if " " in k]
    tokens = merge_phrases(tokens, phrases)
    tagged = tag_tokens(tokens)
    intent = detect_intent([t.lemma for t in tagged])

    content = content_filter(tagged)
    vocab = set(engine.lexicon.keys()) | set(engine.lexicon_auto.keys())
    encodings: List[str] = []
    params: Dict[str, float] = {}
    total_weight = 0.0
    resolved_tokens: List[str] = []
    primary_prime = "Object"
    primary_path: List[str] = []
    primary_source = "unknown"

    for t in content:
        lemma = resolve_token(t.lemma, vocab, t.pos)
        res = engine.encode(lemma)
        encodings.append(f"{res.prime}{res.bitstring}")
        resolved_tokens.append(lemma)
        if not primary_path:
            primary_prime = res.prime
            primary_path = res.path
            if lemma in engine.lexicon:
                primary_source = "lexicon"
            elif lemma in engine.lexicon_auto:
                primary_source = "lexicon_auto"
            else:
                primary_source = "unknown"
        weight = _weight_for_pos(t.pos)
        total_weight += weight
        for k, v in res.parameters.items():
            params[k] = params.get(k, 0.0) + float(v) * weight

    if total_weight > 0:
        for k in list(params.keys()):
            params[k] = params[k] / total_weight

    pos_tags = [(resolved_tokens[i], content[i].pos) for i in range(len(content))]
    return SimplifiedResult(
        raw_tokens=raw_tokens,
        tokens=resolved_tokens,
        encodings=encodings,
        parameters=params,
        intent=intent,
        pos_tags=pos_tags,
        primary_prime=primary_prime,
        primary_path=primary_path,
        primary_source=primary_source,
    )


def context_rewrite(token: str, params: Dict[str, float]) -> str:
    if params.get("p12", 0) > 0.7:
        return "edible"
    if params.get("p13", 0) > 0.7:
        return "sweet"
    if params.get("p14", 0) > 0.7:
        return "carnivorous"
    if params.get("p5", 0) > 0.7:
        return "domestic"
    if params.get("p2", 0) > 0.7:
        return "aggressive"
    if params.get("p9", 0) > 0.7:
        return "dangerous"
    if params.get("p7", 0) > 0.7:
        return "tool"
    if params.get("p8", 0) > 0.7:
        return "artificial"
    if params.get("p8", 0) < 0.3:
        return "natural"
    if params.get("p10", 0) > 0.7:
        return "friendly"
    if params.get("p1", 0) > 0.7:
        return "large"
    if params.get("p1", 0) < 0.3:
        return "small"
    return token
