import re
from typing import Dict, List, Tuple

from .utils import tokenize


_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")

_SIMPLE_SUBS = {
    "approximately": "about",
    "utilize": "use",
    "commence": "start",
    "terminate": "end",
    "individuals": "people",
    "numerous": "many",
    "demonstrate": "show",
    "assistance": "help",
    "require": "need",
    "sufficient": "enough",
    "therefore": "so",
    "however": "but",
    "for example": "for example",
    "such as": "for example",
}

DEFAULT_NLP_PARAMS = {
    "context_depth": 60,
    "intent_weight": 60,
    "entity_weight": 60,
    "coref_weight": 60,
    "sentiment_weight": 20,
    "topic_weight": 50,
    "grammar_weight": 70,
    "structure_weight": 70,
    "brevity": 50,
    "evidence_weight": 70,
    "synthesis_weight": 80,
    "freshness_weight": 60,
    "contradiction_sensitivity": 50,
    "uncertainty_threshold": 40,
    "example_weight": 55,
    "definition_weight": 70,
    "why_weight": 40,
    "how_weight": 40,
    "steps_weight": 30,
    "analogy_weight": 25,
    "caution_weight": 20,
    "bias_mitigation": 40,
    "noise_filter": 60,
    "repetition_penalty": 50,
    "hedging_level": 30,
    "formality": 50,
    "readability_level": 10,
    "max_sentences": 4,
    "max_words_per_sentence": 24,
    "keyword_boost": 50,
    "entity_boost": 50,
    "topic_boost": 50,
    "source_merge": 60,
    "source_diversity": 40,
    "paraphrase_strength": 40,
    "clause_pruning": 60,
    "pronoun_resolution": 60,
    "temporal_sensitivity": 40,
    "domain_specificity": 40,
    "summary_aggressiveness": 60,
    "style_variance": 30,
}


def split_sentences(text: str) -> List[str]:
    text = text.replace("\n", " ").strip()
    if not text:
        return []
    return [s.strip() for s in _SENTENCE_SPLIT.split(text) if s.strip()]


def simplify_sentence(sentence: str) -> str:
    # Remove parenthetical clauses.
    sentence = re.sub(r"\([^)]*\)", "", sentence)
    sentence = re.sub(r"\[[^]]*\]", "", sentence)
    # Replace some complex words.
    lowered = sentence.lower()
    for k, v in _SIMPLE_SUBS.items():
        if k in lowered:
            sentence = re.sub(rf"\b{k}\b", v, sentence, flags=re.IGNORECASE)
    # Compress spaces.
    sentence = re.sub(r"\s+", " ", sentence).strip()
    return sentence


def limit_sentence(sentence: str, max_words: int = 26) -> str:
    words = sentence.split()
    if len(words) <= max_words:
        return sentence
    return " ".join(words[:max_words]).rstrip(" ,;:") + "."


def extract_keywords(text: str, max_words: int = 6) -> List[str]:
    tokens = tokenize(text)
    freq = {}
    for tok in tokens:
        if len(tok) < 4:
            continue
        freq[tok] = freq.get(tok, 0) + 1
    ranked = sorted(freq.items(), key=lambda x: (-x[1], x[0]))
    return [w for w, _ in ranked[:max_words]]


def synthesize_answer(question: str, sources: List[dict], max_sentences: int = 3) -> str:
    # Build a concise answer from source summaries.
    chunks = []
    for src in sources:
        summary = src.get("summary", "") or src.get("text", "") or ""
        if summary:
            chunks.append(summary)
    combined = " ".join(chunks)
    sentences = split_sentences(combined)
    if not sentences:
        return ""
    # Prefer sentences containing keywords from question.
    keywords = set(extract_keywords(question))
    scored = []
    for s in sentences:
        score = sum(1 for k in keywords if k in s.lower())
        scored.append((score, s))
    scored.sort(key=lambda x: (-x[0], len(x[1])))
    picked = [s for _, s in scored[:max_sentences]]
    return " ".join(picked)


def simplify_answer(answer: str, grade_level: int = 10) -> str:
    if not answer:
        return ""
    sentences = split_sentences(answer)
    simplified = []
    for s in sentences:
        s = simplify_sentence(s)
        s = limit_sentence(s, max_words=24 if grade_level <= 10 else 28)
        simplified.append(s)
    # Keep it short for 10th grade.
    max_sentences = 3 if grade_level <= 10 else 4
    return " ".join(simplified[:max_sentences]).strip()


def clamp_params(params: Dict) -> Dict:
    out = DEFAULT_NLP_PARAMS.copy()
    for k, v in params.items():
        if k in out:
            try:
                out[k] = int(v)
            except (TypeError, ValueError):
                continue
    # Hard bounds
    out["readability_level"] = max(6, min(16, out["readability_level"]))
    out["max_sentences"] = max(1, min(6, out["max_sentences"]))
    out["max_words_per_sentence"] = max(10, min(30, out["max_words_per_sentence"]))
    return out


def analyze_text(text: str) -> Dict:
    tokens = tokenize(text)
    lower = text.lower()
    intent = "explain"
    if lower.startswith("what"):
        intent = "define"
    elif lower.startswith("why"):
        intent = "why"
    elif lower.startswith("how"):
        intent = "how"
    elif lower.startswith("compare") or " vs " in lower:
        intent = "compare"

    # Entities: simple proper noun heuristic.
    entities = re.findall(r"\b[A-Z][a-z]{2,}\b", text)
    # Sentiment: basic word list.
    pos = {"good", "great", "helpful", "benefit", "effective", "positive"}
    neg = {"bad", "harm", "risk", "negative", "problem", "danger"}
    score = sum(1 for t in tokens if t in pos) - sum(1 for t in tokens if t in neg)
    sentiment = 0
    if score > 0:
        sentiment = 1
    elif score < 0:
        sentiment = -1

    topics = extract_keywords(text, max_words=6)
    return {
        "intent": intent,
        "entities": entities,
        "sentiment": sentiment,
        "topics": topics,
    }


def rewrite_question(question: str, params: Dict, state: Dict) -> str:
    q = question.strip()
    if not q:
        return q
    if params.get("pronoun_resolution", 0) >= 50:
        last_entities = state.get("entities", [])
        if last_entities:
            last = last_entities[-1]
            q = re.sub(r"\b(it|they|them|this|that)\b", last, q, flags=re.IGNORECASE)
    return q


def paraphrase(text: str, strength: int) -> str:
    if strength < 30:
        return text
    # Light paraphrase by swapping some connectors.
    swaps = {
        "because": "since",
        "also": "as well",
        "for example": "for instance",
        "in addition": "also",
    }
    out = text
    for k, v in swaps.items():
        out = re.sub(rf"\b{k}\b", v, out, flags=re.IGNORECASE)
    return out


def format_answer(question: str, raw: str, params: Dict, analysis: Dict) -> str:
    sentences = split_sentences(raw)
    if not sentences:
        return ""
    max_sentences = params["max_sentences"]
    max_words = params["max_words_per_sentence"]
    sentences = [limit_sentence(simplify_sentence(s), max_words=max_words) for s in sentences]
    sentences = sentences[:max_sentences]

    intent = analysis.get("intent", "explain")
    lines = []
    if params["definition_weight"] >= 50 and intent in {"define", "explain"}:
        lines.append(f"Definition: {sentences[0]}")
        rest = sentences[1:]
    else:
        rest = sentences

    if rest:
        if params["structure_weight"] >= 60:
            lines.append("Key points:")
            for s in rest:
                lines.append(f"- {s}")
        else:
            lines.extend(rest)

    return "\n".join(lines).strip()


def compose_answer(question: str, sources: List[dict], params: Dict, state: Dict) -> Tuple[str, Dict]:
    analysis = analyze_text(question)
    synthesized = synthesize_answer(question, sources, max_sentences=params["max_sentences"])
    base = synthesized or " ".join(
        [s.get("summary", "") for s in sources if s.get("summary")]
    )
    simplified = simplify_answer(base, grade_level=params["readability_level"])
    paraphrased = paraphrase(simplified, params["paraphrase_strength"])
    formatted = format_answer(question, paraphrased or simplified, params, analysis)
    return formatted or simplified, analysis
