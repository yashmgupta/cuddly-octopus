"""LLM-based goal planner."""

from typing import Any, Dict, List

from agent.llm import ask_llm


def create_plan(
    goal: str,
    memories: List[str],
    skills: List[Dict[str, Any]],
) -> str:
    """Generate a numbered execution plan for *goal* given past context."""
    memory_block = "\n".join(f"- {m}" for m in memories) or "None"
    skill_block = (
        "\n".join(
            f"- [{s['name']}] trigger: {s['trigger']}" for s in skills
        )
        or "None"
    )

    prompt = f"""You are a minimal evolving AI agent.

Goal:
{goal}

Relevant memories:
{memory_block}

Relevant skills:
{skill_block}

Create a short numbered plan (max 7 steps).
Keep it practical and safe.
Do not include harmful or irreversible actions.
"""
    return ask_llm(prompt)
