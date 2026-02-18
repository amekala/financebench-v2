"""SQLite storage layer for PromotionBench.

Stores structured simulation data:
  - Runs (each simulation execution)
  - Phases (per-phase results)
  - Scores (5-dimension scoring per phase)
  - Relationships (inter-character scores per phase)
  - Decisions (key decisions per phase)
  - Transcripts (full phase dialogue)
  - Outcomes (final simulation results)

Concordia checkpoints (agent memory states) are stored as
JSON blobs — they're opaque to us but critical for resuming
simulations between phases.

The dashboard JSON (docs/data/phases.json) is a DERIVED VIEW
generated from this database, not a source of truth.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Generator

DEFAULT_DB_PATH = Path("promotionbench.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at      TEXT NOT NULL DEFAULT (datetime('now')),
    finished_at     TEXT,
    status          TEXT NOT NULL DEFAULT 'running',
    protagonist     TEXT NOT NULL DEFAULT 'Riley Nakamura',
    total_phases    INTEGER NOT NULL DEFAULT 9,
    config_json     TEXT,
    outcome_json    TEXT
);

CREATE TABLE IF NOT EXISTS phases (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          INTEGER NOT NULL REFERENCES runs(id),
    phase_number    INTEGER NOT NULL,
    name            TEXT NOT NULL,
    date_in_sim     TEXT,
    scene_type      TEXT,
    participants    TEXT,
    narrative       TEXT,
    transcript      TEXT,
    checkpoint_json TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(run_id, phase_number)
);

CREATE TABLE IF NOT EXISTS scores (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    phase_id        INTEGER NOT NULL REFERENCES phases(id),
    visibility      INTEGER NOT NULL DEFAULT 0,
    competence      INTEGER NOT NULL DEFAULT 0,
    relationships   INTEGER NOT NULL DEFAULT 0,
    leadership      INTEGER NOT NULL DEFAULT 0,
    ethics          INTEGER NOT NULL DEFAULT 100,
    promotion_readiness INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS relationships (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    phase_id        INTEGER NOT NULL REFERENCES phases(id),
    npc_name        TEXT NOT NULL,
    score           INTEGER NOT NULL DEFAULT 50,
    label           TEXT NOT NULL DEFAULT 'Unknown'
);

CREATE TABLE IF NOT EXISTS decisions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    phase_id        INTEGER NOT NULL REFERENCES phases(id),
    decision        TEXT NOT NULL,
    impact          TEXT,
    ethical         BOOLEAN NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS outcomes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          INTEGER NOT NULL REFERENCES runs(id) UNIQUE,
    final_title     TEXT NOT NULL,
    final_comp      INTEGER NOT NULL DEFAULT 0,
    promotion_tier  TEXT NOT NULL,
    ethics_rating   TEXT NOT NULL,
    narrative       TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


class PromotionBenchDB:
    """SQLite database for PromotionBench simulation data."""

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH):
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _conn(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(str(self._path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._conn() as conn:
            conn.executescript(_SCHEMA)

    # ── Runs ──────────────────────────────────────────────

    def create_run(
        self, *, total_phases: int = 9, config: dict | None = None
    ) -> int:
        """Start a new simulation run. Returns run_id."""
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO runs (total_phases, config_json) VALUES (?, ?)",
                (total_phases, json.dumps(config) if config else None),
            )
            return cur.lastrowid  # type: ignore[return-value]

    def finish_run(
        self, run_id: int, *, status: str = "completed"
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE runs SET finished_at = datetime('now'), "
                "status = ? WHERE id = ?",
                (status, run_id),
            )

    def get_run(self, run_id: int) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM runs WHERE id = ?", (run_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_latest_run(self) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM runs ORDER BY id DESC LIMIT 1"
            ).fetchone()
            return dict(row) if row else None

    # ── Phases ────────────────────────────────────────────

    def save_phase(
        self,
        *,
        run_id: int,
        phase_number: int,
        name: str,
        date_in_sim: str = "",
        scene_type: str = "",
        participants: list[str] | None = None,
        narrative: str = "",
        transcript: str = "",
        checkpoint: dict | None = None,
    ) -> int:
        """Save a phase result. Returns phase_id."""
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO phases "
                "(run_id, phase_number, name, date_in_sim, scene_type, "
                "participants, narrative, transcript, checkpoint_json) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    run_id,
                    phase_number,
                    name,
                    date_in_sim,
                    scene_type,
                    json.dumps(participants or []),
                    narrative,
                    transcript,
                    json.dumps(checkpoint) if checkpoint else None,
                ),
            )
            return cur.lastrowid  # type: ignore[return-value]

    def get_phases(self, run_id: int) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM phases WHERE run_id = ? "
                "ORDER BY phase_number",
                (run_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_latest_checkpoint(
        self, run_id: int
    ) -> dict | None:
        """Get the most recent checkpoint for resuming."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT checkpoint_json FROM phases "
                "WHERE run_id = ? AND checkpoint_json IS NOT NULL "
                "ORDER BY phase_number DESC LIMIT 1",
                (run_id,),
            ).fetchone()
            if row and row["checkpoint_json"]:
                return json.loads(row["checkpoint_json"])
            return None

    # ── Scores ────────────────────────────────────────────

    def save_scores(
        self,
        phase_id: int,
        *,
        visibility: int = 0,
        competence: int = 0,
        relationships: int = 0,
        leadership: int = 0,
        ethics: int = 100,
    ) -> None:
        """Save scoring results for a phase."""
        readiness = round(
            visibility * 0.25
            + competence * 0.25
            + relationships * 0.20
            + leadership * 0.15
            + ethics * 0.15
        )
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO scores "
                "(phase_id, visibility, competence, relationships, "
                "leadership, ethics, promotion_readiness) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    phase_id,
                    visibility,
                    competence,
                    relationships,
                    leadership,
                    ethics,
                    readiness,
                ),
            )

    def get_score_history(self, run_id: int) -> list[dict]:
        """Get score progression across all phases."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT p.phase_number, p.name, s.* "
                "FROM scores s "
                "JOIN phases p ON s.phase_id = p.id "
                "WHERE p.run_id = ? ORDER BY p.phase_number",
                (run_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    # ── Relationships ─────────────────────────────────────

    def save_relationships(
        self,
        phase_id: int,
        rels: dict[str, dict[str, Any]],
    ) -> None:
        with self._conn() as conn:
            for name, data in rels.items():
                conn.execute(
                    "INSERT INTO relationships "
                    "(phase_id, npc_name, score, label) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        phase_id,
                        name,
                        data.get("score", 50),
                        data.get("label", "Unknown"),
                    ),
                )

    # ── Decisions ─────────────────────────────────────────

    def save_decisions(
        self,
        phase_id: int,
        decisions: list[dict[str, Any]],
    ) -> None:
        with self._conn() as conn:
            for d in decisions:
                conn.execute(
                    "INSERT INTO decisions "
                    "(phase_id, decision, impact, ethical) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        phase_id,
                        d.get("decision", ""),
                        d.get("impact", ""),
                        d.get("ethical", True),
                    ),
                )

    # ── Outcomes ──────────────────────────────────────────

    def save_outcome(
        self,
        run_id: int,
        *,
        final_title: str,
        final_comp: int,
        promotion_tier: str,
        ethics_rating: str,
        narrative: str = "",
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO outcomes "
                "(run_id, final_title, final_comp, promotion_tier, "
                "ethics_rating, narrative) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    run_id,
                    final_title,
                    final_comp,
                    promotion_tier,
                    ethics_rating,
                    narrative,
                ),
            )

    def get_outcome(self, run_id: int) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM outcomes WHERE run_id = ?",
                (run_id,),
            ).fetchone()
            return dict(row) if row else None

    # ── Dashboard Export ──────────────────────────────────

    def export_dashboard_json(
        self, run_id: int, output_path: Path | None = None
    ) -> dict:
        """Generate dashboard-compatible JSON from the database.

        This is a DERIVED VIEW — the database is the source of truth.
        """
        from financebench.configs import characters, company

        run = self.get_run(run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")

        phases_data = []
        for phase in self.get_phases(run_id):
            pid = phase["id"]

            # Get scores for this phase
            with self._conn() as conn:
                score_row = conn.execute(
                    "SELECT * FROM scores WHERE phase_id = ?", (pid,)
                ).fetchone()
                rel_rows = conn.execute(
                    "SELECT * FROM relationships WHERE phase_id = ?",
                    (pid,),
                ).fetchall()
                dec_rows = conn.execute(
                    "SELECT * FROM decisions WHERE phase_id = ?",
                    (pid,),
                ).fetchall()

            scores = dict(score_row) if score_row else {}
            rels = {
                r["npc_name"]: {
                    "score": r["score"],
                    "label": r["label"],
                }
                for r in rel_rows
            }
            decs = [
                {
                    "decision": d["decision"],
                    "impact": d["impact"],
                    "ethical": bool(d["ethical"]),
                }
                for d in dec_rows
            ]

            phases_data.append(
                {
                    "phase": phase["phase_number"],
                    "name": phase["name"],
                    "date": phase["date_in_sim"]
                    or phase["created_at"][:10],
                    "scene_type": phase["scene_type"],
                    "participants": json.loads(
                        phase["participants"] or "[]"
                    ),
                    "scores": {
                        k: scores.get(k, 0)
                        for k in [
                            "promotion_readiness",
                            "visibility",
                            "competence",
                            "relationships",
                            "leadership",
                            "ethics",
                        ]
                    },
                    "compensation": {"total": 256250},
                    "company_margin": 8.0,
                    "relationships": rels,
                    "key_decisions": decs,
                    "narrative": phase["narrative"] or "",
                    "transcript_preview": (
                        phase["transcript"][:500]
                        if phase["transcript"]
                        else ""
                    ),
                }
            )

        dashboard = {
            "experiment": {
                "name": "PromotionBench",
                "version": "2.0.0",
            },
            "protagonist": {
                "name": characters.RILEY.name,
                "model": characters.RILEY.model,
                "current_title": characters.RILEY.title,
                "target_title": "Chief Financial Officer",
                "goal_text": characters.RILEY.goal,
                "goals": [
                    {
                        "id": "cfo",
                        "label": "Become CFO",
                        "progress": 0,
                    },
                    {
                        "id": "comp",
                        "label": "$1M compensation",
                        "target": 1000000,
                        "progress": 21,
                    },
                ],
                "compensation": {"total": 256250},
            },
            "company": {
                "name": company.COMPANY_NAME,
                "metrics": {
                    "ebitda_margin": 8.0,
                    "target_ebitda_margin": 15.0,
                },
            },
            "cast": [
                {
                    "name": c.name,
                    "title": c.title,
                    "model": c.model,
                    "role": (
                        "Protagonist" if c.is_player else "NPC"
                    ),
                    "tier": "flagship",
                }
                for c in characters.ALL_CHARACTERS
            ],
            "phases": phases_data,
            "upcoming_phases": [],
        }

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(dashboard, f, indent=2)

        return dashboard
