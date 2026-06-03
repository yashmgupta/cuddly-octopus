"""Skill persistence and retrieval."""

from datetime import datetime
from typing import Dict, List

from agent.memory import connect


def save_skill(name: str, trigger: str, instructions: str) -> None:
    """Persist a new skill, or update an existing one with the same name."""
    with connect() as db:
        existing = db.execute(
            "SELECT id FROM skills WHERE name = ?", (name,)
        ).fetchone()
        if existing:
            db.execute(
                """
                UPDATE skills
                SET trigger = ?, instructions = ?, updated_at = ?
                WHERE id = ?
                """,
                (trigger, instructions, datetime.utcnow().isoformat(), existing["id"]),
            )
        else:
            db.execute(
                """
                INSERT INTO skills(name, trigger, instructions, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (name, trigger, instructions, datetime.utcnow().isoformat()),
            )


def search_skills(query: str, limit: int = 5) -> List[Dict[str, str]]:
    """Return the most relevant skills for *query*."""
    with connect() as db:
        rows = db.execute(
            """
            SELECT name, trigger, instructions FROM skills
            WHERE name LIKE ? OR trigger LIKE ? OR instructions LIKE ?
            ORDER BY success_count DESC, id DESC
            LIMIT ?
            """,
            (f"%{query}%", f"%{query}%", f"%{query}%", limit),
        ).fetchall()
    return [
        {"name": r["name"], "trigger": r["trigger"], "instructions": r["instructions"]}
        for r in rows
    ]
