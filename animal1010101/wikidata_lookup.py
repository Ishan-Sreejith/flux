from __future__ import annotations

import json
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List

BASE_DIR = Path(__file__).resolve().parent
CACHE_PATH = BASE_DIR / "wikidata_cache.json"
DISAMBIG_WEIGHTS_PATH = BASE_DIR / "disambig_weights.json"
RATE_LIMIT_SEC = float(os.getenv("WIKIDATA_RATE_LIMIT_SEC", "0.25"))
RETRIES = int(os.getenv("WIKIDATA_RETRIES", "3"))
BACKOFF_SEC = float(os.getenv("WIKIDATA_BACKOFF_SEC", "0.6"))
TIMEOUT_SEC = float(os.getenv("WIKIDATA_TIMEOUT_SEC", "12"))
MAX_WORKERS = int(os.getenv("WIKIDATA_MAX_WORKERS", "8"))
CACHE_FLUSH_EVERY = int(os.getenv("WIKIDATA_CACHE_FLUSH_EVERY", "25"))
CACHE_FLUSH_INTERVAL = float(os.getenv("WIKIDATA_CACHE_FLUSH_INTERVAL", "5"))

_CACHE: dict[str, dict | list] = {}
_LAST_REQUEST = 0.0
_RATE_LOCK = threading.Lock()
_CACHE_LOCK = threading.Lock()
_CACHE_WRITES = 0
_LAST_CACHE_FLUSH = 0.0
_DISAMBIG_WEIGHTS: dict[str, float] | None = None


def _load_cache() -> None:
    global _CACHE
    if CACHE_PATH.exists():
        try:
            _CACHE = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            _CACHE = {}


def _load_disambig_weights() -> None:
    global _DISAMBIG_WEIGHTS
    if DISAMBIG_WEIGHTS_PATH.exists():
        try:
            _DISAMBIG_WEIGHTS = json.loads(DISAMBIG_WEIGHTS_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            _DISAMBIG_WEIGHTS = None


def _save_cache() -> None:
    global _CACHE_WRITES, _LAST_CACHE_FLUSH
    now = time.time()
    if _CACHE_WRITES < CACHE_FLUSH_EVERY and (now - _LAST_CACHE_FLUSH) < CACHE_FLUSH_INTERVAL:
        return
    CACHE_PATH.write_text(json.dumps(_CACHE, indent=2), encoding="utf-8")
    _CACHE_WRITES = 0
    _LAST_CACHE_FLUSH = now


def _rate_limit() -> None:
    global _LAST_REQUEST
    if RATE_LIMIT_SEC <= 0:
        return
    with _RATE_LOCK:
        now = time.time()
        wait = RATE_LIMIT_SEC - (now - _LAST_REQUEST)
        if wait > 0:
            time.sleep(wait)
        _LAST_REQUEST = time.time()


def _fetch_json(url: str) -> dict | list:
    global _CACHE_WRITES
    with _CACHE_LOCK:
        if url in _CACHE:
            return _CACHE[url]

    last_err: Exception | None = None
    for attempt in range(RETRIES):
        try:
            _rate_limit()
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "animal1010101/0.3"},
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            with _CACHE_LOCK:
                _CACHE[url] = payload
                _CACHE_WRITES += 1
                _save_cache()
            return payload
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as err:
            last_err = err
            time.sleep(BACKOFF_SEC * (2**attempt))
    if last_err:
        raise last_err
    return {}


def search_entities(term: str, limit: int = 6) -> List[Dict[str, str]]:
    term = term.strip()
    if not term:
        return []
    params = {
        "action": "wbsearchentities",
        "format": "json",
        "language": "en",
        "limit": str(limit),
        "search": term,
    }
    url = f"https://www.wikidata.org/w/api.php?{urllib.parse.urlencode(params)}"
    try:
        data = _fetch_json(url)
    except Exception:
        return []
    out: List[Dict[str, str]] = []
    for hit in data.get("search", []):
        qid = str(hit.get("id", ""))
        out.append(
            {
                "id": qid,
                "label": str(hit.get("label", "")),
                "description": str(hit.get("description", "")),
                "url": f"https://www.wikidata.org/wiki/{qid}" if qid else "",
                "source": "wikidata",
            }
        )
    return out


def get_entities(ids: List[str]) -> dict:
    ids = [i for i in ids if i]
    if not ids:
        return {}
    params = {
        "action": "wbgetentities",
        "format": "json",
        "ids": "|".join(ids),
        "props": "claims|labels|descriptions",
        "languages": "en",
    }
    url = f"https://www.wikidata.org/w/api.php?{urllib.parse.urlencode(params)}"
    try:
        data = _fetch_json(url)
    except Exception:
        return {}
    return data.get("entities", {})


def _instance_of(entity: dict) -> List[str]:
    claims = entity.get("claims", {}).get("P31", [])
    ids: List[str] = []
    for claim in claims:
        val = claim.get("mainsnak", {}).get("datavalue", {}).get("value", {})
        if isinstance(val, dict) and "id" in val:
            ids.append(val["id"])
    return ids


def _claim_ids(entity: dict, prop: str) -> List[str]:
    claims = entity.get("claims", {}).get(prop, [])
    ids: List[str] = []
    for claim in claims:
        val = claim.get("mainsnak", {}).get("datavalue", {}).get("value", {})
        if isinstance(val, dict) and "id" in val:
            ids.append(val["id"])
    return ids


def _label_for(entity: dict) -> str:
    return str(entity.get("labels", {}).get("en", {}).get("value", "") or "")


POSITIVE_TYPES = {
    "Q16521",
    "Q7432",
    "Q7377",
    "Q729",
    "Q5113",
    "Q10811",
    "Q10908",
    "Q1390",
    "Q756",
}

NEGATIVE_TYPES = {
    "Q5",
    "Q202444",
    "Q101352",
    "Q41298",
    "Q571",
    "Q11424",
    "Q7366",
    "Q482994",
}


def _feature_vector(term: str, hit: Dict[str, str], entity: dict | None) -> dict:
    term_lower = term.strip().lower()
    label = hit.get("label", "").lower()
    desc = (hit.get("description", "") or "").lower()
    feats = {
        "label_exact": 1.0 if label == term_lower else 0.0,
        "label_contains": 1.0 if term_lower in label else 0.0,
        "desc_animal": 1.0
        if any(k in desc for k in ["animal", "mammal", "species", "bird", "fish", "reptile", "amphibian", "insect"])
        else 0.0,
        "desc_tech": 1.0
        if any(k in desc for k in ["field", "computer science", "technology", "software", "intelligent"])
        else 0.0,
        "desc_name": 1.0 if any(k in desc for k in ["given name", "family name"]) else 0.0,
        "type_positive": 0.0,
        "type_negative": 0.0,
    }
    if entity:
        types = _instance_of(entity)
        feats["type_positive"] = 1.0 if any(t in POSITIVE_TYPES for t in types) else 0.0
        feats["type_negative"] = 1.0 if any(t in NEGATIVE_TYPES for t in types) else 0.0
    return feats


def _score_hit(term: str, hit: Dict[str, str], entity: dict | None) -> float:
    feats = _feature_vector(term, hit, entity)
    score = 0.0
    if _DISAMBIG_WEIGHTS:
        for k, v in feats.items():
            score += _DISAMBIG_WEIGHTS.get(k, 0.0) * v
        score += _DISAMBIG_WEIGHTS.get("bias", 0.0)
    else:
        score += 4 * feats["label_exact"] + 1 * feats["label_contains"]
        score += 2 * feats["desc_animal"] + 2 * feats["desc_tech"]
        score -= 3 * feats["desc_name"]
        score += 3 * feats["type_positive"]
        score -= 4 * feats["type_negative"]
    return score


def describe(term: str) -> str:
    hits = search_entities(term, limit=6)
    if not hits:
        return ""
    entities = get_entities([h.get("id", "") for h in hits])

    scored = []
    for idx, hit in enumerate(hits):
        ent = entities.get(hit.get("id", "")) if entities else None
        score = _score_hit(term, hit, ent)
        scored.append((score, -idx, hit))

    scored.sort(reverse=True)
    best = scored[0][2] if scored else hits[0]
    return best.get("description", "") or ""


def resolve_entity(term: str) -> dict | None:
    hits = search_entities(term, limit=6)
    if not hits:
        return None
    entities = get_entities([h.get("id", "") for h in hits])
    scored = []
    for idx, hit in enumerate(hits):
        ent = entities.get(hit.get("id", "")) if entities else None
        score = _score_hit(term, hit, ent)
        scored.append((score, -idx, hit))
    scored.sort(reverse=True)
    best = scored[0][2] if scored else hits[0]
    best_ent = entities.get(best.get("id", "")) if entities else None
    return best_ent


def describe_many(terms: List[str], max_workers: int | None = None) -> Dict[str, str]:
    terms = [t.strip() for t in terms if t and t.strip()]
    if not terms:
        return {}
    unique = list(dict.fromkeys(terms))
    workers = max_workers or MAX_WORKERS
    if workers <= 1:
        return {t: describe(t) for t in unique}
    results: Dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(describe, t): t for t in unique}
        for fut in as_completed(futures):
            term = futures[fut]
            try:
                results[term] = fut.result()
            except Exception:
                results[term] = ""
    return results


def category_entities(qid: str, limit: int = 50) -> List[str]:
    qid = qid.strip().upper()
    if not qid.startswith("Q"):
        return []
    query = f"""
    SELECT ?item ?itemLabel WHERE {{
      ?item wdt:P31/wdt:P279* wd:{qid} .
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language \"en\". }}
    }}
    LIMIT {int(limit)}
    """
    url = f"https://query.wikidata.org/sparql?format=json&query={urllib.parse.quote(query)}"
    try:
        data = _fetch_json(url)
    except Exception:
        return []
    bindings = data.get("results", {}).get("bindings", [])
    return [b.get("itemLabel", {}).get("value", "") for b in bindings if b.get("itemLabel")]


def taxonomy_for(term: str, max_levels: int = 7) -> dict:
    ent = resolve_entity(term)
    if not ent:
        return {}

    lineage = []
    cur = ent
    levels = 0
    rank_ids: List[str] = []

    while cur and levels < max_levels:
        name = _label_for(cur)
        rank_id = ""
        ranks = _claim_ids(cur, "P105")
        if ranks:
            rank_id = ranks[0]
            rank_ids.append(rank_id)
        lineage.append({"name": name, "rank_id": rank_id, "rank": ""})

        parents = _claim_ids(cur, "P171")
        if not parents:
            break
        parent_id = parents[0]
        cur = get_entities([parent_id]).get(parent_id)
        levels += 1

    if rank_ids:
        rank_entities = get_entities(list(dict.fromkeys(rank_ids)))
        for node in lineage:
            rid = node.get("rank_id", "")
            if rid and rid in rank_entities:
                node["rank"] = _label_for(rank_entities[rid])

    return {"lineage": lineage}


_load_cache()
_load_disambig_weights()
