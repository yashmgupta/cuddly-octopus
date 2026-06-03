"""Task executor with reflection and skill learning."""

from agent.llm import ask_llm
from agent.memory import save_memory
from agent.skills import save_skill

_REFLECTION_PROMPT = """
Review this completed task and extract one reusable skill if useful.

Goal:
{goal}

Result:
{result}

If a skill is worth saving, respond in EXACTLY this format (no extra text):

NAME: <short skill name>
TRIGGER: <one-line description of when to use this skill>
INSTRUCTIONS: <step-by-step instructions>

If no skill is worth saving, respond with: NO_SKILL
"""


def execute_goal(goal: str, plan: str) -> str:
    """Execute *plan* for *goal*, then reflect and optionally save a skill."""
    prompt = f"""Complete this task using the plan below.

Goal:
{goal}

Plan:
{plan}

Return a clear, useful final answer.
"""
    result = ask_llm(prompt)

    save_memory(
        content=f"Goal: {goal}\nResult: {result}",
        tags="task,result",
        importance=2,
    )

    reflection = ask_llm(_REFLECTION_PROMPT.format(goal=goal, result=result))

    if reflection.strip().upper() != "NO_SKILL" and all(
        key in reflection for key in ("NAME:", "TRIGGER:", "INSTRUCTIONS:")
    ):
        try:
            name = reflection.split("NAME:")[1].split("TRIGGER:")[0].strip()
            trigger = reflection.split("TRIGGER:")[1].split("INSTRUCTIONS:")[0].strip()
            instructions = reflection.split("INSTRUCTIONS:")[1].strip()
            if name and trigger and instructions:
                save_skill(name, trigger, instructions)
        except Exception:  # noqa: BLE001
            pass

    return result
