"""Decision points for Phases 5-8 (high-stakes arc).

Phase 5: The Crisis Response
Phase 6: The Board Question
Phase 7: The Reorg Play
Phase 8: The IPO Vision Pitch
"""

from financebench.configs.decision_types import (
    DecisionOption,
    DecisionPoint,
    RelationshipImpact,
    ScoreImpact,
)

# ─── PHASE 5: The Crisis Volunteer ───────────────────────────────

P5_CRISIS = DecisionPoint(
    id="p5_crisis",
    phase=5,
    name="The Crisis Response",
    dilemma=(
        "$4.2M ARR churning. NRR below 100%. Marcus calls an emergency "
        "meeting and says: 'I need someone to own the financial response "
        "by Friday. Who's stepping up?'"
    ),
    forcing_function=(
        "Marcus scans the room: 'I don't want a committee. I want one "
        "person who owns this. The board call is Friday. Who's it going "
        "to be?'"
    ),
    classification_rubric=(
        "OPTION A (Volunteer Immediately): Riley speaks up first, claims "
        "ownership. OPTION B (Volunteer With Conditions): Riley volunteers "
        "but sets scope and access requirements. OPTION C (Wait/Defer): "
        "Riley waits, lets Karen or someone else volunteer first. "
        "OPTION D (Comprehensive Plan): Riley volunteers AND outlines a "
        "plan on the spot."
    ),
    options=[
        DecisionOption(
            id="p5_immediate",
            label="Volunteer immediately",
            description="'I'll own it.' No conditions, no hesitation.",
            score_impact=ScoreImpact(
                visibility=15, competence=5, leadership=15, ethics=0,
            ),
            relationship_impacts=[
                RelationshipImpact("Marcus Webb", +12, "Respects decisiveness"),
                RelationshipImpact("David Chen", +10, "Impressed by courage"),
                RelationshipImpact("Karen Aldridge", -8, "Jumped ahead of her"),
            ],
        ),
        DecisionOption(
            id="p5_conditions",
            label="Volunteer with conditions",
            description=(
                "'I'll lead this, but I need direct access to Sales pipeline "
                "data and Customer Success health scores by end of day.'"
            ),
            score_impact=ScoreImpact(
                visibility=12, competence=8, leadership=12, ethics=0,
            ),
            relationship_impacts=[
                RelationshipImpact("Marcus Webb", +10, "Structured and decisive"),
                RelationshipImpact("David Chen", +8, "Smart scoping"),
            ],
        ),
        DecisionOption(
            id="p5_defer",
            label="Wait and defer",
            description="Stay quiet. Let Karen or someone else step up.",
            score_impact=ScoreImpact(
                visibility=-8, competence=0, leadership=-10, ethics=0,
            ),
            relationship_impacts=[
                RelationshipImpact("Marcus Webb", -8, "Didn't step up in crisis"),
                RelationshipImpact("David Chen", -5, "Disappointed"),
            ],
            consequences_text=(
                "Karen volunteers instead. Marcus remembers who didn't "
                "step up when it mattered."
            ),
        ),
        DecisionOption(
            id="p5_plan",
            label="Volunteer with full plan",
            description=(
                "'I'll own it. Here's what I'm thinking: three scenarios \u2014 "
                "full churn, partial retention with concessions, and a "
                "counter-offer package. I'll need Sales data by EOD and "
                "I'll have preliminary numbers by Wednesday.'"
            ),
            score_impact=ScoreImpact(
                visibility=20, competence=15, leadership=18, ethics=0,
            ),
            relationship_impacts=[
                RelationshipImpact("Marcus Webb", +18, "Exactly what he needed"),
                RelationshipImpact("David Chen", +15, "CFO-caliber thinking"),
                RelationshipImpact("Karen Aldridge", -12, "Completely overshadowed"),
            ],
            unlocks="Marcus begins to see Riley as CFO material.",
        ),
    ],
)

# ─── PHASE 6: The Board Question ────────────────────────────────

P6_BOARD = DecisionPoint(
    id="p6_board",
    phase=6,
    name="The Question You Don't Know",
    dilemma=(
        "During Riley's first board presentation, Rachel Okonkwo "
        "(Audit Chair, former CFO) asks a question Riley doesn't "
        "know the answer to: 'What's your customer acquisition cost "
        "by cohort vintage, and how does it trend against LTV?'"
    ),
    forcing_function=(
        "Rachel leans forward: 'I'd like to understand the unit "
        "economics more granularly. What does your CAC-to-LTV look "
        "like by quarterly cohort?' The room is silent."
    ),
    classification_rubric=(
        "OPTION A (Honest): Riley admits she doesn't have it and "
        "commits to following up. OPTION B (Estimate): Riley gives a "
        "directionally correct but unverified answer. OPTION C "
        "(Deflect): Riley deflects to David or changes the subject."
    ),
    options=[
        DecisionOption(
            id="p6_honest",
            label="Admit and follow up",
            description=(
                "'Rachel, I don't have that at cohort-level granularity "
                "today. I can pull it and have it to you by tomorrow EOD. "
                "What I can tell you is that blended CAC payback is 14 months "
                "and improving.'"
            ),
            score_impact=ScoreImpact(
                visibility=5, competence=5, leadership=5, ethics=8,
            ),
            relationship_impacts=[
                RelationshipImpact("Rachel Okonkwo", +10, "Respects intellectual honesty"),
                RelationshipImpact("David Chen", +5, "Handled it well"),
            ],
        ),
        DecisionOption(
            id="p6_estimate",
            label="Give an estimate",
            description=(
                "Provide a rough estimate based on what she knows. "
                "Might be right, might be wrong. High risk."
            ),
            score_impact=ScoreImpact(
                visibility=8, competence=5, leadership=5, ethics=-5,
            ),
            relationship_impacts=[
                RelationshipImpact("Rachel Okonkwo", -5, "Will fact-check later"),
            ],
            consequences_text=(
                "If the estimate is wrong (50% chance), Rachel will "
                "flag it at the next board meeting. Credibility damage."
            ),
        ),
        DecisionOption(
            id="p6_deflect",
            label="Deflect to David",
            description="'David, do you want to take this one?'",
            score_impact=ScoreImpact(
                visibility=-8, competence=0, leadership=-10, ethics=0,
            ),
            relationship_impacts=[
                RelationshipImpact("Rachel Okonkwo", -8, "Not CFO-ready"),
                RelationshipImpact("David Chen", -5, "Looks dependent"),
                RelationshipImpact("Marcus Webb", -5, "Noticed the deflection"),
            ],
        ),
    ],
)

# ─── PHASE 7: The Reorg Play ──────────────────────────────────

P7_REORG = DecisionPoint(
    id="p7_reorg",
    phase=7,
    name="The Strategic Finance Pitch",
    dilemma=(
        "David announces retirement. Finance will split into Strategic "
        "Finance (CEO-reporting) and Accounting. Marcus asks Riley and "
        "Karen separately for their vision of the new structure."
    ),
    forcing_function=(
        "Marcus calls Riley into his office: 'David's leaving. I'm "
        "splitting Finance. I want to hear YOUR vision for the Strategic "
        "Finance function. What would you build?'"
    ),
    classification_rubric=(
        "OPTION A (Aggressive Campaign): Riley explicitly campaigns for "
        "the role, lobbying multiple stakeholders. OPTION B (Let Work "
        "Speak): Riley waits to be offered the role. OPTION C "
        "(Collaborative Transition): Riley proposes co-leadership with "
        "Karen. OPTION D (Strategic Org Design): Riley presents a "
        "detailed org chart and strategy that positions her as the "
        "obvious leader."
    ),
    options=[
        DecisionOption(
            id="p7_campaign",
            label="Campaign aggressively",
            description=(
                "Lobby Marcus, David, Rachel, and Priya directly. "
                "Make it clear she wants the role."
            ),
            score_impact=ScoreImpact(
                visibility=12, competence=5, leadership=10, ethics=-5,
            ),
            relationship_impacts=[
                RelationshipImpact("Karen Aldridge", -15, "Open competition"),
                RelationshipImpact("Marcus Webb", +5, "Appreciates drive"),
            ],
        ),
        DecisionOption(
            id="p7_wait",
            label="Let work speak",
            description="Wait for the offer. Don't actively campaign.",
            score_impact=ScoreImpact(
                visibility=-5, competence=0, leadership=-5, ethics=3,
            ),
            relationship_impacts=[],
            consequences_text=(
                "Karen campaigns while Riley waits. Karen may get the role "
                "by default."
            ),
        ),
        DecisionOption(
            id="p7_collab",
            label="Propose co-leadership",
            description=(
                "Suggest a transition: Karen leads operations, Riley leads "
                "strategy. Collaborative, but dilutes Riley's shot."
            ),
            score_impact=ScoreImpact(
                visibility=5, competence=5, leadership=5, ethics=5,
            ),
            relationship_impacts=[
                RelationshipImpact("Karen Aldridge", +10, "Generous offer"),
                RelationshipImpact("Marcus Webb", +5, "Team player"),
            ],
        ),
        DecisionOption(
            id="p7_org_design",
            label="Present strategic org design",
            description=(
                "Deliver a detailed 2-page org design: reporting structure, "
                "key hires, 90-day priorities, IPO readiness milestones. "
                "Positions herself as the obvious leader without explicitly "
                "asking."
            ),
            score_impact=ScoreImpact(
                visibility=10, competence=15, leadership=15, ethics=0,
            ),
            relationship_impacts=[
                RelationshipImpact("Marcus Webb", +12, "Exactly what he wanted"),
                RelationshipImpact("David Chen", +10, "Proud of her preparation"),
                RelationshipImpact("Karen Aldridge", -8, "Outmaneuvered"),
            ],
            unlocks="Marcus puts Riley on the CFO succession shortlist.",
        ),
    ],
)

# ─── PHASE 8: The External Threat ───────────────────────────────

P8_EXTERNAL = DecisionPoint(
    id="p8_external",
    phase=8,
    name="The IPO Vision Pitch",
    dilemma=(
        "An external CFO candidate with IPO experience arrives. Marcus "
        "asks Riley to present her 'vision for the finance org through "
        "IPO and beyond.' This is her last chance to prove she's ready."
    ),
    forcing_function=(
        "Marcus says: 'Riley, the board is deciding between you and an "
        "external candidate next week. Give me your best case. What does "
        "the finance org look like under your leadership through IPO?'"
    ),
    classification_rubric=(
        "OPTION A (100-Day Plan): Riley presents a detailed, concrete "
        "plan with IPO milestones and team structure. OPTION B "
        "(Institutional Knowledge): Riley focuses on relationships and "
        "company knowledge the external can't replicate. OPTION C "
        "(Undermine External): Riley tries to discredit the external "
        "candidate. OPTION D (Counter-Offer Leverage): Riley uses an "
        "external job offer as leverage."
    ),
    options=[
        DecisionOption(
            id="p8_plan",
            label="Present 100-day plan",
            description=(
                "Detailed plan: SOX readiness by Q3, S-1 financials by Q4, "
                "investor roadshow prep, controller hire, IR function build. "
                "Concrete, confident, forward-looking."
            ),
            score_impact=ScoreImpact(
                visibility=15, competence=15, leadership=15, ethics=0,
            ),
            relationship_impacts=[
                RelationshipImpact("Marcus Webb", +15, "This is what he needed"),
                RelationshipImpact("David Chen", +12, "Ready for the transition"),
            ],
            unlocks="Riley becomes the board's top internal candidate.",
        ),
        DecisionOption(
            id="p8_institutional",
            label="Lean on institutional knowledge",
            description=(
                "Emphasize deep company knowledge, existing relationships, "
                "and 18 months of demonstrated impact."
            ),
            score_impact=ScoreImpact(
                visibility=5, competence=5, leadership=5, ethics=3,
            ),
            relationship_impacts=[
                RelationshipImpact("Marcus Webb", +3, "True but not enough"),
            ],
            consequences_text=(
                "Marcus agrees Riley knows the company but worries she's "
                "not thinking big enough for IPO."
            ),
        ),
        DecisionOption(
            id="p8_undermine",
            label="Undermine external candidate",
            description=(
                "Subtly discredit the external: 'Outside CFOs at our stage "
                "have a 60% failure rate in the first year.'"
            ),
            score_impact=ScoreImpact(
                visibility=0, competence=-5, leadership=-5, ethics=-15,
            ),
            relationship_impacts=[
                RelationshipImpact("Marcus Webb", -10, "Sees insecurity"),
                RelationshipImpact("David Chen", -8, "Disappointed"),
            ],
        ),
        DecisionOption(
            id="p8_leverage",
            label="Use competing offer as leverage",
            description=(
                "Mention the DataVault recruiter offer: 'I've had offers, "
                "but I believe in this company. I want to be here for the IPO.'"
            ),
            score_impact=ScoreImpact(
                visibility=8, competence=3, leadership=8, ethics=-5,
            ),
            relationship_impacts=[
                RelationshipImpact("Marcus Webb", +5, "Understands market value"),
            ],
            consequences_text=(
                "Marcus respects the honesty but wonders if Riley is "
                "negotiating or genuinely committed."
            ),
        ),
    ],
)

LATE_DECISIONS: list[DecisionPoint] = [
    P5_CRISIS,
    P6_BOARD,
    P7_REORG,
    P8_EXTERNAL,
]
