import json
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from typing import Dict, List
import urllib.error
from urllib.error import URLError

from .config import (
    MAX_SUMMARY_SENTENCES,
    MAX_WEB_SOURCES,
    PAGE_TIMEOUT_SECONDS,
    USER_AGENT,
    WEB_TIMEOUT_SECONDS,
)
from .utils import tokenize


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: List[str] = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self._skip = True

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"}:
            self._skip = False

    def handle_data(self, data):
        if not self._skip and data.strip():
            self._parts.append(data.strip())

    def text(self) -> str:
        return " ".join(self._parts)


def _fetch_json(url: str) -> Dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=WEB_TIMEOUT_SECONDS) as resp:
        return json.loads(resp.read().decode("utf-8", errors="ignore"))


def _fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=PAGE_TIMEOUT_SECONDS) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
    parser = _TextExtractor()
    parser.feed(html)
    return parser.text()


def _summarize(text: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    return " ".join(sentences[:MAX_SUMMARY_SENTENCES])


def _wiki_summary(query: str) -> Dict:
    title = query.strip().replace(" ", "_")
    if not title:
        return {}
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
    try:
        payload = _fetch_json(url)
    except (urllib.error.URLError, TimeoutError):
        return {}
    extract = payload.get("extract", "")
    page_url = ""
    content_urls = payload.get("content_urls", {})
    if isinstance(content_urls, dict):
        desktop = content_urls.get("desktop", {})
        page_url = desktop.get("page", "") if isinstance(desktop, dict) else ""
    if extract:
        return {"summary": _summarize(extract), "url": page_url, "source": "wikipedia"}
    return {}


def duckduckgo_search(query: str, max_sources: int | None = None) -> List[Dict]:
    params = {
        "q": query,
        "format": "json",
        "no_redirect": "1",
        "no_html": "1",
    }
    url = "https://api.duckduckgo.com/?" + urllib.parse.urlencode(params)
    try:
        payload = _fetch_json(url)
    except (URLError, TimeoutError):
        return []

    sources = []
    if payload.get("AbstractText"):
        sources.append(
            {
                "text": payload.get("AbstractText", ""),
                "url": payload.get("AbstractURL", ""),
                "source": "duckduckgo",
            }
        )

    def _flatten_related(items):
        for item in items:
            if "Text" in item and "FirstURL" in item:
                yield item
            elif "Topics" in item:
                for sub in _flatten_related(item.get("Topics", [])):
                    yield sub

    for item in _flatten_related(payload.get("RelatedTopics", [])):
        sources.append(
            {
                "text": item.get("Text", ""),
                "url": item.get("FirstURL", ""),
                "source": "duckduckgo",
            }
        )
        cap = MAX_WEB_SOURCES if max_sources is None else max_sources
        if len(sources) >= cap:
            break

    return sources


def web_answer(query: str, fast: bool = False, max_sources: int | None = None) -> Dict:
    sources = duckduckgo_search(query, max_sources=max_sources)
    enriched = []
    for src in sources:
        url = src.get("url")
        text = src.get("text", "")
        if url and not fast:
            try:
                page_text = _fetch_text(url)
                if page_text:
                    text = page_text
            except Exception:
                pass
        summary = _summarize(text)
        if summary:
            enriched.append(
                {
                    "summary": summary,
                    "url": url,
                    "source": src.get("source", "duckduckgo"),
                }
            )

    if not enriched:
        wiki = _wiki_summary(query)
        if wiki:
            return {"answer": wiki["summary"], "sources": [wiki]}
        return {"answer": "", "sources": [], "error": "no_sources"}

    combined = " ".join(item["summary"] for item in enriched)
    return {
        "answer": combined,
        "sources": enriched,
    }
