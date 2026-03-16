# Flux AI Product Guide

This document defines what Flux is intended to be, how it works, and how it should evolve from the current architecture to the target state.

## 1) What This AI Is Supposed To Be

Flux is a self-improving local AI system with these properties:

- Local-first memory.
- Internet-grounded learning with links and citations.
- Progressive autonomy as local memory grows.
- Explainable answers that show provenance.
- Fast UX with streaming responses and local fallback.

The ideal product is a local brain + internet teacher + persistent memory loop.

## 2) Intended User Experience

When working correctly, the flow is:

1. User asks a question in the UI.
2. System checks local memory first.
3. If confidence is high, answer instantly from local store.
4. If confidence is low or the question needs freshness:
5. Gather web context.
6. Optionally synthesize with model(s).
7. Return a streamed answer with source badge.
8. Save useful results into local memory.
9. Future similar questions become local and faster.

This creates a flywheel:
more usage -> more stored Q/A + embeddings -> better local coverage -> fewer API calls -> lower latency and cost.

## 3) Current Architecture (From HOW_IT_WORKS)

Intended architecture and roles:

- Frontend (port 8080): chat UI, SSE stream rendering.
- C++ backend (port 3001): orchestration, retrieval, synthesis, memory writes.
- Python bridge (port 5002): sentence embedding generation on CPU/GPU.
- SQLite (`synapse.db`): durable knowledge + embedding cache.

Backend responsibilities:

- Request classification (`QueryProfile`).
- Standalone query rewriting for follow-ups.
- Dual retrieval:
  - TF-IDF lexical search.
  - Semantic embedding similarity.
- Optional web snapshot enrichment (DuckDuckGo).
- Synthesis with fallback chain.
- Answer verification/arbitration.
- Write-back learning (`db.addIntent(...)` + index refresh).

This is a solid design for a hybrid local + web-taught assistant.

## 4) What “Training” Means Here

Training is not model fine-tuning. It is:

- Repeated Q/A generation.
- Grounded answer collection.
- Embedding + storage of new entries.
- Index refresh so retrieval improves.

Flux gets smarter via memory accumulation and retrieval quality, not by changing LLM weights.

Training quality depends on:

- Question diversity.
- Source quality.
- Filtering bad/noisy answers.
- Deduplication + weighting.
- Confidence thresholds and replay behavior.

## 5) Source-of-Truth and Reliability Goals

Flux should be opinionated about trust:

- Prefer local high-confidence answers.
- For fresh/time-sensitive questions, explicitly use web context.
- Save provenance (URL/source) for learned entries.
- Mark uncertainty when confidence is weak.
- Let human corrections override model responses with a weight boost.

Suggested weighting:

- Auto-learned entries: 1.15.
- Manual correction: 2.0.

## 6) Target State

If iterated properly, the intended end-state is:

Knowledge Core

- Clean schema with source, timestamp, confidence, and weight.
- Semantic + lexical retrieval fusion.
- Dedupe and stale-entry handling.

Training Engine

- Seed sets of hundreds/thousands of questions.
- Web-only source ingestion mode (if desired).
- Automated retries, backoff, progress reports, resumable runs.

Answer Engine

- Local-only fast path.
- Web-augmented path.
- Synthesis path with strict guardrails.
- Structured citations returned in every non-local answer.

Ops/Quality

- Smoke tests (health, ping, representative questions).
- Training metrics dashboard/logs.
- Failure buckets (network, source parse, auth, model error).

## 7) Product Modes

Flux should support three modes:

Local Development Mode

- Auth off.
- Fast iteration.
- Run with `start.sh`.
- Inspect `.logs/*`.

Training Mode

- High-volume question loops (e.g., 2000).
- Non-streaming JSON responses.
- Robust logging and post-run Q/A validation.

Deployment Mode

- Frontend static host (e.g., Vercel).
- Backend + bridge on VM/container.
- Configurable API base in frontend.

## 8) What Success Looks Like

Stack health:

- `5002/health` OK.
- `3001/health` OK.
- `8080` serving UI.

Functional chat:

- `ping` returns `pong`.
- 5 representative questions return non-empty answers.
- Source badges make sense (`local_layered`, `layered_web`, etc.).

Training quality:

- Training run completes target iterations.
- Knowledge row count increases meaningfully.
- Post-training questions show improved local hit rate.

Reliability:

- Graceful behavior when external APIs are unavailable.
- No hard crashes in synthesis path.
- Reproducible startup/training scripts.

## 9) Internet-Source-Only Direction

If the new direction is “internet source only,” then:

- No OpenRouter dependency.
- Web as the primary teacher source.
- Seed hundreds of questions.
- Learn/store with citations.
- Local retrieval answering afterward.

This is compatible with the architecture above; it changes the teacher strategy from LLM-first with web assist to web-ingestion-first with optional summarization.

## 10) Practical Roadmap

1. Freeze current project as reference.
2. Build a clean Flux implementation with:
   - SQLite knowledge store.
   - Web search + page extraction.
   - Embedding retrieval.
   - Simple `/ask` + `/train` API.
3. Add 300+ seed questions and batch trainer.
4. Add mandatory source URL for every learned item.
5. Add quality filters + dedupe.
6. Add smoke test script and benchmark prompts.
7. Iterate toward richer answer synthesis and guardrails.
