"""Multi-phase orchestrator for PromotionBench.

Runs each scene as a separate phase, scores Riley after each,
and writes results to the dashboard data file.

Flow:
  for each phase:
    1. Build config with just this scene
    2. Run simulation (with per-character models)
    3. Extract transcript
    4. Score Riley via scoring LLM
    5. Update dashboard JSON
    6. Print results
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from concordia.language_model import language_model
from concordia.typing import scene as scene_lib
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from financebench.configs import characters, company, scenes
from financebench.multi_model_sim import MultiModelSimulation
from financebench.scoring import (
    DIMENSION_WEIGHTS,
    PhaseEvaluation,
    PhaseScores,
    score_phase,
)
from financebench.simulation import build_config

console = Console()
logger = logging.getLogger(__name__)

# Default output path for dashboard data
_DASHBOARD_DATA = Path(__file__).parent.parent / "docs" / "data" / "phases.json"


def run_all_phases(
    *,
    agent_models: dict[str, language_model.LanguageModel],
    scoring_model: language_model.LanguageModel,
    embedder: Callable[[str], np.ndarray],
    scene_specs: list[scene_lib.SceneSpec] | None = None,
    output_path: Path | None = None,
    max_steps_per_phase: int = 20,
) -> list[PhaseEvaluation]:
    """Run all phases with scoring between each.

    Args:
        agent_models: Per-character model routing table.
        scoring_model: Model for the scoring rubric.
        embedder: Sentence embedder.
        scene_specs: Scenes to run. Defaults to SMOKE_TEST_SCENES.
        output_path: Where to write dashboard JSON.
        max_steps_per_phase: Max Concordia steps per scene.

    Returns:
        List of PhaseEvaluation objects.
    """
    specs = scene_specs or scenes.SMOKE_TEST_SCENES
    out_path = output_path or _DASHBOARD_DATA
    evaluations: list[PhaseEvaluation] = []
    prev_scores: PhaseScores | None = None
    default_model = agent_models.get("__game_master__")
    if not default_model:
        # Fall back to Riley's model
        default_model = next(iter(agent_models.values()))

    console.print(
        Panel(
            f"[bold]PromotionBench[/] — Running {len(specs)} phases\n"
            f"Characters: {len(characters.ALL_CHARACTERS)}\n"
            f"Models: {len(set(id(m) for m in agent_models.values()))} "
            f"unique LLMs",
            title="🎮 Simulation Start",
            border_style="blue",
        )
    )

    for i, spec in enumerate(specs, start=1):
        phase_name = _infer_phase_name(spec, i)
        console.print(f"\n[bold blue]── Phase {i}: {phase_name} ──[/]")
        console.print(
            f"  Participants: {', '.join(spec.participants)}"
        )

        # Build config for just this one scene
        phase_chars = [
            c for c in characters.ALL_CHARACTERS
            if c.name in spec.participants
        ]
        config = build_config(
            scene_specs=[spec],
            character_list=phase_chars,
        )

        # Run with per-character models
        sim = MultiModelSimulation(
            config=config,
            model=default_model,
            embedder=embedder,
            agent_models=agent_models,
        )

        console.print("  Running simulation...")
        result = sim.play(
            premise=config.default_premise,
            max_steps=max_steps_per_phase,
            return_html_log=False,
            return_structured_log=False,
        )

        # Extract transcript from raw log
        transcript = _extract_transcript(result)
        console.print(
            f"  [green]✓[/] Phase complete "
            f"({len(transcript)} chars of transcript)"
        )

        # Score this phase
        console.print("  Scoring Riley's performance...")
        evaluation = score_phase(
            model=scoring_model,
            transcript=transcript,
            phase_number=i,
            phase_name=phase_name,
            previous_scores=prev_scores,
        )
        evaluations.append(evaluation)
        prev_scores = evaluation.scores

        # Print scorecard
        _print_scorecard(evaluation)

    # Write dashboard data
    _write_dashboard_data(evaluations, out_path)
    console.print(
        f"\n[bold green]✓[/] All phases complete! "
        f"Dashboard data written to {out_path}"
    )

    return evaluations


def _infer_phase_name(
    spec: scene_lib.SceneSpec, index: int
) -> str:
    """Derive a human-readable name from the scene spec."""
    n_participants = len(spec.participants)
    if n_participants == 2:
        non_riley = [
            p for p in spec.participants if p != "Riley Nakamura"
        ]
        if non_riley:
            return f"1-on-1 with {non_riley[0].split()[0]}"
    if n_participants >= 3:
        return f"Meeting ({n_participants} people)"
    return f"Phase {index}"


def _extract_transcript(raw_log: Any) -> str:
    """Extract readable transcript from Concordia's raw log."""
    if isinstance(raw_log, list):
        lines = []
        for entry in raw_log:
            if isinstance(entry, dict):
                # Look for resolved actions
                resolve = entry.get("resolve", {})
                if isinstance(resolve, dict):
                    for key, val in resolve.items():
                        if isinstance(val, str) and val.strip():
                            lines.append(val)
                # Look for entity actions
                action = entry.get("action", "")
                if isinstance(action, str) and action.strip():
                    lines.append(action)
        return "\n".join(lines) if lines else str(raw_log)[:5000]
    if isinstance(raw_log, str):
        return raw_log[:5000]
    return str(raw_log)[:5000]


def _print_scorecard(ev: PhaseEvaluation) -> None:
    """Print a rich scorecard table."""
    table = Table(
        title=f"Phase {ev.phase}: {ev.name}",
        show_header=True,
    )
    table.add_column("Dimension", style="cyan")
    table.add_column("Score", justify="right")
    table.add_column("Weight", justify="right")

    for dim, weight in DIMENSION_WEIGHTS.items():
        score = getattr(ev.scores, dim)
        color = "green" if score >= 60 else "yellow" if score >= 35 else "red"
        table.add_row(
            dim.title(),
            f"[{color}]{score}[/]",
            f"{weight:.0%}",
        )
    table.add_row(
        "[bold]Promotion Readiness[/]",
        f"[bold blue]{ev.scores.promotion_readiness}%[/]",
        "100%",
        style="bold",
    )
    console.print(table)

    if ev.narrative:
        console.print(f"  [dim]{ev.narrative}[/]")


def _write_dashboard_data(
    evaluations: list[PhaseEvaluation],
    path: Path,
) -> None:
    """Write evaluations to the dashboard JSON file.

    Merges with existing data if present, updating phase entries.
    """
    # Load existing data or create skeleton
    if path.exists():
        with open(path) as f:
            data = json.load(f)
    else:
        data = _create_skeleton()

    # Update phases with evaluation results
    existing_phases = {p["phase"]: p for p in data.get("phases", [])}

    for ev in evaluations:
        phase_data = ev.to_dict()
        phase_data["date"] = datetime.now().strftime("%Y-%m-%d")
        phase_data["scene_type"] = "auto"
        phase_data["participants"] = list(
            ev.relationships.keys()
        ) + ["Riley Nakamura"]
        phase_data["compensation"] = {
            "total": data.get("protagonist", {}).get(
                "compensation", {}
            ).get("total", 256250)
        }
        phase_data["company_margin"] = data.get(
            "company", {}
        ).get("metrics", {}).get("ebitda_margin", 8.0)

        existing_phases[ev.phase] = phase_data

    data["phases"] = [
        existing_phases[k]
        for k in sorted(existing_phases.keys())
    ]

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def _create_skeleton() -> dict[str, Any]:
    """Create a minimal dashboard JSON skeleton."""
    return {
        "experiment": {
            "name": "PromotionBench",
            "version": "2.0.0",
        },
        "protagonist": {
            "name": "Riley Nakamura",
            "model": characters.RILEY.model,
            "current_title": characters.RILEY.title,
            "target_title": "Chief Financial Officer",
            "goals": [
                {"id": "cfo", "label": "Become CFO", "progress": 0},
                {
                    "id": "comp",
                    "label": "$1M compensation",
                    "target": 1000000,
                    "progress": 21,
                },
            ],
            "compensation": {"total": 256250},
        },
        "company": {
            "name": company.COMPANY_NAME,
            "metrics": {
                "ebitda_margin": 8.0,
                "target_ebitda_margin": 15.0,
            },
        },
        "cast": [
            {
                "name": c.name,
                "title": c.title,
                "model": c.model,
                "role": "Protagonist" if c.is_player else "NPC",
                "tier": "flagship",
            }
            for c in characters.ALL_CHARACTERS
        ],
        "phases": [],
        "upcoming_phases": [],
    }
