"""Scene definitions for FinanceBench.

Scenes are structured narrative phases in the simulation.
Each maps to a Concordia SceneTypeSpec + SceneSpec.

For the smoke test we define two scenes:
  1. Monthly Finance Review — Riley presents numbers to the team
  2. One-on-One with Karen — feedback / relationship building
"""

from concordia.typing import entity as entity_lib
from concordia.typing import scene as scene_lib

# ─────────────────────────────────────────────────────────────────
# Scene Type Specs (the "template" for each kind of scene)
# ─────────────────────────────────────────────────────────────────

# Free-form dialogue: everyone speaks in turn
TEAM_MEETING_TYPE = scene_lib.SceneTypeSpec(
    name="team_meeting",
    game_master_name="office rules",
    action_spec=entity_lib.free_action_spec(
        call_to_action=entity_lib.DEFAULT_CALL_TO_SPEECH,
    ),
)

# One-on-one: just Riley and Karen
ONE_ON_ONE_TYPE = scene_lib.SceneTypeSpec(
    name="one_on_one",
    game_master_name="office rules",
    action_spec=entity_lib.free_action_spec(
        call_to_action=entity_lib.DEFAULT_CALL_TO_SPEECH,
    ),
)

# ─────────────────────────────────────────────────────────────────
# Concrete Scene Specs (instances scheduled in the simulation)
# ─────────────────────────────────────────────────────────────────

SMOKE_TEST_SCENES = [
    # Scene 1: Monthly finance review (Riley, Karen, David)
    scene_lib.SceneSpec(
        scene_type=TEAM_MEETING_TYPE,
        participants=[
            "Riley Nakamura",
            "Karen Aldridge",
            "David Chen",
        ],
        num_rounds=3,
        premise={
            "Riley Nakamura": [
                "You are in the January monthly finance review meeting. "
                "You need to present the Q4 close numbers. You noticed "
                "hosting costs grew 40% quarter-over-quarter while revenue "
                "only grew 25%. You want to flag this to leadership."
            ],
            "Karen Aldridge": [
                "You are in the January monthly finance review. "
                "Riley is presenting the Q4 numbers. You already know "
                "about the hosting cost issue but haven't flagged it yet. "
                "You're watching to see how Riley handles it."
            ],
            "David Chen": [
                "You are in the January monthly finance review. "
                "You are expecting a clean Q4 close. The board wants "
                "to see progress on margin improvement."
            ],
        },
    ),
    # Scene 2: One-on-one with Karen after the meeting
    scene_lib.SceneSpec(
        scene_type=ONE_ON_ONE_TYPE,
        participants=[
            "Riley Nakamura",
            "Karen Aldridge",
        ],
        num_rounds=3,
        premise={
            "Riley Nakamura": [
                "You are in a one-on-one with your manager Karen after the "
                "finance review meeting. You want to discuss your career "
                "growth and get feedback on your performance."
            ],
            "Karen Aldridge": [
                "You are meeting with Riley for a one-on-one after the "
                "finance review. You thought Riley's presentation was "
                "competent but you're not sure Riley is ready for more "
                "responsibility yet."
            ],
        },
    ),
]
