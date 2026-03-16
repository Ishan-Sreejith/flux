import math
from typing import Dict, List, Tuple

from .config import EMBED_DIM
from .embeddings import embed_text
from .utils import tokenize


def embed_text_local(text: str, dim: int = EMBED_DIM) -> List[float]:
    return embed_text(text, dim=dim)


def cosine(a: List[float], b: List[float]) -> float:
    if not a or not b:
        return 0.0
    return sum(x * y for x, y in zip(a, b))


def tfidf_scores(query: str, docs: List[Dict]) -> Dict[int, float]:
    doc_tokens = []
    df = {}
    for doc in docs:
        tokens = tokenize(doc.get("question", "") + " " + doc.get("answer", ""))
        unique = set(tokens)
        for tok in unique:
            df[tok] = df.get(tok, 0) + 1
        doc_tokens.append(tokens)

    query_tokens = tokenize(query)
    if not query_tokens or not docs:
        return {}

    N = len(docs)
    idf = {tok: math.log((1 + N) / (1 + df.get(tok, 0))) + 1 for tok in set(query_tokens)}

    scores = {}
    for doc, tokens in zip(docs, doc_tokens):
        tf = {}
        for tok in tokens:
            tf[tok] = tf.get(tok, 0) + 1
        score = 0.0
        for tok in query_tokens:
            if tok in tf:
                score += (tf[tok] / len(tokens)) * idf.get(tok, 0.0)
        scores[doc["id"]] = score
    return scores


def semantic_scores(query: str, embeddings: Dict[int, List[float]], dim: int = EMBED_DIM) -> Dict[int, float]:
    qv = embed_text(query, dim=dim)
    scores = {}
    for knowledge_id, vec in embeddings.items():
        scores[knowledge_id] = cosine(qv, vec)
    return scores


def fuse_scores(
    lexical: Dict[int, float],
    semantic: Dict[int, float],
    weight_lex: float = 0.5,
    weight_sem: float = 0.5,
) -> Dict[int, float]:
    ids = set(lexical) | set(semantic)
    if not ids:
        return {}

    def norm(values: Dict[int, float]) -> Dict[int, float]:
        if not values:
            return {}
        max_v = max(values.values()) or 1.0
        return {k: v / max_v for k, v in values.items()}

    lex_n = norm(lexical)
    sem_n = norm(semantic)

    fused = {}
    for k in ids:
        fused[k] = weight_lex * lex_n.get(k, 0.0) + weight_sem * sem_n.get(k, 0.0)
    return fused


def top_k(scores: Dict[int, float], k: int = 5) -> List[Tuple[int, float]]:
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]
