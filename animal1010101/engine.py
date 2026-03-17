from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from animal1010101.wikidata_lookup import describe


@dataclass
class EncodeResult:
    prime: str
    bitstring: str
    parameters: Dict[str, float]
    path: List[str]


class LexicalEngine:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.taxonomy = self._load_json(base_dir / "taxonomy.json")
        self.lexicon = self._load_json(base_dir / "lexicon.json")
        self.lexicon_auto_path = base_dir / "lexicon_auto.json"
        self.lexicon_auto = self._load_json(self.lexicon_auto_path) if self.lexicon_auto_path.exists() else {}

    @staticmethod
    def _load_json(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def encode(self, word: str) -> EncodeResult:
        word_key = word.strip().lower()
        if not word_key:
            raise ValueError("Empty word")

        entry = self.lexicon.get(word_key) or self.lexicon_auto.get(word_key)
        if not entry:

            prime, path = self._resolve_unknown(word_key, write=True)
        else:
            prime = entry["prime"]
            path = entry.get("path", [])

        tree = self.taxonomy["primes"].get(prime, {}).get("tree")
        if not tree:
            raise ValueError(f"Unknown prime: {prime}")

        bitstring, params = self._traverse(tree, path)
        overrides = entry.get("overrides", {}) if entry else {}
        for k, v in overrides.items():
            params[k] = float(v)
        bitstring = bitstring + self._feature_bits(params)
        return EncodeResult(prime=prime, bitstring=bitstring, parameters=params, path=path)

    def learn(self, word: str) -> EncodeResult:
        self._resolve_unknown(word, write=True)
        return self.encode(word)

    def infer(self, word: str) -> Tuple[str, List[str]]:
        return self._resolve_unknown(word, write=False)

    def compare(self, a: str, b: str) -> Tuple[bool, EncodeResult, EncodeResult]:
        ra = self.encode(a)
        rb = self.encode(b)
        return (ra.prime == rb.prime and ra.bitstring == rb.bitstring), ra, rb

    def similarity(self, a: str, b: str) -> Tuple[float, EncodeResult, EncodeResult]:
        ra = self.encode(a)
        rb = self.encode(b)
        prime_score = 1.0 if ra.prime == rb.prime else 0.0
        bit_score = self._bit_similarity(ra.bitstring, rb.bitstring)
        param_score = self._param_similarity(ra.parameters, rb.parameters)
        score = 0.4 * prime_score + 0.4 * bit_score + 0.2 * param_score
        return score, ra, rb

    @staticmethod
    def _guess_prime(word: str) -> str:
        if any(k in word for k in ["dog", "cat", "wolf", "bird", "fish"]):
            return "Animal"
        if any(k in word for k in ["apple", "banana", "bread", "steak", "fruit", "food"]):
            return "Food"
        if any(k in word for k in ["feel", "happy", "sad", "fear"]):
            return "Feeling"
        if any(k in word for k in ["run", "fight", "hug", "move"]):
            return "Action"
        return "Object"

    def _resolve_unknown(self, word: str, write: bool) -> Tuple[str, List[str]]:

        desc_result = self._wikidata_classify(word)
        if desc_result:
            prime, path = desc_result
            if path and write:
                self._write_auto_lexicon(word, prime, path)
            return prime, path


        prime = self._guess_prime(word)
        path = self._path_guess_from_tokens(word, prime)
        if path:
            return prime, path


        return self._lookup_and_classify(word, write=write)

    def _lookup_and_classify(self, word: str, write: bool) -> Tuple[str, List[str]]:
        desc = describe(word)
        blob = desc.lower()
        prime = self._guess_prime(blob or word)
        path = self._path_guess_from_tokens(blob or word, prime)
        if path and write:
            self._write_auto_lexicon(word, prime, path)
        return prime, path

    def _wikidata_classify(self, word: str) -> Tuple[str, List[str]] | None:
        desc = describe(word)
        if not desc:
            return None
        blob = desc.lower()
        prime = self._guess_prime(blob or word)
        path = self._path_guess_from_tokens(blob or word, prime)
        if not path:
            return None
        return prime, path

    def _write_auto_lexicon(self, word: str, prime: str, path: List[str]) -> None:
        word_key = word.strip().lower()
        if not word_key:
            return
        self.lexicon_auto[word_key] = {"prime": prime, "path": path}
        self.lexicon_auto_path.write_text(
            json.dumps(self.lexicon_auto, indent=2),
            encoding="utf-8",
        )

    def _path_guess_from_tokens(self, text: str, prime: str) -> List[str]:
        low = text.lower()
        if prime == "Animal":
            mammal = "Mammal" if any(k in low for k in ["mammal", "dog", "cat", "cow", "wolf"]) else "Non-Mammal"
            domestic = "Domestic" if any(k in low for k in ["domestic", "pet", "tame"]) else "Wild"
            carn = "Carnivore" if any(k in low for k in ["carnivore", "predator", "meat"]) else "Herbivore"
            return [mammal, domestic, carn]
        if prime == "Object":
            tool = "Tool" if any(k in low for k in ["tool", "device", "instrument"]) else "Non-Tool"
            mech = "Mechanical" if any(k in low for k in ["mechanical", "engine", "machine"]) else "Natural"
            return [tool, mech]
        if prime == "Action":
            violence = "Violence" if any(k in low for k in ["attack", "violence", "fight", "harm"]) else "Cooperation"
            return [violence]
        if prime == "Feeling":
            positive = "Positive" if any(k in low for k in ["happy", "joy", "pleasure", "positive"]) else "Negative"
            calm = "Calm" if any(k in low for k in ["calm", "peace", "relax"]) else "Arousal"
            return [positive, calm]
        if prime == "Food":
            fruit = "Fruit" if any(k in low for k in ["fruit", "apple", "banana", "berry"]) else "Non-Fruit"
            fresh = "Fresh" if any(k in low for k in ["fresh", "raw"]) else "Cooked"
            return [fruit, fresh]
        return []

    def _traverse(self, tree: dict, path: List[str]) -> Tuple[str, Dict[str, float]]:
        bitstring = ""
        params: Dict[str, float] = {}
        node = tree
        for step in path:
            name = node.get("name", "")
            yes_name = node.get("yes", {}).get("name", "")
            no_name = node.get("no", {}).get("name", "")
            step_low = step.lower()
            if step_low == name.lower():
                is_yes = True
            elif yes_name and step_low == yes_name.lower():
                is_yes = True
            elif no_name and step_low == no_name.lower():
                is_yes = False
            else:
                is_yes = True
            bit = node.get("bit_on_yes" if is_yes else "bit_on_no", "0")
            bitstring += bit
            updates = node.get("params_on_yes" if is_yes else "params_on_no", {})
            for k, v in updates.items():
                params[k] = float(v)
            node = node.get("yes" if is_yes else "no", {})
            if not node:
                break
        return bitstring, params

    @staticmethod
    def _feature_bits(params: Dict[str, float]) -> str:
        def is_true(key: str, thr: float) -> bool:
            return params.get(key, 0.0) >= thr

        bits = [
            is_true("p1", 0.7),
            params.get("p1", 0.0) <= 0.3,
            is_true("p12", 0.7),
            is_true("p13", 0.7),
            is_true("p14", 0.7),
            is_true("p20", 0.7),
            is_true("p5", 0.7),
            is_true("p19", 0.7),
            is_true("p15", 0.7),
            is_true("p16", 0.7),
            is_true("p17", 0.7),
            is_true("p18", 0.7),
            is_true("p2", 0.7),
            is_true("p9", 0.7),
            is_true("p7", 0.7),
            is_true("p8", 0.7),
            params.get("p8", 1.0) <= 0.3,
            is_true("p10", 0.7),
            is_true("p3", 0.7),
            is_true("p6", 0.7),
        ]
        return "".join("1" if b else "0" for b in bits)

    @staticmethod
    def _bit_similarity(a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        max_len = max(len(a), len(b))
        same_prefix = 0
        for i in range(min(len(a), len(b))):
            if a[i] == b[i]:
                same_prefix += 1
            else:
                break
        return same_prefix / max_len

    @staticmethod
    def _param_similarity(a: Dict[str, float], b: Dict[str, float]) -> float:
        if not a or not b:
            return 0.0
        keys = set(a.keys()) | set(b.keys())
        if not keys:
            return 0.0
        diff = 0.0
        for k in keys:
            diff += abs(a.get(k, 0.0) - b.get(k, 0.0))

        return max(0.0, 1.0 - diff / max(1.0, len(keys)))
