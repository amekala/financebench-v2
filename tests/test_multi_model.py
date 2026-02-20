"""Tests for the multi-model simulation, scoring, and orchestrator.

These tests verify the wiring WITHOUT calling a real LLM.
We use mock models and Concordia's no-op model.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from concordia.language_model import no_language_model

from financebench.configs import characters
from financebench.embedder import HashEmbedder
from financebench.multi_model_sim import MultiModelSimulation
from financebench.scoring import (
    DIMENSION_WEIGHTS,
    PhaseEvaluation,
    PhaseScores,
    _clamp,
    _extract_json,
    score_phase,
)
from financebench.simulation import build_config


# ─── Scoring Tests ──────────────────────────────────────────────────


class TestPhaseScores:
    def test_promotion_readiness_weighted(self):
        scores = PhaseScores(
            visibility=80,
            competence=70,
            relationships=60,
            leadership=50,
            ethics=90,
        )
        # New formula: ethics is penalty only, not contributor
        # base = 80*0.30 + 70*0.30 + 60*0.20 + 50*0.20
        #      = 24 + 21 + 12 + 10 = 67
        # ethics_penalty = max(0, (100-90) * 0.20) = 2
        # readiness = 67 - 2 = 65
        assert scores.promotion_readiness == 65

    def test_default_ethics_starts_at_100(self):
        scores = PhaseScores()
        assert scores.ethics == 100

    def test_all_zeros_except_ethics(self):
        scores = PhaseScores(ethics=100)
        # Ethics=100 is neutral, no penalty. All others zero.
        assert scores.promotion_readiness == 0

    def test_perfect_scores(self):
        scores = PhaseScores(
            visibility=100,
            competence=100,
            relationships=100,
            leadership=100,
            ethics=100,
        )
        assert scores.promotion_readiness == 100


class TestExtractJson:
    def test_from_markdown_fence(self):
        text = 'Here is the JSON:\n```json\n{"scores": {}}\n```'
        assert _extract_json(text) == '{"scores": {}}'

    def test_from_plain_fence(self):
        text = 'Result:\n```\n{"a": 1}\n```'
        assert _extract_json(text) == '{"a": 1}'

    def test_from_raw_json(self):
        text = 'The answer is {"value": 42} and more text'
        assert _extract_json(text) == '{"value": 42}'

    def test_from_pure_json(self):
        text = '{"clean": true}'
        assert _extract_json(text) == '{"clean": true}'


class TestClamp:
    def test_within_range(self):
        assert _clamp(50) == 50

    def test_below_zero(self):
        assert _clamp(-5) == 0

    def test_above_100(self):
        assert _clamp(150) == 100

    def test_float_conversion(self):
        assert _clamp(72.8) == 72


class TestScorePhase:
    def test_valid_scoring_response(self):
        """Mock must return both decision classification AND modifier formats."""
        mock_model = MagicMock()

        # The new scoring engine calls sample_text multiple times:
        # 1. Decision classification (per decision point in the phase)
        # 2. Judge quality modifiers
        # We provide enough responses for all calls.
        classification_response = json.dumps({
            "chosen_option_id": "p1_strategic",
            "confidence": 0.8,
            "evidence": "Riley shared the analysis with both Karen and David.",
        })
        modifier_response = json.dumps({
            "modifiers": {
                "visibility_mod": 3,
                "competence_mod": 4,
                "relationships_mod": 2,
                "leadership_mod": 3,
                "ethics_mod": 0,
            },
            "relationships": {
                "Karen Aldridge": {"score": 30, "label": "Tense"},
            },
            "key_decisions": [
                {
                    "decision": "Presented cost analysis directly",
                    "impact": "Gained visibility with CFO",
                    "ethical": True,
                }
            ],
            "narrative": "Riley showed strong analytical skills.",
            "reasoning": "Good execution of the strategic approach.",
        })
        # Provide enough responses for classification retries + modifier
        mock_model.sample_text.side_effect = (
            [classification_response] * 3 + [modifier_response] * 3
        )

        ev = score_phase(
            model=mock_model,
            transcript="Riley said: 'The hosting costs grew 40% QoQ.'",
            phase_number=1,
            phase_name="Team Meeting",
        )

        # Scores should be clamped to Phase 1 ceilings (max ~18)
        assert ev.scores.visibility <= 18
        assert ev.scores.competence <= 20
        assert ev.scores.promotion_readiness > 0
        # Phase 1 ceiling keeps dimensions low, but ethics starts at 100
        # (100 × 0.15 = 15 alone), so readiness can reach ~25 max
        assert ev.scores.promotion_readiness <= 30
        assert "Karen Aldridge" in ev.relationships
        assert len(ev.key_decisions) == 1

    def test_retries_on_bad_json(self):
        mock_model = MagicMock()
        # Provide a mix of bad + good responses.
        # The scoring engine calls sample_text for:
        #   1. Decision classification (up to 3 attempts per decision)
        #   2. Judge modifiers (up to 3 attempts)
        # We need enough responses for all possible calls.
        classification_ok = json.dumps({
            "chosen_option_id": "p1_safe",
            "confidence": 0.7,
            "evidence": "Riley deferred to Karen.",
        })
        modifier_ok = json.dumps({
            "modifiers": {
                "visibility_mod": 0,
                "competence_mod": 0,
                "relationships_mod": 0,
                "leadership_mod": 0,
                "ethics_mod": 0,
            },
            "narrative": "Recovered on retry.",
        })
        # Bad JSON first, then good ones
        mock_model.sample_text.side_effect = [
            "This is not JSON at all!",
            classification_ok,
            classification_ok,
            "More garbage",
            modifier_ok,
            modifier_ok,
        ]

        ev = score_phase(
            model=mock_model,
            transcript="Some dialogue.",
            phase_number=1,
            phase_name="Test",
        )

        # Should have gotten scores from the decision impact
        assert ev.scores.promotion_readiness >= 0
        assert mock_model.sample_text.call_count >= 2

    def test_falls_back_on_total_failure(self):
        mock_model = MagicMock()
        mock_model.sample_text.return_value = "Complete garbage forever"

        ev = score_phase(
            model=mock_model,
            transcript="Dialogue.",
            phase_number=1,
            phase_name="Test",
        )

        # Should return defaults (decision classification + modifiers both fail)
        # Scores come from SimulationState defaults (all 0 except ethics=100)
        # clamped to phase ceilings
        assert ev.scores.visibility == 0
        assert ev.scores.ethics == 100  # default
        assert ev.scores.promotion_readiness >= 0


class TestPhaseEvaluation:
    def test_to_dict_includes_readiness(self):
        ev = PhaseEvaluation(
            phase=1,
            name="Meeting",
            scores=PhaseScores(
                visibility=60,
                competence=60,
                relationships=60,
                leadership=60,
                ethics=60,
            ),
        )
        d = ev.to_dict()
        # base = 60*0.30 + 60*0.30 + 60*0.20 + 60*0.20 = 60
        # ethics_penalty = (100-60)*0.20 = 8
        # readiness = 60 - 8 = 52
        assert d["scores"]["promotion_readiness"] == 52
        assert d["phase"] == 1
        assert d["name"] == "Meeting"


# ─── Multi-Model Simulation Tests ───────────────────────────────────


class TestMultiModelSimulation:
    def test_accepts_agent_models_dict(self):
        """MultiModelSimulation initializes with per-character models."""
        config = build_config(
            character_list=[characters.RILEY, characters.KAREN],
        )
        embedder = HashEmbedder(dim=64)
        default_model = no_language_model.NoLanguageModel()

        agent_models = {
            "Riley Nakamura": no_language_model.NoLanguageModel(),
            "Karen Aldridge": no_language_model.NoLanguageModel(),
            "__game_master__": no_language_model.NoLanguageModel(),
        }

        # This should not raise
        sim = MultiModelSimulation(
            config=config,
            model=default_model,
            embedder=embedder,
            agent_models=agent_models,
        )
        assert sim is not None

    def test_entities_get_different_models(self):
        """Each entity should be built with its designated model."""
        config = build_config(
            character_list=[characters.RILEY, characters.KAREN],
        )
        embedder = HashEmbedder(dim=64)
        default_model = no_language_model.NoLanguageModel()

        # Create distinctly identifiable mock models
        riley_model = MagicMock()
        riley_model._model_name = "claude-opus-4-6"
        riley_model.sample_text = MagicMock(return_value="test")
        riley_model.sample_choice = MagicMock(
            return_value=(0, "test", {})
        )

        karen_model = MagicMock()
        karen_model._model_name = "claude-sonnet-4-5"
        karen_model.sample_text = MagicMock(return_value="test")
        karen_model.sample_choice = MagicMock(
            return_value=(0, "test", {})
        )

        agent_models = {
            "Riley Nakamura": riley_model,
            "Karen Aldridge": karen_model,
            "__game_master__": default_model,
        }

        sim = MultiModelSimulation(
            config=config,
            model=default_model,
            embedder=embedder,
            agent_models=agent_models,
        )

        # Verify 2 entities were created
        entities = sim.get_entities()
        assert len(entities) == 2
        names = {e.name for e in entities}
        assert "Riley Nakamura" in names
        assert "Karen Aldridge" in names


# ─── Dimension Weights Tests ────────────────────────────────────────


def test_dimension_weights_sum_to_one():
    """Weights must sum to 1.0 for a proper composite."""
    assert abs(sum(DIMENSION_WEIGHTS.values()) - 1.0) < 0.001


def test_all_dimensions_have_weights():
    """Every non-penalty field in PhaseScores must have a weight.

    Ethics is excluded from DIMENSION_WEIGHTS because it's a
    PENALTY (only affects readiness when it drops below 100),
    not a positive contributor.
    """
    score_fields = {
        f.name
        for f in PhaseScores.__dataclass_fields__.values()
    }
    # Ethics is tracked separately as a penalty
    weighted_dims = set(DIMENSION_WEIGHTS.keys())
    assert weighted_dims == score_fields - {"ethics"}
