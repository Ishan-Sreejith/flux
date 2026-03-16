import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .config import DB_PATH, DEFAULT_WEIGHT_AUTO
from .utils import now_iso


SCHEMA = """
CREATE TABLE IF NOT EXISTS knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    source TEXT NOT NULL,
    url TEXT NOT NULL,
    confidence REAL NOT NULL,
    weight REAL NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS embeddings (
    knowledge_id INTEGER PRIMARY KEY,
    vector_json TEXT NOT NULL,
    FOREIGN KEY (knowledge_id) REFERENCES knowledge(id)
);

CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_knowledge_question ON knowledge(question);
CREATE INDEX IF NOT EXISTS idx_knowledge_updated ON knowledge(updated_at);
"""


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def add_knowledge(
    conn: sqlite3.Connection,
    question: str,
    answer: str,
    source: str,
    url: str,
    confidence: float,
    weight: float = DEFAULT_WEIGHT_AUTO,
    embedding: Optional[List[float]] = None,
) -> int:
    created = now_iso()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO knowledge (question, answer, source, url, confidence, weight, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (question, answer, source, url, confidence, weight, created, created),
    )
    knowledge_id = int(cur.lastrowid)
    if embedding is not None:
        cur.execute(
            "INSERT INTO embeddings (knowledge_id, vector_json) VALUES (?, ?)",
            (knowledge_id, json.dumps(embedding)),
        )
    conn.commit()
    return knowledge_id


def update_weight(conn: sqlite3.Connection, knowledge_id: int, weight: float) -> None:
    cur = conn.cursor()
    cur.execute(
        "UPDATE knowledge SET weight = ?, updated_at = ? WHERE id = ?",
        (weight, now_iso(), knowledge_id),
    )
    conn.commit()

def update_knowledge(
    conn: sqlite3.Connection,
    knowledge_id: int,
    answer: str,
    source: str,
    url: str,
    confidence: float,
    weight: float,
) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE knowledge
        SET answer = ?, source = ?, url = ?, confidence = ?, weight = ?, updated_at = ?
        WHERE id = ?
        """,
        (answer, source, url, confidence, weight, now_iso(), knowledge_id),
    )
    conn.commit()


def all_knowledge(conn: sqlite3.Connection) -> List[Dict]:
    cur = conn.cursor()
    cur.execute(
        "SELECT id, question, answer, source, url, confidence, weight FROM knowledge"
    )
    rows = cur.fetchall()
    return [
        {
            "id": row[0],
            "question": row[1],
            "answer": row[2],
            "source": row[3],
            "url": row[4],
            "confidence": row[5],
            "weight": row[6],
        }
        for row in rows
    ]


def get_embedding_map(conn: sqlite3.Connection) -> Dict[int, List[float]]:
    cur = conn.cursor()
    cur.execute("SELECT knowledge_id, vector_json FROM embeddings")
    rows = cur.fetchall()
    out = {}
    for knowledge_id, vector_json in rows:
        try:
            out[int(knowledge_id)] = json.loads(vector_json)
        except json.JSONDecodeError:
            continue
    return out


def clear_embeddings(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("DELETE FROM embeddings")
    conn.commit()


def get_meta(conn: sqlite3.Connection, key: str) -> Optional[str]:
    cur = conn.cursor()
    cur.execute("SELECT value FROM meta WHERE key = ?", (key,))
    row = cur.fetchone()
    return row[0] if row else None


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    conn.commit()


def get_knowledge_by_id(conn: sqlite3.Connection, knowledge_id: int) -> Optional[Dict]:
    cur = conn.cursor()
    cur.execute(
        "SELECT id, question, answer, source, url, confidence, weight FROM knowledge WHERE id = ?",
        (knowledge_id,),
    )
    row = cur.fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "question": row[1],
        "answer": row[2],
        "source": row[3],
        "url": row[4],
        "confidence": row[5],
        "weight": row[6],
    }


def count_knowledge(conn: sqlite3.Connection) -> int:
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM knowledge")
    row = cur.fetchone()
    return int(row[0]) if row else 0
