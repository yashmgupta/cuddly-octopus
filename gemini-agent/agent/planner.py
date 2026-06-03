"""Gemini-powered goal planner — produces a numbered step list."""

from __future__ import annotations

from agent.llm import ask

_SYSTEM = (
    "You are a concise step-by-step planner. "
    "Given a goal, relevant context, and available tools, produce a clear numbered plan. "
    "Reply with ONLY the numbered steps, no preamble or extra text."
)


def make_plan(goal: str, context: list[str], tools: list[str]) -> list[str]:
    """Return a list of plain-text steps to achieve *goal*."""
    context_str = "\n".join(f"- {c}" for c in context) if context else "None"
    tools_str = "\n".join(f"- {t}" for t in tools) if tools else "None"

    prompt = (
        f"Goal: {goal}\n\n"
        f"Relevant context:\n{context_str}\n\n"
        f"Available tools:\n{tools_str}\n\n"
        "Write a numbered step-by-step plan to achieve the goal."
    )

    raw = ask(prompt, system=_SYSTEM)

    steps: list[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if line and line[0].isdigit():
            parts = line.split(None, 1)
            steps.append(parts[1].lstrip("). ") if len(parts) == 2 else line)
    return steps or [raw.strip()]
