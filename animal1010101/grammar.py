from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Tuple

TOKEN_RE = re.compile(r"[a-z0-9']+")

QUESTION_WORDS = {
    "who",
    "what",
    "when",
    "where",
    "why",
    "how",
    "explain",
    "define",
    "describe",
    "compare",
    "list",
}

AUX_VERBS = {
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "do",
    "does",
    "did",
    "done",
    "can",
    "could",
    "should",
    "would",
    "will",
    "may",
    "might",
    "must",
    "have",
    "has",
    "had",
}

PREPOSITIONS = {
    "in",
    "on",
    "at",
    "to",
    "of",
    "for",
    "from",
    "by",
    "about",
    "as",
    "into",
    "over",
    "after",
    "before",
    "under",
    "above",
    "with",
    "without",
    "between",
    "through",
    "across",
}

DETERMINERS = {"the", "a", "an", "this", "that", "these", "those"}

PRONOUNS = {
    "i",
    "you",
    "we",
    "they",
    "he",
    "she",
    "it",
    "me",
    "him",
    "her",
    "us",
    "them",
}

CONJUNCTIONS = {"and", "or", "but", "if", "then", "so", "because", "although", "however"}

FILLERS = {
    "simple",
    "simply",
    "terms",
    "please",
    "kindly",
    "basically",
    "overall",
    "generally",
}

SHORT_KEEP = {"ai", "ml", "ui", "ux", "uk", "us"}

STOPWORDS = set().union(
    QUESTION_WORDS,
    AUX_VERBS,
    PREPOSITIONS,
    DETERMINERS,
    PRONOUNS,
    CONJUNCTIONS,
    FILLERS,
)


@dataclass
class TaggedToken:
    token: str
    lemma: str
    pos: str


def tokenize(text: str) -> List[str]:
    return TOKEN_RE.findall(text.lower())


def lemmatize(token: str) -> str:
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"
    if token.endswith("ing") and len(token) > 4:
        return token[:-3]
    if token.endswith("ed") and len(token) > 3:
        return token[:-2]
    if token.endswith("s") and len(token) > 3:
        return token[:-1]
    return token


def tag_token(token: str) -> str:
    if token in QUESTION_WORDS:
        return "question"
    if token in AUX_VERBS:
        return "verb"
    if token in PREPOSITIONS:
        return "prep"
    if token in DETERMINERS:
        return "det"
    if token in PRONOUNS:
        return "pron"
    if token in CONJUNCTIONS:
        return "conj"
    if token.endswith("ly"):
        return "adv"
    if token.endswith("ing") or token.endswith("ed"):
        return "verb"
    if token.endswith("tion") or token.endswith("ment") or token.endswith("ity"):
        return "noun"
    return "noun"


def tag_tokens(tokens: Iterable[str]) -> List[TaggedToken]:
    tagged: List[TaggedToken] = []
    for t in tokens:
        lemma = lemmatize(t)
        tagged.append(TaggedToken(token=t, lemma=lemma, pos=tag_token(lemma)))
    return tagged


def content_filter(tagged: Iterable[TaggedToken]) -> List[TaggedToken]:
    return [
        t
        for t in tagged
        if t.lemma not in STOPWORDS
        and t.token not in STOPWORDS
        and (len(t.lemma) > 2 or t.lemma in SHORT_KEEP)
    ]


def merge_phrases(tokens: List[str], phrases: Iterable[str]) -> List[str]:
    phrase_set = {p.lower() for p in phrases}
    if not phrase_set:
        return tokens
    out: List[str] = []
    i = 0
    while i < len(tokens):
        tri = " ".join(tokens[i : i + 3])
        bi = " ".join(tokens[i : i + 2])
        if tri in phrase_set:
            out.append(tri)
            i += 3
            continue
        if bi in phrase_set:
            out.append(bi)
            i += 2
            continue
        out.append(tokens[i])
        i += 1
    return out


def detect_intent(tokens: Iterable[str]) -> Tuple[str, str]:
    for t in tokens:
        if t in {"explain", "describe", "define"}:
            return "explain", t
        if t in {"compare"}:
            return "compare", t
        if t in {"list"}:
            return "list", t
        if t in {"how"}:
            return "how", t
        if t in {"why"}:
            return "why", t
        if t in {"what"}:
            return "what", t
        if t in {"who"}:
            return "who", t
    return "general", ""
