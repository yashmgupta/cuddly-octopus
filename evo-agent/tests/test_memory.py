"""Tests for the memory module — no OpenAI API required."""

import pytest
import agent.memory as mem


@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    """Use a fresh temporary database for every test."""
    monkeypatch.setattr(mem, "DB_PATH", tmp_path / "test.db")
    mem.init_db()


# ── Memory tests ──────────────────────────────────────────────────────────────

def test_save_and_search_memory():
    mem.save_memory("Paris is the capital of France", tags="geography", importance=3)
    results = mem.search_memory("Paris")
    assert any("Paris" in r for r in results)


def test_search_memory_no_match():
    results = mem.search_memory("xyzzy_no_match")
    assert results == []


def test_search_memory_by_tag():
    mem.save_memory("Some random content", tags="travel,europe", importance=1)
    results = mem.search_memory("europe")
    assert len(results) == 1


# ── Skill tests ───────────────────────────────────────────────────────────────

def test_save_and_search_skill():
    mem.save_skill("summarize", "summarize text", "Read content then output a concise summary.")
    results = mem.search_skills("summarize")
    assert len(results) == 1
    assert results[0]["name"] == "summarize"


def test_search_skills_no_match():
    results = mem.search_skills("xyzzy_no_match")
    assert results == []


def test_save_skill_upsert():
    mem.save_skill("my_skill", "trigger A", "instructions A")
    mem.save_skill("my_skill", "trigger B", "instructions B")  # should update
    results = mem.search_skills("my_skill")
    assert len(results) == 1
    assert results[0]["instructions"] == "instructions B"


def test_update_skill_stats():
    mem.save_skill("track_me", "track", "do tracking")
    skill_id = mem.search_skills("track_me")[0]["id"]
    mem.update_skill_stats(skill_id, success=True)
    mem.update_skill_stats(skill_id, success=True)
    mem.update_skill_stats(skill_id, success=False)
    updated = mem.search_skills("track_me")[0]
    assert updated["success_count"] == 2
    assert updated["fail_count"] == 1
