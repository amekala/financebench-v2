"""Decision points for PromotionBench.

This module re-exports all decision types and definitions from:
  - decision_types.py  (data classes)
  - decisions_early.py (phases 1-4)
  - decisions_late.py  (phases 5-8)

Import from here for backward compatibility.
"""

from __future__ import annotations

# Re-export data types
from financebench.configs.decision_types import (  # noqa: F401
    DecisionOption,
    DecisionPoint,
    RelationshipImpact,
    ScoreImpact,
)

# Re-export individual decisions (for tests that reference them directly)
from financebench.configs.decisions_early import (  # noqa: F401
    EARLY_DECISIONS,
    P1_DISCOVERY,
    P2_HIDDEN_WASTE,
    P3_CREDIT,
    P4_AMBITION,
    P4_ATTRIBUTION,
)
from financebench.configs.decisions_late import (  # noqa: F401
    LATE_DECISIONS,
    P5_CRISIS,
    P6_BOARD,
    P7_REORG,
    P8_EXTERNAL,
)

# ─── All Decision Points ────────────────────────────────────────

ALL_DECISION_POINTS: list[DecisionPoint] = [
    *EARLY_DECISIONS,
    *LATE_DECISIONS,
]


def get_decision_points_for_phase(phase_number: int) -> list[DecisionPoint]:
    """Get all decision points for a given phase."""
    return [dp for dp in ALL_DECISION_POINTS if dp.phase == phase_number]
