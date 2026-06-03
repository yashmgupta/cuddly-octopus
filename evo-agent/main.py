"""Entry point for the Evo-Agent."""

from rich import print as rprint
from rich.panel import Panel
from rich.prompt import Prompt

from agent.memory import init_db, search_memory
from agent.skills import search_skills
from agent.planner import create_plan
from agent.executor import execute_goal


def main() -> None:
    init_db()

    rprint(Panel("[bold green]Evo-Agent MVP[/bold green]", expand=False))
    rprint("[dim]Type 'exit' or 'quit' to stop.[/dim]\n")

    while True:
        goal = Prompt.ask("[bold]Goal[/bold]").strip()

        if not goal:
            continue

        if goal.lower() in {"exit", "quit"}:
            rprint("[dim]Goodbye.[/dim]")
            break

        memories = search_memory(goal)
        skills = search_skills(goal)

        rprint("\n[bold yellow]Creating plan...[/bold yellow]")
        plan = create_plan(goal, memories, skills)
        rprint(Panel(plan, title="[bold yellow]Plan[/bold yellow]", expand=False))

        rprint("\n[bold cyan]Executing...[/bold cyan]")
        result = execute_goal(goal, plan)
        rprint(Panel(result, title="[bold cyan]Result[/bold cyan]", expand=False))


if __name__ == "__main__":
    main()
