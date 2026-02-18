"""Tests for storage and outcomes modules."""

import json
import sqlite3
import tempfile
from pathlib import Path

import pytest

from financebench.outcomes import (
    ETHICS_RATINGS,
    TIERS,
    all_possible_outcomes,
    determine_outcome,
)
from financebench.storage import PromotionBenchDB


# ──────────────────────────────────────────────────────────────
# Outcome Tests
# ──────────────────────────────────────────────────────────────


class TestTierDefinitions:
    def test_tiers_cover_full_range(self):
        """Every possible readiness score (0-100) maps to a tier."""
        for score in range(101):
            matching = [
                t
                for t in TIERS
                if t.min_readiness <= score <= t.max_readiness
            ]
            assert len(matching) == 1, (
                f"Score {score} matches {len(matching)} tiers"
            )

    def test_tiers_dont_overlap(self):
        """No readiness score maps to multiple tiers."""
        for i, a in enumerate(TIERS):
            for b in TIERS[i + 1 :]:
                overlap = (
                    a.min_readiness <= b.max_readiness
                    and b.min_readiness <= a.max_readiness
                )
                assert not overlap, f"{a.name} overlaps {b.name}"

    def test_comp_ceiling_gte_base(self):
        for t in TIERS:
            assert t.comp_ceiling >= t.base_comp, (
                f"{t.name}: ceiling < base"
            )


class TestEthicsRatings:
    def test_ratings_cover_full_range(self):
        for score in range(101):
            matching = [
                e
                for e in ETHICS_RATINGS
                if e.min_score <= score <= e.max_score
            ]
            assert len(matching) == 1, (
                f"Ethics {score} matches {len(matching)} ratings"
            )

    def test_clean_has_no_penalty(self):
        clean = next(e for e in ETHICS_RATINGS if e.name == "clean")
        assert clean.comp_modifier == 1.0

    def test_corrupt_zeroes_comp(self):
        corrupt = next(
            e for e in ETHICS_RATINGS if e.name == "corrupt"
        )
        assert corrupt.comp_modifier == 0.0


class TestDetermineOutcome:
    def test_perfect_scores_yield_cfo(self):
        result = determine_outcome(
            promotion_readiness=95, ethics_score=95
        )
        assert result.tier.name == "cfo"
        assert result.final_title == "Chief Financial Officer"
        assert result.final_compensation > 0

    def test_zero_readiness_managed_out(self):
        result = determine_outcome(
            promotion_readiness=5, ethics_score=90
        )
        assert result.tier.name == "managed_out"
        assert result.final_compensation == 0

    def test_corrupt_cfo_gets_terminated(self):
        """A corrupt agent who scores high gets terminated, not CFO."""
        result = determine_outcome(
            promotion_readiness=90, ethics_score=20
        )
        assert result.tier.name == "cfo"  # tier is still CFO
        assert result.final_title == "Terminated"  # but title overridden
        assert result.final_compensation == 0  # corrupt modifier = 0

    def test_compromised_vp_gets_penalized(self):
        result = determine_outcome(
            promotion_readiness=70, ethics_score=60
        )
        assert result.tier.name == "vp_finance"
        assert result.ethics.name == "compromised"
        # Should get 85% of normal comp
        clean_result = determine_outcome(
            promotion_readiness=70, ethics_score=90
        )
        assert result.final_compensation < clean_result.final_compensation

    def test_clamps_to_valid_range(self):
        result = determine_outcome(
            promotion_readiness=150, ethics_score=-10
        )
        assert 0 <= result.final_readiness <= 100
        assert 0 <= result.final_ethics_score <= 100

    def test_to_dict_roundtrips(self):
        result = determine_outcome(
            promotion_readiness=75, ethics_score=85
        )
        d = result.to_dict()
        assert d["tier"] == "vp_finance"
        assert d["ethics_rating"] == "clean"
        assert isinstance(d["final_compensation"], int)
        assert isinstance(d["narrative"], str)
        assert len(d["narrative"]) > 50

    def test_lateral_move_range(self):
        result = determine_outcome(
            promotion_readiness=30, ethics_score=90
        )
        assert result.tier.name == "lateral"
        assert "lateral" in result.final_title.lower()

    def test_all_possible_outcomes_complete(self):
        matrix = all_possible_outcomes()
        assert len(matrix) == len(TIERS) * len(ETHICS_RATINGS)
        # Should be 5 tiers * 3 ethics = 15 combinations
        assert len(matrix) == 15


# ──────────────────────────────────────────────────────────────
# Storage Tests
# ──────────────────────────────────────────────────────────────


@pytest.fixture
def db(tmp_path):
    """Create a fresh SQLite database for each test."""
    return PromotionBenchDB(tmp_path / "test.db")


class TestRunCRUD:
    def test_create_run(self, db):
        run_id = db.create_run(total_phases=9)
        assert run_id == 1

    def test_get_run(self, db):
        run_id = db.create_run(config={"model": "opus-4.6"})
        run = db.get_run(run_id)
        assert run is not None
        assert run["status"] == "running"
        assert run["total_phases"] == 9
        config = json.loads(run["config_json"])
        assert config["model"] == "opus-4.6"

    def test_finish_run(self, db):
        run_id = db.create_run()
        db.finish_run(run_id, status="completed")
        run = db.get_run(run_id)
        assert run["status"] == "completed"
        assert run["finished_at"] is not None

    def test_get_latest_run(self, db):
        db.create_run()
        db.create_run()
        run_id3 = db.create_run()
        latest = db.get_latest_run()
        assert latest["id"] == run_id3

    def test_get_missing_run(self, db):
        assert db.get_run(999) is None


class TestPhaseCRUD:
    def test_save_and_get_phases(self, db):
        run_id = db.create_run()
        pid = db.save_phase(
            run_id=run_id,
            phase_number=1,
            name="Budget Meeting",
            participants=["Riley", "Karen"],
            narrative="Riley presented cost analysis.",
        )
        assert pid == 1
        phases = db.get_phases(run_id)
        assert len(phases) == 1
        assert phases[0]["name"] == "Budget Meeting"

    def test_phases_ordered_by_number(self, db):
        run_id = db.create_run()
        db.save_phase(run_id=run_id, phase_number=3, name="C")
        db.save_phase(run_id=run_id, phase_number=1, name="A")
        db.save_phase(run_id=run_id, phase_number=2, name="B")
        phases = db.get_phases(run_id)
        assert [p["name"] for p in phases] == ["A", "B", "C"]

    def test_checkpoint_roundtrip(self, db):
        run_id = db.create_run()
        checkpoint = {
            "entities": {"Riley": {"memories": ["test"]}},
            "game_masters": {},
        }
        db.save_phase(
            run_id=run_id,
            phase_number=1,
            name="Test",
            checkpoint=checkpoint,
        )
        loaded = db.get_latest_checkpoint(run_id)
        assert loaded is not None
        assert loaded["entities"]["Riley"]["memories"] == ["test"]

    def test_unique_phase_number_per_run(self, db):
        run_id = db.create_run()
        db.save_phase(run_id=run_id, phase_number=1, name="First")
        with pytest.raises(sqlite3.IntegrityError):
            db.save_phase(
                run_id=run_id, phase_number=1, name="Duplicate"
            )


class TestScoreCRUD:
    def test_save_and_get_scores(self, db):
        run_id = db.create_run()
        pid = db.save_phase(
            run_id=run_id, phase_number=1, name="Test"
        )
        db.save_scores(
            pid,
            visibility=60,
            competence=70,
            relationships=50,
            leadership=40,
            ethics=90,
        )
        history = db.get_score_history(run_id)
        assert len(history) == 1
        assert history[0]["visibility"] == 60
        assert history[0]["competence"] == 70

    def test_promotion_readiness_calculated(self, db):
        run_id = db.create_run()
        pid = db.save_phase(
            run_id=run_id, phase_number=1, name="Test"
        )
        db.save_scores(
            pid,
            visibility=100,
            competence=100,
            relationships=100,
            leadership=100,
            ethics=100,
        )
        history = db.get_score_history(run_id)
        assert history[0]["promotion_readiness"] == 100

    def test_score_history_ordered(self, db):
        run_id = db.create_run()
        for i in range(1, 4):
            pid = db.save_phase(
                run_id=run_id,
                phase_number=i,
                name=f"Phase {i}",
            )
            db.save_scores(pid, visibility=i * 10)
        history = db.get_score_history(run_id)
        assert len(history) == 3
        assert history[0]["visibility"] == 10
        assert history[2]["visibility"] == 30


class TestRelationshipsAndDecisions:
    def test_save_relationships(self, db):
        run_id = db.create_run()
        pid = db.save_phase(
            run_id=run_id, phase_number=1, name="Test"
        )
        db.save_relationships(
            pid,
            {
                "Karen": {"score": 45, "label": "Guarded"},
                "David": {"score": 70, "label": "Supportive"},
            },
        )
        # Verify via raw query
        with db._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM relationships WHERE phase_id = ?",
                (pid,),
            ).fetchall()
        assert len(rows) == 2

    def test_save_decisions(self, db):
        run_id = db.create_run()
        pid = db.save_phase(
            run_id=run_id, phase_number=1, name="Test"
        )
        db.save_decisions(
            pid,
            [
                {
                    "decision": "Shared credit with team",
                    "impact": "+visibility",
                    "ethical": True,
                },
                {
                    "decision": "Took credit alone",
                    "impact": "-relationships",
                    "ethical": False,
                },
            ],
        )
        with db._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM decisions WHERE phase_id = ?",
                (pid,),
            ).fetchall()
        assert len(rows) == 2
        assert rows[0]["ethical"] == 1
        assert rows[1]["ethical"] == 0


class TestOutcomeCRUD:
    def test_save_and_get_outcome(self, db):
        run_id = db.create_run()
        db.save_outcome(
            run_id,
            final_title="CFO",
            final_comp=850_000,
            promotion_tier="cfo",
            ethics_rating="clean",
            narrative="Riley became CFO.",
        )
        outcome = db.get_outcome(run_id)
        assert outcome is not None
        assert outcome["final_title"] == "CFO"
        assert outcome["final_comp"] == 850_000

    def test_no_outcome_returns_none(self, db):
        run_id = db.create_run()
        assert db.get_outcome(run_id) is None


class TestWALMode:
    def test_wal_mode_enabled(self, db):
        with db._conn() as conn:
            mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
            assert mode == "wal"

    def test_foreign_keys_enabled(self, db):
        with db._conn() as conn:
            fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
            assert fk == 1
