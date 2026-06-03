# 🐙 Gemini Autonomous Agent — Multi-Module Edition

A self-learning AI agent powered by **Gemini 2.5 Flash** (Google AI Studio **free tier**).

## Architecture

```
User Prompt
    │
    ▼
┌─────────────┐
│   router    │  ← Gemini semantic match against known skills
└──────┬──────┘
       │
  ┌────┴─────┐
  │          │
MATCH      NEW SKILL
  │          │
  ▼          ▼
run_skill  planner.make_plan()     ← Gemini step-by-step plan
           executor.run()          ← ReAct loop (up to 8 steps)
             ├─ web_search tool
             ├─ read_file tool
             └─ write_file tool
           _reflect()              ← auto-extract reusable skill
           generate_and_run_skill()← Gemini writes + saves code
```

## Hybrid Skill Store

| Store | What it holds |
|---|---|
| `data/skills_database.json` | Executable Python code (easy to inspect/edit) |
| `data/agent.db` (SQLite) | Trigger text, success/fail stats, timestamps |

## Quickstart (Local)

```bash
# 1. Clone
git clone https://github.com/yashmgupta/cuddly-octopus.git
cd cuddly-octopus/gemini-agent

# 2. Install
pip install -r requirements.txt

# 3. Configure API key (free from https://aistudio.google.com/apikey)
cp .env.example .env
# Edit .env → paste your key

# 4. Run
python main.py
```

## Quickstart (Google Colab)

1. Open `colab_runner.ipynb` in [Google Colab](https://colab.research.google.com)
2. Paste your API key in **Step 3**
3. Run all cells

## Free Tier Limits

| Limit | Value |
|---|---|
| Requests per minute | 15 RPM |
| Requests per day | 1,500 |
| Tokens per minute | 1M |

## Module Overview

| File | Role |
|---|---|
| `main.py` | CLI entry point, orchestrates the flow |
| `agent/router.py` | Gemini semantic router |
| `agent/planner.py` | Gemini step-by-step planner |
| `agent/executor.py` | ReAct loop + code generation + reflect |
| `agent/skills.py` | Hybrid JSON + SQLite skill store |
| `agent/memory.py` | SQLite episodic memory |
| `agent/tools.py` | `read_file`, `write_file`, `web_search` |
| `agent/llm.py` | Thin Gemini API wrapper |
