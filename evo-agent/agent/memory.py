"""SQLite-backed memory and skills store for the agent."""

import sqlite3
from pathlib import Path
from datetime import datetime, UTC
from typing import List

DB_PATH = Path(__file__).parent.parent / "data" / "agent.db"


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


# ── Memory ────────────────────────────────────────────────────────────────────

def save_memory(content: str, tags: str = "", importance: int = 1) -> None:
    """Persist a new memory entry."""
    with connect() as db:
        db.execute(
            "INSERT INTO memories(content, tags, importance, created_at) VALUES (?, ?, ?, ?)",
            (content, tags, importance, datetime.now(UTC).isoformat()),
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


# ── Skills ────────────────────────────────────────────────────────────────────

def save_skill(name: str, trigger: str, instructions: str) -> None:
    """Persist a new skill (upsert by name)."""
    with connect() as db:
        existing = db.execute(
            "SELECT id FROM skills WHERE name = ?", (name,)
        ).fetchone()
        if existing:
            db.execute(
                "UPDATE skills SET trigger=?, instructions=?, updated_at=? WHERE id=?",
                (trigger, instructions, datetime.now(UTC).isoformat(), existing["id"]),
            )
        else:
            db.execute(
                "INSERT INTO skills(name, trigger, instructions, updated_at) VALUES (?, ?, ?, ?)",
                (name, trigger, instructions, datetime.now(UTC).isoformat()),
            )


def search_skills(query: str, limit: int = 3) -> List[dict]:
    """Return skills whose trigger or name matches *query*."""
    with connect() as db:
        rows = db.execute(
            """
            SELECT id, name, trigger, instructions, success_count, fail_count
            FROM skills
            WHERE trigger LIKE ? OR name LIKE ?
            ORDER BY success_count DESC, id DESC
            LIMIT ?
            """,
            (f"%{query}%", f"%{query}%", limit),
        ).fetchall()
    return [dict(r) for r in rows]


def update_skill_stats(skill_id: int, success: bool) -> None:
    """Increment the success or fail counter for a skill."""
    with connect() as db:
        db.execute(
            """
            UPDATE skills
            SET success_count = success_count + ?,
                fail_count    = fail_count + ?,
                updated_at    = ?
            WHERE id = ?
            """,
            (1 if success else 0, 0 if success else 1, datetime.now(UTC).isoformat(), skill_id),
        )
