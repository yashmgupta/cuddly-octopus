# evo-agent — Minimal Evolving AI Agent

A lightweight Python AI agent with memory, skills, planning, and a ReAct execution loop.

## Features

- **Memory** — Persists past task results in SQLite, ranked by importance
- **Skills** — Saves reusable patterns learned from completed tasks (upsert by name)
- **Planner** — Uses an LLM to generate a step-by-step plan from goal + context
- **Executor** — ReAct loop: act → observe → repeat → save result → reflect
- **Tools** — Declarative `Tool` class; built-ins: `read_file`, `write_file`
- **CI** — GitHub Actions runs `pytest` on every push / PR

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

## Usage

```bash
python main.py
```

```
Goal > Make a short plan for researching budget hotels in Bangkok
```

The agent will:
1. Search relevant memories
2. Build a plan via the LLM
3. Execute the plan step-by-step (ReAct loop)
4. Save the result to memory
5. Reflect and optionally create a reusable skill

## Project Structure

```
evo-agent/
  main.py              # CLI entry point (rich-based)
  requirements.txt
  .env.example
  agent/
    llm.py             # OpenAI chat.completions wrapper (chat / ask)
    memory.py          # SQLite store: memories + skills tables
    tools.py           # Tool dataclass + read_file / write_file built-ins
    skills.py          # Skill interface (thin re-export from memory)
    planner.py         # LLM-based goal → numbered step list
    executor.py        # ReAct loop: plan → act → observe → reflect
  tests/
    test_memory.py     # Memory + skills unit tests
    test_tools.py      # Tool unit tests
  data/                # SQLite DB lives here (gitignored)
  workspace/           # Agent file workspace (gitignored)
  .github/workflows/
    test.yml           # CI: pytest on push / PR
```

## Running Tests

```bash
python -m pytest --tb=short -v
```

## Environment Variables

| Variable        | Default        | Description                  |
|-----------------|----------------|------------------------------|
| `OPENAI_API_KEY` | —             | Required — your OpenAI key   |
| `MODEL`         | `gpt-4.1-mini` | OpenAI model name            |

## Next Steps

- Add a `web_search` tool to enable real-time research
- Expand tool set (calculator, code runner, etc.)
- Add a skill editor / memory browser CLI
