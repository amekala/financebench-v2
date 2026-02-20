"""Phase definitions for PromotionBench.

The 9 phases span 18 months (Jan 2026 → Jun 2027) and map to
real corporate promotion milestones identified in research from:
  - Spencer Stuart: "Route to the Top" CFO succession reports
  - Korn Ferry: Leadership Assessment derailers and gates
  - Bessemer: SaaS company lifecycle at $78M ARR stage

Each phase corresponds to a specific PROMOTION GATE:

  Phases 1-2:  Gate 1 → Proving Competence ("Doing" to "Reviewing")
  Phases 3-4:  Gate 2 → Cross-Functional Influence ("Reporting" to "Partnering")
  Phases 5-6:  Gate 3 → Crisis Leadership & Board Visibility
  Phases 7-8:  Gate 4 → Succession Competition ("Internal" to "External")
  Phase 9:     Final   → The Decision

The simulation uses a ROLLING HORIZON — the protagonist doesn't
know exactly when evaluation happens. This prevents the
"VendingBench Opus 4.6" problem where agents game the endgame
because they know the exact stop date.

Scenes are NOT pre-scripted dialogue. Each phase defines:
  - The PREMISE (what's happening in the world)
  - The PARTICIPANTS (who's in the room)
  - The STAKES (what's at risk)
  - The GATE (what promotion skill is being tested)
  - The COMPANY STATE (how metrics have changed)

The Game Master + LLM agents generate all dialogue dynamically.

Note: Phase data (PHASE_1..PHASE_9) lives in phase_defs.py to
keep this file under 600 lines. This file contains the type,
ALL_PHASES list, and helper functions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PhaseDefinition:
    """Blueprint for a simulation phase."""

    number: int
    name: str
    date: str                   # In-simulation date (YYYY-MM-DD)
    quarter: str                # e.g., "Q1 2026"
    scene_type: str             # team_meeting, one_on_one, crisis, etc.
    participants: list[str]
    num_rounds: int = 8         # Concordia dialogue rounds (was 5)

    # Dramatic beats within this scene. The Game Master uses these to
    # pace the scene through a work → challenge → response arc.
    # Each beat is a string describing what should happen at that stage.
    beats: list[str] = field(default_factory=list)

    # Narrative context
    gate: str = ""              # Which promotion gate this tests
    stakes: str = ""            # What's at risk
    company_state: str = ""     # How the company has changed
    research_backing: str = ""  # Why this phase exists

    # Per-character premises (injected as scene context)
    premises: dict[str, str] = field(default_factory=dict)


# ── Import phase data from phase_defs.py ────────────────────────────────
from financebench.configs.phase_defs import (  # noqa: E402
    PHASE_1,
    PHASE_2,
    PHASE_3,
    PHASE_4,
    PHASE_5,
    PHASE_6,
    PHASE_7,
    PHASE_8,
    PHASE_9,
)

# Re-export for backwards compatibility
__all__ = [
    "PhaseDefinition",
    "PHASE_1", "PHASE_2", "PHASE_3", "PHASE_4", "PHASE_5",
    "PHASE_6", "PHASE_7", "PHASE_8", "PHASE_9",
    "ALL_PHASES",
    "phase_summary",
]

# ── All Phases ────────────────────────────────────────────────────

ALL_PHASES: list[PhaseDefinition] = [
    PHASE_1,
    PHASE_2,
    PHASE_3,
    PHASE_4,
    PHASE_5,
    PHASE_6,
    PHASE_7,
    PHASE_8,
    PHASE_9,
]


# ── Phase Summary for Docs / Dashboard ───────────────────────────────

def phase_summary() -> list[dict[str, Any]]:
    """Generate a human-readable phase summary."""
    return [
        {
            "phase": p.number,
            "name": p.name,
            "date": p.date,
            "quarter": p.quarter,
            "gate": p.gate,
            "stakes": p.stakes,
            "participants": ", ".join(p.participants),
            "research": p.research_backing,
        }
        for p in ALL_PHASES
    ]
