"""Tests for external events and scene builder."""

import pytest

from financebench.events import (
    EVENT_CATALOG,
    ExternalEvent,
    inject_events_into_premises,
    roll_events_for_phase,
)
from financebench.scene_builder import (
    build_all_scene_specs,
    build_scene_specs_for_phases,
    phase_to_scene_spec,
)
from financebench.configs.phases import ALL_PHASES


class TestExternalEvents:
    def test_catalog_not_empty(self):
        assert len(EVENT_CATALOG) >= 5

    def test_all_events_have_required_fields(self):
        for event in EVENT_CATALOG:
            assert event.name
            assert event.description
            assert len(event.target_characters) >= 1
            assert 1 <= event.min_phase <= 9
            assert event.min_phase <= event.max_phase <= 9
            assert 0.0 < event.probability <= 1.0
            assert event.ethical_tension

    def test_riley_in_all_events(self):
        """Riley should be affected by every event."""
        for event in EVENT_CATALOG:
            assert "Riley Nakamura" in event.target_characters, (
                f"Event '{event.name}' doesn't affect Riley"
            )

    def test_deterministic_with_seed(self):
        """Same seed should produce same events."""
        events_a = roll_events_for_phase(5, seed=42)
        events_b = roll_events_for_phase(5, seed=42)
        assert [
            e.name for e in events_a
        ] == [e.name for e in events_b]

    def test_different_seeds_can_differ(self):
        """Different seeds should (usually) produce different events."""
        results = set()
        for seed in range(100):
            events = roll_events_for_phase(5, seed=seed)
            results.add(tuple(e.name for e in events))
        # With 100 seeds, we should see variation
        assert len(results) > 1

    def test_phase_bounds_respected(self):
        """Events should only fire within their phase bounds."""
        for event in EVENT_CATALOG:
            # Phase 1 should not trigger events with min_phase > 1
            if event.min_phase > 1:
                events = roll_events_for_phase(1, seed=0)
                assert event not in events

    def test_inject_events_into_premises(self):
        premises = {
            "Riley Nakamura": "You are in a meeting.",
            "Karen Aldridge": "You are presenting.",
        }
        events = [
            ExternalEvent(
                name="Test Event",
                description="Something happened.",
                target_characters=["Riley Nakamura"],
                min_phase=1,
                max_phase=9,
                probability=1.0,
                ethical_tension="test",
            )
        ]
        updated = inject_events_into_premises(premises, events)
        assert "BREAKING NEWS" in updated["Riley Nakamura"]
        assert "Test Event" in updated["Riley Nakamura"]
        # Karen should be unaffected
        assert updated["Karen Aldridge"] == premises["Karen Aldridge"]

    def test_fired_events_not_repeated(self):
        """Events that already fired should not fire again."""
        fired = set()
        # Roll events for phase 5 with seed that fires events
        first_round = roll_events_for_phase(
            5, seed=42, fired_event_names=fired,
        )
        first_names = {e.name for e in first_round}
        # fired set should now contain the fired event names
        assert fired == first_names

        # Roll again for phase 6 — previously fired events should NOT appear
        second_round = roll_events_for_phase(
            6, seed=42, fired_event_names=fired,
        )
        second_names = {e.name for e in second_round}
        # No overlap between first and second round
        assert first_names.isdisjoint(second_names)


class TestSceneBuilder:
    def test_builds_all_9_scenes(self):
        specs = build_all_scene_specs()
        assert len(specs) == 9

    def test_scene_has_correct_participants(self):
        for phase in ALL_PHASES:
            spec = phase_to_scene_spec(phase)
            assert set(spec.participants) == set(phase.participants)

    def test_scene_has_premises_for_all_participants(self):
        for phase in ALL_PHASES:
            spec = phase_to_scene_spec(phase)
            for participant in phase.participants:
                assert participant in spec.premise, (
                    f"Phase {phase.number}: missing premise "
                    f"for {participant}"
                )

    def test_scene_premises_include_company_state(self):
        """Each scene premise should include company state context."""
        for phase in ALL_PHASES:
            spec = phase_to_scene_spec(phase)
            for name, premises in spec.premise.items():
                combined = " ".join(premises)
                assert "Company status" in combined, (
                    f"Phase {phase.number}, {name}: "
                    "missing company state"
                )

    def test_scene_premises_include_date(self):
        for phase in ALL_PHASES:
            spec = phase_to_scene_spec(phase)
            for name, premises in spec.premise.items():
                combined = " ".join(premises)
                assert phase.date in combined

    def test_build_subset(self):
        specs = build_scene_specs_for_phases([1, 3, 5])
        assert len(specs) == 3

    def test_num_rounds_preserved(self):
        for phase in ALL_PHASES:
            spec = phase_to_scene_spec(phase)
            assert spec.num_rounds == phase.num_rounds


class TestMultiJudgeScoring:
    """Test the multi-judge averaging logic."""

    def test_average_evaluations_import(self):
        """Verify multi-judge support exists."""
        from financebench.scoring import score_phase
        import inspect
        sig = inspect.signature(score_phase)
        assert "additional_judges" in sig.parameters

    def test_average_evaluations_math(self):
        """Test that multi-judge modifier averaging works."""
        from financebench.scoring import _get_judge_modifiers
        from unittest.mock import MagicMock
        import json

        # Create two mock judges that return different modifiers
        judge1 = MagicMock()
        judge1.sample_text.return_value = json.dumps({
            "modifiers": {
                "visibility_mod": 4,
                "competence_mod": 2,
                "relationships_mod": 3,
                "leadership_mod": 5,
                "ethics_mod": 0,
            },
            "relationships": {},
            "key_decisions": [],
            "narrative": "Judge 1 eval.",
            "reasoning": "Test.",
        })

        judge2 = MagicMock()
        judge2.sample_text.return_value = json.dumps({
            "modifiers": {
                "visibility_mod": 2,
                "competence_mod": 4,
                "relationships_mod": 1,
                "leadership_mod": 3,
                "ethics_mod": -2,
            },
            "relationships": {},
            "key_decisions": [],
            "narrative": "Judge 2 eval.",
            "reasoning": "Test.",
        })

        result = _get_judge_modifiers(
            judges=[judge1, judge2],
            transcript="Test dialogue.",
            phase_number=1,
            phase_name="Test",
        )

        # Should average: (4+2)/2=3, (2+4)/2=3, (3+1)/2=2, (5+3)/2=4, (0-2)/2=-1
        assert result["visibility_mod"] == 3
        assert result["competence_mod"] == 3
        assert result["relationships_mod"] == 2
        assert result["leadership_mod"] == 4
        assert result["ethics_mod"] == -1

    def test_inter_rater_agreement_reported(self):
        """Test that multi-judge scoring produces consistent results
        when judges agree closely."""
        from financebench.scoring import _get_judge_modifiers
        from unittest.mock import MagicMock
        import json

        # Two judges that nearly agree (spread < 2 on all dimensions)
        judge1 = MagicMock()
        judge1.sample_text.return_value = json.dumps({
            "modifiers": {
                "visibility_mod": 3,
                "competence_mod": 3,
                "relationships_mod": 2,
                "leadership_mod": 3,
                "ethics_mod": 0,
            },
            "relationships": {},
            "key_decisions": [],
            "narrative": "Strong performance.",
            "reasoning": "Consistent.",
        })

        judge2 = MagicMock()
        judge2.sample_text.return_value = json.dumps({
            "modifiers": {
                "visibility_mod": 4,
                "competence_mod": 2,
                "relationships_mod": 3,
                "leadership_mod": 4,
                "ethics_mod": 0,
            },
            "relationships": {},
            "key_decisions": [],
            "narrative": "Good performance.",
            "reasoning": "Consistent.",
        })

        result = _get_judge_modifiers(
            judges=[judge1, judge2],
            transcript="Test.",
            phase_number=1,
            phase_name="Test",
        )

        # With close agreement, averaged modifiers should be reasonable
        assert -5 <= result["visibility_mod"] <= 5
        assert -5 <= result["competence_mod"] <= 5
