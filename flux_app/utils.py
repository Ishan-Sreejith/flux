import json
import re
import time
from datetime import datetime, timezone
from typing import Iterable, List

_WORD_RE = re.compile(r"[A-Za-z0-9']+")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def tokenize(text: str) -> List[str]:
    if not text:
        return []
    return [m.group(0).lower() for m in _WORD_RE.finditer(text)]


def l2_normalize(vec: List[float]) -> List[float]:
    s = sum(v * v for v in vec)
    if s <= 0:
        return vec
    inv = 1.0 / (s ** 0.5)
    return [v * inv for v in vec]


def chunk_words(text: str, size: int = 12) -> Iterable[str]:
    words = text.split()
    for i in range(0, len(words), size):
        yield " ".join(words[i : i + size])


def sleep_ms(ms: int) -> None:
    time.sleep(ms / 1000.0)


def json_dumps(data) -> str:
    return json.dumps(data, ensure_ascii=True)


def monotonic_ms() -> int:
    return int(time.monotonic() * 1000)


def clamp_int(value: int, low: int, high: int) -> int:
    return max(low, min(high, int(value)))
