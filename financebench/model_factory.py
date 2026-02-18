"""Model factory for per-character LLM instances.

Element LLM Gateway supports all major foundational models:
  - Anthropic: claude-opus-4-5, claude-sonnet-4-5, claude-haiku-4-5
  - OpenAI:    gpt-5, gpt-4.1, gpt-4o, gpt-4o-mini
  - Google:    gemini-3-pro-preview, gemini-2.5-pro, gemini-2.0-flash

This module creates a separate ElementLanguageModel instance for each
character, so each agent in the simulation is powered by its own LLM.
"""

from __future__ import annotations

import logging

from concordia.language_model import language_model
from rich.console import Console

from financebench.configs.characters import (
    ALL_CHARACTERS,
    GAME_MASTER_MODEL,
    Character,
)
from financebench.model import ElementLanguageModel

console = Console()
logger = logging.getLogger(__name__)

# Fallback chain: if a model isn't available, try these alternatives.
_FALLBACKS: dict[str, list[str]] = {
    "claude-opus-4-6": ["claude-opus-4-5", "claude-sonnet-4-5"],
    "claude-opus-4-5": ["claude-sonnet-4-5", "gpt-4.1"],
    "gpt-5": ["gpt-4.1", "gpt-4o"],
    "gemini-3-pro-preview": ["gemini-2.5-pro", "gemini-2.0-flash"],
}


def build_model_for_character(
    char: Character,
    *,
    api_key: str,
    gateway_url: str,
) -> ElementLanguageModel:
    """Create an ElementLanguageModel for a specific character."""
    return ElementLanguageModel(
        model_name=char.model,
        api_key=api_key,
        azure_endpoint=gateway_url,
    )


def build_all_models(
    *,
    api_key: str,
    gateway_url: str,
    character_list: list[Character] | None = None,
) -> dict[str, language_model.LanguageModel]:
    """Build a model instance for every character + Game Master.

    Returns a dict keyed by character name (+ 'game_master').
    Models are deduplicated: characters sharing the same model_name
    share the same instance (saves memory, same API client).
    """
    chars = character_list or ALL_CHARACTERS

    # Deduplicate: group characters by model_name
    model_cache: dict[str, ElementLanguageModel] = {}
    result: dict[str, language_model.LanguageModel] = {}

    for char in chars:
        if char.model not in model_cache:
            model_cache[char.model] = ElementLanguageModel(
                model_name=char.model,
                api_key=api_key,
                azure_endpoint=gateway_url,
            )
            console.print(
                f"  ✓ Created model: [cyan]{char.model}[/]"
                f" (for {char.name})"
            )
        result[char.name] = model_cache[char.model]

    # Game Master model
    if GAME_MASTER_MODEL not in model_cache:
        model_cache[GAME_MASTER_MODEL] = ElementLanguageModel(
            model_name=GAME_MASTER_MODEL,
            api_key=api_key,
            azure_endpoint=gateway_url,
        )
        console.print(
            f"  ✓ Created model: [cyan]{GAME_MASTER_MODEL}[/]"
            f" (Game Master)"
        )
    result["__game_master__"] = model_cache[GAME_MASTER_MODEL]

    console.print(
        f"  [bold green]✓[/] {len(model_cache)} unique models for"
        f" {len(chars)} characters + GM"
    )
    return result
