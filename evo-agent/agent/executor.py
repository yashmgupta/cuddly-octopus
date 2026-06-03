"""Task executor: plan → act → observe → remember → reflect (ReAct loop)."""

from __future__ import annotations

import json
import re

from agent import llm, memory
from agent.planner import make_plan
from agent.tools import DEFAULT_TOOLS

MAX_STEPS = 8

_ACT_SYSTEM = """\
You are a task executor. Work through a plan one action at a time using available tools.

For each action respond with EXACTLY one JSON object (no extra text):
  {{"tool": "<tool_name>", "params": {{<key>: <value>, ...}}}}

To submit the final answer use:
  {{"tool": "finish", "params": {{"answer": "<your answer>"}}}}

Available tools:
{tools}"""

_REFLECT_SYSTEM = """\
You are a learning agent. Given a completed task, decide whether the approach was
generic enough to save as a reusable skill.

If yes, reply with JSON: {{"name": "...", "trigger": "...", "instructions": "..."}}
If no, reply with exactly: null"""


def run(goal: str) -> str:
    """Run the full plan → execute → reflect loop for *goal* and return the answer."""
    # 1. Load relevant context
    past = memory.search_memory(goal, limit=3)
    tool_descs = [t.prompt_repr() for t in DEFAULT_TOOLS.values()]

    # 2. Plan
    steps = make_plan(goal, past, tool_descs)
    plan_text = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(steps))

    # 3. ReAct loop
    system = _ACT_SYSTEM.format(tools="\n".join(tool_descs))
    history: list[dict] = [
        {"role": "user", "content": f"Task: {goal}\n\nPlan:\n{plan_text}"}
    ]

    answer = ""
    for _ in range(MAX_STEPS):
        response = llm.chat(history, system=system)
        history.append({"role": "assistant", "content": response})

        action = _parse_json(response)
        if action is None:
            break

        tool_name = action.get("tool", "finish")
        params = action.get("params", {})

        if tool_name == "finish":
            answer = params.get("answer", response)
            break

        tool = DEFAULT_TOOLS.get(tool_name)
        observation = tool.run(**params) if tool else f"Unknown tool: {tool_name}"
        history.append({"role": "user", "content": f"Observation: {observation}"})

    if not answer:
        answer = "Task completed."

    # 4. Save to memory
    memory.save_memory(f"Goal: {goal}\nAnswer: {answer}", tags=goal[:50], importance=2)

    # 5. Reflect and optionally create a skill
    _reflect(goal, history)

    return answer


def _parse_json(text: str) -> dict | None:
    """Try to extract a JSON object from *text*, returning None on failure."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return None


def _reflect(goal: str, history: list[dict]) -> None:
    """Extract a reusable skill from the completed execution history."""
    summary = "\n".join(m["content"] for m in history[-6:])
    raw = llm.ask(
        f"Task: {goal}\n\nExecution summary:\n{summary}",
        system=_REFLECT_SYSTEM,
    )
    raw = raw.strip()
    if raw.lower() == "null":
        return
    skill = _parse_json(raw)
    if skill and {"name", "trigger", "instructions"} <= skill.keys():
        memory.save_skill(skill["name"], skill["trigger"], skill["instructions"])
