import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .config import EMBED_DIM, LOG_DIR
from .storage import connect, init_db
from .utils import now_iso
from .web import web_answer
from .embeddings import embed_text, update_model
from .storage import add_knowledge, clear_embeddings, get_meta, set_meta


def _fetch_one(question: str, fast: bool, max_sources: int | None):
    web = web_answer(question, fast=fast, max_sources=max_sources)
    answer_text = web.get("answer", "")
    sources = web.get("sources", [])
    source_meta = sources[0] if sources else {"source": "web", "url": ""}
    return question, answer_text, source_meta


def train_questions(
    questions,
    skip_failures: bool = True,
    workers: int = 6,
    fast: bool = True,
    max_sources: int | None = 1,
    dim: int = EMBED_DIM,
    use_word2vec: bool = True,
):
    conn = connect()
    init_db(conn)
    active_dim = int(get_meta(conn, "embed_dim") or EMBED_DIM)
    if dim != active_dim:
        clear_embeddings(conn)
        set_meta(conn, "embed_dim", str(dim))
    results = []
    cleaned = [q.strip() for q in questions if q.strip()]
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(_fetch_one, q, fast, max_sources): q for q in cleaned
        }
        for future in as_completed(futures):
            q = futures[future]
            try:
                question, answer_text, source_meta = future.result()
            except Exception as exc:
                if skip_failures:
                    results.append({"question": q, "error": str(exc)})
                    continue
                raise
            if not answer_text:
                if skip_failures:
                    results.append({"question": q, "error": "no_answer"})
                    continue
            embedding = embed_text(question + " " + answer_text, dim=dim)
            add_knowledge(
                conn,
                question=question,
                answer=answer_text,
                source=source_meta.get("source", "web"),
                url=source_meta.get("url", ""),
                confidence=0.5,
                weight=1.15,
                embedding=embedding,
            )
            results.append({"question": question, "source": source_meta.get("source", "web")})
    conn.close()
    if use_word2vec:
        texts = [f"{r['question']} {r.get('answer', '')}" for r in results]
        update_model(texts, dim=dim, workers=workers)
    return results


def main() -> None:
    from .seeds import generate_seeds

    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=300)
    parser.add_argument("--out", type=str, default="")
    parser.add_argument("--no-skip-failures", action="store_true")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--full", action="store_true", help="Fetch full pages (slower).")
    parser.add_argument("--max-sources", type=int, default=1)
    parser.add_argument("--dim", type=int, default=EMBED_DIM)
    parser.add_argument("--no-word2vec", action="store_true")
    args = parser.parse_args()

    questions = generate_seeds(min_count=args.count)
    results = train_questions(
        questions,
        skip_failures=not args.no_skip_failures,
        workers=args.workers,
        fast=not args.full,
        max_sources=args.max_sources,
        dim=args.dim,
        use_word2vec=not args.no_word2vec,
    )

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = now_iso().replace(":", "-").replace("+", "_")
    out_path = Path(args.out) if args.out else LOG_DIR / f"train_{stamp}.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for row in results:
            f.write(json.dumps(row, ensure_ascii=True) + "\n")

    print(f"Trained {len(results)} questions. Log: {out_path}")


if __name__ == "__main__":
    main()
