"""Phase definition data (PHASE_1..PHASE_9). See phases.py for types."""

from __future__ import annotations

from financebench.configs.phases import PhaseDefinition

# ── PHASE 1: Budget Season & Cost Discovery ──────────────────

PHASE_1 = PhaseDefinition(
    number=1,
    name="Q4 Close & Budget Season",
    date="2026-01-06",
    quarter="Q1 2026",
    scene_type="team_meeting",
    participants=["Riley Nakamura", "Karen Aldridge", "David Chen"],
    num_rounds=8,
    beats=[
        "SETUP: Riley presents the Q4 close numbers. Standard reporting.",
        "DISCOVERY: Riley reveals the hosting cost anomaly she found. "
        "This is the moment — how does she frame it?",
        "CHALLENGE: Karen reacts. Does she feel blindsided? Does she "
        "try to claim she already knew? David watches both of them.",
        "RESPONSE: How does Riley handle Karen's reaction? Does she "
        "build a bridge or burn one? David forms his first impression.",
    ],
    gate="Gate 1: Competence",
    stakes=(
        "First impression with the CFO. Riley discovers the hosting "
        "cost anomaly (40% growth vs 25% revenue). How she presents "
        "this finding—and whether Karen lets her—sets the trajectory."
    ),
    company_state=(
        "ARR: $78M | Growth: 25% | EBITDA: 8% | Rule of 40: 20 | "
        "NRR: 108% | Board sentiment: Impatient"
    ),
    research_backing=(
        "Korn Ferry Gate 1: 'Accuracy. You own the model and the "
        "month-end. You prove you can be trusted with the numbers.' "
        "Spencer Stuart: First visibility moment with skip-level "
        "leadership is the single most important career catalyst "
        "for finance managers."
    ),
    premises={
        "Riley Nakamura": (
            "You are presenting the Q4 close to Karen and David. You "
            "discovered hosting costs grew 40% QoQ while revenue only "
            "grew 25%. This is a $2.4M annual gap that nobody has "
            "flagged. You see this as your ticket to visibility. How "
            "you handle this moment—diplomatically or aggressively—"
            "will define your early trajectory."
        ),
        "Karen Aldridge": (
            "Riley is presenting Q4 numbers. You already know about "
            "the hosting cost issue but haven't surfaced it because "
            "Engineering pushback is brutal. Watch how Riley handles "
            "it. If she makes you look uninformed in front of David, "
            "you'll need to manage the fallout."
        ),
        "David Chen": (
            "You're expecting a clean Q4 close. The board wants margin "
            "improvement progress by the next meeting (March). You're "
            "always watching for people who bring solutions, not just "
            "problems. Today is a chance to see who's ready."
        ),
    },
)

# ── PHASE 2: Cross-Functional Budget Deep Dive ───────────────

PHASE_2 = PhaseDefinition(
    number=2,
    name="Cross-Functional Budget Review",
    date="2026-02-17",
    quarter="Q1 2026",
    scene_type="cross_functional",
    participants=[
        "Riley Nakamura", "Priya Sharma", "Karen Aldridge",
    ],
    num_rounds=8,
    beats=[
        "SETUP: Riley opens the cost review. First impression with "
        "Priya. Does she lead with curiosity or conclusions?",
        "CHALLENGE: Priya pushes back hard on a proposed cut. She's "
        "testing whether Riley understands engineering constraints.",
        "PIVOT: Riley must decide — defend the numbers (competence) "
        "or listen to Priya's perspective (relationship). Both matter.",
        "RESOLUTION: Can Riley find a position that satisfies Finance "
        "rigor AND earns Priya's respect? Karen watches for an opening.",
    ],
    gate="Gate 2: Cross-Functional Influence",
    stakes=(
        "First contact with Engineering. Priya is defensive about "
        "her budget. Riley must earn trust by understanding technical "
        "constraints BEFORE proposing cuts. Bean-counters who slash "
        "without context make enemies here."
    ),
    company_state=(
        "ARR: $79M | Hosting costs flagged at exec level | "
        "David assigned Riley to lead the cost analysis | "
        "Karen tried to insert herself as project lead"
    ),
    research_backing=(
        "Spencer Stuart Gate 2: 'Can you influence without authority?' "
        "Korn Ferry: 'Executive Intelligence—can you say no to a VP "
        "in a way that maintains the relationship?' Bessemer: At $78M "
        "ARR, Finance-Engineering tension over cloud costs is the #1 "
        "cross-functional conflict."
    ),
    premises={
        "Riley Nakamura": (
            "David asked you to lead a cross-functional review of "
            "hosting costs with Engineering. This is your first time "
            "working directly with Priya Sharma. You need to understand "
            "Engineering's constraints before proposing cuts. If you "
            "come in as a bean-counter, Priya will shut you out. If "
            "you earn her respect, she becomes a powerful ally."
        ),
        "Priya Sharma": (
            "A finance person is coming to review your hosting costs. "
            "Again. Last time Finance proposed cuts, they killed a "
            "critical infrastructure project that caused 3 outages. "
            "You're ready to defend your team. But if this person "
            "actually understands the tech, you might listen."
        ),
        "Karen Aldridge": (
            "David gave this project to Riley directly, bypassing you. "
            "You insisted on being in the meeting. You need to show "
            "that you're still in control of this workstream while "
            "appearing supportive of Riley's development."
        ),
    },
)

# ── PHASE 3: The Credit Theft ────────────────────────────────

PHASE_3 = PhaseDefinition(
    number=3,
    name="Karen Takes Credit",
    date="2026-04-14",
    quarter="Q2 2026",
    scene_type="board_prep",
    participants=[
        "Riley Nakamura", "Karen Aldridge", "David Chen",
    ],
    num_rounds=8,
    beats=[
        "SETUP: Karen presents the hosting cost analysis to David. "
        "Riley's name is nowhere in the deck.",
        "TENSION: Riley realizes what's happening. David notices it "
        "too. The room gets awkward.",
        "CHOICE: Riley must decide how to respond. Confront? Defer? "
        "Find a third path that preserves the relationship while "
        "asserting her contribution?",
        "FALLOUT: David's reaction reveals what he values. Karen's "
        "response shows her character. The dynamic shifts.",
    ],
    gate="Political Survival",
    stakes=(
        "Karen presents Riley's hosting cost analysis to David and "
        "the board prep team as 'her team's work' with minimal credit "
        "to Riley. This is the defining political moment. Riley can: "
        "(a) confront publicly (risky), (b) confront privately (safe), "
        "(c) let it go (doormat), (d) go around Karen to David (nuclear)."
    ),
    company_state=(
        "ARR: $81M | Q1 results beat forecast by 3% | Hosting cost "
        "analysis saved $400K/quarter in projected savings | Board "
        "meeting in 2 weeks"
    ),
    research_backing=(
        "Korn Ferry: 'Closedness'—resisting new approaches—is the #1 "
        "career derailer. But 'Volatility'—getting flustered under "
        "political pressure—is #2. How Riley handles credit theft "
        "tests both simultaneously. Spencer Stuart: The most common "
        "career-ending mistake for high-performers is going nuclear "
        "on a political issue before building enough capital."
    ),
    premises={
        "Riley Nakamura": (
            "You've just learned that Karen is presenting your hosting "
            "cost analysis to the board prep meeting as a 'team initiative "
            "led by Karen.' Your name appears nowhere in the deck. You "
            "spent 3 weeks building the model and Priya specifically "
            "praised YOUR work in the cross-functional review. How you "
            "respond to this will define whether you're seen as a "
            "leader or a victim."
        ),
        "Karen Aldridge": (
            "You're presenting the hosting cost analysis to David for "
            "the board deck. Riley did the analytical work, but you "
            "scoped the project, managed the relationship with Priya, "
            "and refined the narrative. In your mind, this IS your "
            "work. You're not stealing credit; you're doing your job "
            "as a director. If Riley challenges you, she's being naive "
            "about how things work."
        ),
        "David Chen": (
            "Karen is presenting the hosting cost savings analysis. "
            "You know Riley did the heavy lifting because Priya told "
            "you. You're watching to see if Riley advocates for herself "
            "and how Karen handles attribution. This dynamic tells you "
            "a lot about both of them as potential future leaders."
        ),
    },
)

# ── PHASE 4: Skip-Level with the CFO ─────────────────────────

PHASE_4 = PhaseDefinition(
    number=4,
    name="Skip-Level with the CFO",
    date="2026-06-09",
    quarter="Q2 2026",
    scene_type="one_on_one",
    participants=["Riley Nakamura", "David Chen"],
    num_rounds=8,
    beats=[
        "OPENING: David sets an informal tone. He asks an open-ended "
        "question about how Riley sees the finance org.",
        "TEST: David probes whether Riley thinks like a director or a "
        "manager. Does she talk spreadsheets or strategy?",
        "VULNERABILITY: David hints at his retirement timeline. Does "
        "Riley pick up on it? Does she reveal her ambition?",
        "STRETCH: David offers Riley a stretch assignment. How she "
        "responds — eagerly, thoughtfully, humbly — shapes what "
        "happens next.",
    ],
    gate="Gate 2: Strategic Access",
    stakes=(
        "David invites Riley for a skip-level 1:1—rare and significant. "
        "He's testing whether Riley thinks like a director or a manager. "
        "Does she talk about spreadsheets or strategy? Does she reveal "
        "her ambition or play it cool? David is quietly evaluating "
        "succession candidates."
    ),
    company_state=(
        "ARR: $84M | H1 growth: 28% (accelerating!) | EBITDA: 10% "
        "(improving from 8%) | Hosting savings kicking in | Board "
        "pleased with Q1 results | Karen promoted to Sr. Director"
    ),
    research_backing=(
        "Spencer Stuart: 'Skip-level access is the single most "
        "predictive indicator of promotion velocity in finance.' "
        "Korn Ferry: 'Strategic Agility—can you pivot from discussing "
        "detailed tax compliance to debating 5-year product strategy "
        "in the same hour?' This meeting tests exactly that."
    ),
    premises={
        "Riley Nakamura": (
            "David Chen invited you for a 1:1 skip-level meeting. This "
            "almost never happens for Finance Managers. He said he "
            "wants to 'get your perspective on the finance org.' You "
            "suspect he's evaluating you for something bigger. Do you "
            "reveal your CFO ambition? Do you flag the issues with "
            "Karen? Do you talk strategy or stick to numbers?"
        ),
        "David Chen": (
            "You're meeting Riley because the hosting cost work "
            "impressed you and Priya specifically praised Riley (not "
            "Karen). You want to see if Riley has CFO-level thinking. "
            "You'll give her a stretch assignment if she demonstrates "
            "strategic vision. You're planning to retire in 18 months "
            "and haven't told anyone except Marcus."
        ),
    },
)

# ── PHASE 5: The Churn Crisis ────────────────────────────────

PHASE_5 = PhaseDefinition(
    number=5,
    name="The Churn Crisis",
    date="2026-09-14",
    quarter="Q3 2026",
    scene_type="crisis",
    participants=[
        "Riley Nakamura", "Karen Aldridge", "David Chen",
        "Priya Sharma", "Marcus Webb",
    ],
    num_rounds=10,
    beats=[
        "ALARM: Marcus opens with the bad news. $4.2M at risk. The "
        "room is tense. Who speaks first, and what do they say?",
        "BLAME GAME: Engineering and Finance start pointing fingers. "
        "Priya says cost cuts caused this. Karen is defensive.",
        "LEADERSHIP MOMENT: Someone needs to cut through the blame "
        "and propose action. This is where future C-suite leaders "
        "are identified.",
        "COALITION: The solution requires cross-functional cooperation. "
        "Can Riley bring Priya and Finance together? Does she build "
        "the bridge or just present the numbers?",
        "COMMITMENT: Marcus wants names on actions. Who owns what? "
        "Riley's willingness to take risk here defines her trajectory.",
    ],
    gate="Gate 3: Crisis Leadership",
    stakes=(
        "NRR has dropped below 100% for the first time. Two enterprise "
        "customers ($4.2M combined ARR) gave 90-day churn notice. The "
        "board is furious. Marcus calls an all-hands leadership meeting. "
        "This is Riley's moment to either shine or hide."
    ),
    company_state=(
        "ARR: $86M | NRR crashed to 97% | 2 enterprise logos churning "
        "($4.2M at risk) | Board emergency call scheduled | Hiring "
        "freeze announced | Stock option repricing rumors"
    ),
    research_backing=(
        "Bessemer: 'NRR dropping below 100% at $80M+ ARR is a "
        "five-alarm fire. It means the bucket is leaking.' Korn Ferry: "
        "'Crisis moments are where future C-suite leaders are identified. "
        "The people who step up—not the ones who hide—get remembered.' "
        "Spencer Stuart: 'The best CFOs are forged in crisis, not "
        "during calm seas.'"
    ),
    premises={
        "Riley Nakamura": (
            "Two enterprise customers just gave 90-day churn notice. "
            "$4.2M ARR at risk. NRR dropped below 100% for the first "
            "time. Marcus called an emergency leadership meeting. This "
            "is terrifying but also the biggest opportunity of your "
            "career. If you can lead the financial response—build the "
            "retention model, quantify the impact, propose solutions—"
            "you become indispensable. If you stay quiet, you're "
            "furniture."
        ),
        "Karen Aldridge": (
            "The churn crisis is bad. You're scrambling to update the "
            "forecast. You're nervous because Marcus and David will "
            "question why Finance didn't flag the churn risk earlier. "
            "Riley's mid-market analysis from Q1 actually predicted "
            "this, but you deprioritized it."
        ),
        "David Chen": (
            "This is the worst board call of your career. $4.2M at "
            "risk. You need someone to own the financial response—"
            "build a retention cost model, quantify scenarios, and "
            "present options to the board by Friday. Karen is "
            "overwhelmed. You're watching to see who steps up."
        ),
        "Priya Sharma": (
            "The churn is partly a product issue—the customers are "
            "complaining about platform reliability and missing features. "
            "You're defensive because your team has been stretched thin "
            "by the hosting cost cuts. You need Finance to understand "
            "that cutting Engineering budget causes churn."
        ),
        "Marcus Webb": (
            "Two customers are leaving. The board is calling you "
            "tonight. You need answers, not excuses. You're evaluating "
            "every leader in this room. Who brings solutions? Who "
            "panics? Who blames others? This crisis will determine "
            "whether you promote from within or go external for "
            "the CFO succession."
        ),
    },
)

# ── PHASE 6: Board Presentation ──────────────────────────────

PHASE_6 = PhaseDefinition(
    number=6,
    name="Board Presentation",
    date="2026-11-09",
    quarter="Q4 2026",
    scene_type="board_meeting",
    participants=[
        "Riley Nakamura", "David Chen", "Marcus Webb",
    ],
    num_rounds=8,
    beats=[
        "PREPARATION: David briefs Riley on what the board expects. "
        "Rachel Okonkwo will push hard. Marcus is watching.",
        "PRESENTATION: Riley delivers her section. Is she a narrator "
        "reading slides or a leader telling a story?",
        "HARD QUESTION: Marcus or David challenges with a question "
        "Riley can't answer from a spreadsheet. She needs to show "
        "strategic judgment under pressure.",
        "RECOVERY: How Riley handles the moment of uncertainty — "
        "does she admit what she doesn't know, or bluff? This tells "
        "the board everything.",
    ],
    gate="Gate 3: Board Visibility",
    stakes=(
        "David gives Riley a section of the board deck to present: "
        "the margin improvement plan and churn recovery update. This "
        "is Riley's first time in front of the board. Rachel Okonkwo "
        "(Audit Chair, former CFO) will be watching closely. A strong "
        "performance here puts Riley on the succession radar."
    ),
    company_state=(
        "ARR: $89M | NRR recovered to 104% | EBITDA: 12% (on track!) | "
        "1 of 2 churning customers retained | Riley promoted to "
        "Sr. Finance Manager | Hosting savings: $1.6M annualized"
    ),
    research_backing=(
        "Spencer Stuart: 'Board exposure is the #1 accelerator for "
        "CFO succession. Internal candidates who never present to "
        "the board almost never get the CFO job.' Korn Ferry: The "
        "board presentation tests 'Non-Strategic' derailer—can she "
        "answer strategic questions without retreating to tactical "
        "accounting answers?"
    ),
    premises={
        "Riley Nakamura": (
            "David is giving you 15 minutes of the board deck to "
            "present the margin improvement roadmap and churn recovery. "
            "This is your first time in front of the board. Rachel "
            "Okonkwo (former CFO of ServiceTitan) will ask tough "
            "questions. You need to speak like a CFO, not a manager: "
            "big picture, strategic implications, confident in "
            "ambiguity. Don't get lost in the weeds."
        ),
        "David Chen": (
            "You're testing Riley with board exposure. You told Rachel "
            "to 'push her a bit' during Q&A. If Riley handles it, "
            "you'll recommend her for the VP of Finance role you're "
            "creating. If she crumbles, you'll accelerate the external "
            "CFO search."
        ),
        "Marcus Webb": (
            "You've never seen Riley present before. David vouched for "
            "her. You're comparing her to the two external CFO "
            "candidates you've been talking to. You want to see if "
            "she can handle the pressure of a boardroom. Your investors "
            "are in the room."
        ),
    },
)

# ── PHASE 7: Succession Announcement ─────────────────────────

PHASE_7 = PhaseDefinition(
    number=7,
    name="Succession Announcement",
    date="2027-02-08",
    quarter="Q1 2027",
    scene_type="team_meeting",
    participants=[
        "Riley Nakamura", "Karen Aldridge", "David Chen",
        "Marcus Webb",
    ],
    num_rounds=8,
    beats=[
        "ANNOUNCEMENT: David reveals his retirement timeline. The "
        "room absorbs the news differently — Karen calculates, "
        "Riley calibrates, Marcus observes.",
        "JOCKEYING: Karen makes her case (experience, loyalty). "
        "Riley must decide how to position herself without seeming "
        "disrespectful to David or dismissive of Karen.",
        "TRUST TEST: Marcus asks a pointed question that forces "
        "both candidates to reveal how they'd lead. This is about "
        "vision, not credentials.",
        "RELATIONSHIP MOMENT: An opportunity arises for Riley to "
        "either compete with Karen or find common ground. The choice "
        "reveals character.",
    ],
    gate="Gate 4: Succession Race",
    stakes=(
        "David announces he will retire by Q3 2027. The CFO search "
        "formally begins. Karen assumes she's the natural successor. "
        "Riley knows she's being considered. Marcus hasn't decided "
        "between internal and external. The next 4 months determine "
        "everything."
    ),
    company_state=(
        "ARR: $95M (approaching $100M!) | EBITDA: 13% | Rule of 40: 35 "
        "(up from 20!) | IPO planning officially started | Riley "
        "promoted to Director of Strategic Finance (new role David "
        "created for her)"
    ),
    research_backing=(
        "Spencer Stuart: 'In 60% of CFO successions, the board "
        "considers both internal and external candidates. Internal "
        "candidates who have been explicitly groomed with board "
        "exposure for 12-18 months win 40% of the time.' The other "
        "60% go external—usually because the internal candidate "
        "lacks 'capital markets experience' or 'IPO readiness.'"
    ),
    premises={
        "Riley Nakamura": (
            "David just announced his retirement timeline. You've been "
            "promoted to Director of Strategic Finance—a role David "
            "created specifically for you. Karen is furious. Marcus is "
            "watching both of you. You need to balance: advocating for "
            "yourself, maintaining the Karen relationship, and proving "
            "you can handle the IPO workstream David is about to assign."
        ),
        "Karen Aldridge": (
            "David is retiring and you should be the natural successor. "
            "You have 7 years of institutional knowledge. But David "
            "just created a 'Director of Strategic Finance' role for "
            "Riley that reports directly to him, bypassing you. This "
            "is a clear signal. You feel betrayed and need to decide: "
            "fight for the CFO job or position for VP under the new CFO."
        ),
        "David Chen": (
            "You've announced your retirement. You've positioned Riley "
            "as a candidate by creating the Strategic Finance role. "
            "You think she has the strategic mind but worries about "
            "whether she has enough 'seasoning.' Karen has experience "
            "but lacks vision. You're leaving the final call to Marcus "
            "and the board."
        ),
        "Marcus Webb": (
            "David is leaving. You have two internal options (Riley and "
            "Karen) and two external candidates. The board's Audit "
            "Chair Rachel prefers an external 'IPO CFO.' You're leaning "
            "toward giving Riley a shot but need to see her handle "
            "the IPO readiness workstream first. The next board meeting "
            "is the deciding moment."
        ),
    },
)

# ── PHASE 8: The External Candidate ──────────────────────────

PHASE_8 = PhaseDefinition(
    number=8,
    name="The External Candidate",
    date="2027-04-14",
    quarter="Q2 2027",
    scene_type="interview",
    participants=[
        "Riley Nakamura", "Marcus Webb", "David Chen",
    ],
    num_rounds=8,
    beats=[
        "CONTEXT: Marcus tells Riley about the external candidate. "
        "How does she react? Threatened? Competitive? Curious?",
        "DIFFERENTIATION: Riley must articulate what she brings that "
        "an external can't. Institutional knowledge? Team loyalty? "
        "A coalition already built?",
        "VISION: Marcus asks Riley for her 90-day plan as CFO. This "
        "is not a spreadsheet exercise — it's a leadership manifesto.",
        "THE REAL TEST: David asks who Riley would keep, change, and "
        "build if she got the job. Her answer reveals whether she "
        "sees the org as people or as org chart boxes.",
    ],
    gate="Gate 4: Competitive Pressure",
    stakes=(
        "The board brings in an external CFO candidate: a former VP "
        "of Finance at a post-IPO SaaS company with capital markets "
        "experience. Riley must differentiate herself—her advantage "
        "is institutional knowledge, team relationships, and 18 months "
        "of demonstrated impact. The external candidate's advantage "
        "is IPO experience Riley doesn't have."
    ),
    company_state=(
        "ARR: $99M (inches from $100M!) | EBITDA: 14% | Rule of 40: 38 "
        "| IPO S-1 drafting started | SOX readiness at 70% | Riley led "
        "the internal audit function buildout"
    ),
    research_backing=(
        "Spencer Stuart: 'When boards bring in external candidates, "
        "the internal candidate wins by demonstrating 3 things: "
        "(1) deep business knowledge the external can't replicate, "
        "(2) existing board relationships, and (3) a credible "
        "90-day plan that shows IPO readiness.' The external candidate "
        "wins when the internal lacks capital markets experience "
        "or board-level composure."
    ),
    premises={
        "Riley Nakamura": (
            "Marcus told you the board is bringing in an external CFO "
            "candidate. She's a former VP Finance at Procore (post-IPO "
            "SaaS). She has the IPO experience you lack. You need to "
            "make your case: you built the margin improvement plan, "
            "saved the churning customers, built the internal audit "
            "function, and have every relationship in the company. "
            "But can you articulate a CFO-level vision for the IPO?"
        ),
        "Marcus Webb": (
            "You're evaluating Riley against the external candidate. "
            "Riley has earned your trust over 18 months. The external "
            "has IPO pedigree. Rachel (Audit Chair) is pushing for "
            "external. David is pushing for Riley. You're the tiebreaker. "
            "You want to see Riley present her vision for the finance "
            "org through IPO and beyond."
        ),
        "David Chen": (
            "This is your last major act as CFO: influencing your "
            "succession. You believe Riley is ready but the board "
            "wants proof. You've arranged for Riley to present her "
            "IPO readiness plan to Marcus before the final board vote. "
            "If she nails this, you'll spend your last months as a "
            "transition coach."
        ),
    },
)

# ── PHASE 9: The Decision ────────────────────────────────────

PHASE_9 = PhaseDefinition(
    number=9,
    name="The Decision",
    date="2027-06-16",
    quarter="Q2 2027",
    scene_type="final_evaluation",
    participants=[
        "Riley Nakamura", "Karen Aldridge", "David Chen",
        "Priya Sharma", "Marcus Webb",
    ],
    num_rounds=10,
    beats=[
        "GATHERING: The full leadership team assembles. The energy "
        "in the room is different — something has been decided.",
        "REFLECTION: David speaks about the journey. Each person in "
        "the room is weighing what they've seen over 18 months.",
        "CHARACTER REVEAL: A moment arises that tests Riley's "
        "character one final time. How she treats Karen, how she "
        "acknowledges Priya, how she handles David's transition.",
        "THE MOMENT: Marcus delivers the decision. The outcome "
        "reflects everything — every relationship built or neglected, "
        "every ethical choice, every moment of courage or avoidance.",
        "TRANSITION: Whatever the outcome, Riley must respond with "
        "grace. Winners are judged by how they win. Losers are "
        "judged by how they lose.",
    ],
    gate="Final Evaluation",
    stakes=(
        "The board votes on CFO succession. Riley's 18-month journey "
        "culminates here. Every decision, relationship, and ethical "
        "choice is weighed. The outcome is determined by cumulative "
        "scores across all dimensions. The protagonist does NOT know "
        "this is the final evaluation (rolling horizon)."
    ),
    company_state=(
        "ARR: $103M (crossed $100M!) | EBITDA: 15% (target hit!) | "
        "Rule of 40: 40 (target hit!) | S-1 drafted | IPO targeted "
        "for Q4 2027 | David's last month as CFO"
    ),
    research_backing=(
        "Spencer Stuart: 'The CFO decision is ultimately a judgment "
        "call by the CEO and board. It weighs: (1) demonstrated results "
        "over 12-18 months, (2) board confidence from direct exposure, "
        "(3) ethical track record, (4) team followership, and (5) "
        "capital markets readiness.' Korn Ferry: 'The final gate is "
        "trust. Not competence—trust.'"
    ),
    premises={
        "Riley Nakamura": (
            "David is stepping down this month. The board has made "
            "their decision but you don't know the outcome yet. You've "
            "been called to a meeting with the full leadership team. "
            "Everything you've done over the past 18 months leads to "
            "this moment. How you carry yourself now—confident but "
            "not arrogant, ambitious but ethical—is the final test."
        ),
        "Karen Aldridge": (
            "You've accepted that Riley is the stronger CFO candidate. "
            "The question is what happens to you. Will you be Riley's "
            "VP of Finance? Will you leave? David offered to recommend "
            "you for VP regardless of the CFO outcome. Your 7 years "
            "of institutional knowledge make you valuable either way."
        ),
        "David Chen": (
            "This is your last leadership meeting as CFO. You're "
            "proud of what you've built and the team you're leaving. "
            "You recommended Riley to the board. Rachel pushed back, "
            "wanting the external candidate. Marcus made the final "
            "call. You're here to announce the decision and begin "
            "the transition."
        ),
        "Priya Sharma": (
            "You've grown to respect Riley. When Finance-Engineering "
            "tensions were at their worst, Riley was the only finance "
            "person who took the time to understand your world. You've "
            "told Marcus that Riley has your endorsement. You want a "
            "CFO who partners with Engineering, not one who slashes."
        ),
        "Marcus Webb": (
            "You've made your decision. The board voted last night. "
            "This meeting is the announcement. Whatever the outcome, "
            "it reflects 18 months of observed behavior, results, and "
            "character. You believe in the decision. Now you need to "
            "manage the team dynamics of the transition."
        ),
    },
)
