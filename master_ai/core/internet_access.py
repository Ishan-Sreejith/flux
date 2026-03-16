from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Dict, List


FORBIDDEN_PHRASES = []
ALLOW_SOURCES: List[str] | None = None
BLOCK_SOURCES: List[str] = []
SOURCE_TRUST = {
    "wikipedia": 0.9,
    "duckduckgo": 0.6,
}


def set_forbidden_phrases(phrases: List[str]) -> None:
    global FORBIDDEN_PHRASES
    FORBIDDEN_PHRASES = [p.strip().lower() for p in phrases if p.strip()]


def set_allow_sources(sources: List[str] | None) -> None:
    global ALLOW_SOURCES
    if sources is None:
        ALLOW_SOURCES = None
        return
    ALLOW_SOURCES = [s.strip().lower() for s in sources if s.strip()]


def set_block_sources(sources: List[str]) -> None:
    global BLOCK_SOURCES
    BLOCK_SOURCES = [s.strip().lower() for s in sources if s.strip()]


def _is_forbidden(query: str) -> bool:
    low = query.lower()
    return any(p in low for p in FORBIDDEN_PHRASES)


def _fetch_json(url: str, headers: Dict[str, str] | None = None) -> dict | list:
    req = urllib.request.Request(
        url,
        headers=headers or {"User-Agent": "master-ai/0.1"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=12) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _ddg(query: str, max_results: int) -> List[Dict[str, str]]:
    url = "https://api.duckduckgo.com/"
    params = {"q": query, "format": "json", "no_redirect": 1, "no_html": 1}
    data = _fetch_json(f"{url}?{urllib.parse.urlencode(params)}")
    out: List[Dict[str, str]] = []
    abstract = data.get("AbstractText", "")
    heading = data.get("Heading", "")
    if abstract:
        out.append(
            {
                "title": heading or "summary",
                "snippet": abstract,
                "source": "duckduckgo",
                "trust": SOURCE_TRUST.get("duckduckgo", 0.5),
            }
        )
    for topic in data.get("RelatedTopics", []):
        if isinstance(topic, dict) and "Text" in topic:
            out.append(
                {
                    "title": topic.get("FirstURL", ""),
                    "snippet": topic["Text"],
                    "source": "duckduckgo",
                    "trust": SOURCE_TRUST.get("duckduckgo", 0.5),
                }
            )
        if len(out) >= max_results:
            break
    return out[:max_results]


def _wikipedia(query: str, max_results: int) -> List[Dict[str, str]]:
    params = {
        "action": "opensearch",
        "search": query,
        "limit": str(max_results),
        "namespace": "0",
        "format": "json",
    }
    data = _fetch_json(f"https://en.wikipedia.org/w/api.php?{urllib.parse.urlencode(params)}")
    out: List[Dict[str, str]] = []
    if isinstance(data, list) and len(data) >= 4:
        titles = data[1] or []
        snippets = data[2] or []
        urls = data[3] or []
        for title, snippet, page_url in zip(titles, snippets, urls):
            out.append(
                {
                    "title": str(title),
                    "snippet": str(snippet),
                    "url": str(page_url),
                    "source": "wikipedia",
                    "trust": SOURCE_TRUST.get("wikipedia", 0.9),
                }
            )
    return out[:max_results]


def search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    if _is_forbidden(query):
        return []
    out: List[Dict[str, str]] = []
    try:
        out.extend(_ddg(query, max_results))
    except Exception:
        pass
    try:
        out.extend(_wikipedia(query, max_results))
    except Exception:
        pass
    if ALLOW_SOURCES is not None:
        out = [x for x in out if str(x.get("source", "")).lower() in ALLOW_SOURCES]
    if BLOCK_SOURCES:
        out = [x for x in out if str(x.get("source", "")).lower() not in BLOCK_SOURCES]
    return out[:max_results]
