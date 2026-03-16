from __future__ import annotations

from typing import Dict, List

from animal1010101.wikidata_lookup import describe


def lookup_definitions(term: str) -> List[Dict[str, str]]:
    term = term.strip()
    if not term:
        return []
    desc = describe(term)
    if not desc:
        return []
    return [{"title": term, "definition": desc, "source": "wikidata"}]
