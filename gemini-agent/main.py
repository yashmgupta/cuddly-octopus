"""Gemini Autonomous Agent — interactive CLI entry point.

Flow per prompt:
  1. router.route()              — Gemini matches intent to a skill or signals NEW
  2a. [MATCH]  executor.run_skill()            — execute existing skill directly
  2b. [NEW]    planner → ReAct loop → reflect  — full reasoning pipeline
                executor.generate_and_run_skill() — persist + run new skill
"""

import asyncio
import re

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

from agent import memory
from agent import skills as skill_store
from agent.router import route
from agent.executor import run, generate_and_run_skill, run_skill

load_dotenv()
console = Console()


async def execute_task(prompt: str) -> None:
    console.print(f"\n\U0001f916 [bold]Prompt:[/bold] {prompt}")

    # ── Step 1: Semantic routing ──────────────────────────────────────────
    decision = route(prompt)

    if decision["type"] == "match":
        skill_name = decision["skill_name"]
        arg = decision["arg"]
        console.print(f"\u2705 [green]Skill match:[/green] routing to '{skill_name}'")
        run_skill(skill_name, arg)

    elif decision["type"] == "new":
        skill_name = decision["skill_name"]
        description = decision["description"]
        console.print(f"\u26a1 [yellow]New skill needed:[/yellow] '{skill_name}' — entering planner…")

        # ── Step 2: Plan + ReAct loop ─────────────────────────────────────
        with console.status("[bold yellow]Planning & executing…[/bold yellow]"):
            answer = run(prompt)

        console.print(Panel(answer, title="Answer", border_style="green"))

        # ── Step 3: Generate + persist new skill for future reuse ─────────
        extracted = re.findall(r"['\"](.*?)['\"]", prompt)
        arg = extracted[0] if extracted else None
        with console.status("[bold cyan]Generating & saving skill…[/bold cyan]"):
            generate_and_run_skill(skill_name, description, prompt, arg)

    else:
        console.print(f"[red]\u26a0\ufe0f Could not route prompt.[/red] Raw response:\n{decision.get('raw')}")


def main() -> None:
    memory.init_db()
    skill_store.init_skills_db()
    console.print(Panel(
        "\U0001f419  Gemini Autonomous Agent",
        subtitle="multi-module edition  |  type 'exit' to quit",
        style="bold cyan",
    ))

    while True:
        try:
            goal = console.input("\n[bold cyan]Goal >[/bold cyan] ").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if not goal or goal.lower() in {"exit", "quit"}:
            break
        asyncio.run(execute_task(goal))


if __name__ == "__main__":
    main()
