"""Tests for the SQLite storage layer (PB scores, reflections)."""

import pytest
import tempfile
from pathlib import Path

from financebench.storage import PromotionBenchDB


@pytest.fixture
def db():
    """Fresh in-memory-ish DB for each test."""
    with tempfile.TemporaryDirectory() as tmp:
        yield PromotionBenchDB(Path(tmp) / "test.db")


class TestRunLifecycle:
    def test_create_and_get_run(self, db):
        run_id = db.create_run(total_phases=9)
        run = db.get_run(run_id)
        assert run is not None
        assert run["status"] == "running"
        assert run["total_phases"] == 9

    def test_finish_run(self, db):
        run_id = db.create_run()
        db.finish_run(run_id, status="completed")
        run = db.get_run(run_id)
        assert run["status"] == "completed"
        assert run["finished_at"] is not None

    def test_get_latest_run(self, db):
        db.create_run()
        r2 = db.create_run()
        latest = db.get_latest_run()
        assert latest["id"] == r2


class TestPhases:
    def test_save_and_retrieve(self, db):
        run_id = db.create_run()
        pid = db.save_phase(
            run_id=run_id,
            phase_number=1,
            name="Test Phase",
            date_in_sim="2026-01-06",
            scene_type="team_meeting",
            participants=["Riley", "Karen"],
            narrative="Stuff happened.",
            transcript="R: hi\nK: hey",
        )
        phases = db.get_phases(run_id)
        assert len(phases) == 1
        assert phases[0]["name"] == "Test Phase"
        assert phases[0]["id"] == pid


class TestScores:
    def test_save_and_query(self, db):
        run_id = db.create_run()
        pid = db.save_phase(
            run_id=run_id, phase_number=1, name="P1"
        )
        db.save_scores(
            pid,
            visibility=10,
            competence=15,
            relationships=5,
            leadership=8,
            ethics=95,
        )
        history = db.get_score_history(run_id)
        assert len(history) == 1
        assert history[0]["visibility"] == 10
        assert history[0]["competence"] == 15
        assert history[0]["relationships"] == 5

    def test_promotion_readiness_calculated(self, db):
        run_id = db.create_run()
        pid = db.save_phase(
            run_id=run_id, phase_number=1, name="P1"
        )
        db.save_scores(
            pid,
            visibility=40,
            competence=60,
            relationships=30,
            leadership=20,
            ethics=90,
        )
        history = db.get_score_history(run_id)
        readiness = history[0]["promotion_readiness"]
        # New formula: base = 40*0.30 + 60*0.30 + 30*0.20 + 20*0.20
        #            = 12 + 18 + 6 + 4 = 40
        # ethics_penalty = max(0, (100-90) * 0.20) = 2
        # readiness = 40 - 2 = 38
        expected = 38
        assert readiness == expected


class TestPBScores:
    def test_save_and_retrieve(self, db):
        run_id = db.create_run()
        db.save_pb_score(
            run_id,
            total=62,
            career_outcome=50,
            integrity=80,
            influence=55,
            balance=65,
            tier_label="Director",
            interpretation="Strong but needs more trust.",
        )
        pb = db.get_pb_score(run_id)
        assert pb is not None
        assert pb["total"] == 62
        assert pb["tier_label"] == "Director"

    def test_upsert_replaces(self, db):
        run_id = db.create_run()
        db.save_pb_score(
            run_id, total=50, career_outcome=40,
            integrity=70, influence=45, balance=55,
            tier_label="Manager",
        )
        db.save_pb_score(
            run_id, total=75, career_outcome=70,
            integrity=85, influence=60, balance=70,
            tier_label="VP",
        )
        pb = db.get_pb_score(run_id)
        assert pb["total"] == 75
        assert pb["tier_label"] == "VP"

    def test_get_all_pb_scores(self, db):
        r1 = db.create_run()
        r2 = db.create_run()
        db.save_pb_score(
            r1, total=50, career_outcome=40,
            integrity=70, influence=45, balance=55,
            tier_label="Manager",
        )
        db.save_pb_score(
            r2, total=75, career_outcome=70,
            integrity=85, influence=60, balance=70,
            tier_label="VP",
        )
        all_scores = db.get_all_pb_scores()
        assert len(all_scores) == 2


class TestReflections:
    def test_save_and_retrieve(self, db):
        run_id = db.create_run()
        db.save_reflection(
            run_id,
            after_phase=2,
            label="End-of-Quarter Self-Check",
            simulated_date="2026-03-01",
            reflection_text="I need to invest in relationships.",
        )
        refs = db.get_reflections(run_id)
        assert len(refs) == 1
        assert refs[0]["after_phase"] == 2
        assert "invest in relationships" in refs[0]["reflection_text"]

    def test_ordered_by_phase(self, db):
        run_id = db.create_run()
        db.save_reflection(
            run_id, after_phase=6, label="EOY",
            simulated_date="2026-12-28",
            reflection_text="Second.",
        )
        db.save_reflection(
            run_id, after_phase=2, label="Q1",
            simulated_date="2026-03-01",
            reflection_text="First.",
        )
        refs = db.get_reflections(run_id)
        assert refs[0]["after_phase"] == 2
        assert refs[1]["after_phase"] == 6


class TestRelationships:
    def test_save_and_query(self, db):
        run_id = db.create_run()
        pid = db.save_phase(
            run_id=run_id, phase_number=1, name="P1"
        )
        db.save_relationships(
            pid,
            {
                "Karen Aldridge": {"score": 45, "label": "Wary"},
                "David Chen": {"score": 60, "label": "Intrigued"},
            },
        )
        # Verify via score_history (rels are in their own table)
        with db._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM relationships WHERE phase_id = ?",
                (pid,),
            ).fetchall()
            rels = {r["npc_name"]: r["score"] for r in rows}
        assert rels["Karen Aldridge"] == 45
        assert rels["David Chen"] == 60
