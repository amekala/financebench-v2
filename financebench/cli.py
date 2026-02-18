"""CLI entry point for FinanceBench.

Usage:
    python -m financebench smoke      # Quick smoke test (2 scenes)
    python -m financebench info        # Show config
"""

import os
import sys

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from financebench.configs import characters, company

console = Console()


def cmd_info() -> None:
    """Print simulation configuration."""
    console.print("\n[bold blue]FinanceBench v2[/] \u2014 AI Career Simulation\n")

    table = Table(title="Company")
    table.add_column("Setting", style="cyan")
    table.add_column("Value")
    table.add_row("Company", company.COMPANY_NAME)
    table.add_row("Industry", company.INDUSTRY)
    table.add_row("HQ", company.HEADQUARTERS)
    table.add_row(
        "Start Date",
        f"{company.SIM_START_YEAR}-{company.SIM_START_MONTH:02d}-{company.SIM_START_DAY:02d}",
    )
    table.add_row(
        "Duration",
        f"{company.SIM_DURATION_MONTHS} months",
    )
    console.print(table)

    char_table = Table(title="\nCharacters")
    char_table.add_column("Name", style="cyan")
    char_table.add_column("Title")
    char_table.add_column("Role")
    for c in characters.ALL_CHARACTERS:
        role = "\u2b50 PLAYER" if c.is_player else "NPC"
        char_table.add_row(c.name, c.title, role)
    console.print(char_table)


def _build_model():
    """Build a Concordia language model from env vars.

    Priority: ELEMENT_API_KEY > OPENAI_API_KEY > GEMINI_API_KEY.
    """
    element_key = os.getenv("ELEMENT_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if element_key:
        from financebench.model import ElementLanguageModel

        model_name = os.getenv("FINANCEBENCH_MODEL", "gpt-4o")
        gateway_url = os.getenv(
            "ELEMENT_GATEWAY_URL",
            "https://wmtllmgateway.prod.walmart.com/wmtllmgateway",
        )
        console.print(f"  Provider: [cyan]Element LLM Gateway[/] \u2764\ufe0f")
        console.print(f"  Model: {model_name}")
        console.print(f"  Gateway: {gateway_url}")

        return ElementLanguageModel(
            model_name=model_name,
            api_key=element_key,
            azure_endpoint=gateway_url,
        )

    if openai_key:
        from financebench.model import ElementLanguageModel

        model_name = os.getenv("FINANCEBENCH_MODEL", "gpt-4o")
        base_url = os.getenv("OPENAI_BASE_URL")
        console.print(f"  Provider: [cyan]OpenAI Direct[/]")
        console.print(f"  Model: {model_name}")

        # Standard OpenAI uses the regular client, not Azure
        import openai as openai_lib
        from concordia.language_model import language_model

        client = openai_lib.OpenAI(api_key=openai_key, base_url=base_url)
        # Use Concordia's built-in GPT model
        from concordia.contrib.language_models.openai.base_gpt_model import (
            BaseGPTModel,
        )

        return BaseGPTModel(model_name=model_name, client=client)

    if gemini_key:
        from concordia.contrib.language_models.google import (
            google_aistudio_model,
        )

        model_name = os.getenv("FINANCEBENCH_MODEL", "gemini-2.0-flash")
        console.print(f"  Provider: [cyan]Google AI Studio[/]")
        console.print(f"  Model: {model_name}")

        return google_aistudio_model.GoogleAIStudioLanguageModel(
            model_name=model_name,
            api_key=gemini_key,
        )

    console.print(
        "[bold red]Error:[/] No API key found.\n\n"
        "Set one of these in your environment or .env file:\n"
        "  ELEMENT_API_KEY  \u2014 Walmart Element LLM Gateway (preferred)\n"
        "  OPENAI_API_KEY   \u2014 Direct OpenAI\n"
        "  GEMINI_API_KEY   \u2014 Google AI Studio\n\n"
        "Get an Element key at: https://console.dx.walmart.com/elementgenai/llm_gateway\n"
        "Need help? #element-genai-support on Slack"
    )
    sys.exit(1)


def _build_multi_models() -> dict:
    """Build per-character model instances from Element Gateway."""
    element_key = os.getenv("ELEMENT_API_KEY")
    if not element_key:
        console.print(
            "[bold red]Error:[/] ELEMENT_API_KEY required for multi-model mode.\n"
            "Get a key at: https://console.dx.walmart.com/elementgenai/llm_gateway\n"
            "Need help? #element-genai-support on Slack"
        )
        sys.exit(1)

    gateway_url = os.getenv(
        "ELEMENT_GATEWAY_URL",
        "https://wmtllmgateway.prod.walmart.com/wmtllmgateway",
    )
    console.print(f"  Provider: [cyan]Element LLM Gateway[/] \u2764\ufe0f")
    console.print(f"  Gateway: {gateway_url}")

    from financebench.model_factory import build_all_models

    return build_all_models(
        api_key=element_key,
        gateway_url=gateway_url,
    )


def cmd_smoke() -> None:
    """Run the smoke test (2 scenes, ~6 rounds of dialogue)."""
    load_dotenv()

    console.print(f"\n[bold blue]FinanceBench Smoke Test[/]")

    model = _build_model()

    from financebench.embedder import HashEmbedder
    from financebench.simulation import run_simulation

    embedder = HashEmbedder()

    results = run_simulation(
        model=model,
        embedder=embedder,
        max_steps=20,
    )

    console.print(f"\n[bold]Entities:[/] {results['entities']}")
    console.print(f"[bold]Game Masters:[/] {results['game_masters']}")

    # Print the narrative log
    log_data = results.get("log")
    if log_data:
        console.print("\n[bold yellow]\u2500\u2500 Simulation Narrative \u2500\u2500[/]")
        if hasattr(log_data, "all_entries"):
            for entry in log_data.all_entries:
                console.print(f"  {entry}")
        elif isinstance(log_data, dict):
            for key, val in log_data.items():
                console.print(f"  [cyan]{key}:[/] {val}")
        else:
            console.print(f"  {log_data}")


def cmd_run() -> None:
    """Run the full multi-phase simulation with per-character models."""
    load_dotenv()

    console.print("\n[bold blue]PromotionBench[/] \u2014 Multi-Phase Simulation\n")

    models = _build_multi_models()

    from financebench.embedder import HashEmbedder
    from financebench.orchestrator import run_all_phases

    embedder = HashEmbedder()
    scoring_model = models["__game_master__"]

    # Parse optional --phases argument (e.g., --phases 1,2,3)
    phase_numbers = None
    for i, arg in enumerate(sys.argv):
        if arg == "--phases" and i + 1 < len(sys.argv):
            phase_numbers = [
                int(x.strip()) for x in sys.argv[i + 1].split(",")
            ]

    # Parse optional --variant argument
    variant = "neutral"
    for i, arg in enumerate(sys.argv):
        if arg == "--variant" and i + 1 < len(sys.argv):
            variant = sys.argv[i + 1].strip().lower()

    if variant == "ruthless":
        console.print(
            "  [yellow]\u26a0 Running RUTHLESS variant[/] "
            "(biased goal: 'at any cost')"
        )
        # Swap Riley variant in models (model stays the same)
        from financebench.configs.characters import RILEY_RUTHLESS
        console.print(
            f"  Riley goal: {RILEY_RUTHLESS.goal[:60]}..."
        )
    else:
        console.print(
            "  [green]\u2713 Running NEUTRAL variant[/] "
            "(balanced goal: observe emergent behavior)"
        )

    evaluations = run_all_phases(
        agent_models=models,
        scoring_model=scoring_model,
        embedder=embedder,
        phase_numbers=phase_numbers,
    )

    # Final summary
    console.print("\n[bold blue]\u2500\u2500 Final Summary \u2500\u2500[/]")
    for ev in evaluations:
        console.print(
            f"  Phase {ev.phase} ({ev.name}): "
            f"[bold]{ev.scores.promotion_readiness}%[/] readiness"
        )
    if evaluations:
        final = evaluations[-1].scores.promotion_readiness
        if final >= 70:
            console.print("\n  [bold green]\ud83c\udf1f Riley is on track for CFO![/]")
        elif final >= 40:
            console.print("\n  [bold yellow]\u26a0 Riley needs to step it up.[/]")
        else:
            console.print("\n  [bold red]\ud83d\udea8 Riley is struggling.[/]")


def cmd_run_single() -> None:
    """Run smoke test with multi-model (no scoring, for quick validation)."""
    load_dotenv()

    console.print("\n[bold blue]FinanceBench Multi-Model Smoke Test[/]\n")

    models = _build_multi_models()
    default_model = models["__game_master__"]

    from financebench.embedder import HashEmbedder
    from financebench.simulation import run_simulation

    embedder = HashEmbedder()

    results = run_simulation(
        model=default_model,
        embedder=embedder,
        agent_models=models,
        max_steps=20,
    )

    console.print(f"\n[bold]Entities:[/] {results['entities']}")
    console.print(f"[bold]Game Masters:[/] {results['game_masters']}")


def main() -> None:
    """Route CLI commands."""
    if len(sys.argv) < 2:
        cmd_info()
        return

    command = sys.argv[1]
    match command:
        case "info":
            cmd_info()
        case "smoke":
            cmd_smoke()
        case "run":
            cmd_run()
        case "run-single":
            cmd_run_single()
        case _:
            console.print(f"[red]Unknown command: {command}[/]")
            console.print(
                "Usage: python -m financebench "
                "[info|smoke|run|run-single]\n"
                "\nOptions for 'run':\n"
                "  --phases 1,2,3   Run specific phases only\n"
                "  --variant ruthless  Use ruthless Riley variant"
            )
            sys.exit(1)


if __name__ == "__main__":
    main()
