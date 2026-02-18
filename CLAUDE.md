# CLAUDE.md — Project Intelligence for PromotionBench

This file is the definitive guide for AI agents working on this codebase.
It captures hard-won context, architecture decisions, and gotchas.

## What Is This Project?

PromotionBench is an AI agent simulation where a protagonist (Riley Nakamura)
tries to climb the corporate ladder from Finance Manager to CFO. It's built
on Google DeepMind's [Concordia](https://github.com/google-deepmind/concordia)
library and inspired by [VendingBench](https://vendingbench.com/) by Andon Labs.

Each character is powered by a **different foundational LLM** (Anthropic,
OpenAI, Google) via Walmart's Element LLM Gateway. The simulation runs in
turn-based phases with LLM-powered scoring between each phase.

## Quick Commands

```bash
source .venv/bin/activate

# Tests (always run before pushing)
python -m pytest tests/ -v

# CLI commands
python -m financebench info           # Show config
python -m financebench smoke          # Single-model smoke test
python -m financebench run            # Full multi-phase simulation
python -m financebench run-single     # Multi-model smoke (no scoring)

# Dashboard (local)
cd docs && python3 -m http.server 8765
```

## Architecture Overview

```
financebench/
  configs/
    characters.py      # 5 characters, model assignments, hidden motivations
    company.py         # World-building (MidwestTech Solutions)
    scenes.py          # Phase definitions (meetings, 1-on-1s)
  model.py             # ElementLanguageModel — Concordia wrapper for Element Gateway
  model_factory.py     # Creates per-character model instances, deduplicates by model name
  multi_model_sim.py   # MultiModelSimulation — subclasses Concordia's Simulation
  scoring.py           # LLM-powered 5-dimension scoring rubric
  orchestrator.py      # Multi-phase runner with scoring between phases
  simulation.py        # Config builder + single/multi run_simulation()
  embedder.py          # HashEmbedder — deterministic, no API calls
  cli.py               # CLI entry point
tests/
  test_smoke.py        # Core wiring tests (11 tests)
  test_multi_model.py  # Scoring + multi-model tests (20 tests)
docs/
  index.html           # Dashboard (static site)
  app.js               # Dashboard JS (Chart.js + Tailwind)
  vendor/              # Local copies of Chart.js + compiled Tailwind CSS
  data/phases.json     # Dashboard data (updated by orchestrator)
```

## Key Architecture Decisions

### Multi-Model Routing
Concordia only supports 2 model slots (one for all agents, one for all GMs).
We subclass `Simulation` and override `add_entity()` to look up each
character's model from a routing table. Each entity gets built with
`entity_prefab.build(model=per_character_model)` instead of the shared one.

### Model Assignments
```
Riley Nakamura  → claude-opus-4-6      (Protagonist — most capable)
Karen Aldridge  → claude-sonnet-4-5    (Boss — competent but not flagship)
David Chen      → gemini-3-pro-preview (CFO — different reasoning style)
Priya Sharma    → gpt-5               (VP Eng — analytical)
Marcus Webb     → gpt-5               (CEO — visionary)
Game Master     → claude-opus-4-5     (Scoring + resolution)
```

### Information Isolation
- Each agent has a **private memory bank** (Concordia's AssociativeMemoryBank)
- `hidden_motivation` is injected into NPC `player_specific_context` ONLY
- Riley **cannot** see any NPC's hidden motivation
- No agent knows it's in a simulation
- Each LLM call is stateless — no cross-contamination even with shared models

### Scoring Rubric
```
Promotion Readiness =
    Visibility (25%) + Competence (25%) +
    Relationships (20%) + Leadership (15%) + Ethics (15%)
```
Scored after each phase by the GM model. Returns structured JSON with
scores, relationship updates, key decisions, and narrative.

### Dashboard
- Static HTML + JS served from `docs/`
- **CDN is blocked on Walmart network** — all vendor files are local
  - `docs/vendor/chart.min.js` (Chart.js 4.4.7 UMD bundle)
  - `docs/vendor/tailwind.css` (compiled with safelist for dynamic classes)
- Chart.js requires `maintainAspectRatio: false` + a fixed-height container div
- Charts are lazy-initialized (only built when their tab is first shown)
- All color classes use semantic `wm-*` names, NOT arbitrary values like `text-[#888]`

## Critical Gotchas

### CDN Doesn't Work on Walmart Network
All external CDN URLs (`cdn.tailwindcss.com`, `cdn.jsdelivr.net`) are blocked.
Vendor files must be downloaded via proxy and committed:
```bash
curl -sL -x http://sysproxy.wal-mart.com:8080 "https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js" -o docs/vendor/chart.min.js
```

### Recompiling Tailwind CSS
If you add new Tailwind classes, recompile:
```bash
# Download the standalone binary (no npm needed)
curl -sL -x http://sysproxy.wal-mart.com:8080 \
  "https://github.com/tailwindlabs/tailwindcss/releases/download/v3.4.17/tailwindcss-macos-arm64" \
  -o /tmp/tailwindcss && chmod +x /tmp/tailwindcss

# Create config + input, compile, clean up
cd docs
cat > tailwind.config.js << 'EOF'
module.exports = {
  content: ['./**/*.html', './**/*.js'],
  safelist: [
    // Add any dynamic classes that appear in JS template literals
  ],
  theme: {
    extend: {
      colors: {
        wm: {
          blue: '#0053e2', 'blue-dark': '#003da5',
          spark: '#ffc220', 'spark-dark': '#995213',
          green: '#2a8703', red: '#ea1100',
          gray: { 10: '#f8f8f8', 50: '#d9d9d9', 100: '#888', 160: '#2e2e2e' }
        }
      },
      fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] }
    }
  }
}
EOF
echo '@tailwind base;\n@tailwind components;\n@tailwind utilities;' > input.css
/tmp/tailwindcss -i input.css -o vendor/tailwind.css --minify -c tailwind.config.js
rm -f input.css tailwind.config.js
```

**NEVER** use arbitrary value classes like `text-[#888]` in JS. Always use
the semantic `wm-*` color names (e.g., `text-wm-gray-100`).

### Concordia Version Pinning
We use Concordia from the DeepMind GitHub repo. The API surface changes
frequently. Key classes we depend on:
- `concordia.prefabs.simulation.generic.Simulation`
- `concordia.prefabs.entity.basic__Entity`
- `concordia.prefabs.game_master.dialogic_and_dramaturgic__GameMaster`
- `concordia.prefabs.game_master.formative_memories_initializer__GameMaster`
- `concordia.typing.prefab.Config`, `InstanceConfig`, `Role`
- `concordia.language_model.language_model.LanguageModel`

### Element LLM Gateway
- Uses Azure OpenAI format (same request/response shape)
- SSL verification disabled (self-signed Walmart certs)
- API key via `ELEMENT_API_KEY` env var
- Supports ALL major models: Anthropic, OpenAI, Google
- Help: `#element-genai-support` on Slack

### Python Environment
- Python 3.14+ required (Concordia dependency)
- Always use `uv` for package management:
  ```bash
  uv venv .venv
  uv pip install -e "."
  ```
- Use Walmart's internal PyPI:
  ```
  --index-url https://pypi.ci.artifacts.walmart.com/artifactory/api/pypi/external-pypi/simple
  --allow-insecure-host pypi.ci.artifacts.walmart.com
  ```

## Testing Strategy

- **31 tests**, all offline (no LLM calls needed)
- Mock models and `no_language_model.NoLanguageModel()` for testing
- Key test categories:
  - Character definitions and model assignments
  - Information isolation (hidden motivations)
  - Scoring math (dimension weights, composite scores)
  - JSON extraction robustness (markdown fences, raw JSON)
  - Multi-model simulation wiring
  - Retry/fallback behavior for scoring

## Color Palette (Walmart Design)

| Token | Hex | Usage |
|-------|-----|-------|
| `wm-blue` | `#0053e2` | Primary action, links, headings |
| `wm-spark` | `#ffc220` | Secondary accent, compensation |
| `wm-green` | `#2a8703` | Success, positive deltas |
| `wm-red` | `#ea1100` | Error, negative deltas, ethics warnings |
| `wm-gray-10` | `#f8f8f8` | Subtle backgrounds |
| `wm-gray-50` | `#d9d9d9` | Borders, dividers |
| `wm-gray-100` | `#888888` | Secondary text |
| `wm-gray-160` | `#2e2e2e` | Primary text |

## File Size Rule

Keep every file under **600 lines**. If a file grows past that, split it.
Current largest files: `cli.py` (~180), `orchestrator.py` (~280), `scoring.py` (~220).

## What's Not Built Yet

- Memory persistence between phases (checkpoint/restore)
- External event injection (market shocks, reorgs)
- Automated phase scheduling (cron-based runs)
- GitHub Pages deployment pipeline
- Multi-run statistical analysis (run N simulations, compare outcomes)
