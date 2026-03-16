from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional

from .config import EMBED_DIM, W2V_DIR
from .utils import l2_normalize, tokenize

try:
    from gensim.models import Word2Vec
except Exception:  # pragma: no cover
    Word2Vec = None


def _model_path(dim: int) -> Path:
    W2V_DIR.mkdir(parents=True, exist_ok=True)
    return W2V_DIR / f"word2vec_{dim}.model"


def load_model(dim: int) -> Optional["Word2Vec"]:
    if Word2Vec is None:
        return None
    path = _model_path(dim)
    if not path.exists():
        return None
    return Word2Vec.load(str(path))


def save_model(model: "Word2Vec", dim: int) -> None:
    path = _model_path(dim)
    model.save(str(path))


def embed_text(text: str, dim: int = EMBED_DIM) -> List[float]:
    tokens = tokenize(text)
    if not tokens:
        return [0.0] * dim

    model = load_model(dim)
    if model is None:
        # Fallback to hashed bag-of-words if Word2Vec is unavailable.
        vec = [0.0] * dim
        for tok in tokens:
            vec[hash(tok) % dim] += 1.0
        return l2_normalize(vec)

    vectors = []
    for tok in tokens:
        if tok in model.wv:
            vectors.append(model.wv[tok])
    if not vectors:
        return [0.0] * dim

    avg = [0.0] * dim
    for vec in vectors:
        for i in range(dim):
            avg[i] += float(vec[i])
    avg = [v / len(vectors) for v in avg]
    return l2_normalize(avg)


def update_model(
    texts: Iterable[str],
    dim: int = EMBED_DIM,
    min_count: int = 1,
    window: int = 5,
    epochs: int = 10,
    workers: int = 2,
) -> Optional["Word2Vec"]:
    if Word2Vec is None:
        return None

    sentences = [tokenize(t) for t in texts if t]
    if not sentences:
        return None

    model = load_model(dim)
    if model is None:
        model = Word2Vec(
            vector_size=dim,
            min_count=min_count,
            window=window,
            workers=workers,
        )
        model.build_vocab(sentences)
    else:
        model.build_vocab(sentences, update=True)

    model.train(sentences, total_examples=len(sentences), epochs=epochs)
    save_model(model, dim)
    return model
