# 🐙 Gemini Autonomous Agent

A self-learning AI agent powered by **Gemini 2.5 Flash** (Google AI Studio free tier).

## Features
- 🧠 Semantic skill routing via Gemini
- ⚡ Dynamically generates & saves new Python skills
- 💾 Persistent skill storage in `skills_database.json`
- 🔍 Web search via `googlesearch-python`

## Quickstart (Local)

```bash
# 1. Clone
git clone https://github.com/yashmgupta/cuddly-octopus.git
cd cuddly-octopus/gemini-agent

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your API key (get it free from https://aistudio.google.com/apikey)
cp .env.example .env
# Edit .env and paste your key

# 4. Run
python agent.py
```

## Quickstart (Google Colab)

1. Open `colab_runner.ipynb` in [Google Colab](https://colab.research.google.com)
2. Paste your free API key in **Step 3**
3. Run all cells

## Free Tier Limits (Google AI Studio)

| Limit | Value |
|---|---|
| Requests per minute | 15 RPM |
| Requests per day | 1,500 |
| Tokens per minute | 1M |

## Customise

Edit the last line of `agent.py` to change the task prompt:
```python
await agent.execute_task("Search for latest AI news")
```
