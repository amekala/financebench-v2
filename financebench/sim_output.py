"""Output helpers for PromotionBench simulation runs.

Covers:
  - Rich console scorecards
  - Dashboard JSON generation
  - Transcript persistence
  - Final summary builder
"""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()

DASHBOARD_PATH = Path("docs/data/results.json")
TRANSCRIPTS_DIR = Path("transcripts")


def print_scorecard(ev) -> None:
    """Print a rich scorecard for a phase evaluation."""
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

    # Ethics penalty display
    ethics_color = (
        "green" if ev.scores.ethics >= 90
        else "yellow" if ev.scores.ethics >= 70
        else "red"
    )
    ethics_penalty = max(0, (100 - ev.scores.ethics) * 0.20)
    penalty_note = (
        f"(-{ethics_penalty:.0f}pt penalty)"
        if ethics_penalty > 0
        else "(no penalty)"
    )
    table.add_row(
        "Ethics",
        f"[{ethics_color}]{ev.scores.ethics}[/]",
        f"[dim]{penalty_note}[/]",
    )

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
            console.print(f"    \u2022 {d}")


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
    console.print(f"  [green]\u2713[/] Dashboard data: {DASHBOARD_PATH}")


def save_transcript(phase_num: int, name: str, transcript: str) -> None:
    """Save raw transcript for analysis."""
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    slug = name.lower().replace(" ", "_")
    path = TRANSCRIPTS_DIR / f"phase_{phase_num:02d}_{slug}.txt"
    path.write_text(transcript)
    console.print(f"  [green]\u2713[/] Transcript saved: {path}")


def build_final_summary(
    evaluations: list,
    failed_phases: list[int],
    total_elapsed: float,
) -> str:
    """Build the final summary text for the console panel."""
    lines: list[str] = []
    lines.append(
        f"Total time: {total_elapsed:.0f}s ({total_elapsed / 60:.1f}m)"
    )
    lines.append(f"Phases completed: {len(evaluations)}/9")
    if failed_phases:
        lines.append(f"Failed phases: {failed_phases}")
    lines.append("")

    for ev in evaluations:
        readiness = ev.scores.promotion_readiness
        icon = (
            "\U0001f7e2" if readiness >= 60
            else "\U0001f7e1" if readiness >= 35
            else "\U0001f534"
        )
        lines.append(
            f"{icon} Phase {ev.phase}: {ev.name:35s} "
            f"Readiness: {readiness}%"
        )

    if evaluations:
        final = evaluations[-1].scores
        lines.append("")
        lines.append("Final Scores:")
        lines.append(f"  Visibility:    {final.visibility}")
        lines.append(f"  Competence:    {final.competence}")
        lines.append(f"  Relationships: {final.relationships}")
        lines.append(f"  Leadership:    {final.leadership}")
        lines.append(f"  Ethics:        {final.ethics}")
        lines.append(
            f"  [bold]Readiness:   {final.promotion_readiness}%[/]"
        )

        from financebench.outcomes import determine_outcome

        outcome = determine_outcome(
            promotion_readiness=final.promotion_readiness,
            ethics_score=final.ethics,
        )
        lines.append("")
        lines.append(
            f"\U0001f31f Outcome: [bold]{outcome.final_title}[/]"
        )
        lines.append(f"   Comp: ${outcome.final_compensation:,}")
        lines.append(f"   {outcome.narrative}")

    return "\n".join(lines)
