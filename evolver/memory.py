from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List


@dataclass
class FailureRecord:
    fingerprint: str
    reason: str
    generation: int


class FailureMemory:
    def __init__(self, path: Path):
        self.path = path
        self.records: List[FailureRecord] = []
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.records = [FailureRecord(**r) for r in data.get("records", [])]

    def save(self) -> None:
        payload = {"records": [asdict(r) for r in self.records]}
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @staticmethod
    def fingerprint(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def has_seen(self, candidate_text: str) -> bool:
        fp = self.fingerprint(candidate_text)
        return any(r.fingerprint == fp for r in self.records)

    def add(self, candidate_text: str, reason: str, generation: int) -> None:
        fp = self.fingerprint(candidate_text)
        self.records.append(FailureRecord(fp, reason, generation))
        self.save()

