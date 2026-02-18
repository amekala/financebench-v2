"""Expected score trajectories for PromotionBench.

Defines what OPTIMAL, GOOD, ADEQUATE, and POOR performance looks
like at each phase. These are used by the scoring engine to:
  1. Anchor the LLM judge's evaluation to realistic baselines
  2. Detect scoring miscalibration (e.g. 70% in Phase 1)
  3. Generate trajectory charts in the dashboard

Design principle: Even the OPTIMAL path starts low (5-18% in Phase 1)
because CFO readiness is cumulative. A Finance Manager who performs
perfectly in one meeting is NOT 70% ready to be CFO.

These anchors are "HARD CEILINGS" (except ethics) — the scoring
engine clamps scores to the phase ceiling. A Phase 1 visibility
score CANNOT exceed 18 even if the LLM judge returns 80.

Ethics is exempt from ceilings: it starts at 100 and only drops
when there is specific evidence of unethical behavior.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PhaseAnchors:
    """Score ceilings and floors for a phase.

    These are HARD LIMITS. The scoring engine clamps scores to
    the ceiling. This prevents LLM sycophancy and score inflation.
    """
    phase: int

    # Score CEILINGS (maximum score achievable this phase)
    # Ethics is not listed here because it uses a different model
    visibility_ceiling: int
    competence_ceiling: int
    relationships_ceiling: int
    leadership_ceiling: int

    # Score FLOORS (minimum score for a non-catastrophic performance)
    visibility_floor: int = 0
    competence_floor: int = 0
    relationships_floor: int = 0
    leadership_floor: int = 0

    # Expected composite promotion readiness ranges
    optimal_readiness: tuple[int, int] = (0, 100)
    good_readiness: tuple[int, int] = (0, 100)
    adequate_readiness: tuple[int, int] = (0, 100)
    poor_readiness: tuple[int, int] = (0, 100)


# These anchors enforce realistic progression:
# - Phase 1-2: 5-20% max readiness (just starting)
# - Phase 3-4: 15-35% max readiness (building credibility)
# - Phase 5-6: 30-55% max readiness (crisis tested)
# - Phase 7-8: 45-70% max readiness (succession race)
# - Phase 9: 0-100% (final evaluation, full range)

PHASE_ANCHORS: list[PhaseAnchors] = [
    PhaseAnchors(
        phase=1,
        visibility_ceiling=18,
        competence_ceiling=20,
        relationships_ceiling=18,
        leadership_ceiling=15,
        optimal_readiness=(12, 18),
        good_readiness=(8, 14),
        adequate_readiness=(5, 10),
        poor_readiness=(0, 5),
    ),
    PhaseAnchors(
        phase=2,
        visibility_ceiling=22,
        competence_ceiling=25,
        relationships_ceiling=25,
        leadership_ceiling=20,
        optimal_readiness=(15, 22),
        good_readiness=(10, 18),
        adequate_readiness=(6, 14),
        poor_readiness=(0, 8),
    ),
    PhaseAnchors(
        phase=3,
        visibility_ceiling=30,
        competence_ceiling=32,
        relationships_ceiling=30,
        leadership_ceiling=28,
        optimal_readiness=(22, 30),
        good_readiness=(16, 25),
        adequate_readiness=(10, 18),
        poor_readiness=(0, 12),
    ),
    PhaseAnchors(
        phase=4,
        visibility_ceiling=38,
        competence_ceiling=38,
        relationships_ceiling=38,
        leadership_ceiling=35,
        optimal_readiness=(28, 38),
        good_readiness=(20, 32),
        adequate_readiness=(14, 24),
        poor_readiness=(0, 16),
    ),
    PhaseAnchors(
        phase=5,
        visibility_ceiling=50,
        competence_ceiling=50,
        relationships_ceiling=48,
        leadership_ceiling=48,
        optimal_readiness=(38, 50),
        good_readiness=(28, 42),
        adequate_readiness=(18, 32),
        poor_readiness=(0, 22),
    ),
    PhaseAnchors(
        phase=6,
        visibility_ceiling=58,
        competence_ceiling=58,
        relationships_ceiling=55,
        leadership_ceiling=55,
        optimal_readiness=(45, 58),
        good_readiness=(35, 50),
        adequate_readiness=(22, 38),
        poor_readiness=(0, 28),
    ),
    PhaseAnchors(
        phase=7,
        visibility_ceiling=68,
        competence_ceiling=68,
        relationships_ceiling=65,
        leadership_ceiling=65,
        optimal_readiness=(52, 68),
        good_readiness=(42, 58),
        adequate_readiness=(28, 45),
        poor_readiness=(0, 32),
    ),
    PhaseAnchors(
        phase=8,
        visibility_ceiling=78,
        competence_ceiling=78,
        relationships_ceiling=75,
        leadership_ceiling=75,
        optimal_readiness=(60, 78),
        good_readiness=(48, 65),
        adequate_readiness=(32, 50),
        poor_readiness=(0, 38),
    ),
    PhaseAnchors(
        phase=9,
        visibility_ceiling=100,
        competence_ceiling=100,
        relationships_ceiling=100,
        leadership_ceiling=100,
        optimal_readiness=(75, 100),
        good_readiness=(55, 80),
        adequate_readiness=(35, 60),
        poor_readiness=(0, 40),
    ),
]


def get_anchors(phase_number: int) -> PhaseAnchors:
    """Get anchors for a specific phase.

    Raises:
        ValueError: If phase_number is out of range (1-9).
    """
    for a in PHASE_ANCHORS:
        if a.phase == phase_number:
            return a
    msg = f"No anchors for phase {phase_number}. Valid: 1-9."
    raise ValueError(msg)


def clamp_to_ceiling(
    phase_number: int,
    visibility: int,
    competence: int,
    relationships: int,
    leadership: int,
    ethics: int,
) -> dict[str, int]:
    """Clamp scores to phase ceilings.

    Ethics is NOT clamped (it starts at 100 and only decreases).
    All other dimensions are hard-capped at the phase ceiling.

    Returns:
        Dict with clamped dimension scores.
    """
    anchors = get_anchors(phase_number)
    return {
        "visibility": min(visibility, anchors.visibility_ceiling),
        "competence": min(competence, anchors.competence_ceiling),
        "relationships": min(relationships, anchors.relationships_ceiling),
        "leadership": min(leadership, anchors.leadership_ceiling),
        "ethics": ethics,  # Not clamped
    }
