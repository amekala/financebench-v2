"""Smoke tests for FinanceBench v2.

These tests verify the wiring works WITHOUT calling a real LLM.
We use Concordia's built-in no-op language model for deterministic testing.
"""

import numpy as np
import pytest
from concordia.language_model import no_language_model

from financebench.configs import characters, company, scenes
from financebench.embedder import HashEmbedder
from financebench.simulation import build_config


def test_characters_exist():
    """All expected characters are defined."""
    names = {c.name for c in characters.ALL_CHARACTERS}
    assert "Riley Nakamura" in names
    assert "Karen Aldridge" in names
    assert "David Chen" in names
    assert "Priya Sharma" in names
    assert "Marcus Webb" in names


def test_player_is_riley():
    """Riley is the player character."""
    players = [c for c in characters.ALL_CHARACTERS if c.is_player]
    assert len(players) == 1
    assert players[0].name == "Riley Nakamura"


def test_npcs_have_hidden_motivations():
    """Every NPC has a hidden motivation defined."""
    for npc in characters.NPC_CHARACTERS:
        assert npc.hidden_motivation, f"{npc.name} missing hidden_motivation"


def test_all_characters_have_models():
    """Every character has a model assignment."""
    for c in characters.ALL_CHARACTERS:
        assert c.model, f"{c.name} missing model"
    # Protagonist should have the flagship model
    assert "opus" in characters.RILEY.model.lower()


def test_shared_memories_not_empty():
    """Company shared memories are defined."""
    assert len(company.SHARED_MEMORIES) >= 5


def test_smoke_scenes_defined():
    """Smoke test scenes are well-formed."""
    assert len(scenes.SMOKE_TEST_SCENES) == 2
    # First scene is team meeting with 3 people
    meeting = scenes.SMOKE_TEST_SCENES[0]
    assert len(meeting.participants) == 3
    assert "Riley Nakamura" in meeting.participants
    # Second scene is 1:1
    one_on_one = scenes.SMOKE_TEST_SCENES[1]
    assert len(one_on_one.participants) == 2


def test_hash_embedder_deterministic():
    """HashEmbedder produces consistent, normalized vectors."""
    embedder = HashEmbedder(dim=64)
    v1 = embedder("hello world")
    v2 = embedder("hello world")
    v3 = embedder("goodbye world")

    np.testing.assert_array_equal(v1, v2)  # deterministic
    assert not np.allclose(v1, v3)  # different inputs → different vectors
    assert abs(np.linalg.norm(v1) - 1.0) < 0.01  # normalized


def test_build_config_produces_valid_config():
    """build_config() creates a Concordia Config with expected structure."""
    config = build_config()

    # Should have instances for: 5 characters + 1 initializer + 1 GM
    assert len(config.instances) == 7

    # Check roles
    entities = [i for i in config.instances if i.role.name == "ENTITY"]
    gms = [i for i in config.instances if i.role.name == "GAME_MASTER"]
    inits = [i for i in config.instances if i.role.name == "INITIALIZER"]

    assert len(entities) == 5
    assert len(gms) == 1
    assert len(inits) == 1

    # Premise should be set
    assert company.COMPANY_NAME in config.default_premise


def test_build_config_with_subset_of_characters():
    """Can build a config with only a few characters."""
    subset = [characters.RILEY, characters.KAREN]
    config = build_config(character_list=subset)

    entities = [i for i in config.instances if i.role.name == "ENTITY"]
    assert len(entities) == 2
