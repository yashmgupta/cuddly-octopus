"""Tests for agent/memory.py."""

import pytest
from pathlib import Path

import agent.memory as mem_module


@pytest.fixture(autouse=True)
def _tmp_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Point the DB at a temporary file for each test."""
    monkeypatch.setattr(mem_module, "DB_PATH", tmp_path / "test_agent.db")
    yield


def test_init_db_creates_tables():
    mem_module.init_db()
    with mem_module.connect() as db:
        tables = {
            r[0]
            for r in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    assert "memories" in tables
    assert "skills" in tables


def test_save_and_search_memory():
    mem_module.init_db()
    mem_module.save_memory("Python agent test memory", tags="test", importance=3)
    results = mem_module.search_memory("Python agent")
    assert len(results) > 0
    assert "Python agent test memory" in results[0]


def test_search_memory_empty():
    mem_module.init_db()
    results = mem_module.search_memory("nonexistent xyz")
    assert results == []


def test_memory_importance_ordering():
    mem_module.init_db()
    mem_module.save_memory("low importance", tags="test", importance=1)
    mem_module.save_memory("high importance", tags="test", importance=5)
    results = mem_module.search_memory("importance")
    assert results[0] == "high importance"
