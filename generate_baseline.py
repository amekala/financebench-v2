#!/usr/bin/env python3
"""Generate a baseline report from simulation results.

Usage:
    python generate_baseline.py [--results PATH] [--report-only]

Flags:
    --results PATH    Path to results.json (default: docs/data/results.json)
    --report-only     Only generate the markdown report, skip registry
"""

import argparse
from pathlib import Path

from rich.console import Console

from financebench.reporting import (
    build_baseline_from_results,
    save_baseline,
    load_registry,
)
from financebench.report_generator import save_report

console = Console()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate simulation baseline")
    parser.add_argument(
        "--results",
        type=Path,
        default=Path("docs/data/results.json"),
        help="Path to results.json",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Only generate markdown report",
    )
    args = parser.parse_args()

    if not args.results.exists():
        console.print(f"[red]✗ Results file not found: {args.results}[/]")
        return

    console.print(f"\n[bold]Building baseline from {args.results}...[/]")
    baseline = build_baseline_from_results(args.results)
    pbs = baseline.pb_score

    # Print summary
    console.print(f"\n[bold blue]═══ Baseline Summary ═══[/]")
    console.print(f"  Run ID:    {baseline.run_id}")
    console.print(f"  Date:      {baseline.run_date[:10]}")
    console.print(f"  Variant:   {baseline.variant}")
    console.print(
        f"  Model:     {baseline.model_assignments.get('Riley Nakamura', '?')}"
    )
    console.print(f"  Timeline:  {baseline.calendar_months} months "
                  f"(~{baseline.simulated_career_years} career years)")
    console.print(f"")

    console.print(
        f"  [bold yellow]🎯 PB Score: {pbs['total']} / 1000  "
        f"—  {pbs['tier_label']}[/]"
    )
    console.print(f"     {pbs['interpretation']}")
    console.print(f"")
    console.print(f"     Career Outcome: {pbs['career_outcome']:>4} / 400")
    console.print(f"     Integrity:      {pbs['integrity']:>4} / 200")
    console.print(f"     Influence:      {pbs['influence']:>4} / 300")
    console.print(f"     Balance:        {pbs['balance']:>4} / 100")
    console.print(f"")

    console.print(f"  Readiness:     {baseline.final_readiness}%")
    console.print(f"  Ethics:        {baseline.final_ethics}/100")
    console.print(f"  Relationships: {baseline.final_relationships}/100")
    console.print(f"  Outcome:       {baseline.outcome_title}")
    console.print(f"  Compensation:  ${baseline.outcome_compensation:,}")
    console.print(f"")

    # Emergent behaviors
    if baseline.emergent_behaviors:
        console.print(f"  [bold]Emergent Behaviors:[/]")
        for eb in baseline.emergent_behaviors:
            icon = {
                "high": "🚨", "medium": "⚠️", "low": "💡",
            }.get(eb.significance, "•")
            console.print(
                f"    {icon} P{eb.phase} [{eb.category}] {eb.description}"
            )
        console.print(f"")

    # Save baseline
    if not args.report_only:
        filepath = save_baseline(baseline)
        console.print(f"  [green]✓[/] Baseline saved: {filepath}")

    # Generate report
    report_path = save_report(baseline, Path("baselines"))
    console.print(f"  [green]✓[/] Report saved: {report_path}")

    # Show registry comparison
    registry = load_registry()
    if len(registry) > 1:
        console.print(
            f"\n[bold blue]═══ Cross-Simulation Comparison "
            f"({len(registry)} runs) ═══[/]"
        )
        console.print(
            f"  {'Run ID':<45} {'Model':<20} {'PB':>4} "
            f"{'Tier':<12} {'Ready':>6} {'Outcome':<25}"
        )
        console.print(
            f"  {'─'*45} {'─'*20} {'─'*4} "
            f"{'─'*12} {'─'*6} {'─'*25}"
        )
        for r in registry:
            marker = " ◀" if r["run_id"] == baseline.run_id else ""
            console.print(
                f"  {r['run_id']:<45} "
                f"{r.get('protagonist_model', '?'):<20} "
                f"{r['pb_score']:>4} "
                f"{r.get('pb_tier', '?'):<12} "
                f"{r['final_readiness']:>5}% "
                f"{r['outcome_title']:<25}{marker}"
            )
        console.print(f"")
    else:
        console.print(
            f"\n  [dim]First run — baseline established. "
            f"Run more simulations to compare![/]"
        )

    console.print(f"")


if __name__ == "__main__":
    main()
