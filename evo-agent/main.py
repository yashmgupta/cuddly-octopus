#!/usr/bin/env python
"""Evo-Agent — minimal evolving AI agent."""

from rich.console import Console
from rich.panel import Panel

from agent import memory, executor

console = Console()


def main() -> None:
    memory.init_db()
    console.print(Panel("🐙  Evo-Agent", subtitle="type 'exit' to quit", style="bold cyan"))

    while True:
        try:
            goal = console.input("\n[bold cyan]Goal >[/bold cyan] ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not goal or goal.lower() in {"exit", "quit"}:
            break

        with console.status("[bold yellow]Thinking…[/bold yellow]"):
            try:
                answer = executor.run(goal)
            except Exception as exc:
                console.print(f"[red]Error:[/red] {exc}")
                continue

        console.print(Panel(answer, title="Answer", border_style="green"))


if __name__ == "__main__":
    main()
