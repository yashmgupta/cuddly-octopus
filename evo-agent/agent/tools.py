"""File-based workspace tools available to the agent."""

from pathlib import Path
from typing import Callable, Dict

WORKSPACE = Path("workspace")
WORKSPACE.mkdir(exist_ok=True)


def write_file(filename: str, content: str) -> str:
    """Write *content* to *filename* inside the workspace directory."""
    path = WORKSPACE / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"Saved to {path}"


def read_file(filename: str) -> str:
    """Return the contents of *filename* from the workspace directory."""
    path = WORKSPACE / filename
    if not path.exists():
        return f"File not found: {filename}"
    return path.read_text(encoding="utf-8")


TOOLS: Dict[str, Callable] = {
    "write_file": write_file,
    "read_file": read_file,
}
