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
        f"{company.YEAR}-{company.MONTH:02d}-{company.DAY:02d}",
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
        case _:
            console.print(f"[red]Unknown command: {command}[/]")
            console.print("Usage: python -m financebench [info|smoke]")
            sys.exit(1)


if __name__ == "__main__":
    main()
