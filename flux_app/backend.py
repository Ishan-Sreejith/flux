import json
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, List
from urllib.parse import parse_qs, urlparse

from .config import (
    ALLOW_ORIGINS,
    BACKEND_HOST,
    BACKEND_PORT,
    BRIDGE_PORT,
    DEFAULT_WEIGHT_AUTO,
    EMBED_DIM,
    LOCAL_CONFIDENCE_THRESHOLD,
    LOCAL_MIN_SCORE,
    MAX_REQUEST_BYTES,
    MAX_TRAIN_QUESTIONS,
    MAX_SESSIONS,
    MAX_SESSION_HISTORY,
    RATE_LIMIT_PER_MIN,
    REQUEST_TIME_BUDGET_MS,
)
from .embeddings import embed_text, update_model
from .nlp import clamp_params, compose_answer, rewrite_question
from .retrieval import fuse_scores, semantic_scores, tfidf_scores, top_k
from .storage import (
    add_knowledge,
    all_knowledge,
    clear_embeddings,
    connect,
    count_knowledge,
    get_embedding_map,
    get_knowledge_by_id,
    get_meta,
    init_db,
    set_meta,
    update_knowledge,
)
from .utils import chunk_words, json_dumps, monotonic_ms
from .web import web_answer


FRESH_KEYWORDS = {
    "today",
    "latest",
    "recent",
    "current",
    "now",
    "this week",
    "this month",
    "this year",
    "yesterday",
    "tomorrow",
}

SESSION_CONTEXT: dict = {}
SESSION_PARAMS: dict = {}
RATE_BUCKETS: dict = {}


def _allow_origin() -> str:
    return ALLOW_ORIGINS[0] if len(ALLOW_ORIGINS) == 1 else "*"


def _rate_limit(ip: str, limit_per_min: int = RATE_LIMIT_PER_MIN) -> bool:
    now = time.time()
    bucket = RATE_BUCKETS.get(ip)
    if not bucket or now - bucket["ts"] > 60:
        RATE_BUCKETS[ip] = {"ts": now, "count": 1}
        return True
    if bucket["count"] >= limit_per_min:
        return False
    bucket["count"] += 1
    return True


def _get_session(session_id: str) -> dict:
    if session_id not in SESSION_CONTEXT and len(SESSION_CONTEXT) >= MAX_SESSIONS:
        SESSION_CONTEXT.pop(next(iter(SESSION_CONTEXT)))
    return SESSION_CONTEXT.setdefault(session_id, {"history": [], "entities": [], "topics": []})


def _set_params(session_id: str, params: dict) -> dict:
    SESSION_PARAMS[session_id] = clamp_params(params)
    return SESSION_PARAMS[session_id]


def _get_params(session_id: str) -> dict:
    return SESSION_PARAMS.get(session_id, clamp_params({}))


def _needs_freshness(question: str) -> bool:
    q = question.lower()
    return any(k in q for k in FRESH_KEYWORDS)

def _call_bridge(text: str, dim: int) -> List[float]:
    url = f"http://127.0.0.1:{BRIDGE_PORT}/embed"
    data = json.dumps({"text": text, "dim": dim}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return payload.get("vector", [])


def _compute_embedding(text: str, dim: int) -> List[float]:
    try:
        return _call_bridge(text, dim)
    except Exception:
        return embed_text(text, dim=dim)


def _select_local_answer(
    question: str,
    docs: List[Dict],
    embeddings: Dict[int, List[float]],
    dim: int,
):
    lexical = tfidf_scores(question, docs)
    semantic = semantic_scores(question, embeddings, dim=dim)
    fused = fuse_scores(lexical, semantic)
    top = top_k(fused, k=3)
    if not top:
        return None
    best_id, best_score = top[0]
    if best_score < LOCAL_MIN_SCORE:
        return None
    record = next((d for d in docs if d["id"] == best_id), None)
    if not record:
        return None
    confidence = min(1.0, best_score)
    return {
        "record": record,
        "score": best_score,
        "confidence": confidence,
        "badge": "local" if confidence >= LOCAL_CONFIDENCE_THRESHOLD else "local_low_confidence",
    }

def _best_similarity(question: str, embeddings: Dict[int, List[float]], dim: int) -> Dict:
    scores = semantic_scores(question, embeddings, dim=dim)
    top = top_k(scores, k=1)
    if not top:
        return {}
    knowledge_id, score = top[0]
    return {"id": knowledge_id, "score": score}


def _answer_with_web(question: str) -> Dict:
    result = web_answer(question)
    return result


class BackendHandler(BaseHTTPRequestHandler):
    server_version = "FluxBackend/0.2"

    def _send_json(self, payload: dict, code: int = 200) -> None:
        body = json_dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", _allow_origin())
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_sse_headers(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", _allow_origin())
        self.end_headers()

    def _sse_send(self, payload: dict) -> None:
        data = json_dumps(payload)
        self.wfile.write(f"data: {data}\n\n".encode("utf-8"))
        self.wfile.flush()

    def do_GET(self):
        if not _rate_limit(self.client_address[0]):
            self._send_json({"error": "rate limit exceeded"}, code=429)
            return
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._send_json({"status": "ok", "service": "backend"})
            return
        if parsed.path == "/ping":
            self._send_json({"pong": True})
            return
        if parsed.path == "/stats":
            conn = connect()
            init_db(conn)
            total = count_knowledge(conn)
            conn.close()
            self._send_json({"knowledge": total})
            return
        if parsed.path == "/config":
            self._send_json(
                {
                    "time_budget_ms": REQUEST_TIME_BUDGET_MS,
                    "max_train_questions": MAX_TRAIN_QUESTIONS,
                    "max_request_bytes": MAX_REQUEST_BYTES,
                }
            )
            return
        if parsed.path == "/ask_stream":
            qs = parse_qs(parsed.query)
            question = (qs.get("question") or [""])[0].strip()
            refresh = (qs.get("refresh") or ["0"])[0] == "1"
            grade_level = int((qs.get("grade_level") or ["10"])[0])
            session_id = (qs.get("session_id") or ["default"])[0]
            self._send_sse_headers()
            if not question:
                self._sse_send({"delta": "Please ask a specific question.", "done": True})
                return
            answer = self._handle_question(
                question,
                refresh=refresh,
                grade_level=grade_level,
                session_id=session_id,
            )
            text = answer["answer"]
            for chunk in chunk_words(text, size=12):
                self._sse_send({"delta": chunk + " ", "done": False})
            self._sse_send({"done": True, "answer": text, "meta": answer.get("meta", {})})
            return

        self._send_json({"error": "not found"}, code=404)

    def do_POST(self):
        if not _rate_limit(self.client_address[0]):
            self._send_json({"error": "rate limit exceeded"}, code=429)
            return
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0"))
        if length > MAX_REQUEST_BYTES:
            self._send_json({"error": "payload too large"}, code=413)
            return
        raw = self.rfile.read(length).decode("utf-8", errors="ignore")
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            self._send_json({"error": "invalid json"}, code=400)
            return

        if parsed.path == "/ask":
            question = str(payload.get("question", "")).strip()
            refresh = bool(payload.get("refresh", False))
            grade_level = int(payload.get("grade_level", 10))
            session_id = str(payload.get("session_id", "default"))
            if not question:
                self._send_json({"error": "question required"}, code=400)
                return
            answer = self._handle_question(
                question,
                refresh=refresh,
                grade_level=grade_level,
                session_id=session_id,
            )
            self._send_json(answer)
            return

        if parsed.path == "/config":
            session_id = str(payload.get("session_id", "default"))
            nlp_params = payload.get("nlp_params", {})
            applied = _set_params(session_id, nlp_params)
            self._send_json({"status": "ok", "nlp_params": applied})
            return

        if parsed.path == "/train":
            questions = payload.get("questions", [])
            dim = int(payload.get("dim", EMBED_DIM))
            full = bool(payload.get("full", False))
            max_sources = int(payload.get("max_sources", 1))
            workers = int(payload.get("workers", 2))
            use_word2vec = bool(payload.get("use_word2vec", True))
            grade_level = int(payload.get("grade_level", 10))
            session_id = str(payload.get("session_id", "default"))
            if not isinstance(questions, list) or not questions:
                self._send_json({"error": "questions list required"}, code=400)
                return
            if len(questions) > MAX_TRAIN_QUESTIONS:
                self._send_json({"error": "too many questions"}, code=400)
                return
            results = []
            conn = connect()
            init_db(conn)
            active_dim = int(get_meta(conn, "embed_dim") or EMBED_DIM)
            if dim != active_dim:
                clear_embeddings(conn)
                set_meta(conn, "embed_dim", str(dim))
            for q in questions:
                q = str(q).strip()
                if not q:
                    continue
                web = _answer_with_web(q) if full else web_answer(
                    q,
                    fast=True,
                    max_sources=max_sources,
                    time_budget_ms=REQUEST_TIME_BUDGET_MS,
                )
                answer_text = web.get("answer", "")
                sources = web.get("sources", [])
                if not answer_text or not sources:
                    results.append({"question": q, "error": "no_sources"})
                    continue
                source_meta = sources[0]
                params = _get_params(session_id)
                params["readability_level"] = grade_level
                final_answer, _analysis = compose_answer(q, sources, params, _get_session(session_id))
                embedding = _compute_embedding(q + " " + answer_text, dim=dim)
                add_knowledge(
                    conn,
                    question=q,
                    answer=final_answer,
                    source=source_meta.get("source", "web"),
                    url=source_meta.get("url", ""),
                    confidence=0.5,
                    weight=DEFAULT_WEIGHT_AUTO,
                    embedding=embedding,
                )
                results.append({"question": q, "answer": final_answer})
            conn.close()
            if use_word2vec:
                texts = [f"{r['question']} {r.get('answer', '')}" for r in results]
                update_model(texts, dim=dim, workers=workers)
            self._send_json({"trained": len(results), "results": results})
            return

        if parsed.path == "/feedback":
            knowledge_id = payload.get("knowledge_id")
            question = str(payload.get("question", "")).strip()
            answer = str(payload.get("answer", "")).strip()
            source = str(payload.get("source", "manual")).strip() or "manual"
            url = str(payload.get("url", "")).strip()
            weight = float(payload.get("weight", 2.0))
            confidence = float(payload.get("confidence", 0.9))

            if knowledge_id:
                conn = connect()
                init_db(conn)
                update_knowledge(
                    conn,
                    knowledge_id=int(knowledge_id),
                    answer=answer or "Updated by user.",
                    source=source,
                    url=url,
                    confidence=confidence,
                    weight=weight,
                )
                conn.close()
                self._send_json({"status": "updated", "knowledge_id": int(knowledge_id)})
                return

            if not question or not answer:
                self._send_json({"error": "question and answer required"}, code=400)
                return

            conn = connect()
            init_db(conn)
            active_dim = int(get_meta(conn, "embed_dim") or EMBED_DIM)
            embedding = _compute_embedding(question + " " + answer, dim=active_dim)
            knowledge_id = add_knowledge(
                conn,
                question=question,
                answer=answer,
                source=source,
                url=url,
                confidence=confidence,
                weight=weight,
                embedding=embedding,
            )
            conn.close()
            self._send_json({"status": "created", "knowledge_id": knowledge_id})
            return

        self._send_json({"error": "not found"}, code=404)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", _allow_origin())
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def _handle_question(
        self,
        question: str,
        refresh: bool = False,
        force_web: bool = False,
        grade_level: int = 10,
        session_id: str = "default",
    ) -> Dict:
        start_ms = monotonic_ms()
        conn = connect()
        init_db(conn)
        docs = all_knowledge(conn)
        embeddings = get_embedding_map(conn)
        active_dim = int(get_meta(conn, "embed_dim") or EMBED_DIM)

        session = _get_session(session_id)
        params = _get_params(session_id)
        params["readability_level"] = grade_level
        rewritten = rewrite_question(question, params, session)

        local = None
        if not force_web and not refresh and not _needs_freshness(question):
            local = _select_local_answer(rewritten, docs, embeddings, dim=active_dim)

        if local and local["confidence"] >= LOCAL_CONFIDENCE_THRESHOLD:
            record = local["record"]
            conn.close()
            return {
                "answer": record["answer"],
                "sources": [{"source": record["source"], "url": record["url"]}],
                "meta": {"badge": local["badge"], "confidence": local["confidence"]},
            }

        elapsed_ms = monotonic_ms() - start_ms
        budget_ms = max(250, REQUEST_TIME_BUDGET_MS - elapsed_ms)
        web = web_answer(rewritten, fast=True, max_sources=3, time_budget_ms=budget_ms)
        answer_text = web.get("answer", "")
        sources = web.get("sources", [])
        if not answer_text or not sources:
            conn.close()
            return {
                "answer": "I could not find a reliable web source for that question.",
                "sources": [],
                "meta": {"badge": "no_source", "confidence": 0.0},
            }
        source_meta = sources[0]
        final_answer, analysis = compose_answer(rewritten, sources, params, session)
        session["entities"] = analysis.get("entities", [])
        session["topics"] = analysis.get("topics", [])
        session["history"].append({"q": question, "a": final_answer})
        if len(session["history"]) > MAX_SESSION_HISTORY:
            session["history"] = session["history"][-MAX_SESSION_HISTORY:]

        # Dedupe: if a very similar entry exists, update weight instead of inserting.
        best = _best_similarity(question, embeddings, dim=active_dim)
        if best and best.get("score", 0.0) >= 0.9:
            update_knowledge(
                conn,
                knowledge_id=int(best["id"]),
                answer=final_answer,
                source=source_meta.get("source", "web"),
                url=source_meta.get("url", ""),
                confidence=0.5,
                weight=DEFAULT_WEIGHT_AUTO,
            )
        else:
            embedding = _compute_embedding(rewritten + " " + answer_text, dim=active_dim)
            add_knowledge(
                conn,
                question=rewritten,
                answer=final_answer,
                source=source_meta.get("source", "web"),
                url=source_meta.get("url", ""),
                confidence=0.5,
                weight=DEFAULT_WEIGHT_AUTO,
                embedding=embedding,
            )
        conn.close()
        return {
            "answer": final_answer,
            "sources": sources,
            "meta": {"badge": "layered_web", "confidence": 0.5},
        }


def run() -> None:
    server = ThreadingHTTPServer((BACKEND_HOST, BACKEND_PORT), BackendHandler)
    print(f"Backend listening on :{BACKEND_PORT}")
    server.serve_forever()


if __name__ == "__main__":
    run()
