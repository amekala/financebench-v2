"""Tests for enhanced phase definitions with beats."""

import pytest

from financebench.configs.phases import ALL_PHASES, PhaseDefinition


class TestPhaseBeats:
    """Every phase should have dramatic beats that structure the scene."""

    def test_all_phases_have_beats(self):
        for phase in ALL_PHASES:
            assert len(phase.beats) >= 3, (
                f"Phase {phase.number} ({phase.name}) needs at least "
                f"3 beats, has {len(phase.beats)}"
            )

    def test_beats_have_substance(self):
        for phase in ALL_PHASES:
            for i, beat in enumerate(phase.beats):
                assert len(beat) > 30, (
                    f"Phase {phase.number} beat {i+1} too short: "
                    f"{beat[:50]}"
                )

    def test_beats_no_game_language(self):
        """Beats should use narrative language, not game mechanics."""
        for phase in ALL_PHASES:
            for beat in phase.beats:
                lower = beat.lower()
                assert "score" not in lower, (
                    f"Phase {phase.number} beat uses 'score'"
                )
                assert "dimension" not in lower, (
                    f"Phase {phase.number} beat uses 'dimension'"
                )


class TestPhaseRounds:
    """Phases should have enough rounds for dramatic depth."""

    def test_minimum_rounds(self):
        for phase in ALL_PHASES:
            assert phase.num_rounds >= 8, (
                f"Phase {phase.number} has only {phase.num_rounds} "
                f"rounds — needs at least 8 for dramatic depth"
            )

    def test_crisis_has_more_rounds(self):
        crisis = [p for p in ALL_PHASES if p.scene_type == "crisis"]
        for p in crisis:
            assert p.num_rounds >= 10, (
                f"Crisis phase {p.number} needs ≥10 rounds"
            )

    def test_final_has_more_rounds(self):
        final = [p for p in ALL_PHASES if p.scene_type == "final_evaluation"]
        for p in final:
            assert p.num_rounds >= 10, (
                f"Final phase {p.number} needs ≥10 rounds"
            )


class TestPhaseParticipants:
    def test_riley_in_all_phases(self):
        for phase in ALL_PHASES:
            assert "Riley Nakamura" in phase.participants, (
                f"Phase {phase.number} missing Riley!"
            )

    def test_all_phases_have_premises(self):
        for phase in ALL_PHASES:
            for p in phase.participants:
                assert p in phase.premises, (
                    f"Phase {phase.number} missing premise for {p}"
                )
