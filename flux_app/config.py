import os
from pathlib import Path

def _getenv_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _getenv_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _getenv_list(name: str, default: list[str]) -> list[str]:
    raw = os.getenv(name)
    if raw is None:
        return default
    items = [x.strip() for x in raw.split(",") if x.strip()]
    return items or default

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
LOG_DIR = ROOT / "logs"
DB_PATH = DATA_DIR / "synapse.db"

BACKEND_PORT = _getenv_int("FLUX_BACKEND_PORT", 3001)
BRIDGE_PORT = _getenv_int("FLUX_BRIDGE_PORT", 5002)
FRONTEND_PORT = _getenv_int("FLUX_FRONTEND_PORT", 8080)
BACKEND_HOST = os.getenv("FLUX_BACKEND_HOST", "0.0.0.0")
BRIDGE_HOST = os.getenv("FLUX_BRIDGE_HOST", "127.0.0.1")

EMBED_DIM = _getenv_int("FLUX_EMBED_DIM", 200)

LOCAL_CONFIDENCE_THRESHOLD = 0.65
LOCAL_MIN_SCORE = 0.15

MAX_WEB_SOURCES = _getenv_int("FLUX_MAX_WEB_SOURCES", 3)
MAX_SUMMARY_SENTENCES = _getenv_int("FLUX_MAX_SUMMARY_SENTENCES", 3)
WEB_TIMEOUT_SECONDS = _getenv_float("FLUX_WEB_TIMEOUT_SECONDS", 3.0)
PAGE_TIMEOUT_SECONDS = _getenv_float("FLUX_PAGE_TIMEOUT_SECONDS", 3.5)
MAX_PAGE_BYTES = _getenv_int("FLUX_MAX_PAGE_BYTES", 350_000)
MAX_REQUEST_BYTES = _getenv_int("FLUX_MAX_REQUEST_BYTES", 64_000)
MAX_TRAIN_QUESTIONS = _getenv_int("FLUX_MAX_TRAIN_QUESTIONS", 200)
REQUEST_TIME_BUDGET_MS = _getenv_int("FLUX_REQUEST_TIME_BUDGET_MS", 5000)
ALLOW_ORIGINS = _getenv_list("FLUX_ALLOW_ORIGINS", ["*"])
RATE_LIMIT_PER_MIN = _getenv_int("FLUX_RATE_LIMIT_PER_MIN", 120)
MAX_SESSIONS = _getenv_int("FLUX_MAX_SESSIONS", 5000)
MAX_SESSION_HISTORY = _getenv_int("FLUX_MAX_SESSION_HISTORY", 40)

USER_AGENT = "FluxAI/0.1"

DEFAULT_WEIGHT_AUTO = 1.15
DEFAULT_WEIGHT_MANUAL = 2.0

W2V_DIR = DATA_DIR / "word2vec"
