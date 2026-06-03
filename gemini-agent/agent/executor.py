"""Task executor: plan → ReAct loop → reflect.

For new skills the flow is:
  router signals NEW_SKILL
    → planner.make_plan()        (Gemini step-by-step plan)
    → ReAct loop with tools      (observe → act × MAX_STEPS)
    → _reflect()                 (auto-save reusable skill)
    → generate_and_run_skill()   (persist + execute the generated code)
"""

from __future__ import annotations

import inspect
import json
import re

from agent import llm, memory
from agent import skills as skill_store
from agent.planner import make_plan
from agent.tools import DEFAULT_TOOLS

MAX_STEPS = 8

_ACT_SYSTEM = """\
You are a task executor. Work through a plan one action at a time using available tools.

For each step respond with EXACTLY one JSON object (no extra text):
  {{"tool": "<tool_name>", "params": {{"<key>": "<value>", ...}}}}

To submit the final answer:
  {{"tool": "finish", "params": {{"answer": "<your answer>"}}}}

Available tools:
{tools}"""

_REFLECT_SYSTEM = """\
You are a learning agent. Given a completed task, decide whether the approach
was generic enough to save as a reusable skill.

If yes, reply with JSON: {{"name": "...", "trigger": "...", "instructions": "..."}}
  IMPORTANT: "name" MUST be a valid Python snake_case identifier (lowercase, underscores only, no spaces).
If no, reply with exactly: null"""

_CODEGEN_SYSTEM = """\
You are a Python code generator.
Generate a single, clean Python function with the exact name provided.
- For web searching use: from googlesearch import search
- Output ONLY the function inside a ```python block — no explanation."""


def _to_snake_case(name: str) -> str:
    """Convert any string to a valid Python snake_case identifier."""
    # Replace spaces/hyphens/dots with underscores
    name = re.sub(r"[\s\-\.]+", "_", name.strip())
    # Remove any characters that are not alphanumeric or underscore
    name = re.sub(r"[^\w]", "", name)
    # Lowercase everything
    name = name.lower()
    # Strip leading digits/underscores
    name = name.lstrip("_0123456789") or "skill"
    return name


# ── Public entry points ────────────────────────────────────────────────────

def run(goal: str) -> str:
    """Run the full plan → ReAct → reflect loop and return the answer."""
    past = memory.search_memory(goal, limit=3)
    tool_descs = [t.prompt_repr() for t in DEFAULT_TOOLS.values()]

    steps = make_plan(goal, past, tool_descs)
    plan_text = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(steps))

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

    memory.save_memory(f"Goal: {goal}\nAnswer: {answer}", tags=goal[:50], importance=2)
    _reflect(goal, history)
    return answer


def generate_and_run_skill(skill_name: str, description: str, goal: str, arg=None) -> None:
    """Ask Gemini to write the skill code, persist it, then execute it."""
    # Always ensure skill_name is a valid Python identifier
    skill_name = _to_snake_case(skill_name)

    prompt = (
        f"Generate a Python function named '{skill_name}' that: {description}\n"
        f"Original goal: {goal}"
    )
    raw = llm.ask(prompt, system=_CODEGEN_SYSTEM)
    code = raw.split("```python")[-1].split("```")[0].strip()

    skill_store.save_skill(skill_name, goal[:80], description, code)
    print(f"\U0001f4be Saved new skill '{skill_name}' to hybrid store (JSON + SQLite).")
    _run_skill_code(skill_name, code, arg)


def run_skill(skill_name: str, arg=None) -> None:
    """Execute an existing skill by name and update its stats."""
    all_skills = skill_store.load_all_skills()

    # If exact name not found, try snake_case version
    if skill_name not in all_skills:
        snake = _to_snake_case(skill_name)
        if snake in all_skills:
            skill_name = snake
        else:
            print(f"\u26a0\ufe0f Skill '{skill_name}' not found.")
            return

    code = all_skills[skill_name]["code"]
    success = _run_skill_code(skill_name, code, arg)
    try:
        skill_store.update_skill_stats(skill_name, success)
    except Exception:
        pass


# ── Internal helpers ───────────────────────────────────────────────────────

def _run_skill_code(skill_name: str, code_str: str, arg=None) -> bool:
    """exec() the skill code and call the function; returns True on success."""
    # Sanitize skill name for use as a Python function name
    safe_name = _to_snake_case(skill_name)

    # If the code uses the original (possibly invalid) name, patch it
    if skill_name != safe_name:
        code_str = code_str.replace(f"def {skill_name}(", f"def {safe_name}(")

    try:
        from googlesearch import search  # make available to generated code
        local_ctx: dict = {"search": search}
        global_ctx = globals().copy()
        global_ctx["search"] = search

        exec(code_str, global_ctx, local_ctx)  # noqa: S102
        func = local_ctx.get(safe_name) or global_ctx.get(safe_name)

        if func:
            sig = inspect.signature(func)
            if sig.parameters and arg is not None:
                func(arg)
            else:
                func()
            return True

        print("\u26a0\ufe0f Function not found in execution scope.")
        return False
    except Exception as exc:
        print(f"\U0001f6a8 Runtime Error: {exc}")
        return False


def _parse_json(text: str) -> dict | None:
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
    """After task completion, auto-extract a reusable skill via Gemini."""
    summary = "\n".join(m["content"] for m in history[-6:])
    raw = llm.ask(
        f"Task: {goal}\n\nExecution summary:\n{summary}",
        system=_REFLECT_SYSTEM,
    ).strip()

    if raw.lower() == "null":
        return
    skill = _parse_json(raw)
    if skill and {"name", "trigger", "instructions"} <= skill.keys():
        # Always sanitize the name Gemini returns
        safe_name = _to_snake_case(skill["name"])
        stub = (
            f"# Auto-reflected from goal: {goal[:60]}\n"
            f"def {safe_name}():\n"
            f"    \"\"\"{ skill['instructions'] }\"\"\"\n"
            f"    pass  # Replace with real implementation\n"
        )
        skill_store.save_skill(
            safe_name,
            skill["trigger"],
            skill["instructions"][:120],
            stub,
        )
        print(f"\U0001f9e0 Reflected new skill saved: '{safe_name}'")
