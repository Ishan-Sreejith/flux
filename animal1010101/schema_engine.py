from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from animal1010101.engine import LexicalEngine


@dataclass
class SchemaResult:
    text: str
    activated: List[str]
    parameters: Dict[str, float]
    scripts: List[str]
    accommodation: List[str]


class SchemaEngine:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.schema_path = base_dir / "schema_data.json"
        self.runtime_path = base_dir / "schema_runtime.json"
        self.data = self._load_json(self.schema_path)
        self.runtime = self._load_json(self.runtime_path) if self.runtime_path.exists() else {"schemas": {}}
        self.lex = LexicalEngine(base_dir)

    @staticmethod
    def _load_json(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def _save_runtime(self) -> None:
        self.runtime_path.write_text(json.dumps(self.runtime, indent=2), encoding="utf-8")

    def interpret(self, text: str) -> SchemaResult:
        tokens = [t.strip().lower() for t in text.split() if t.strip()]
        activated = []
        params: Dict[str, float] = {}
        scripts = []
        accommodation = []

        for token in tokens:
            schema = self._get_schema(token)
            if schema:
                activated.append(token)
                for k, v in schema.get("params", {}).items():
                    params[k] = float(v)
                if "script" in schema:
                    scripts.append(token)
            else:
                # Assimilation attempt: map to BaseWord1010101 and create a new schema.
                result = self.lex.encode(token)
                new_schema = {
                    "type": "object",
                    "prime": result.prime,
                    "params": result.parameters,
                    "sensory": [],
                }
                self.runtime["schemas"][token] = new_schema
                accommodation.append(token)
                for k, v in result.parameters.items():
                    params[k] = float(v)

        if accommodation:
            self._save_runtime()

        return SchemaResult(
            text=text,
            activated=activated,
            parameters=params,
            scripts=scripts,
            accommodation=accommodation,
        )

    def _get_schema(self, key: str) -> dict | None:
        return self.runtime.get("schemas", {}).get(key) or self.data.get("schemas", {}).get(key)

    def script_for(self, key: str) -> List[str]:
        schema = self._get_schema(key)
        if not schema:
            return []
        return schema.get("script", [])

