"""SQLite-backed memory store for the agent."""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List

DB_PATH = Path("data/agent.db")


def connect() -> sqlite3.Connection:
    """Open (and if needed create) the SQLite database."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the required tables if they do not yet exist."""
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
        db.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL,
            trigger       TEXT    NOT NULL,
            instructions  TEXT    NOT NULL,
            success_count INTEGER DEFAULT 0,
            fail_count    INTEGER DEFAULT 0,
            updated_at    TEXT    NOT NULL
        )
        """)


def save_memory(content: str, tags: str = "", importance: int = 1) -> None:
    """Persist a new memory entry."""
    with connect() as db:
        db.execute(
            "INSERT INTO memories(content, tags, importance, created_at) VALUES (?, ?, ?, ?)",
            (content, tags, importance, datetime.utcnow().isoformat()),
        )


def search_memory(query: str, limit: int = 5) -> List[str]:
    """Return the most relevant memory snippets for *query*."""
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
