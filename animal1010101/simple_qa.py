from __future__ import annotations

import argparse
import math
from pathlib import Path

from animal1010101.algorithm import simplify
from animal1010101.engine import LexicalEngine
from animal1010101.wikidata_lookup import describe, describe_many, taxonomy_for
from animal1010101.weights import load_weights
from animal1010101.reasoning import reason
from animal1010101.tone import pick_tone, render_with_tone


def search_web(question: str, engine: LexicalEngine, tokens: list[str]) -> str:
    candidates: list[str] = []
    if tokens:
        candidates.append(" ".join(tokens[:3]))
    candidates.append(question)
    candidates.extend(tokens[:6])
    results = describe_many(candidates)
    for c in candidates:
        desc = results.get(c, "")
        if desc:
            return desc
    return ""


TRAITS = [
    "negative",
    "edible",
    "sweet",
    "carnivorous",
    "herbivorous",
    "domesticated",
    "wild",
    "aquatic",
    "flying",
    "nocturnal",
    "social",
    "aggressive",
    "dangerous",
    "tool-like",
    "artificial",
    "natural",
    "friendly",
    "large",
    "small",
    "intelligent",
    "agentic",
]

PRIMES = ["Animal", "Object", "Action", "Feeling", "Food"]


def _dot(w: dict, x: dict) -> float:
    return sum(w.get(k, 0.0) * x.get(k, 0.0) for k in x.keys()) + w.get("bias", 0.0)


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _trait_list(params: dict, weights: dict | None) -> list[str]:
    if weights:
        traits = []
        for t in TRAITS:
            w = weights.get(t, {})
            if not w:
                continue
            if _sigmoid(_dot(w, params)) >= 0.55:
                traits.append(t)
        # Merge rule-based traits to avoid missing obvious signals.
        rule_traits = _trait_list(params, None)
        for t in rule_traits:
            if t not in traits:
                traits.append(t)
        return traits
    traits: list[str] = []
    if params.get("p10", 0) < 0.4:
        traits.append("negative")
    if params.get("p12", 0) > 0.7:
        traits.append("edible")
    if params.get("p13", 0) > 0.7:
        traits.append("sweet")
    if params.get("p14", 0) > 0.7:
        traits.append("carnivorous")
    if params.get("p20", 0) > 0.7:
        traits.append("herbivorous")
    if params.get("p5", 0) > 0.7:
        traits.append("domesticated")
    if params.get("p19", 0) > 0.7:
        traits.append("wild")
    if params.get("p15", 0) > 0.7:
        traits.append("aquatic")
    if params.get("p16", 0) > 0.7:
        traits.append("flying")
    if params.get("p17", 0) > 0.7:
        traits.append("nocturnal")
    if params.get("p18", 0) > 0.7:
        traits.append("social")
    if params.get("p2", 0) > 0.7:
        traits.append("aggressive")
    if params.get("p9", 0) > 0.7:
        traits.append("dangerous")
    if params.get("p7", 0) > 0.7:
        traits.append("tool-like")
    if params.get("p8", 0) > 0.7:
        traits.append("artificial")
    if params.get("p8", 0) < 0.3:
        traits.append("natural")
    if params.get("p10", 0) >= 0.7:
        traits.append("friendly")
    if params.get("p1", 0) > 0.7:
        traits.append("large")
    if params.get("p1", 0) < 0.3:
        traits.append("small")
    if params.get("p3", 0) > 0.7:
        traits.append("intelligent")
    if params.get("p6", 0) > 0.7:
        traits.append("agentic")
    return traits


def _predict_prime(params: dict, weights: dict | None, fallback: str) -> str:
    if not weights:
        return fallback
    best_p = fallback
    best_score = -1.0
    for p in PRIMES:
        w = weights.get(f"prime:{p}", {})
        if not w:
            continue
        score = _sigmoid(_dot(w, params))
        if score > best_score:
            best_score = score
            best_p = p
    return best_p


def synthesize_answer(simplified, weights: dict | None = None) -> str:
    if not simplified.tokens:
        return "I need a specific subject to explain."
    subject = " ".join(simplified.tokens[:3])
    encoding = simplified.encodings[0] if simplified.encodings else "Object"
    prime = "".join([c for c in encoding if c.isalpha()]) or "Object"
    params = simplified.parameters
    if simplified.primary_source in {"lexicon", "lexicon_auto"}:
        prime = simplified.primary_prime or prime
        traits = _trait_list(params, None)
    else:
        prime_guess = _predict_prime(params, weights, prime)
        if weights:
            # Only override the prime if the model is confident.
            score = _sigmoid(_dot(weights.get(f"prime:{prime_guess}", {}), params))
            if score >= 0.65:
                prime = prime_guess
        traits = _trait_list(params, weights)
    if prime != "Feeling" and "negative" in traits:
        traits = [t for t in traits if t != "negative"]
    if params.get("p5", 0) < 0.6 and "domesticated" in traits:
        traits = [t for t in traits if t != "domesticated"]
    if params.get("p19", 0) > 0.7 and "wild" not in traits:
        traits.append("wild")
    tone = pick_tone(params, simplified.raw_tokens or simplified.tokens)
    return render_with_tone(subject, prime, traits, tone)


def build_answer(intent: tuple[str, str], web_text: str, simplified, weights: dict | None) -> str:
    synthesized = synthesize_answer(simplified, weights)
    traits = _trait_list(simplified.parameters, weights)
    prime_guess = _predict_prime(simplified.parameters, weights, "Object")
    if prime_guess != "Feeling" and "negative" in traits:
        traits = [t for t in traits if t != "negative"]
    reasoning = reason(traits, prime_guess)
    web_hint = web_text.strip()
    taxonomy_text = ""
    if simplified.tokens:
        tax = taxonomy_for(simplified.tokens[0])
        lineage = tax.get("lineage", []) if isinstance(tax, dict) else []
        if lineage:
            parts = []
            for node in lineage[:6]:
                name = node.get("name", "")
                rank = node.get("rank", "")
                if name:
                    if rank:
                        parts.append(f"{rank}:{name}")
                    else:
                        parts.append(name)
            if parts:
                taxonomy_text = "Taxonomy: " + " > ".join(parts)
    if web_hint:
        web_tokens = web_hint.split()
        web_hint = " ".join(web_tokens[:28])
        if intent[0] in {"explain", "describe"}:
            base = f"Synthesized: {synthesized} Web hint: {web_hint}."
        else:
            base = f"Synthesized: {synthesized} Web hint: {web_hint}."
    else:
        base = f"Synthesized: {synthesized}"
    if taxonomy_text:
        base = base + " " + taxonomy_text + "."
    if reasoning:
        return base + " Reasoning: " + " ".join(reasoning)
    return base


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Simple Q&A using Base+Bit algorithm")
    p.add_argument("question", type=str)
    return p


def main() -> None:
    args = build_parser().parse_args()
    engine = LexicalEngine(Path(__file__).resolve().parent)

    simplified = simplify(args.question, engine)
    web_text = search_web(args.question, engine, simplified.tokens)
    weights = load_weights(Path(__file__).resolve().parent / "model_weights.json")
    answer = build_answer(simplified.intent, web_text, simplified, weights or None)

    print("Simplified:")
    print(f"tokens={simplified.tokens}")
    print(f"encodings={simplified.encodings}")
    print(f"params={simplified.parameters}")
    print(f"intent={simplified.intent}")
    print(f"pos_tags={simplified.pos_tags}")
    print("\nAnswer:")
    print(answer)


if __name__ == "__main__":
    main()
