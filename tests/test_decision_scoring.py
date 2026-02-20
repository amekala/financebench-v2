"""Tests for decision_points.py, trajectory.py, and consequences.py.

Covers the new deterministic scoring framework:
  - Decision point structure and completeness
  - Phase ceiling enforcement
  - Consequence state tracking
  - Score clamping behavior
"""

import pytest

from financebench.configs.decision_points import (
    ALL_DECISION_POINTS,
    DecisionOption,
    DecisionPoint,
    ScoreImpact,
    get_decision_points_for_phase,
)
from financebench.configs.trajectory import (
    PHASE_ANCHORS,
    PhaseAnchors,
    clamp_to_ceiling,
    get_anchors,
)
from financebench.consequences import SimulationState


class TestDecisionPoints:
    """Tests for decision point definitions."""

    def test_all_decision_points_are_defined(self):
        """We should have decision points for phases 1-8 (phase 9 is final)."""
        assert len(ALL_DECISION_POINTS) >= 9  # 1 per phase + extras

    def test_every_decision_has_options(self):
        for dp in ALL_DECISION_POINTS:
            assert len(dp.options) >= 2, (
                f"Decision {dp.id} needs at least 2 options"
            )

    def test_every_option_has_unique_id(self):
        all_ids = [opt.id for dp in ALL_DECISION_POINTS for opt in dp.options]
        assert len(all_ids) == len(set(all_ids)), "Duplicate option IDs found"

    def test_every_decision_has_classification_rubric(self):
        for dp in ALL_DECISION_POINTS:
            assert dp.classification_rubric, (
                f"Decision {dp.id} missing classification rubric"
            )

    def test_every_decision_has_forcing_function(self):
        for dp in ALL_DECISION_POINTS:
            assert dp.forcing_function, (
                f"Decision {dp.id} missing forcing function"
            )

    def test_get_decision_points_for_phase(self):
        phase_1 = get_decision_points_for_phase(1)
        assert len(phase_1) >= 1
        assert all(dp.phase == 1 for dp in phase_1)

        phase_4 = get_decision_points_for_phase(4)
        assert len(phase_4) == 2  # ambition + attribution
        assert all(dp.phase == 4 for dp in phase_4)

    def test_no_decision_points_for_phase_9(self):
        """Phase 9 is final evaluation only — no new decisions."""
        assert get_decision_points_for_phase(9) == []

    def test_phases_1_through_8_have_decisions(self):
        for phase in range(1, 9):
            dps = get_decision_points_for_phase(phase)
            assert len(dps) >= 1, (
                f"Phase {phase} has no decision points"
            )

    def test_score_impacts_are_bounded(self):
        """No single decision should have extreme impacts."""
        for dp in ALL_DECISION_POINTS:
            for opt in dp.options:
                imp = opt.score_impact
                for dim in ["visibility", "competence", "relationships",
                            "leadership", "ethics"]:
                    val = getattr(imp, dim)
                    assert -30 <= val <= 30, (
                        f"{dp.id}/{opt.id}: {dim}={val} out of bounds"
                    )

    def test_no_free_lunches(self):
        """Every option should have some trade-off — no option is
        purely positive across all dimensions."""
        for dp in ALL_DECISION_POINTS:
            for opt in dp.options:
                imp = opt.score_impact
                vals = [
                    imp.visibility, imp.competence, imp.relationships,
                    imp.leadership, imp.ethics,
                ]
                # Check relationship impacts too
                rel_vals = [r.delta for r in opt.relationship_impacts]
                all_vals = vals + rel_vals
                # At least one value should be <= 0 (trade-off)
                has_negative = any(v < 0 for v in all_vals)
                has_zero = any(v == 0 for v in vals)
                assert has_negative or has_zero, (
                    f"{dp.id}/{opt.id}: no trade-off detected. "
                    f"Scores: {vals}, Relationships: {rel_vals}"
                )


class TestTrajectory:
    """Tests for phase ceiling enforcement."""

    def test_all_9_phases_have_anchors(self):
        assert len(PHASE_ANCHORS) == 9
        for i, a in enumerate(PHASE_ANCHORS, 1):
            assert a.phase == i

    def test_ceilings_increase_monotonically(self):
        """Each phase's ceiling should be >= the previous phase."""
        for i in range(1, len(PHASE_ANCHORS)):
            prev = PHASE_ANCHORS[i - 1]
            curr = PHASE_ANCHORS[i]
            assert curr.visibility_ceiling >= prev.visibility_ceiling
            assert curr.competence_ceiling >= prev.competence_ceiling
            assert curr.relationships_ceiling >= prev.relationships_ceiling
            assert curr.leadership_ceiling >= prev.leadership_ceiling

    def test_phase_1_ceilings_are_low(self):
        """This is the critical fix — Phase 1 CANNOT produce 80% scores."""
        a = get_anchors(1)
        assert a.visibility_ceiling <= 20
        assert a.competence_ceiling <= 25
        assert a.relationships_ceiling <= 20
        assert a.leadership_ceiling <= 20

    def test_phase_9_ceilings_are_100(self):
        a = get_anchors(9)
        assert a.visibility_ceiling == 100
        assert a.competence_ceiling == 100

    def test_clamp_to_ceiling_caps_high_scores(self):
        result = clamp_to_ceiling(
            1,
            visibility=80,  # Way too high for Phase 1
            competence=90,
            relationships=70,
            leadership=60,
            ethics=95,
        )
        assert result["visibility"] <= 18
        assert result["competence"] <= 20
        assert result["relationships"] <= 18
        assert result["leadership"] <= 15
        assert result["ethics"] == 95  # Ethics NOT clamped

    def test_clamp_does_not_increase_scores(self):
        result = clamp_to_ceiling(
            1,
            visibility=5,
            competence=3,
            relationships=2,
            leadership=1,
            ethics=100,
        )
        assert result["visibility"] == 5
        assert result["competence"] == 3

    def test_get_anchors_invalid_phase(self):
        with pytest.raises(ValueError):
            get_anchors(0)
        with pytest.raises(ValueError):
            get_anchors(10)

    def test_optimal_readiness_ranges_are_sensible(self):
        for a in PHASE_ANCHORS:
            lo, hi = a.optimal_readiness
            assert lo < hi, f"Phase {a.phase}: optimal range is inverted"
            assert hi <= 100
            assert lo >= 0


class TestConsequences:
    """Tests for SimulationState tracking."""

    def test_initial_state(self):
        state = SimulationState()
        assert state.scores["visibility"] == 0
        assert state.scores["ethics"] == 100
        assert len(state.classified_decisions) == 0

    def test_apply_decision_updates_scores(self):
        state = SimulationState()
        option = DecisionOption(
            id="test_bold",
            label="Bold move",
            description="Go for it",
            score_impact=ScoreImpact(
                visibility=15, competence=8, leadership=10, ethics=-5,
            ),
            relationship_impacts=[],
        )
        state.apply_decision("test_dp", "test_bold", option)
        assert state.scores["visibility"] == 15
        assert state.scores["competence"] == 8
        assert state.scores["leadership"] == 10
        assert state.scores["ethics"] == 95  # 100 - 5

    def test_apply_multiple_decisions_accumulate(self):
        state = SimulationState()
        opt1 = DecisionOption(
            id="opt1", label="First", description="",
            score_impact=ScoreImpact(visibility=10),
            relationship_impacts=[],
        )
        opt2 = DecisionOption(
            id="opt2", label="Second", description="",
            score_impact=ScoreImpact(visibility=5, competence=8),
            relationship_impacts=[],
        )
        state.apply_decision("dp1", "opt1", opt1)
        state.apply_decision("dp2", "opt2", opt2)
        assert state.scores["visibility"] == 15
        assert state.scores["competence"] == 8

    def test_relationship_impacts(self):
        from financebench.configs.decision_points import RelationshipImpact
        state = SimulationState()
        option = DecisionOption(
            id="test", label="Test", description="",
            score_impact=ScoreImpact(),
            relationship_impacts=[
                RelationshipImpact("Karen Aldridge", -18, "Bypassed"),
                RelationshipImpact("David Chen", +10, "Impressed"),
            ],
        )
        state.apply_decision("dp", "test", option)
        assert state.relationship_deltas["Karen Aldridge"] == -18
        assert state.relationship_deltas["David Chen"] == 10

    def test_ethics_only_decreases(self):
        state = SimulationState()
        # Positive ethics impact should NOT increase from 100
        option = DecisionOption(
            id="good", label="Good", description="",
            score_impact=ScoreImpact(ethics=5),  # Positive
            relationship_impacts=[],
        )
        state.apply_decision("dp", "good", option)
        assert state.scores["ethics"] == 100  # Still 100, not 105

    def test_unlocks_tracked(self):
        state = SimulationState()
        option = DecisionOption(
            id="test", label="Test", description="",
            score_impact=ScoreImpact(),
            relationship_impacts=[],
            unlocks="David begins mentoring Riley.",
        )
        state.apply_decision("dp", "test", option)
        assert "David begins mentoring Riley." in state.unlocks

    def test_relationship_context_generation(self):
        state = SimulationState()
        state.relationship_deltas["Karen Aldridge"] = -15
        state.relationship_deltas["David Chen"] = 12
        context = state.get_relationship_context()
        assert "hostile" in context.lower() or "distrustful" in context.lower()
        assert "ally" in context.lower()

    def test_to_dict_is_serializable(self):
        import json
        state = SimulationState()
        state.fired_events.add("test_event")
        state.unlocks.append("something")
        data = state.to_dict()
        # Should be JSON serializable
        json_str = json.dumps(data)
        assert "test_event" in json_str


class TestScoringIntegration:
    """Tests for scoring.py changes (no API calls needed)."""

    def test_extract_json_with_markdown(self):
        from financebench.scoring import _extract_json
        text = 'Here is the result:\n```json\n{"key": "value"}\n```\nDone.'
        result = _extract_json(text)
        assert '"key"' in result
        assert '"value"' in result

    def test_extract_json_with_multiple_fences(self):
        from financebench.scoring import _extract_json
        text = (
            'Some ```code``` here and '
            '```json\n{"scores": {"visibility": 10}}\n```'
        )
        result = _extract_json(text)
        assert '"scores"' in result

    def test_extract_json_raw_braces(self):
        from financebench.scoring import _extract_json
        text = 'Here is: {"a": 1}'
        result = _extract_json(text)
        assert result == '{"a": 1}'

    def test_clamp_modifier_bounds(self):
        from financebench.scoring import _clamp_modifier
        assert _clamp_modifier(10) == 5
        assert _clamp_modifier(-10) == -5
        assert _clamp_modifier(3) == 3
        assert _clamp_modifier(0) == 0

    def test_phase_evaluation_to_dict(self):
        from financebench.scoring import PhaseEvaluation, PhaseScores
        ev = PhaseEvaluation(
            phase=1,
            name="Test",
            scores=PhaseScores(
                visibility=10, competence=15,
                relationships=8, leadership=5, ethics=95,
            ),
            classified_decisions={"p1_discovery": "p1_bold"},
        )
        d = ev.to_dict()
        assert d["phase"] == 1
        assert "promotion_readiness" in d["scores"]
        assert d["classified_decisions"]["p1_discovery"] == "p1_bold"

    def test_promotion_readiness_math(self):
        from financebench.scoring import PhaseScores
        # New formula: ethics is penalty only, not contributor
        # base = 10*0.30 + 20*0.30 + 10*0.20 + 10*0.20
        #      = 3 + 6 + 2 + 2 = 13
        # ethics=100 → penalty=0
        # readiness = 13
        scores = PhaseScores(
            visibility=10, competence=20,
            relationships=10, leadership=10, ethics=100,
        )
        assert scores.promotion_readiness == 13
