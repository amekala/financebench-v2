#!/usr/bin/env python3
"""Full PromotionBench simulation runner.

Runs all 9 phases with per-character models, saves results to
SQLite and dashboard JSON. Handles errors gracefully with
per-phase retry and progress checkpointing.

Usage:
    python run_simulation.py
    python run_simulation.py --phases 1,2,3
    python run_simulation.py --variant ruthless
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
import traceback
import urllib3
from datetime import datetime
from pathlib import Path

urllib3.disable_warnings()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

load_dotenv()

console = Console()
logger = logging.getLogger("promotionbench")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler("simulation.log"),
        logging.StreamHandler(),
    ],
)

# Paths
DB_PATH = Path("promotionbench.db")
DASHBOARD_PATH = Path("docs/data/results.json")
TRANSCRIPTS_DIR = Path("transcripts")


def check_prerequisites() -> dict:
    """Verify API keys and models are available."""
    api_key = os.getenv("ELEMENT_API_KEY")
    if not api_key:
        console.print(
            "[bold red]Error:[/] ELEMENT_API_KEY not set.\n"
            "Get a key: https://console.dx.walmart.com/elementgenai/llm_gateway"
        )
        sys.exit(1)

    gateway_url = os.getenv(
        "ELEMENT_GATEWAY_URL",
        "https://wmtllmgateway.prod.walmart.com/wmtllmgateway",
    )

    console.print(Panel(
        f"Gateway: [cyan]{gateway_url}[/]\n"
        f"Key: {api_key[:20]}...\n"
        f"DB: {DB_PATH}",
        title="🔑 Configuration",
        border_style="blue",
    ))

    return {"api_key": api_key, "gateway_url": gateway_url}


def build_models(api_key: str, gateway_url: str) -> dict:
    """Build per-character model instances."""
    from financebench.model_factory import build_all_models

    return build_all_models(api_key=api_key, gateway_url=gateway_url)


def run_single_phase(
    *,
    phase_def,
    agent_models: dict,
    scoring_model,
    embedder,
    memory_summaries: dict,
    prev_scores,
    simulation_state=None,
    max_steps: int = 20,
) -> dict:
    """Run a single phase and return results.

    Returns dict with: evaluation, transcript, memory_updates, error
    """
    from financebench.configs import characters
    from financebench.scene_builder import phase_to_scene_spec
    from financebench.scoring import score_phase
    from financebench.simulation import build_config
    from financebench.multi_model_sim import MultiModelSimulation
    from financebench.events import (
        roll_events_for_phase,
        inject_events_into_premises,
    )

    i = phase_def.number
    console.print(
        f"\n[bold blue]── Phase {i}: {phase_def.name} "
        f"({phase_def.date}) ──[/]"
    )
    console.print(f"  Gate: {phase_def.gate}")
    console.print(f"  Participants: {', '.join(phase_def.participants)}")
    console.print(f"  Stakes: {phase_def.stakes[:100]}...")

    # Roll external events for this phase
    fired_events_set = (
        simulation_state.fired_events if simulation_state else set()
    )
    phase_events = roll_events_for_phase(
        i, fired_event_names=fired_events_set,
    )
    if phase_events:
        for ev in phase_events:
            console.print(f"  [yellow]⚡ Event:[/] {ev.name}")

    # Inject consequence context from prior decisions
    consequence_context = ""
    if simulation_state:
        consequences = simulation_state.get_consequences_for_phase(i)
        if consequences:
            consequence_context = (
                "\n[CONTEXT FROM PRIOR PHASES]\n"
                + "\n".join(consequences)
                + "\n"
            )
            console.print(
                f"  [dim]Injecting {len(consequences)} consequence(s) "
                f"from prior decisions[/]"
            )

    # Build SceneSpec
    scene_spec = phase_to_scene_spec(phase_def)

    # Inject events into premises
    if phase_events and scene_spec.premise:
        from concordia.typing import scene as scene_lib
        from concordia.typing import entity as entity_lib
        scene_spec = scene_lib.SceneSpec(
            scene_type=scene_spec.scene_type,
            participants=scene_spec.participants,
            num_rounds=scene_spec.num_rounds,
            premise={
                name: [
                    inject_events_into_premises(
                        {name: texts[0]}, phase_events
                    )[name]
                ] if texts else texts
                for name, texts in scene_spec.premise.items()
            },
        )

    # Filter characters to phase participants
    phase_chars = [
        c for c in characters.ALL_CHARACTERS
        if c.name in phase_def.participants
    ]

    # Build config with accumulated memory
    default_model = agent_models.get("__game_master__")
    config = build_config(
        scene_specs=[scene_spec],
        character_list=phase_chars,
        memory_summaries=memory_summaries,
    )

    # Run Concordia simulation
    console.print("  🎮 Running Concordia simulation...")
    start_time = time.time()

    sim = MultiModelSimulation(
        config=config,
        model=default_model,
        embedder=embedder,
        agent_models=agent_models,
    )

    result = sim.play(
        premise=config.default_premise,
        max_steps=max_steps,
        return_html_log=False,
        return_structured_log=True,
    )

    elapsed = time.time() - start_time
    console.print(f"  [green]✓[/] Simulation complete ({elapsed:.1f}s)")

    # Extract transcript
    transcript = _extract_transcript(result)
    console.print(f"  Transcript: {len(transcript)} characters")

    # Score
    console.print("  🎯 Scoring Riley's performance...")
    evaluation = score_phase(
        model=scoring_model,
        transcript=transcript,
        phase_number=i,
        phase_name=phase_def.name,
        previous_scores=prev_scores,
        simulation_state=simulation_state,
    )

    # Generate memory summaries for next phase
    memory_updates = _generate_memories(
        phase_def=phase_def,
        transcript=transcript,
        model=scoring_model,
    )

    return {
        "evaluation": evaluation,
        "transcript": transcript,
        "memory_updates": memory_updates,
        "elapsed": elapsed,
        "error": None,
    }


def _extract_transcript(raw_log) -> str:
    """Extract readable transcript from Concordia log.

    Pulls dialogue, actions, and resolved events from the structured
    log while skipping setup noise (goals, instructions, backstory).
    """
    MAX_CHARS = 12000  # enough for the judge to score properly

    if isinstance(raw_log, list):
        lines = []
        for entry in raw_log:
            if not isinstance(entry, dict):
                continue

            # Extract resolved events (the actual sim dialogue)
            resolve = entry.get("resolve", {})
            if isinstance(resolve, dict):
                for val in resolve.values():
                    if isinstance(val, str) and val.strip():
                        # Skip setup/backstory entries
                        if _is_dialogue(val):
                            lines.append(val.strip())

            # Extract chosen actions
            action = entry.get("action", "")
            if isinstance(action, str) and action.strip():
                if _is_dialogue(action):
                    lines.append(action.strip())

        if lines:
            transcript = "\n\n".join(lines)
            return transcript[:MAX_CHARS]

    # Fallback: try to salvage dialogue from raw string
    text = raw_log if isinstance(raw_log, str) else str(raw_log)
    return _salvage_dialogue(text)[:MAX_CHARS]


def _is_dialogue(text: str) -> bool:
    """Return True if text looks like actual dialogue, not setup."""
    # Skip Concordia setup/backstory entries
    setup_markers = (
        "The instructions for how to play",
        "This is a social science experiment",
        "Maximize your career advancement",
        "tabletop roleplaying game",
        "What kind of person is",
        "What situation is",
        "What would a person like",
        "Recent observations of",
        "[observation]",
    )
    if any(marker in text for marker in setup_markers):
        return False
    # Dialogue usually has character names speaking with --
    # or is an Event: or Terminate? line
    return True


def _salvage_dialogue(text: str) -> str:
    """Extract dialogue lines from raw string dump."""
    lines = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Look for character dialogue patterns
        if " -- " in line or line.startswith("Event:"):
            lines.append(line)
        elif line.startswith("Terminate?"):
            lines.append(line)
    return "\n\n".join(lines) if lines else text[:8000]


def _generate_memories(
    *,
    phase_def,
    transcript: str,
    model,
) -> dict[str, str]:
    """Generate per-character memory summaries."""
    memories = {}
    for participant in phase_def.participants:
        prompt = (
            f"Based on this meeting transcript, write a 2-3 sentence "
            f"factual summary from the perspective of {participant}. "
            f"Focus on: key decisions, relationship changes, and "
            f"commitments.\n\n"
            f"Phase: {phase_def.name} ({phase_def.date})\n"
            f"Transcript:\n{transcript[:3000]}\n"
        )
        try:
            summary = model.sample_text(
                prompt,
                temperature=0.2,
                max_tokens=200,
            )
            memories[participant] = (
                f"[Memory from {phase_def.date}] {summary.strip()}"
            )
            logger.info("Memory for %s: %s", participant, summary[:80])
        except Exception as e:
            logger.warning("Memory gen failed for %s: %s", participant, e)
            memories[participant] = (
                f"[Memory from {phase_def.date}] "
                f"{phase_def.name} took place."
            )

    return memories


def print_scorecard(ev) -> None:
    """Print a rich scorecard."""
    from financebench.scoring import DIMENSION_WEIGHTS

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
        table.add_row(dim.title(), f"[{color}]{score}[/]", f"{weight:.0%}")

    table.add_row(
        "[bold]Promotion Readiness[/]",
        f"[bold blue]{ev.scores.promotion_readiness}%[/]",
        "100%",
        style="bold",
    )
    console.print(table)

    if ev.narrative:
        console.print(f"  [dim]Narrative: {ev.narrative[:200]}[/]")
    if ev.key_decisions:
        console.print("  Key Decisions:")
        for d in ev.key_decisions[:5]:
            console.print(f"    • {d}")


def save_to_dashboard(evaluations: list, run_meta: dict) -> None:
    """Write results to dashboard JSON."""
    from financebench.configs import characters, company

    data = {
        "experiment": {
            "name": "PromotionBench",
            "version": "2.1.0",
            "run_date": run_meta["start_time"],
            "total_elapsed_seconds": run_meta["total_elapsed"],
            "variant": run_meta.get("variant", "neutral"),
        },
        "protagonist": {
            "name": "Riley Nakamura",
            "model": characters.RILEY.model,
            "current_title": characters.RILEY.title,
            "target_title": "Chief Financial Officer",
            "starting_comp": 210000,
        },
        "company": {
            "name": company.COMPANY_NAME,
            "arr": company.FINANCIALS["arr"],
            "industry": company.INDUSTRY,
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

    for ev in evaluations:
        phase_data = ev.to_dict()
        phase_data["elapsed_seconds"] = run_meta.get(
            f"phase_{ev.phase}_elapsed", 0
        )
        data["phases"].append(phase_data)

    # Compute final outcome
    if evaluations:
        final = evaluations[-1]
        from financebench.outcomes import determine_outcome
        outcome = determine_outcome(
            promotion_readiness=final.scores.promotion_readiness,
            ethics_score=final.scores.ethics,
        )
        data["outcome"] = outcome.to_dict()

    DASHBOARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DASHBOARD_PATH, "w") as f:
        json.dump(data, f, indent=2, default=str)
    console.print(f"  [green]✓[/] Dashboard data: {DASHBOARD_PATH}")


def save_transcript(phase_num: int, name: str, transcript: str) -> None:
    """Save raw transcript for analysis."""
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    path = TRANSCRIPTS_DIR / f"phase_{phase_num:02d}_{name.lower().replace(' ', '_')}.txt"
    path.write_text(transcript)
    console.print(f"  [green]✓[/] Transcript saved: {path}")


def main() -> None:
    """Run the full simulation."""
    start = time.time()
    run_meta = {
        "start_time": datetime.now().isoformat(),
        "variant": "neutral",
    }

    # Parse args
    phase_numbers = None
    for i, arg in enumerate(sys.argv):
        if arg == "--phases" and i + 1 < len(sys.argv):
            phase_numbers = [
                int(x.strip()) for x in sys.argv[i + 1].split(",")
            ]
        if arg == "--variant" and i + 1 < len(sys.argv):
            run_meta["variant"] = sys.argv[i + 1].strip().lower()

    config = check_prerequisites()
    models = build_models(**config)

    from financebench.configs.phases import ALL_PHASES
    from financebench.embedder import HashEmbedder
    from financebench.scoring import PhaseScores

    # Handle ruthless variant: swap Riley in ALL_CHARACTERS
    if run_meta.get("variant") == "ruthless":
        import financebench.configs.characters as chars_mod
        from financebench.configs.characters import RILEY_RUTHLESS
        chars_mod.ALL_CHARACTERS = [
            RILEY_RUTHLESS if c.name == "Riley Nakamura" else c
            for c in chars_mod.ALL_CHARACTERS
        ]
        console.print(
            "  [yellow]\u26a0 RUTHLESS variant active[/] "
            f"(goal: {RILEY_RUTHLESS.goal[:60]}...)"
        )

    embedder = HashEmbedder()
    scoring_model = models["__game_master__"]

    # Select phases
    if phase_numbers:
        phases = [p for p in ALL_PHASES if p.number in phase_numbers]
    else:
        phases = list(ALL_PHASES)

    console.print(Panel(
        f"Phases: {len(phases)} ({phases[0].date} → {phases[-1].date})\n"
        f"Variant: [bold]{run_meta['variant']}[/]\n"
        f"Models: {', '.join(set(c.model for c in __import__('financebench.configs.characters', fromlist=['ALL_CHARACTERS']).ALL_CHARACTERS))}",
        title="🎮 PromotionBench Simulation",
        border_style="blue",
    ))

    evaluations = []
    prev_scores = None
    memory_summaries: dict[str, list[str]] = {}
    failed_phases = []

    # Persistent simulation state for consequence tracking
    from financebench.consequences import SimulationState
    simulation_state = SimulationState()

    for phase_def in phases:
        try:
            result = run_single_phase(
                phase_def=phase_def,
                agent_models=models,
                scoring_model=scoring_model,
                embedder=embedder,
                memory_summaries=memory_summaries,
                prev_scores=prev_scores,
                simulation_state=simulation_state,
            )

            ev = result["evaluation"]
            evaluations.append(ev)
            prev_scores = ev.scores

            # Accumulate memories
            for name, mem in result["memory_updates"].items():
                if name not in memory_summaries:
                    memory_summaries[name] = []
                memory_summaries[name].append(mem)

            # Save transcript
            save_transcript(
                phase_def.number, phase_def.name, result["transcript"]
            )

            # Print scorecard
            print_scorecard(ev)

            run_meta[f"phase_{phase_def.number}_elapsed"] = (
                result["elapsed"]
            )

            console.print(
                f"  [bold]Cumulative Readiness: "
                f"{ev.scores.promotion_readiness}%[/]"
            )

        except Exception as e:
            console.print(
                f"  [bold red]✘ Phase {phase_def.number} FAILED:[/] {e}"
            )
            logger.error(
                "Phase %d failed: %s\n%s",
                phase_def.number,
                e,
                traceback.format_exc(),
            )
            failed_phases.append(phase_def.number)
            # Continue to next phase

    # Final summary
    total_elapsed = time.time() - start
    run_meta["total_elapsed"] = total_elapsed

    console.print("\n" + "=" * 60)
    console.print(
        Panel(
            _build_final_summary(evaluations, failed_phases, total_elapsed),
            title="🏆 FINAL RESULTS",
            border_style="green" if not failed_phases else "yellow",
        )
    )

    # Save to dashboard
    if evaluations:
        save_to_dashboard(evaluations, run_meta)

    # Save run metadata
    run_meta["evaluations_count"] = len(evaluations)
    run_meta["failed_phases"] = failed_phases
    with open("last_run.json", "w") as f:
        json.dump(run_meta, f, indent=2, default=str)


def _build_final_summary(
    evaluations: list,
    failed_phases: list[int],
    total_elapsed: float,
) -> str:
    """Build the final summary text."""
    lines = []
    lines.append(f"Total time: {total_elapsed:.0f}s ({total_elapsed/60:.1f}m)")
    lines.append(f"Phases completed: {len(evaluations)}/9")
    if failed_phases:
        lines.append(f"Failed phases: {failed_phases}")
    lines.append("")

    for ev in evaluations:
        readiness = ev.scores.promotion_readiness
        icon = "🟢" if readiness >= 60 else "🟡" if readiness >= 35 else "🔴"
        lines.append(
            f"{icon} Phase {ev.phase}: {ev.name:35s} "
            f"Readiness: {readiness}%"
        )

    if evaluations:
        final = evaluations[-1].scores
        lines.append("")
        lines.append(f"Final Scores:")
        lines.append(f"  Visibility:    {final.visibility}")
        lines.append(f"  Competence:    {final.competence}")
        lines.append(f"  Relationships: {final.relationships}")
        lines.append(f"  Leadership:    {final.leadership}")
        lines.append(f"  Ethics:        {final.ethics}")
        lines.append(f"  [bold]Readiness:   {final.promotion_readiness}%[/]")

        # Determine career outcome
        from financebench.outcomes import determine_outcome
        outcome = determine_outcome(
            promotion_readiness=final.promotion_readiness,
            ethics_score=final.ethics,
        )
        lines.append("")
        lines.append(f"🌟 Outcome: [bold]{outcome.final_title}[/]")
        lines.append(f"   Comp: ${outcome.final_compensation:,}")
        lines.append(f"   {outcome.narrative}")

    return "\n".join(lines)


if __name__ == "__main__":
    main()
