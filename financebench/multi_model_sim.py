"""Multi-model Simulation subclass.

Concordia's stock Simulation uses ONE model for all agents.
This subclass overrides add_entity() to look up the correct
model from a per-character routing table.

This is the heart of the multi-model architecture:
  Riley  → claude-opus-4-6
  Karen  → claude-sonnet-4-5
  David  → gemini-3-pro-preview
  Priya  → gpt-5
  Marcus → gpt-5
  GM     → claude-opus-4-5
"""

from __future__ import annotations

import copy
import logging
from collections.abc import Callable
from typing import Any

import numpy as np
from concordia.associative_memory import (
    basic_associative_memory as associative_memory,
)
from concordia.environment.engines import sequential
from concordia.language_model import language_model
from concordia.prefabs.simulation import generic as simulation_lib
from concordia.typing import entity_component, prefab as prefab_lib
from rich.console import Console

console = Console()
logger = logging.getLogger(__name__)

Role = prefab_lib.Role


class MultiModelSimulation(simulation_lib.Simulation):
    """Simulation that assigns different LLMs to different entities.

    Usage:
        models = build_all_models(api_key=key, gateway_url=url)
        sim = MultiModelSimulation(
            config=config,
            model=models['__game_master__'],  # default fallback
            embedder=embedder,
            agent_models=models,              # per-entity routing
        )
    """

    def __init__(
        self,
        config: prefab_lib.Config,
        model: language_model.LanguageModel,
        embedder: Callable[[str], np.ndarray],
        *,
        agent_models: dict[str, language_model.LanguageModel] | None = None,
        engine: sequential.Sequential | None = None,
        override_game_master_model: language_model.LanguageModel | None = None,
    ):
        """Initialize multi-model simulation.

        Args:
            config: Concordia config.
            model: Default/fallback model.
            embedder: Sentence embedder.
            agent_models: Dict mapping entity name -> model.
            engine: Concordia engine (defaults to Sequential).
            override_game_master_model: Optional separate GM model.
        """
        self._agent_models = agent_models or {}
        gm_model = (
            override_game_master_model
            or self._agent_models.get("__game_master__")
            or model
        )
        super().__init__(
            config=config,
            model=model,
            embedder=embedder,
            engine=engine or sequential.Sequential(),
            override_game_master_model=gm_model,
        )

    def add_entity(
        self,
        instance_config: prefab_lib.InstanceConfig,
        state: entity_component.EntityState | None = None,
    ) -> None:
        """Add entity with per-character model routing.

        Looks up the entity name in agent_models dict.
        Falls back to self._agent_model if not found.
        """
        if instance_config.role != Role.ENTITY:
            raise ValueError("Instance config role must be ENTITY")

        entity_name = instance_config.params.get("name", "Unknown")

        # Route to per-character model or fall back to default
        entity_model = self._agent_models.get(
            entity_name, self._agent_model
        )
        model_name = getattr(entity_model, "_model_name", "unknown")
        console.print(
            f"  🎭 {entity_name} → [cyan]{model_name}[/]"
        )

        # Build entity with the correct model (not self._agent_model)
        entity_prefab = copy.deepcopy(
            self._config.prefabs[instance_config.prefab]
        )
        entity_prefab.params = instance_config.params

        memory_bank = associative_memory.AssociativeMemoryBank(
            sentence_embedder=self._embedder,
        )
        entity = entity_prefab.build(
            model=entity_model,  # <-- PER-CHARACTER MODEL
            memory_bank=memory_bank,
        )

        if any(e.name == entity.name for e in self.entities):
            logger.info("Entity %s already exists.", entity.name)
            return

        # Handle pre-loaded memory state
        memory_state = instance_config.params.get("memory_state")
        if memory_state:
            try:
                mem = entity.get_component("__memory__")
                mem.set_state(memory_state)
            except (KeyError, TypeError, ValueError) as e:
                logger.error(
                    "Error setting memory for %s: %s", entity.name, e
                )
                raise

        if state:
            entity.set_state(state)

        self.entities.append(entity)
        self._entity_to_prefab_config[entity.name] = instance_config

        # Update GMs to know about new entity
        for gm in self.game_masters:
            if hasattr(gm, "entities"):
                gm.entities = self.entities
