"""Hybrid skill store: JSON for code, SQLite for metadata & stats.

JSON  → stores executable skill code (easy to inspect / edit manually)
SQLite → stores trigger text, success/fail stats, and timestamps
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from datetime import datetime, UTC
from typing import Dict, List

SKILLS_JSON = Path(__file__).parent.parent / "data" / "skills_database.json"
DB_PATH = Path(__file__).parent.parent / "data" / "agent.db"

# ── Built-in hardcoded skills ──────────────────────────────────────────────
_BUILTIN_SKILLS: Dict[str, dict] = {
    "fetch_weather": {
        "description": "Returns current atmospheric weather conditions.",
        "code": "def fetch_weather():\n    print('The weather is currently sunny and 72\u00b0F.')",
    }
}


# ── DB helpers ────────────────────────────────────────────────────────────
def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_skills_db() -> None:
    """Create the skills metadata table if it does not yet exist."""
    with connect() as db:
        db.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL UNIQUE,
            trigger       TEXT    NOT NULL,
            description   TEXT    NOT NULL DEFAULT '',
            success_count INTEGER DEFAULT 0,
            fail_count    INTEGER DEFAULT 0,
            updated_at    TEXT    NOT NULL
        )
        """)


# ── Core operations ───────────────────────────────────────────────────────
def load_all_skills() -> Dict[str, dict]:
    """Return merged dict of builtin + JSON-persisted skills."""
    skills = dict(_BUILTIN_SKILLS)
    SKILLS_JSON.parent.mkdir(parents=True, exist_ok=True)
    if SKILLS_JSON.exists():
        try:
            with open(SKILLS_JSON) as f:
                skills.update(json.load(f))
        except Exception:
            pass
    return skills


def save_skill(name: str, trigger: str, description: str, code: str) -> None:
    """Persist skill code → JSON  and  metadata → SQLite."""
    # 1. Write code to JSON
    SKILLS_JSON.parent.mkdir(parents=True, exist_ok=True)
    all_skills: dict = {}
    if SKILLS_JSON.exists():
        try:
            with open(SKILLS_JSON) as f:
                all_skills = json.load(f)
        except Exception:
            pass
    all_skills[name] = {"description": description, "code": code}
    with open(SKILLS_JSON, "w") as f:
        json.dump(all_skills, f, indent=4)

    # 2. Upsert metadata to SQLite
    now = datetime.now(UTC).isoformat()
    with connect() as db:
        existing = db.execute("SELECT id FROM skills WHERE name = ?", (name,)).fetchone()
        if existing:
            db.execute(
                "UPDATE skills SET trigger=?, description=?, updated_at=? WHERE name=?",
                (trigger, description, now, name),
            )
        else:
            db.execute(
                "INSERT INTO skills(name, trigger, description, updated_at) VALUES (?, ?, ?, ?)",
                (name, trigger, description, now),
            )


def search_skills(query: str, limit: int = 5) -> List[dict]:
    """Search skills by name or trigger in SQLite metadata."""
    with connect() as db:
        rows = db.execute(
            """
            SELECT name, trigger, description, success_count, fail_count
            FROM skills
            WHERE trigger LIKE ? OR name LIKE ?
            ORDER BY success_count DESC, name
            LIMIT ?
            """,
            (f"%{query}%", f"%{query}%", limit),
        ).fetchall()
    return [dict(r) for r in rows]


def update_skill_stats(name: str, success: bool) -> None:
    """Increment success or fail counter for a skill in SQLite."""
    with connect() as db:
        db.execute(
            """
            UPDATE skills
            SET success_count = success_count + ?,
                fail_count    = fail_count    + ?,
                updated_at    = ?
            WHERE name = ?
            """,
            (1 if success else 0, 0 if success else 1, datetime.now(UTC).isoformat(), name),
        )


def get_skills_manifest() -> Dict[str, str]:
    """Return {skill_name: description} for the router prompt."""
    return {name: data["description"] for name, data in load_all_skills().items()}
