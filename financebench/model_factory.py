"""Model factory for per-character LLM instances.

Element LLM Gateway supports all major foundational models:
  - Anthropic: claude-opus-4-5, claude-sonnet-4-5, claude-haiku-4-5
  - OpenAI:    gpt-5, gpt-5.2, gpt-4.1, gpt-4o, gpt-4o-mini
  - Google:    gemini-3-pro-preview, gemini-2.5-pro, gemini-2.0-flash

This module creates a separate ElementLanguageModel instance for each
character, so each agent in the simulation is powered by its own LLM.

Fallback system: when a model isn't yet deployed on the gateway,
we map it to the best available alternative and log a warning.
The character config keeps the *intended* model name so the design
stays correct and automatically upgrades when the gateway adds support.
"""

from __future__ import annotations

import logging
import os

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


# ── Fallback Mapping ────────────────────────────────────────────────
# Maps unavailable models to the best available alternative.
# The intent is to preserve *differentiation* between characters:
#   - Flagship protagonist → strongest available (gpt-4.1)
#   - Mid-tier NPCs → gpt-4o (reliable, different style)
#   - Lightweight NPCs → gpt-4.1-mini (fast, cheaper)
#
# When Element Gateway adds support for claude/gemini/gpt-5,
# remove entries from this dict and models upgrade automatically.
# ─────────────────────────────────────────────────────────────

_FALLBACK_MAP: dict[str, str] = {
    # Anthropic flagship → best OpenAI (protagonist + GM need top reasoning)
    "claude-opus-4-6":       "gpt-4.1",
    "claude-opus-4-5":       "gpt-4.1",
    # Anthropic mid-tier → reliable mid-tier
    "claude-sonnet-4-5":     "gpt-4o",
    "claude-sonnet-4":       "gpt-4o",
    "claude-haiku-4-5":      "gpt-4o-mini",
    # Google flagship → differentiated (keep models distinct!)
    "gemini-3-pro-preview":  "gpt-4.1-mini",
    "gemini-2.5-pro":        "gpt-4.1-mini",
    "gemini-2.0-flash":      "gpt-4o-mini",
    # OpenAI next-gen → best available alternatives
    # Spread across different models to keep character differentiation
    "gpt-5":                 "gpt-4o-mini",
    "gpt-5.2":               "gpt-4.1-nano",
}


def _resolve_model(requested: str) -> tuple[str, bool]:
    """Resolve a model name, applying fallback if needed.

    Returns (actual_model_name, was_fallback).
    """
    if os.getenv("PROMOTIONBENCH_NO_FALLBACK"):
        return requested, False
    fallback = _FALLBACK_MAP.get(requested)
    if fallback:
        return fallback, True
    return requested, False


def build_model_for_character(
    char: Character,
    *,
    api_key: str,
    gateway_url: str,
) -> ElementLanguageModel:
    """Create an ElementLanguageModel for a specific character."""
    actual, fell_back = _resolve_model(char.model)
    if fell_back:
        logger.info(
            "[%s] %s not available, falling back to %s",
            char.name, char.model, actual,
        )
    return ElementLanguageModel(
        model_name=actual,
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

    Returns a dict keyed by character name (+ '__game_master__').
    Models are deduplicated: characters sharing the same actual model
    share the same instance (saves memory, same API client).
    """
    chars = character_list or ALL_CHARACTERS

    # Deduplicate by *actual* model (post-fallback)
    model_cache: dict[str, ElementLanguageModel] = {}
    result: dict[str, language_model.LanguageModel] = {}

    for char in chars:
        actual, fell_back = _resolve_model(char.model)
        if actual not in model_cache:
            model_cache[actual] = ElementLanguageModel(
                model_name=actual,
                api_key=api_key,
                azure_endpoint=gateway_url,
            )
        result[char.name] = model_cache[actual]

        label = char.model
        if fell_back:
            label = f"{char.model} → {actual}"
            console.print(
                f"  ⚠ [yellow]{char.name}[/]: "
                f"[dim]{char.model}[/] → [cyan]{actual}[/] (fallback)"
            )
        else:
            console.print(
                f"  ✓ [green]{char.name}[/]: [cyan]{actual}[/]"
            )

    # Game Master model
    gm_actual, gm_fell_back = _resolve_model(GAME_MASTER_MODEL)
    if gm_actual not in model_cache:
        model_cache[gm_actual] = ElementLanguageModel(
            model_name=gm_actual,
            api_key=api_key,
            azure_endpoint=gateway_url,
        )
    result["__game_master__"] = model_cache[gm_actual]

    if gm_fell_back:
        console.print(
            f"  ⚠ [yellow]Game Master[/]: "
            f"[dim]{GAME_MASTER_MODEL}[/] → [cyan]{gm_actual}[/] (fallback)"
        )
    else:
        console.print(
            f"  ✓ [green]Game Master[/]: [cyan]{gm_actual}[/]"
        )

    console.print(
        f"  [bold green]✓[/] {len(model_cache)} unique models for"
        f" {len(chars)} characters + GM"
    )
    return result
