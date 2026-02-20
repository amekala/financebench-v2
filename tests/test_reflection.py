"""Tests for the reflective self-assessment system."""

import pytest

from financebench.reflection import (
    REFLECTION_MOMENTS,
    get_reflection_for_phase,
    generate_reflection,
    format_reflection_as_memory,
)


class TestReflectionMoments:
    """Test the reflection moment definitions."""

    def test_four_moments_defined(self):
        assert len(REFLECTION_MOMENTS) == 4

    def test_moments_keyed_to_phases(self):
        phases = {rm.after_phase for rm in REFLECTION_MOMENTS}
        assert phases == {2, 4, 6, 8}

    def test_no_game_language(self):
        """Reflections should use career language, not game language."""
        for rm in REFLECTION_MOMENTS:
            combined = (
                rm.label + rm.framing
                + " ".join(rm.focus_areas)
            ).lower()
            assert "phase" not in combined, (
                f"{rm.label} uses 'phase' — should use career language"
            )
            assert "simulation" not in combined, (
                f"{rm.label} uses 'simulation' — breaks immersion"
            )
            assert "score" not in combined, (
                f"{rm.label} uses 'score' — Riley shouldn't see scores"
            )

    def test_moments_have_natural_dates(self):
        """Each moment should have a realistic calendar date."""
        for rm in REFLECTION_MOMENTS:
            assert rm.simulated_date, f"{rm.label} has no date"
            year = int(rm.simulated_date[:4])
            assert 2026 <= year <= 2027, f"{rm.label} date out of range"

    def test_focus_areas_ask_questions(self):
        """Focus areas should be reflective questions, not instructions."""
        for rm in REFLECTION_MOMENTS:
            assert len(rm.focus_areas) >= 3, (
                f"{rm.label} needs at least 3 focus areas"
            )
            for area in rm.focus_areas:
                assert len(area) > 30, (
                    f"{rm.label} focus area too short: {area[:50]}"
                )

    def test_moments_address_relationships(self):
        """Every reflection should touch on relationships — that's
        the whole point of adding this system."""
        for rm in REFLECTION_MOMENTS:
            combined = " ".join(rm.focus_areas).lower()
            has_rel = any(
                word in combined
                for word in [
                    "relationship", "trust", "ally", "allies",
                    "coalition", "loyalty", "advocate",
                ]
            )
            assert has_rel, (
                f"{rm.label} doesn't mention relationships/trust"
            )


class TestGetReflection:
    def test_returns_moment_after_phase_2(self):
        rm = get_reflection_for_phase(2)
        assert rm is not None
        assert rm.after_phase == 2

    def test_returns_none_for_non_reflection_phase(self):
        assert get_reflection_for_phase(1) is None
        assert get_reflection_for_phase(3) is None
        assert get_reflection_for_phase(9) is None

    def test_returns_all_four(self):
        found = [get_reflection_for_phase(i) for i in range(1, 10)]
        non_none = [rm for rm in found if rm is not None]
        assert len(non_none) == 4


class TestFormatMemory:
    def test_format_includes_date(self):
        rm = REFLECTION_MOMENTS[0]
        mem = format_reflection_as_memory("I need more allies.", rm)
        assert rm.simulated_date in mem

    def test_format_includes_label(self):
        rm = REFLECTION_MOMENTS[0]
        mem = format_reflection_as_memory("test", rm)
        assert rm.label in mem

    def test_format_marked_as_private(self):
        rm = REFLECTION_MOMENTS[0]
        mem = format_reflection_as_memory("test", rm)
        assert "Private reflection" in mem


class TestGenerateReflection:
    """Test the reflection generator with a mock model."""

    class _MockModel:
        def sample_text(self, prompt, temperature=0.7, max_tokens=300):
            return (
                "I've been so focused on the numbers that I've "
                "forgotten to invest in people. Priya barely knows "
                "me. Karen sees me as a threat, not a partner. "
                "Jessica would be disappointed."
            )

    def test_generates_reflection(self):
        rm = REFLECTION_MOMENTS[0]
        result = generate_reflection(
            model=self._MockModel(),
            reflection=rm,
            memories=["Memory 1", "Memory 2"],
            relationship_context="Karen is wary. Priya is neutral.",
        )
        assert "focused on the numbers" in result
        assert len(result) > 50

    def test_handles_model_failure(self):
        class FailModel:
            def sample_text(self, *a, **kw):
                raise RuntimeError("API down")

        rm = REFLECTION_MOMENTS[0]
        result = generate_reflection(
            model=FailModel(),
            reflection=rm,
            memories=[],
            relationship_context="",
        )
        # Should return fallback, not crash
        assert "relationship" in result.lower() or "trust" in result.lower()

    def test_handles_empty_memories(self):
        rm = REFLECTION_MOMENTS[0]
        result = generate_reflection(
            model=self._MockModel(),
            reflection=rm,
            memories=[],
            relationship_context="",
        )
        assert len(result) > 20
