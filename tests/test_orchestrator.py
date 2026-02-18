"""Tests for orchestrator memory persistence and CLI fixes."""

import pytest

from financebench.configs import characters, company
from financebench.simulation import build_config


class TestMemoryPersistence:
    """Verify memory summaries are injected into subsequent phases."""

    def test_build_config_accepts_memory_summaries(self):
        """build_config should accept and inject memory summaries."""
        memories = {
            "Riley Nakamura": [
                "[Memory from 2026-01-06] Riley presented Q4 numbers.",
                "[Memory from 2026-02-17] Riley met with Priya.",
            ],
            "Karen Aldridge": [
                "[Memory from 2026-01-06] Karen observed Riley's Q4 pres.",
            ],
        }
        config = build_config(memory_summaries=memories)

        # Find the initializer
        init = [
            i for i in config.instances if i.role.name == "INITIALIZER"
        ][0]
        ctx = init.params["player_specific_context"]

        # Riley's context should contain memory summaries
        assert "Memory from 2026-01-06" in ctx["Riley Nakamura"]
        assert "Memory from 2026-02-17" in ctx["Riley Nakamura"]

        # Karen's context should contain her memory
        assert "Memory from 2026-01-06" in ctx["Karen Aldridge"]

    def test_memory_summaries_dont_leak(self):
        """One character's memories should not appear in another's."""
        memories = {
            "Riley Nakamura": [
                "[Memory] Riley's secret plan to bypass Karen.",
            ],
        }
        config = build_config(memory_summaries=memories)
        init = [
            i for i in config.instances if i.role.name == "INITIALIZER"
        ][0]
        ctx = init.params["player_specific_context"]

        # Karen should NOT see Riley's memories
        assert "secret plan" not in ctx.get("Karen Aldridge", "")
        # David should NOT see Riley's memories
        assert "secret plan" not in ctx.get("David Chen", "")

    def test_without_memories_still_works(self):
        """build_config should work fine without memory summaries."""
        config = build_config(memory_summaries=None)
        assert config is not None
        config2 = build_config()
        assert config2 is not None


class TestNeutralRileyVariant:
    """Verify both Riley variants exist and differ."""

    def test_neutral_riley_exists(self):
        assert characters.RILEY is not None
        assert characters.RILEY.is_player

    def test_ruthless_riley_exists(self):
        assert characters.RILEY_RUTHLESS is not None
        assert characters.RILEY_RUTHLESS.is_player

    def test_neutral_is_default(self):
        """RILEY (neutral) should be in ALL_CHARACTERS, not RUTHLESS."""
        names_and_goals = [
            (c.name, c.goal) for c in characters.ALL_CHARACTERS
        ]
        riley_in_all = [
            g for n, g in names_and_goals if n == "Riley Nakamura"
        ]
        assert len(riley_in_all) == 1
        # Neutral goal should NOT contain "at any cost"
        assert "at any cost" not in riley_in_all[0].lower()

    def test_ruthless_is_explicitly_aggressive(self):
        assert "at any cost" in characters.RILEY_RUTHLESS.goal.lower()

    def test_neutral_is_balanced(self):
        """Neutral Riley should mention both results AND relationships."""
        goal = characters.RILEY.goal.lower()
        assert "results" in goal or "career" in goal
        assert "relationship" in goal or "alliance" in goal

    def test_both_share_backstory(self):
        """Variants should share the same backstory (only goal differs)."""
        assert characters.RILEY.backstory == characters.RILEY_RUTHLESS.backstory


class TestCompanyConstantsFix:
    """Verify the CLI crash from old constant names is fixed."""

    def test_sim_start_constants_exist(self):
        assert hasattr(company, "SIM_START_YEAR")
        assert hasattr(company, "SIM_START_MONTH")
        assert hasattr(company, "SIM_START_DAY")
        assert hasattr(company, "SIM_DURATION_MONTHS")

    def test_old_constants_removed(self):
        """Old YEAR/MONTH/DAY constants should not exist."""
        assert not hasattr(company, "YEAR")
        assert not hasattr(company, "MONTH")
        assert not hasattr(company, "DAY")

    def test_sim_constants_reasonable(self):
        assert company.SIM_START_YEAR == 2026
        assert 1 <= company.SIM_START_MONTH <= 12
        assert 1 <= company.SIM_START_DAY <= 31
        assert company.SIM_DURATION_MONTHS == 18


class TestDeadCodeCleaned:
    """Verify dead code from review has been removed."""

    def test_no_fallbacks_in_model_factory(self):
        from financebench import model_factory
        assert not hasattr(model_factory, "_FALLBACKS")


class TestPinnedDependencies:
    """Verify dependencies are pinned for reproducibility."""

    def test_pyproject_has_version_constraints(self):
        from pathlib import Path
        pyproject = Path(__file__).parent.parent / "pyproject.toml"
        content = pyproject.read_text()
        # Should have version constraints, not bare package names
        assert ">=" in content or "<" in content
        assert 'gdm-concordia[openai]"' not in content  # Not bare
