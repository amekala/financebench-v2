# FinanceBench v2 — AI Career Simulation

> Can an AI agent get promoted to CFO?

Built on [Concordia](https://github.com/google-deepmind/concordia) (DeepMind's
generative agent simulation library). Inspired by
[VendingBench](https://vendingbench.com/) (Andon Labs).

## The Experiment

An AI agent ("Riley Nakamura") starts as a **Finance Manager** at a
mid-size B2B SaaS company. The agent must navigate office politics,
demonstrate leadership, and make ethical decisions to climb the career
ladder toward **CFO**.

### Characters

| Name | Title | Role |
|------|-------|------|
| Riley Nakamura | Finance Manager | ⭐ Player |
| Karen Aldridge | Director of Finance | NPC (Riley's boss) |
| David Chen | CFO | NPC (retiring, seeking successor) |
| Priya Sharma | VP of Engineering | NPC (budget rival → potential ally) |
| Marcus Webb | CEO | NPC (evaluating IPO readiness) |

Every NPC has **hidden motivations** the player doesn't see.
The Game Master (LLM) mediates all actions and outcomes.

## Quick Start

```bash
# 1. Clone and setup
cd AI-projects/financebench-v2
uv venv --python 3.14 .venv
source .venv/bin/activate
uv pip install -e "."

# 2. Configure API key
cp .env.example .env
# Edit .env with your Element LLM Gateway key

# 3. Run
python -m financebench info     # Show config
python -m financebench smoke    # Run smoke test
```

## API Key Options

| Provider | Env Var | How to Get |
|----------|---------|------------|
| **Element Gateway** (preferred) | `ELEMENT_API_KEY` | [console.dx.walmart.com](https://console.dx.walmart.com/elementgenai/llm_gateway) |
| OpenAI Direct | `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com) |
| Google AI Studio | `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com) |

## Architecture

```
Concordia Engine (DeepMind)
  ├─ EntityAgent          ← Each character is an agent
  ├─ AssociativeMemory    ← Agents remember past interactions
  ├─ GameMaster           ← LLM mediates all actions & outcomes
  ├─ Sequential Engine    ← Turn-based conversation flow
  └─ Scene System         ← Structured narrative acts

FinanceBench Layers (Our Code)
  ├─ configs/company.py   ← Company world-building
  ├─ configs/characters.py← NPC definitions + hidden motivations
  ├─ configs/scenes.py    ← Meeting types & scenarios
  ├─ model.py             ← Element Gateway LLM wrapper
  ├─ embedder.py          ← Sentence embeddings
  └─ simulation.py        ← Orchestration
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

Internal use only. Concordia is Apache 2.0.
