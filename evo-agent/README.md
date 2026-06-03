# Evo-Agent MVP

A minimal evolving AI agent with memory, skills, planning, and execution.

## Features

- **Memory** — Persists past task results in SQLite, ranked by importance
- **Skills** — Saves reusable skill patterns learned from completed tasks
- **Planner** — Uses an LLM to generate a step-by-step plan given goal + context
- **Executor** — Runs the plan, saves the outcome, and reflects to create new skills
- **Tools** — File read/write workspace utilities
- **CI** — GitHub Actions runs `pytest` on every push/PR

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

python main.py
```

## Usage

```
Goal > Make a short plan for researching budget hotels in Bangkok
```

The agent will:
1. Search relevant memories
2. Search relevant skills
3. Create a numbered plan via LLM
4. Execute the plan and produce an answer
5. Save the result to memory
6. Reflect and optionally create a reusable skill

## Project Structure

```
evo-agent/
  main.py              # Entry point
  requirements.txt
  .env.example
  agent/
    llm.py             # OpenAI client wrapper
    memory.py          # SQLite-backed memory store
    tools.py           # File workspace tools
    skills.py          # Skill persistence & search
    planner.py         # LLM-based goal planner
    executor.py        # Task executor + reflection loop
  data/                # SQLite DB lives here (gitignored)
  tests/
    test_memory.py
  .github/workflows/
    test.yml
```

## Running Tests

```bash
pytest
```

## Next Steps

- Add a `web_search` tool to enable real-time research
- Expand tool set (calculator, code runner, etc.)
- Add a skill editor / memory browser CLI
