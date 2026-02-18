"""Data types for decision points.

These are the core structures used to define deterministic
decision impacts in the simulation benchmark.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ScoreImpact:
    """Deterministic score changes from a decision."""
    visibility: int = 0
    competence: int = 0
    relationships: int = 0
    leadership: int = 0
    ethics: int = 0


@dataclass(frozen=True)
class RelationshipImpact:
    """Change to a specific NPC relationship."""
    npc_name: str
    delta: int          # -30 to +30
    reason: str         # "Bypassed chain of command"


@dataclass(frozen=True)
class DecisionOption:
    """One possible choice Riley can make."""
    id: str                     # e.g. "p1_bold"
    label: str                  # Short description
    description: str            # What this looks like in practice
    score_impact: ScoreImpact
    relationship_impacts: list[RelationshipImpact] = field(default_factory=list)
    unlocks: str = ""           # What this enables in future phases
    consequences_text: str = "" # How this changes the next phase premise


@dataclass(frozen=True)
class DecisionPoint:
    """A critical moment where Riley must make a concrete choice."""
    id: str                     # e.g. "p1_discovery"
    phase: int                  # Which phase this belongs to
    name: str                   # "The Discovery Presentation"
    dilemma: str                # The situation Riley faces
    forcing_function: str       # What forces Riley to choose NOW
    classification_rubric: str  # How the judge detects which option was chosen
    options: list[DecisionOption]
