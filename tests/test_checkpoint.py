"""Tests for checkpoint / resume system.

Verifies:
  - Save and load round-trips
  - Atomic writes (no corruption on crash)
  - Find latest checkpoint
  - SimulationState serialization/deserialization
  - Evaluation restoration
  - Checkpoint deletion on completion
"""

import json
import pytest
from pathlib import Path

from financebench.checkpoint import (
    save_checkpoint,
    load_checkpoint,
    find_latest_checkpoint,
    restore_simulation_state,
    restore_evaluations,
    delete_checkpoint,
)
from financebench.consequences import SimulationState


@pytest.fixture
def tmp_checkpoint_dir(tmp_path):
    """Provide a temporary directory for checkpoints."""
    d = tmp_path / "checkpoints"
    d.mkdir()
    return d


@pytest.fixture
def sample_state():
    """Build a SimulationState with non-default values."""
    state = SimulationState()
    state.scores["visibility"] = 15
    state.scores["competence"] = 20
    state.scores["relationships"] = 8
    state.scores["leadership"] = 10
    state.scores["ethics"] = 95
    state.relationship_deltas["Karen Aldridge"] = -5
    state.relationship_deltas["David Chen"] = 3
    state.classified_decisions["p1_discovery"] = "p1_bold"
    state.fired_events.add("Recruiter Call")
    state.pending_consequences[3] = ["Riley was bold in Phase 1."]
    state.unlocks.append("David noticed Riley's initiative.")
    return state


@pytest.fixture
def sample_evaluations():
    """Evaluation dicts as they'd appear in a checkpoint."""
    return [
        {
            "phase": 1,
            "name": "The Discovery",
            "scores": {
                "visibility": 15,
                "competence": 20,
                "relationships": 8,
                "leadership": 10,
                "ethics": 95,
            },
            "narrative": "Riley showed initiative.",
            "key_decisions": ["Presented analysis directly"],
        },
        {
            "phase": 2,
            "name": "The First Test",
            "scores": {
                "visibility": 25,
                "competence": 30,
                "relationships": 12,
                "leadership": 18,
                "ethics": 95,
            },
            "narrative": "Riley navigated the challenge.",
            "key_decisions": ["Built coalition with Priya"],
        },
    ]


class TestSaveAndLoad:
    def test_roundtrip(self, tmp_checkpoint_dir, sample_state):
        path = save_checkpoint(
            run_id="test-run-001",
            variant="neutral",
            completed_phases=[1, 2],
            evaluations=[{"phase": 1, "scores": {}}],
            memory_summaries={"Riley": ["mem1", "mem2"]},
            simulation_state=sample_state,
            run_meta={"start_time": "2026-02-19"},
            directory=tmp_checkpoint_dir,
        )

        assert path.exists()
        loaded = load_checkpoint("test-run-001", tmp_checkpoint_dir)
        assert loaded is not None
        assert loaded["run_id"] == "test-run-001"
        assert loaded["variant"] == "neutral"
        assert loaded["completed_phases"] == [1, 2]
        assert loaded["memory_summaries"]["Riley"] == ["mem1", "mem2"]

    def test_missing_checkpoint_returns_none(self, tmp_checkpoint_dir):
        result = load_checkpoint("nonexistent", tmp_checkpoint_dir)
        assert result is None

    def test_completed_phases_sorted(self, tmp_checkpoint_dir, sample_state):
        save_checkpoint(
            run_id="sort-test",
            variant="neutral",
            completed_phases=[3, 1, 2],
            evaluations=[],
            memory_summaries={},
            simulation_state=sample_state,
            run_meta={},
            directory=tmp_checkpoint_dir,
        )
        loaded = load_checkpoint("sort-test", tmp_checkpoint_dir)
        assert loaded["completed_phases"] == [1, 2, 3]

    def test_atomic_write_no_tmp_left(self, tmp_checkpoint_dir, sample_state):
        save_checkpoint(
            run_id="atomic-test",
            variant="neutral",
            completed_phases=[1],
            evaluations=[],
            memory_summaries={},
            simulation_state=sample_state,
            run_meta={},
            directory=tmp_checkpoint_dir,
        )
        # No .tmp file should remain
        tmp_files = list(tmp_checkpoint_dir.glob("*.tmp"))
        assert tmp_files == []

    def test_overwrite_updates(self, tmp_checkpoint_dir, sample_state):
        # Save once
        save_checkpoint(
            run_id="overwrite",
            variant="neutral",
            completed_phases=[1],
            evaluations=[],
            memory_summaries={},
            simulation_state=sample_state,
            run_meta={},
            directory=tmp_checkpoint_dir,
        )
        # Save again with more phases
        save_checkpoint(
            run_id="overwrite",
            variant="neutral",
            completed_phases=[1, 2, 3],
            evaluations=[],
            memory_summaries={},
            simulation_state=sample_state,
            run_meta={},
            directory=tmp_checkpoint_dir,
        )
        loaded = load_checkpoint("overwrite", tmp_checkpoint_dir)
        assert loaded["completed_phases"] == [1, 2, 3]


class TestFindLatest:
    def test_finds_most_recent(self, tmp_checkpoint_dir, sample_state):
        import time

        for rid in ["run-old", "run-new"]:
            save_checkpoint(
                run_id=rid,
                variant="neutral",
                completed_phases=[1],
                evaluations=[],
                memory_summaries={},
                simulation_state=sample_state,
                run_meta={},
                directory=tmp_checkpoint_dir,
            )
            time.sleep(0.05)  # Ensure distinct mtime

        latest = find_latest_checkpoint(tmp_checkpoint_dir)
        assert latest is not None
        assert latest["run_id"] == "run-new"

    def test_empty_dir_returns_none(self, tmp_checkpoint_dir):
        result = find_latest_checkpoint(tmp_checkpoint_dir)
        assert result is None

    def test_nonexistent_dir_returns_none(self, tmp_path):
        result = find_latest_checkpoint(tmp_path / "nope")
        assert result is None


class TestRestoreSimulationState:
    def test_roundtrip_state(self, sample_state):
        data = {"simulation_state": sample_state.to_dict()}
        restored = restore_simulation_state(data)

        assert restored.scores["visibility"] == 15
        assert restored.scores["competence"] == 20
        assert restored.scores["ethics"] == 95
        assert restored.relationship_deltas["Karen Aldridge"] == -5
        assert restored.relationship_deltas["David Chen"] == 3
        assert restored.classified_decisions["p1_discovery"] == "p1_bold"
        assert "Recruiter Call" in restored.fired_events
        assert restored.pending_consequences[3] == [
            "Riley was bold in Phase 1."
        ]
        assert "David noticed Riley's initiative." in restored.unlocks

    def test_empty_state_gets_defaults(self):
        restored = restore_simulation_state({})
        assert restored.scores["ethics"] == 100
        assert restored.scores["visibility"] == 0
        assert len(restored.fired_events) == 0


class TestRestoreEvaluations:
    def test_roundtrip_evaluations(self, sample_evaluations):
        data = {"evaluations": sample_evaluations}
        evals = restore_evaluations(data)

        assert len(evals) == 2
        assert evals[0].phase == 1
        assert evals[0].name == "The Discovery"
        assert evals[0].scores.visibility == 15
        assert evals[0].scores.competence == 20
        assert evals[0].scores.ethics == 95
        assert evals[0].narrative == "Riley showed initiative."
        assert evals[0].key_decisions == ["Presented analysis directly"]

        assert evals[1].phase == 2
        assert evals[1].scores.relationships == 12

    def test_empty_evaluations(self):
        evals = restore_evaluations({})
        assert evals == []

    def test_readiness_recalculated(self, sample_evaluations):
        """Readiness is a computed property, not stored."""
        evals = restore_evaluations({"evaluations": sample_evaluations})
        # Phase 1: vis=15*0.30 + comp=20*0.30 + rel=8*0.20 + lead=10*0.20
        #        = 4.5 + 6 + 1.6 + 2 = 14.1 -> 14
        # ethics=95 -> penalty = 5*0.20 = 1 -> 14-1 = 13
        assert evals[0].scores.promotion_readiness == 13


class TestDeleteCheckpoint:
    def test_delete_existing(self, tmp_checkpoint_dir, sample_state):
        save_checkpoint(
            run_id="to-delete",
            variant="neutral",
            completed_phases=[1],
            evaluations=[],
            memory_summaries={},
            simulation_state=sample_state,
            run_meta={},
            directory=tmp_checkpoint_dir,
        )
        assert delete_checkpoint("to-delete", tmp_checkpoint_dir)
        assert load_checkpoint("to-delete", tmp_checkpoint_dir) is None

    def test_delete_nonexistent_returns_false(self, tmp_checkpoint_dir):
        assert not delete_checkpoint("nope", tmp_checkpoint_dir)


class TestSimulationStateFromDict:
    def test_fired_events_are_set(self):
        data = {"fired_events": ["A", "B", "A"]}
        state = SimulationState.from_dict(data)
        assert isinstance(state.fired_events, set)
        assert state.fired_events == {"A", "B"}

    def test_pending_consequences_keys_are_int(self):
        data = {"pending_consequences": {"3": ["text"], "5": ["more"]}}
        state = SimulationState.from_dict(data)
        assert 3 in state.pending_consequences
        assert 5 in state.pending_consequences
        assert "3" not in state.pending_consequences
