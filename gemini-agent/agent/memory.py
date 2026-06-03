"""SQLite-backed episodic memory store."""

import sqlite3
from pathlib import Path
from datetime import datetime, UTC
from typing import List

DB_PATH = Path(__file__).parent.parent / "data" / "agent.db"


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the memories table if it does not yet exist."""
    with connect() as db:
        db.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            content     TEXT    NOT NULL,
            tags        TEXT    DEFAULT '',
            importance  INTEGER DEFAULT 1,
            created_at  TEXT    NOT NULL
        )
        """)


def save_memory(content: str, tags: str = "", importance: int = 1) -> None:
    with connect() as db:
        db.execute(
            "INSERT INTO memories(content, tags, importance, created_at) VALUES (?, ?, ?, ?)",
            (content, tags, importance, datetime.now(UTC).isoformat()),
        )


def search_memory(query: str, limit: int = 5) -> List[str]:
    with connect() as db:
        rows = db.execute(
            """
            SELECT content FROM memories
            WHERE content LIKE ? OR tags LIKE ?
            ORDER BY importance DESC, id DESC
            LIMIT ?
            """,
            (f"%{query}%", f"%{query}%", limit),
        ).fetchall()
    return [r["content"] for r in rows]
