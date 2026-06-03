"""Tests for the tools module — no OpenAI API required."""

import pytest
import agent.tools as tools_mod
from agent.tools import DEFAULT_TOOLS


@pytest.fixture(autouse=True)
def tmp_workspace(tmp_path, monkeypatch):
    """Redirect all file operations to a temporary directory."""
    monkeypatch.setattr(tools_mod, "WORKSPACE", tmp_path)


# ── Tool registry ─────────────────────────────────────────────────────────────

def test_default_tools_present():
    assert "read_file" in DEFAULT_TOOLS
    assert "write_file" in DEFAULT_TOOLS


def test_tool_prompt_repr():
    desc = DEFAULT_TOOLS["read_file"].prompt_repr()
    assert "read_file" in desc
    assert "path" in desc


# ── File tools ────────────────────────────────────────────────────────────────

def test_write_and_read_file():
    result = DEFAULT_TOOLS["write_file"].run(path="hello.txt", content="hello world")
    assert "Wrote" in result
    content = DEFAULT_TOOLS["read_file"].run(path="hello.txt")
    assert content == "hello world"


def test_read_missing_file():
    result = DEFAULT_TOOLS["read_file"].run(path="missing.txt")
    assert "not found" in result


def test_write_creates_subdirectory(tmp_path):
    result = DEFAULT_TOOLS["write_file"].run(path="subdir/nested.txt", content="nested")
    assert "Wrote" in result
    assert (tmp_path / "subdir" / "nested.txt").exists()


def test_tool_run_returns_error_string():
    """Tool.run() must not raise — it returns an error string instead."""
    result = DEFAULT_TOOLS["write_file"].run(path="/absolute/forbidden", content="x")
    # Should return an Error string, not raise
    assert isinstance(result, str)
