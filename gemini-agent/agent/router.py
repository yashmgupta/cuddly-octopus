"""Gemini-powered semantic router — matches user intent to a known skill
or signals that a new skill must be generated."""

from __future__ import annotations

import json
from agent.llm import ask
from agent import skills as skill_store

_ROUTER_SYSTEM = """\
You are a Semantic Router for an AI Agent.
Match the user's intent to an existing skill OR declare a new one is needed.

RULES — reply with EXACTLY one of the two formats below, nothing else:

1. If intent matches an existing skill (even with typos / rephrasing):
   MATCH: <skill_name> | ARG: <extracted_argument_or_None>

2. If NO skill matches:
   NEW_SKILL: <snake_case_function_name> | DESC: <one-line description>
"""


def route(prompt: str) -> dict:
    """Return a routing decision dict.

    Returns one of:
      {"type": "match", "skill_name": str, "arg": str | None}
      {"type": "new",   "skill_name": str, "description": str}
      {"type": "unknown", "raw": str}
    """
    manifest = skill_store.get_skills_manifest()
    full_prompt = (
        f"Available skills:\n{json.dumps(manifest, indent=2)}\n\n"
        f"User request: {prompt}"
    )
    response = ask(full_prompt, system=_ROUTER_SYSTEM)
    first_line = response.strip().split("\n")[0]

    if "MATCH:" in first_line:
        parts = first_line.split("|")
        skill_name = parts[0].replace("MATCH:", "").strip()
        arg_val = parts[1].replace("ARG:", "").strip() if len(parts) > 1 else "None"
        arg = arg_val.strip("'\"") if arg_val.lower() != "none" else None
        return {"type": "match", "skill_name": skill_name, "arg": arg}

    if "NEW_SKILL:" in first_line:
        parts = first_line.split("|")
        skill_name = parts[0].replace("NEW_SKILL:", "").strip()
        description = parts[1].replace("DESC:", "").strip() if len(parts) > 1 else ""
        return {"type": "new", "skill_name": skill_name, "description": description}

    return {"type": "unknown", "raw": response}
