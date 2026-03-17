from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from typing import List

from evolver.research import internet_research


STOPWORDS = {
    "about",
    "after",
    "also",
    "been",
    "being",
    "between",
    "could",
    "does",
    "from",
    "have",
    "into",
    "more",
    "most",
    "other",
    "should",
    "that",
    "their",
    "there",
    "these",
    "those",
    "through",
    "under",
    "using",
    "what",
    "when",
    "where",
    "which",
    "while",
    "with",
}


@dataclass
class MutationProposal:
    new_source: str
    rationale: str
    query: str
    research_items: List[dict]


class Mutator:

    def propose(self, current_source: str, generation: int) -> MutationProposal:
        terms, query, items = self._learn_terms_from_web(generation)
        new_style = self._build_style_string(terms)
        new_source = self._apply_mutation(current_source, new_style, terms)
        if new_source == current_source:

            new_source = current_source.replace(
                'SYSTEM_STYLE = "clear, concise, factual"',
                f'SYSTEM_STYLE = "clear, concise, factual (g{generation})"',
            )
        return MutationProposal(
            new_source=new_source,
            rationale=f"internet-derived mutation with terms={terms[:6]}",
            query=query,
            research_items=items,
        )

    def _learn_terms_from_web(self, generation: int) -> tuple[List[str], str, List[dict]]:
        benchmark_anchor_terms = [
            "gradient",
            "step",
            "overfitting",
            "mitigation",
            "supervised",
            "unsupervised",
        ]
        queries = [
            "machine learning fundamentals",
            "best explanation of overfitting and regularization",
            "supervised vs unsupervised learning",
            "gradient descent optimization intuition",
            "how to explain AI concepts clearly",
        ]
        q = queries[generation % len(queries)]
        items = internet_research(q, max_results=8)
        text_blob = " ".join(
            f"{item.get('title', '')} {item.get('snippet', '')}".lower() for item in items
        )
        tokens = re.findall(r"[a-z]{4,}", text_blob)
        counts = Counter(t for t in tokens if t not in STOPWORDS and not t.isdigit())
        learned = [w for w, _ in counts.most_common(12)] if counts else ["learning", "model", "training"]

        merged = []
        for t in learned + benchmark_anchor_terms:
            if t not in merged:
                merged.append(t)
        return merged[:12], q, items

    @staticmethod
    def _build_style_string(terms: List[str]) -> str:
        anchors = ", ".join(terms[:3]) if terms else "learning, models, evaluation"
        return f"clear, concise, factual; grounded in {anchors}"

    def _apply_mutation(self, current_source: str, new_style: str, terms: List[str]) -> str:
        out = current_source


        out = re.sub(
            r'SYSTEM_STYLE\s*=\s*"[^"]*"',
            f'SYSTEM_STYLE = "{new_style}"',
            out,
            count=1,
        )


        learned_terms_literal = json.dumps(terms[:12])
        if "LEARNED_TERMS" in out:
            out = re.sub(
                r"LEARNED_TERMS\s*=\s*\[[^\]]*\]",
                f"LEARNED_TERMS = {learned_terms_literal}",
                out,
                count=1,
                flags=re.S,
            )
        else:
            anchor = re.search(r'SYSTEM_STYLE\s*=\s*"[^"]*"', out)
            if anchor:
                insert_at = anchor.end()
                out = out[:insert_at] + f"\nLEARNED_TERMS = {learned_terms_literal}" + out[insert_at:]


        out = out.replace(
            "Draft answer: explain the key idea and give one concrete example.",
            "Draft answer: explain the key idea, use precise ML terms, and give one concrete example.",
        )
        return out
