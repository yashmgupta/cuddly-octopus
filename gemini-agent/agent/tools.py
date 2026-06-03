"""Built-in tools available to the executor."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

WORKSPACE = Path(__file__).parent.parent / "workspace"


@dataclass
class Tool:
    name: str
    description: str
    params: dict[str, str]
    _fn: Callable

    def run(self, **kwargs) -> str:
        try:
            return self._fn(**kwargs)
        except Exception as exc:
            return f"Error: {exc}"

    def prompt_repr(self) -> str:
        param_str = ", ".join(f"{k}: {v}" for k, v in self.params.items())
        return f"{self.name}({param_str}) — {self.description}"


# ── Tool implementations ──────────────────────────────────────────────────

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


def _web_search(query: str, num_results: int = 3) -> str:
    try:
        from googlesearch import search
        results = list(search(query, num_results=int(num_results)))
        return "\n".join(results) if results else "No results found."
    except Exception as exc:
        return f"Search error: {exc}"


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

web_search = Tool(
    name="web_search",
    description="Search the web and return top URLs",
    params={"query": "search query", "num_results": "number of results (default 3)"},
    _fn=_web_search,
)

DEFAULT_TOOLS: dict[str, Tool] = {t.name: t for t in [read_file, write_file, web_search]}
