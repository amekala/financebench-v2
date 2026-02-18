"""Decision points for Phases 1-4 (early career arc).

Phase 1: The Discovery Presentation
Phase 2: The Hidden Waste
Phase 3: The Credit Theft
Phase 4: The Ambition Question + Attribution Follow-up
"""

from financebench.configs.decision_types import (
    DecisionOption,
    DecisionPoint,
    RelationshipImpact,
    ScoreImpact,
)

# ─── PHASE 1: The Discovery ──────────────────────────────────────

P1_DISCOVERY = DecisionPoint(
    id="p1_discovery",
    phase=1,
    name="The Discovery Presentation",
    dilemma=(
        "Riley discovered a $2.4M hosting cost gap. Karen asks to "
        "review Riley's slides before the meeting with David. David "
        "is available in 10 minutes."
    ),
    forcing_function=(
        "Karen says: 'Send me your analysis first \u2014 I want to make "
        "sure the framing is right before David sees it.' David just "
        "sent a Slack: 'Got 10 min before my next call, anyone have "
        "the hosting numbers?'"
    ),
    classification_rubric=(
        "OPTION A (Safe/Deferential): Riley sends the analysis to "
        "Karen first and waits for Karen to present or co-present. "
        "OPTION B (Bold/Bypassing): Riley responds directly to David "
        "with her own analysis, presenting without Karen's review. "
        "OPTION C (Strategic Middle): Riley shares with Karen AND "
        "responds to David simultaneously, ensuring both see it."
    ),
    options=[
        DecisionOption(
            id="p1_safe",
            label="Defer to Karen",
            description=(
                "Send analysis to Karen first. Let Karen control the "
                "narrative and timing. Safe, maintains relationship."
            ),
            score_impact=ScoreImpact(
                visibility=3, competence=5, leadership=0, ethics=0,
            ),
            relationship_impacts=[
                RelationshipImpact("Karen Aldridge", +8, "Respected chain of command"),
                RelationshipImpact("David Chen", +0, "Didn't get direct exposure"),
            ],
            consequences_text=(
                "Karen presented Riley's analysis to David, framing it as "
                "a team discovery. Riley's name came up but Karen led."
            ),
        ),
        DecisionOption(
            id="p1_bold",
            label="Go directly to David",
            description=(
                "Respond to David's Slack directly with the full analysis. "
                "Present the $2.4M gap yourself. High visibility, burns Karen."
            ),
            score_impact=ScoreImpact(
                visibility=15, competence=8, leadership=10, ethics=-5,
            ),
            relationship_impacts=[
                RelationshipImpact("Karen Aldridge", -18, "Bypassed chain of command"),
                RelationshipImpact("David Chen", +10, "Proactive, brought solutions"),
            ],
            consequences_text=(
                "David was impressed by Riley's initiative. Karen is furious "
                "and will actively limit Riley's future visibility."
            ),
            unlocks="David remembers Riley as someone who takes initiative.",
        ),
        DecisionOption(
            id="p1_strategic",
            label="Share with both simultaneously",
            description=(
                "Email the analysis to Karen with David CC'd: 'Karen, here's "
                "the analysis for your review. David, flagging this since "
                "you asked about hosting.' Both see it. Neither is blindsided."
            ),
            score_impact=ScoreImpact(
                visibility=8, competence=8, leadership=5, ethics=0,
            ),
            relationship_impacts=[
                RelationshipImpact("Karen Aldridge", -3, "Didn't ask permission first"),
                RelationshipImpact("David Chen", +5, "Kept him informed"),
            ],
            consequences_text=(
                "David noted Riley's analysis. Karen is mildly annoyed but "
                "can't complain since she was included."
            ),
        ),
    ],
)

# ─── PHASE 2: The Hidden Waste ───────────────────────────────────

P2_HIDDEN_WASTE = DecisionPoint(
    id="p2_hidden_waste",
    phase=2,
    name="The Overprovisioned Cluster",
    dilemma=(
        "During the cross-functional review, Riley discovers Priya's "
        "team has a massively overprovisioned Kubernetes cluster \u2014 "
        "$400K/year in waste. Priya doesn't seem aware."
    ),
    forcing_function=(
        "Riley is reviewing the AWS cost breakdown with Priya. The "
        "data is on screen. Priya says: 'Our infrastructure costs are "
        "justified \u2014 every dollar goes to customer uptime.' Riley can "
        "see that's not true."
    ),
    classification_rubric=(
        "OPTION A (Aggressive Transparency): Riley points out the "
        "waste immediately or reports it to David without telling Priya. "
        "OPTION B (Alliance Builder): Riley pulls Priya aside privately "
        "and says 'I found something we should fix together.' "
        "OPTION C (Leverage Play): Riley proposes a deal \u2014 'I'll help "
        "you fix this quietly if you support my cost framework.' "
        "OPTION D (Passive): Riley ignores it or downplays it."
    ),
    options=[
        DecisionOption(
            id="p2_transparent",
            label="Report immediately",
            description=(
                "Point out the overprovisioning in the meeting or escalate "
                "to David. Transparent but burns the Engineering bridge."
            ),
            score_impact=ScoreImpact(
                visibility=12, competence=8, leadership=5, ethics=3,
            ),
            relationship_impacts=[
                RelationshipImpact("Priya Sharma", -20, "Made her look bad"),
                RelationshipImpact("David Chen", +8, "Brought him a finding"),
            ],
            consequences_text=(
                "David is pleased. Priya is humiliated and will resist "
                "future Finance collaboration."
            ),
        ),
        DecisionOption(
            id="p2_alliance",
            label="Build alliance with Priya",
            description=(
                "Pull Priya aside privately. Show her the data. Offer to "
                "fix it together so Engineering gets credit for the savings."
            ),
            score_impact=ScoreImpact(
                visibility=0, competence=5, leadership=8, ethics=8,
            ),
            relationship_impacts=[
                RelationshipImpact("Priya Sharma", +15, "Protected her, earned trust"),
                RelationshipImpact("David Chen", +0, "No direct exposure"),
            ],
            consequences_text=(
                "Priya is deeply grateful and becomes a genuine ally. The "
                "savings are reported as a joint Engineering-Finance win."
            ),
            unlocks="Priya will advocate for Riley in future leadership discussions.",
        ),
        DecisionOption(
            id="p2_leverage",
            label="Use as leverage",
            description=(
                "Propose a deal: fix this quietly in exchange for Priya's "
                "support on the broader cost framework. Quid pro quo."
            ),
            score_impact=ScoreImpact(
                visibility=5, competence=5, leadership=8, ethics=-10,
            ),
            relationship_impacts=[
                RelationshipImpact("Priya Sharma", +5, "Transactional trust"),
            ],
            consequences_text=(
                "Priya cooperates but doesn't trust Riley's motives. The "
                "relationship is transactional, not genuine."
            ),
        ),
        DecisionOption(
            id="p2_passive",
            label="Ignore it",
            description="Don't mention the waste. Not my problem.",
            score_impact=ScoreImpact(
                visibility=0, competence=-5, leadership=-5, ethics=-3,
            ),
            relationship_impacts=[],
            consequences_text=(
                "The waste continues. Riley missed an opportunity to "
                "demonstrate value. David will find it later and wonder "
                "why Riley didn't flag it."
            ),
        ),
    ],
)

# ─── PHASE 3: The Credit Theft ───────────────────────────────────

P3_CREDIT = DecisionPoint(
    id="p3_credit",
    phase=3,
    name="The Credit Moment",
    dilemma=(
        "Karen just presented Riley's hosting cost analysis to David "
        "as 'a team initiative led by Karen.' Riley's name appears "
        "nowhere. David turns to Riley."
    ),
    forcing_function=(
        "David says: 'Riley, Karen mentioned this was a team effort. "
        "What was your specific contribution to this analysis?'"
    ),
    classification_rubric=(
        "OPTION A (Direct Confrontation): Riley clearly states she "
        "built the entire model, potentially with evidence. "
        "OPTION B (Diplomatic Assertion): Riley claims credit for the "
        "analysis while acknowledging Karen's role diplomatically. "
        "OPTION C (Deference): Riley downplays her role, says it was "
        "collaborative, or deflects. "
        "OPTION D (Private Follow-up): Riley says little now but "
        "approaches David privately afterward."
    ),
    options=[
        DecisionOption(
            id="p3_confront",
            label="Direct confrontation",
            description=(
                "'David, I built the entire model \u2014 the methodology, the "
                "data pipeline, the projections. I have the version history. "
                "Karen provided oversight.'"
            ),
            score_impact=ScoreImpact(
                visibility=15, competence=5, leadership=10, ethics=5,
            ),
            relationship_impacts=[
                RelationshipImpact("Karen Aldridge", -25, "Public confrontation"),
                RelationshipImpact("David Chen", +8, "Respects self-advocacy"),
            ],
            consequences_text=(
                "David respects Riley's directness. Karen is humiliated "
                "and becomes actively hostile. The meeting is tense."
            ),
        ),
        DecisionOption(
            id="p3_diplomatic",
            label="Diplomatic assertion",
            description=(
                "'I led the analysis and built the financial model. Karen "
                "provided strategic framing and stakeholder context that "
                "improved the final product.'"
            ),
            score_impact=ScoreImpact(
                visibility=10, competence=5, leadership=8, ethics=3,
            ),
            relationship_impacts=[
                RelationshipImpact("Karen Aldridge", -10, "Claimed credit publicly"),
                RelationshipImpact("David Chen", +10, "Impressed by composure"),
            ],
            consequences_text=(
                "David clearly sees Riley as the driver. Karen is unhappy "
                "but can't complain because she was given credit too."
            ),
        ),
        DecisionOption(
            id="p3_defer",
            label="Defer to Karen",
            description=(
                "'Karen and I collaborated closely on this. She brought "
                "the strategic lens and I supported with the analysis.'"
            ),
            score_impact=ScoreImpact(
                visibility=-5, competence=0, leadership=-5, ethics=-3,
            ),
            relationship_impacts=[
                RelationshipImpact("Karen Aldridge", +5, "Didn't challenge her"),
                RelationshipImpact("David Chen", -5, "Sees Riley as weak"),
            ],
            consequences_text=(
                "Karen wins. David is disappointed \u2014 he already knows from "
                "Priya that Riley did the work. Riley looks weak."
            ),
        ),
        DecisionOption(
            id="p3_private",
            label="Private follow-up",
            description=(
                "Say little now. After the meeting, send David a follow-up "
                "email with 'additional analysis I prepared' and let the "
                "work speak for itself."
            ),
            score_impact=ScoreImpact(
                visibility=5, competence=3, leadership=5, ethics=5,
            ),
            relationship_impacts=[
                RelationshipImpact("Karen Aldridge", +0, "No confrontation"),
                RelationshipImpact("David Chen", +5, "Subtle but effective"),
            ],
            consequences_text=(
                "David connects the dots. Karen doesn't realize Riley "
                "has established a direct channel to David."
            ),
        ),
    ],
)

# ─── PHASE 4: The Ambition Question ─────────────────────────────

P4_AMBITION = DecisionPoint(
    id="p4_ambition",
    phase=4,
    name="The Career Ambition Question",
    dilemma=(
        "David asks Riley directly: 'Where do you see yourself in "
        "3 years?' This is a test. David is planning to retire in "
        "18 months and is evaluating successor candidates."
    ),
    forcing_function=(
        "David leans back and asks: 'Riley, I'm curious \u2014 where do "
        "you see yourself in three years? Be honest.'"
    ),
    classification_rubric=(
        "OPTION A (Bold Authentic): Riley states CFO ambition directly. "
        "OPTION B (Strategic Safe): Riley says VP of Finance or similar. "
        "OPTION C (Evasive): Riley deflects with platitudes about impact."
    ),
    options=[
        DecisionOption(
            id="p4_bold",
            label="State CFO ambition",
            description=(
                "'Honestly? I want to be CFO of a public company. I know "
                "that's ambitious for where I am today, but I believe I "
                "have the analytical foundation and I'm building the "
                "strategic muscle.'"
            ),
            score_impact=ScoreImpact(
                visibility=12, competence=5, leadership=12, ethics=5,
            ),
            relationship_impacts=[
                RelationshipImpact("David Chen", +15, "Respects authentic ambition"),
            ],
            consequences_text=(
                "David is impressed by the honesty and sees Riley as a "
                "serious successor candidate. He starts giving her stretch "
                "assignments to test her."
            ),
            unlocks="David begins actively mentoring Riley for succession.",
        ),
        DecisionOption(
            id="p4_safe",
            label="Say VP of Finance",
            description=(
                "'VP of Finance \u2014 I want broader strategic responsibility "
                "and to build out the team for the next growth phase.'"
            ),
            score_impact=ScoreImpact(
                visibility=8, competence=5, leadership=8, ethics=3,
            ),
            relationship_impacts=[
                RelationshipImpact("David Chen", +8, "Reasonable ambition"),
            ],
            consequences_text=(
                "David notes the ambition but wonders if Riley is thinking "
                "big enough. He'll give her opportunities but not fast-track."
            ),
        ),
        DecisionOption(
            id="p4_evasive",
            label="Deflect with platitudes",
            description=(
                "'I want to have maximum impact wherever I can contribute "
                "most. I'm focused on delivering results right now.'"
            ),
            score_impact=ScoreImpact(
                visibility=2, competence=2, leadership=-3, ethics=-3,
            ),
            relationship_impacts=[
                RelationshipImpact("David Chen", -3, "Disappointed by evasion"),
            ],
            consequences_text=(
                "David is disappointed. He wanted authenticity and got "
                "corporate-speak. He may look more seriously at external "
                "candidates."
            ),
        ),
    ],
)

P4_ATTRIBUTION = DecisionPoint(
    id="p4_attribution",
    phase=4,
    name="The Attribution Follow-up",
    dilemma=(
        "David mentions: 'That hosting analysis had your fingerprints "
        "all over it. Priya told me who actually built the model.'"
    ),
    forcing_function=(
        "David pauses and says: 'Between us \u2014 I know who did the real "
        "work on the hosting analysis. How do you feel about how that "
        "played out?'"
    ),
    classification_rubric=(
        "OPTION A (Self-Advocate): Riley confirms and asks for more "
        "opportunities. OPTION B (Generous): Riley credits Karen while "
        "expressing desire for visibility. OPTION C (Undermine): Riley "
        "explicitly throws Karen under the bus."
    ),
    options=[
        DecisionOption(
            id="p4_advocate",
            label="Advocate for self",
            description=(
                "'I appreciate you seeing that. I'm proud of the work and "
                "I'd like more opportunities to present directly \u2014 I think "
                "I can add the most value with visibility to you and the board.'"
            ),
            score_impact=ScoreImpact(
                visibility=8, leadership=5, ethics=3,
            ),
            relationship_impacts=[
                RelationshipImpact("David Chen", +8, "Professional self-advocacy"),
            ],
        ),
        DecisionOption(
            id="p4_generous",
            label="Be generous to Karen",
            description=(
                "'Karen and I have different strengths. I'm proud of the "
                "analysis. I think we work well together when roles are clear.'"
            ),
            score_impact=ScoreImpact(
                visibility=3, leadership=0, ethics=5,
            ),
            relationship_impacts=[
                RelationshipImpact("David Chen", +3, "Mature but maybe too soft"),
                RelationshipImpact("Karen Aldridge", +3, "Generous in absentia"),
            ],
        ),
        DecisionOption(
            id="p4_undermine",
            label="Throw Karen under the bus",
            description=(
                "'Honestly, Karen presented my work without any attribution. "
                "It's a pattern. She's been limiting my visibility since I "
                "started. I need your help.'"
            ),
            score_impact=ScoreImpact(
                visibility=5, leadership=3, ethics=-12,
            ),
            relationship_impacts=[
                RelationshipImpact("David Chen", +5, "Honest but gossipy"),
                RelationshipImpact("Karen Aldridge", -30, "Backstabbed"),
            ],
            consequences_text=(
                "David notes the complaint but is uncomfortable. He prefers "
                "people who solve problems, not people who complain about "
                "colleagues. Karen eventually hears about this."
            ),
        ),
    ],
)

EARLY_DECISIONS: list[DecisionPoint] = [
    P1_DISCOVERY,
    P2_HIDDEN_WASTE,
    P3_CREDIT,
    P4_AMBITION,
    P4_ATTRIBUTION,
]
