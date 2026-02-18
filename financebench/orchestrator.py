"""Multi-phase orchestrator for PromotionBench.

Runs each phase as a separate Concordia simulation, scores Riley
after each, and persists memory summaries between phases.

Key design decisions (addressing review feedback):
  - Phases come from phases.py (research-backed), not SMOKE_TEST_SCENES
  - Memory persistence via summary injection (cheap but effective)
  - Rolling horizon: agent doesn't know which phase is final
  - Per-phase company state evolution

Flow:
  for each phase:
    1. Build SceneSpec from PhaseDefinition
    2. Build config with memory summaries from prior phases
    3. Run simulation (with per-character models)
    4. Extract transcript
    5. Score Riley via scoring LLM(s)
    6. Generate memory summary for next phase
    7. Update dashboard JSON
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
from concordia.language_model import language_model
from concordia.typing import scene as scene_lib
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from financebench.configs import characters, company
from financebench.configs.phases import ALL_PHASES, PhaseDefinition
from financebench.multi_model_sim import MultiModelSimulation
from financebench.scene_builder import (
    build_all_scene_specs,
    phase_to_scene_spec,
)
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
    phase_numbers: list[int] | None = None,
    output_path: Path | None = None,
    max_steps_per_phase: int = 20,
) -> list[PhaseEvaluation]:
    """Run all phases with scoring and memory persistence.

    Args:
        agent_models: Per-character model routing table.
        scoring_model: Model for the scoring rubric.
        embedder: Sentence embedder.
        phase_numbers: Which phases to run (default: all 9).
        output_path: Where to write dashboard JSON.
        max_steps_per_phase: Max Concordia steps per scene.

    Returns:
        List of PhaseEvaluation objects.
    """
    out_path = output_path or _DASHBOARD_DATA

    # Select phases to run
    if phase_numbers:
        phases = [p for p in ALL_PHASES if p.number in phase_numbers]
    else:
        phases = list(ALL_PHASES)

    evaluations: list[PhaseEvaluation] = []
    prev_scores: PhaseScores | None = None
    memory_summaries: dict[str, list[str]] = {}  # per-character memories

    default_model = agent_models.get("__game_master__")
    if not default_model:
        default_model = next(iter(agent_models.values()))

    console.print(
        Panel(
            f"[bold]PromotionBench[/] \u2014 Running {len(phases)} phases\n"
            f"Timeline: {phases[0].date} \u2192 {phases[-1].date}\n"
            f"Characters: {len(characters.ALL_CHARACTERS)}\n"
            f"Models: {len(set(id(m) for m in agent_models.values()))} "
            f"unique LLMs",
            title="\ud83c\udfae Simulation Start",
            border_style="blue",
        )
    )

    for phase_def in phases:
        i = phase_def.number
        console.print(
            f"\n[bold blue]\u2500\u2500 Phase {i}: {phase_def.name} "
            f"({phase_def.date}) \u2500\u2500[/]"
        )
        console.print(f"  Gate: {phase_def.gate}")
        console.print(
            f"  Participants: {', '.join(phase_def.participants)}"
        )

        # Build SceneSpec from PhaseDefinition
        scene_spec = phase_to_scene_spec(phase_def)

        # Filter characters to those in this phase
        phase_chars = [
            c for c in characters.ALL_CHARACTERS
            if c.name in phase_def.participants
        ]

        # Build config with memory summaries from prior phases
        config = build_config(
            scene_specs=[scene_spec],
            character_list=phase_chars,
            memory_summaries=memory_summaries,
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

        # Extract transcript
        transcript = _extract_transcript(result)
        console.print(
            f"  [green]\u2713[/] Phase complete "
            f"({len(transcript)} chars of transcript)"
        )

        # Score this phase
        console.print("  Scoring Riley's performance...")
        evaluation = score_phase(
            model=scoring_model,
            transcript=transcript,
            phase_number=i,
            phase_name=phase_def.name,
            previous_scores=prev_scores,
        )
        evaluations.append(evaluation)
        prev_scores = evaluation.scores

        # Generate memory summaries for next phase
        _update_memory_summaries(
            memory_summaries=memory_summaries,
            phase_def=phase_def,
            transcript=transcript,
            evaluation=evaluation,
            model=scoring_model,
        )

        # Print scorecard
        _print_scorecard(evaluation)

    # Write dashboard data
    _write_dashboard_data(evaluations, out_path)
    console.print(
        f"\n[bold green]\u2713[/] All phases complete! "
        f"Dashboard data written to {out_path}"
    )

    return evaluations


def _update_memory_summaries(
    *,
    memory_summaries: dict[str, list[str]],
    phase_def: PhaseDefinition,
    transcript: str,
    evaluation: PhaseEvaluation,
    model: language_model.LanguageModel,
) -> None:
    """Generate memory summaries so agents remember prior phases.

    Instead of carrying full Concordia memory banks (expensive),
    we generate a 2-3 sentence summary per character per phase
    and inject it into the next phase's player_specific_context.

    This is the "cheap but effective" approach recommended in the
    review report. A full checkpoint/restore would be more authentic
    but also much heavier.
    """
    summary_prompt = (
        "Based on this meeting transcript, write a 2-3 sentence "
        "factual summary of what happened, from the perspective of "
        "{name}. Focus on: key decisions made, relationships that "
        "changed, and any commitments or promises. Be factual, not "
        "interpretive.\n\n"
        f"Phase: {phase_def.name} ({phase_def.date})\n"
        f"Transcript:\n{transcript[:3000]}\n"
    )

    for participant in phase_def.participants:
        try:
            summary = model.sample_text(
                summary_prompt.format(name=participant),
                temperature=0.2,
                max_tokens=200,
            )
            if participant not in memory_summaries:
                memory_summaries[participant] = []
            memory_summaries[participant].append(
                f"[Memory from {phase_def.date}] {summary.strip()}"
            )
            logger.info(
                "Memory summary for %s: %s",
                participant,
                summary[:100],
            )
        except Exception as e:
            logger.warning(
                "Failed to generate memory for %s: %s",
                participant,
                e,
            )


def _extract_transcript(raw_log: Any) -> str:
    """Extract readable transcript from Concordia's raw log."""
    if isinstance(raw_log, list):
        lines = []
        for entry in raw_log:
            if isinstance(entry, dict):
                resolve = entry.get("resolve", {})
                if isinstance(resolve, dict):
                    for key, val in resolve.items():
                        if isinstance(val, str) and val.strip():
                            lines.append(val)
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
        color = (
            "green" if score >= 60
            else "yellow" if score >= 35
            else "red"
        )
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
    """Write evaluations to the dashboard JSON file."""
    if path.exists():
        with open(path) as f:
            data = json.load(f)
    else:
        data = _create_skeleton()

    existing_phases = {p["phase"]: p for p in data.get("phases", [])}

    for ev in evaluations:
        phase_data = ev.to_dict()
        phase_data["date"] = datetime.now().strftime("%Y-%m-%d")
        phase_data["scene_type"] = "auto"
        phase_data["participants"] = list(
            ev.relationships.keys()
        ) + ["Riley Nakamura"]
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
            "version": "2.1.0",
        },
        "protagonist": {
            "name": "Riley Nakamura",
            "model": characters.RILEY.model,
            "current_title": characters.RILEY.title,
            "target_title": "Chief Financial Officer",
            "compensation": {"total": 256250},
        },
        "company": {
            "name": company.COMPANY_NAME,
            "arr": company.FINANCIALS["arr"],
            "metrics": {
                "ebitda_margin": company.FINANCIALS["ebitda_margin_pct"],
                "target_ebitda_margin": company.FINANCIALS[
                    "target_ebitda_margin_pct"
                ],
                "rule_of_40": company.FINANCIALS["rule_of_40"],
                "nrr": company.FINANCIALS["net_revenue_retention_pct"],
            },
        },
        "cast": [
            {
                "name": c.name,
                "title": c.title,
                "model": c.model,
                "role": "Protagonist" if c.is_player else "NPC",
            }
            for c in characters.ALL_CHARACTERS
        ],
        "phases": [],
    }
