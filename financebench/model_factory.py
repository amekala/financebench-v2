"""Model factory for per-character LLM instances.

Element LLM Gateway - verified working models:
  - gpt-4.1, gpt-4o, gpt-4o-mini, gpt-4.1-mini, gpt-4.1-nano, o3

No fallback system. No silent swaps. If a model isn't available,
you'll get a clear error. Change models in configs/characters.py.
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

    Returns a dict keyed by character name (+ '__game_master__').
    Models are deduplicated: characters sharing the same model_name
    share the same instance (saves memory, same API client).
    """
    chars = character_list or ALL_CHARACTERS

    model_cache: dict[str, ElementLanguageModel] = {}
    result: dict[str, language_model.LanguageModel] = {}

    for char in chars:
        if char.model not in model_cache:
            model_cache[char.model] = ElementLanguageModel(
                model_name=char.model,
                api_key=api_key,
                azure_endpoint=gateway_url,
            )
        result[char.name] = model_cache[char.model]
        console.print(
            f"  \u2713 [green]{char.name}[/]: [cyan]{char.model}[/]"
        )

    # Game Master model
    if GAME_MASTER_MODEL not in model_cache:
        model_cache[GAME_MASTER_MODEL] = ElementLanguageModel(
            model_name=GAME_MASTER_MODEL,
            api_key=api_key,
            azure_endpoint=gateway_url,
        )
    result["__game_master__"] = model_cache[GAME_MASTER_MODEL]
    console.print(
        f"  \u2713 [green]Game Master[/]: [cyan]{GAME_MASTER_MODEL}[/]"
    )

    console.print(
        f"  [bold green]\u2713[/] {len(model_cache)} unique models for"
        f" {len(chars)} characters + GM"
    )
    return result
