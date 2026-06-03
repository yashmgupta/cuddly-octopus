"""Built-in tools for the agent (file workspace utilities)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

WORKSPACE = Path(__file__).parent.parent / "workspace"


@dataclass
class Tool:
    """A callable capability the agent can invoke."""

    name: str
    description: str
    params: dict[str, str]  # param_name → short description
    _fn: Callable

    def run(self, **kwargs) -> str:
        try:
            return self._fn(**kwargs)
        except Exception as exc:
            return f"Error: {exc}"

    def prompt_repr(self) -> str:
        """One-liner description suitable for injection into a prompt."""
        param_str = ", ".join(f"{k}: {v}" for k, v in self.params.items())
        return f"{self.name}({param_str}) — {self.description}"


# ── Built-in tools ────────────────────────────────────────────────────────────

def _read_file(path: str) -> str:
    full = WORKSPACE / path
    if not full.exists():
        return f"[file not found: {path}]"
    return full.read_text()


def _write_file(path: str, content: str) -> str:
    full = WORKSPACE / path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content)
    return f"Wrote {len(content)} characters to {path}"


read_file = Tool(
    name="read_file",
    description="Read a file from the workspace",
    params={"path": "relative path inside workspace"},
    _fn=_read_file,
)

write_file = Tool(
    name="write_file",
    description="Write text to a file in the workspace",
    params={"path": "relative path", "content": "text to write"},
    _fn=_write_file,
)

DEFAULT_TOOLS: dict[str, Tool] = {t.name: t for t in [read_file, write_file]}
