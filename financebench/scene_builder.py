"""Scene builder: converts PhaseDefinition → Concordia SceneSpec.

This module bridges our research-backed phase definitions with
Concordia's scene system. Each PhaseDefinition becomes a SceneSpec
with the correct participants, premises, and scene type.

The old scenes.py with SMOKE_TEST_SCENES is preserved for quick
smoke tests, but the full simulation uses this builder.
"""

from __future__ import annotations

from concordia.typing import entity as entity_lib
from concordia.typing import scene as scene_lib

from financebench.configs.phases import ALL_PHASES, PhaseDefinition

# ─── Scene Type Specs ─────────────────────────────────────────────
# Templates for different kinds of corporate scenes.
# All use the same structure (DRY factory), differentiated by name.

_SCENE_TYPE_NAMES = [
    "team_meeting", "cross_functional", "one_on_one", "board_prep",
    "crisis", "board_meeting", "interview", "final_evaluation",
]

_SCENE_TYPES: dict[str, scene_lib.SceneTypeSpec] = {
    name: scene_lib.SceneTypeSpec(
        name=name,
        game_master_name="office rules",
        action_spec=entity_lib.free_action_spec(
            call_to_action=entity_lib.DEFAULT_CALL_TO_SPEECH,
        ),
    )
    for name in _SCENE_TYPE_NAMES
}


def phase_to_scene_spec(phase: PhaseDefinition) -> scene_lib.SceneSpec:
    """Convert a PhaseDefinition into a Concordia SceneSpec.

    Maps the phase's premises dict into Concordia's expected format
    (each participant gets a list of premise strings).
    """
    scene_type = _SCENE_TYPES.get(
        phase.scene_type,
        _SCENE_TYPES["team_meeting"],  # safe fallback
    )

    # Concordia expects {name: [str, ...]} for premises
    premise_map: dict[str, list[str]] = {}

    # Build dramatic beats context (injected into every participant's
    # premise so the Game Master can pace the scene)
    beats_context = ""
    if phase.beats:
        beats_context = (
            "\n\nDRAMATIC ARC for this scene (pace the dialogue "
            "through these beats):\n"
            + "\n".join(
                f"  {i+1}. {beat}" for i, beat in enumerate(phase.beats)
            )
            + "\n"
        )

    for participant in phase.participants:
        text = phase.premises.get(participant, "")
        # Prepend the company state as context
        context = (
            f"Date: {phase.date} ({phase.quarter}). "
            f"Company status: {phase.company_state}. "
            f"{text}"
            f"{beats_context}"
        )
        premise_map[participant] = [context]

    return scene_lib.SceneSpec(
        scene_type=scene_type,
        participants=list(phase.participants),
        num_rounds=phase.num_rounds,
        premise=premise_map,
    )


def build_all_scene_specs() -> list[scene_lib.SceneSpec]:
    """Build SceneSpecs for all 9 phases."""
    return [phase_to_scene_spec(p) for p in ALL_PHASES]


def build_scene_specs_for_phases(
    phase_numbers: list[int],
) -> list[scene_lib.SceneSpec]:
    """Build SceneSpecs for specific phase numbers.

    Useful for running a subset (e.g., phases 1-3 only).
    """
    phases = [p for p in ALL_PHASES if p.number in phase_numbers]
    return [phase_to_scene_spec(p) for p in phases]
