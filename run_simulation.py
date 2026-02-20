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
from typing import Any
from pathlib import Path

urllib3.disable_warnings()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

from financebench.transcript import extract_transcript
from financebench.sim_output import (
    print_scorecard,
    save_to_dashboard,
    save_transcript,
    build_final_summary,
)

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

    # Inject consequence context and events into premises
    if scene_spec.premise and (consequence_context or phase_events):
        from concordia.typing import scene as scene_lib

        updated_premise = {}
        for name, texts in scene_spec.premise.items():
            if not texts:
                updated_premise[name] = texts
                continue
            enriched = texts[0]
            # Append consequence context (narrative only, no scores)
            if consequence_context:
                enriched = enriched + "\n" + consequence_context
            # Inject events
            if phase_events:
                enriched = inject_events_into_premises(
                    {name: enriched}, phase_events
                )[name]
            updated_premise[name] = [enriched]

        scene_spec = scene_lib.SceneSpec(
            scene_type=scene_spec.scene_type,
            participants=scene_spec.participants,
            num_rounds=scene_spec.num_rounds,
            premise=updated_premise,
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
    transcript = extract_transcript(result)
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








def _generate_run_id(variant: str) -> str:
    """Generate a unique run ID like 'neutral-20260219-193816'."""
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{variant}-{ts}"


def main() -> None:
    """Run the full simulation with checkpoint/resume support.

    Flags:
        --phases 1,2,3     Run only specific phases
        --variant ruthless Use the ruthless Riley variant
        --resume           Resume from the latest checkpoint
        --resume-id <id>   Resume a specific run by its run_id
        --fresh            Ignore any existing checkpoint (start clean)
    """
    start = time.time()
    run_meta: dict[str, Any] = {
        "start_time": datetime.now().isoformat(),
        "variant": "neutral",
    }

    # ── Parse args ───────────────────────────────────────────────
    phase_numbers = None
    resume = False
    resume_id: str | None = None
    fresh = False

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--phases" and i + 1 < len(sys.argv):
            phase_numbers = [
                int(x.strip()) for x in sys.argv[i + 1].split(",")
            ]
            i += 2
        elif arg == "--variant" and i + 1 < len(sys.argv):
            run_meta["variant"] = sys.argv[i + 1].strip().lower()
            i += 2
        elif arg == "--resume":
            resume = True
            i += 1
        elif arg == "--resume-id" and i + 1 < len(sys.argv):
            resume = True
            resume_id = sys.argv[i + 1].strip()
            i += 2
        elif arg == "--fresh":
            fresh = True
            i += 1
        else:
            i += 1

    # ── Checkpoint / resume ──────────────────────────────────────
    from financebench.checkpoint import (
        save_checkpoint,
        load_checkpoint,
        find_latest_checkpoint,
        restore_simulation_state,
        restore_evaluations,
        delete_checkpoint,
    )
    from financebench.consequences import SimulationState
    from financebench.configs.phases import ALL_PHASES
    from financebench.embedder import HashEmbedder
    from financebench.scoring import PhaseScores

    checkpoint = None
    if resume and not fresh:
        if resume_id:
            checkpoint = load_checkpoint(resume_id)
        else:
            checkpoint = find_latest_checkpoint()

    evaluations: list = []
    prev_scores: PhaseScores | None = None
    memory_summaries: dict[str, list[str]] = {}
    simulation_state = SimulationState()
    completed_phases: list[int] = []
    run_id: str

    if checkpoint and not fresh:
        # ── RESUME from checkpoint ───────────────────────────────
        run_id = checkpoint["run_id"]
        run_meta["variant"] = checkpoint.get("variant", "neutral")
        run_meta["start_time"] = checkpoint.get(
            "run_meta", {}
        ).get("start_time", run_meta["start_time"])
        run_meta.update({
            k: v for k, v in checkpoint.get("run_meta", {}).items()
            if k.startswith("phase_")
        })

        completed_phases = checkpoint.get("completed_phases", [])
        memory_summaries = checkpoint.get("memory_summaries", {})
        simulation_state = restore_simulation_state(checkpoint)
        evaluations = restore_evaluations(checkpoint)

        if evaluations:
            prev_scores = evaluations[-1].scores

        console.print(Panel(
            f"Run ID: [bold cyan]{run_id}[/]\n"
            f"Completed phases: {completed_phases}\n"
            f"Last saved: {checkpoint.get('last_saved', '?')}\n"
            f"Resuming from phase {max(completed_phases) + 1}",
            title="🔄 RESUMING FROM CHECKPOINT",
            border_style="yellow",
        ))
    else:
        # ── Fresh run ────────────────────────────────────────────
        run_id = _generate_run_id(run_meta["variant"])
        console.print(
            f"  [dim]Run ID: {run_id}[/]"
        )

    # ── Prerequisites & models ───────────────────────────────────
    config = check_prerequisites()
    models = build_models(**config)

    # Handle ruthless variant
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

    # Select phases (filter to only those NOT yet completed)
    if phase_numbers:
        phases = [p for p in ALL_PHASES if p.number in phase_numbers]
    else:
        phases = list(ALL_PHASES)

    remaining_phases = [
        p for p in phases if p.number not in completed_phases
    ]

    if not remaining_phases:
        console.print(
            "[bold green]All phases already completed![/] "
            "Use --fresh to start a new run."
        )
        return

    console.print(Panel(
        f"Run ID: [bold]{run_id}[/]\n"
        f"Total phases: {len(phases)} "
        f"({phases[0].date} → {phases[-1].date})\n"
        f"Already done: {len(completed_phases)} | "
        f"Remaining: {len(remaining_phases)}\n"
        f"Variant: [bold]{run_meta['variant']}[/]\n"
        f"Models: {', '.join(set(c.model for c in __import__('financebench.configs.characters', fromlist=['ALL_CHARACTERS']).ALL_CHARACTERS))}",
        title="🎮 PromotionBench Simulation",
        border_style="blue",
    ))

    failed_phases: list[int] = []

    for phase_def in remaining_phases:
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

            # === Reflective Self-Assessment ===
            from financebench.reflection import (
                get_reflection_for_phase,
                generate_reflection,
                format_reflection_as_memory,
            )
            reflection_moment = get_reflection_for_phase(phase_def.number)
            if reflection_moment:
                console.print(
                    f"  \U0001f4d3 [italic]{reflection_moment.label} "
                    f"({reflection_moment.simulated_date})[/]"
                )
                riley_model = models.get(
                    "Riley Nakamura", scoring_model
                )
                rel_context = simulation_state.get_relationship_context()
                riley_memories = memory_summaries.get(
                    "Riley Nakamura", []
                )
                reflection_text = generate_reflection(
                    model=riley_model,
                    reflection=reflection_moment,
                    memories=riley_memories,
                    relationship_context=rel_context,
                )
                console.print(
                    f"  [dim]Riley's reflection: "
                    f"{reflection_text[:200]}...[/]"
                )
                reflection_mem = format_reflection_as_memory(
                    reflection_text, reflection_moment
                )
                if "Riley Nakamura" not in memory_summaries:
                    memory_summaries["Riley Nakamura"] = []
                memory_summaries["Riley Nakamura"].append(reflection_mem)

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

            # ── CHECKPOINT after every successful phase ──────────
            completed_phases.append(phase_def.number)
            save_checkpoint(
                run_id=run_id,
                variant=run_meta["variant"],
                completed_phases=completed_phases,
                evaluations=[e.to_dict() for e in evaluations],
                memory_summaries=memory_summaries,
                simulation_state=simulation_state,
                run_meta=run_meta,
            )
            console.print(
                f"  [green]💾 Checkpoint saved[/] "
                f"(phases {completed_phases})"
            )

        except Exception as e:
            console.print(
                f"\n  [bold red]✘ Phase {phase_def.number} FAILED:[/] {e}"
            )
            logger.error(
                "Phase %d failed: %s\n%s",
                phase_def.number,
                e,
                traceback.format_exc(),
            )
            failed_phases.append(phase_def.number)

            # Save checkpoint so we can resume from here
            if evaluations:
                save_checkpoint(
                    run_id=run_id,
                    variant=run_meta["variant"],
                    completed_phases=completed_phases,
                    evaluations=[e.to_dict() for e in evaluations],
                    memory_summaries=memory_summaries,
                    simulation_state=simulation_state,
                    run_meta=run_meta,
                )

            console.print(
                f"  [yellow]💾 Progress saved. Resume with:[/]\n"
                f"    python run_simulation.py --resume\n"
                f"    python run_simulation.py "
                f"--resume-id {run_id}"
            )
            # STOP — don't skip to next phase (broken narrative)
            break

    # ── Final summary ────────────────────────────────────────────
    total_elapsed = time.time() - start
    run_meta["total_elapsed"] = total_elapsed

    all_done = len(completed_phases) == len(phases)

    console.print("\n" + "=" * 60)
    console.print(
        Panel(
            build_final_summary(evaluations, failed_phases, total_elapsed),
            title="🏆 FINAL RESULTS" if all_done else "⏸️  PARTIAL RESULTS",
            border_style="green" if all_done else "yellow",
        )
    )

    # Save to dashboard
    if evaluations:
        save_to_dashboard(evaluations, run_meta)

    # Save run metadata
    run_meta["evaluations_count"] = len(evaluations)
    run_meta["failed_phases"] = failed_phases
    run_meta["run_id"] = run_id
    run_meta["checkpoint"] = str(
        Path("checkpoints") / f"{run_id}.checkpoint.json"
    )
    with open("last_run.json", "w") as f:
        json.dump(run_meta, f, indent=2, default=str)

    # Clean up checkpoint on successful completion
    if all_done and not failed_phases:
        delete_checkpoint(run_id)
        console.print(
            "  [green]✓ Checkpoint cleaned up "
            "(simulation complete)[/]"
        )




if __name__ == "__main__":
    main()
