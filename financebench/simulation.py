"""FinanceBench simulation builder.

Assembles Concordia entities, game masters, and scenes into
a runnable simulation. This is the main orchestration module.
"""

from collections.abc import Callable
from typing import Any

import numpy as np
from concordia.associative_memory import basic_associative_memory
from concordia.environment.engines import sequential
from concordia.language_model import language_model
from concordia.prefabs import entity as entity_prefabs
from concordia.prefabs import game_master as gm_prefabs
from concordia.prefabs.simulation import generic as simulation_lib
from concordia.typing import prefab as prefab_lib
from concordia.utils import helper_functions
from rich.console import Console

from financebench.configs import characters, company, scenes

console = Console()


def build_config(
    *,
    scene_specs: list | None = None,
    character_list: list[characters.Character] | None = None,
) -> prefab_lib.Config:
    """Build a Concordia Config from our game design.

    Args:
        scene_specs: Concordia SceneSpecs to run. Defaults to smoke test.
        character_list: Characters to include. Defaults to all.

    Returns:
        A Concordia Config ready for Simulation().
    """
    if scene_specs is None:
        scene_specs = scenes.SMOKE_TEST_SCENES
    if character_list is None:
        character_list = characters.ALL_CHARACTERS

    # Load all built-in prefabs from Concordia
    prefabs = {
        **helper_functions.get_package_classes(entity_prefabs),
        **helper_functions.get_package_classes(gm_prefabs),
    }

    instances: list[prefab_lib.InstanceConfig] = []

    # --- Create agent instances from our character definitions ---
    for char in character_list:
        # Build per-character context string
        context = "\n".join(char.backstory)

        params = {
            "name": char.name,
            "goal": char.goal,
        }

        instances.append(
            prefab_lib.InstanceConfig(
                prefab="basic__Entity",
                role=prefab_lib.Role.ENTITY,
                params=params,
            )
        )

    # --- Formative memories initializer (backstories) ---
    # player_specific_context is injected ONLY into that character's
    # private memory. This is how we achieve information isolation:
    # - Riley sees her goal but NOT Karen's hidden motivation
    # - Karen sees her hidden motivation but NOT Riley's goal
    # - No agent knows this is a simulation
    player_context = {}
    for char in character_list:
        lines = list(char.backstory)
        # Inject hidden motivation as private memory (NPCs only)
        if char.hidden_motivation and not char.is_player:
            lines.append(char.hidden_motivation)
        player_context[char.name] = "\n".join(lines)

    instances.append(
        prefab_lib.InstanceConfig(
            prefab="formative_memories_initializer__GameMaster",
            role=prefab_lib.Role.INITIALIZER,
            params={
                "name": "initial setup rules",
                "next_game_master_name": "office rules",
                "shared_memories": company.SHARED_MEMORIES,
                "player_specific_context": player_context,
      },
        )
    )

    # --- Game Master for dialogic scenes ---
    instances.append(
        prefab_lib.InstanceConfig(
            prefab="dialogic_and_dramaturgic__GameMaster",
            role=prefab_lib.Role.GAME_MASTER,
            params={
                "name": "office rules",
                "scenes": scene_specs,
                "next_game_master_name": "office rules",
            },
        )
    )

    return prefab_lib.Config(
        default_premise=company.SCENARIO_PREMISE,
        default_max_steps=50,
        prefabs=prefabs,
        instances=instances,
    )


def run_simulation(
    *,
    model: language_model.LanguageModel,
    embedder: Callable[[str], np.ndarray],
    config: prefab_lib.Config | None = None,
    max_steps: int | None = None,
) -> dict[str, Any]:
    """Run the FinanceBench simulation end-to-end.

    Args:
        model: A Concordia-compatible language model.
        embedder: A callable that maps text -> numpy vector.
        config: Simulation config. Defaults to smoke test.
        max_steps: Override max steps.

    Returns:
        A dict with the simulation log and entity states.
    """
    if config is None:
        config = build_config()

    console.print("\n[bold blue]FinanceBench v2[/] — Building simulation...")
    console.print(f"  Characters: {len(config.instances) - 2}")  # minus GM + init
    console.print(f"  Engine: Sequential (turn-based)")

    engine = sequential.Sequential()

    sim = simulation_lib.Simulation(
        config=config,
        model=model,
        embedder=embedder,
        engine=engine,
    )

    console.print("[bold green]✓[/] Simulation built. Running...\n")

    results = sim.play(
        premise=config.default_premise,
        max_steps=max_steps or config.default_max_steps,
    )

    console.print("\n[bold green]✓[/] Simulation complete!")

    return {
        "log": results,
        "entities": [e.name for e in sim.get_entities()],
        "game_masters": [gm.name for gm in sim.get_game_masters()],
    }
