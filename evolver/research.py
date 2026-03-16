from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Dict, List


def _fetch_json(url: str, headers: Dict[str, str] | None = None) -> dict | list:
    req = urllib.request.Request(
        url,
        headers=headers or {"User-Agent": "self-evolver/0.1"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _ddg_research(query: str, max_results: int) -> List[Dict[str, str]]:
    url = "https://api.duckduckgo.com/"
    params = {"q": query, "format": "json", "no_redirect": 1, "no_html": 1}
    full_url = f"{url}?{urllib.parse.urlencode(params)}"
    data = _fetch_json(full_url)
    out: List[Dict[str, str]] = []
    abstract = data.get("AbstractText", "")
    heading = data.get("Heading", "")
    if abstract:
        out.append({"title": heading or "summary", "snippet": abstract, "source": "duckduckgo"})
    for topic in data.get("RelatedTopics", []):
        if isinstance(topic, dict) and "Text" in topic:
            out.append(
                {
                    "title": topic.get("FirstURL", ""),
                    "snippet": topic["Text"],
                    "source": "duckduckgo",
                }
            )
        if len(out) >= max_results:
            break
    return out[:max_results]


def _wikipedia_research(query: str, max_results: int) -> List[Dict[str, str]]:
    params = {
        "action": "opensearch",
        "search": query,
        "limit": str(max_results),
        "namespace": "0",
        "format": "json",
    }
    full_url = f"https://en.wikipedia.org/w/api.php?{urllib.parse.urlencode(params)}"
    data = _fetch_json(full_url)
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
                }
            )
    return out[:max_results]


def internet_research(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """Aggregate lightweight research from multiple internet sources."""
    out: List[Dict[str, str]] = []
    try:
        out.extend(_ddg_research(query, max_results))
    except Exception:
        pass
    try:
        out.extend(_wikipedia_research(query, max_results))
    except Exception:
        pass
    return out[:max_results]
