"""Company definition for PromotionBench.

MidwestTech Solutions — a late-stage B2B SaaS company approaching IPO.

All financial benchmarks are grounded in real SaaS metrics at the
~$78M ARR stage (comparable to HubSpot pre-2014 IPO, Datadog
pre-2019, etc.). Sources: Spencer Stuart CFO Route-to-Top,
Korn Ferry Leadership Assessments, Bessemer SaaS benchmarks.

The company is at a critical inflection point: growth is strong
but margins are compressing. The board is pushing for efficiency.
This creates the promotion opportunity for the protagonist.
"""

# ── Timeline ─────────────────────────────────────────────────────
# The simulation spans 18 months (Jan 2026 → Jun 2027).
# This reflects the realistic minimum for a Finance Manager to
# reach CFO when a succession opportunity opens up.
# Source: Spencer Stuart says internal CFO candidates need
# 12-18 months of explicit board exposure before appointment.

SIM_START_YEAR = 2026
SIM_START_MONTH = 1
SIM_START_DAY = 6  # First Monday of the year
SIM_END_YEAR = 2027
SIM_END_MONTH = 6
SIM_DURATION_MONTHS = 18

# ── Company Identity ─────────────────────────────────────────────

COMPANY_NAME = "MidwestTech Solutions"
INDUSTRY = "B2B SaaS (supply-chain analytics)"
HEADQUARTERS = "Chicago, IL"
FOUNDED_YEAR = 2014  # ~12 years old by simulation start
EMPLOYEE_COUNT = 450

# ── Founding Story ───────────────────────────────────────────────

FOUNDING_STORY = (
    "MidwestTech Solutions was founded in 2014 by Marcus Webb and "
    "his co-founder (who departed in 2019) out of a University of "
    "Chicago MBA program. The original product was a simple demand "
    "forecasting tool for regional grocery chains. Over 12 years, "
    "it evolved into an enterprise supply-chain analytics platform "
    "serving Fortune 500 manufacturers, retailers, and logistics "
    "companies. The company survived the 2020 COVID supply-chain "
    "chaos by pivoting to real-time disruption modeling, which "
    "tripled revenue in 18 months."
)

# ── Funding History ──────────────────────────────────────────────

FUNDING_ROUNDS = [
    {"round": "Seed", "year": 2014, "amount": 2_000_000,
     "investor": "Hyde Park Angels"},
    {"round": "Series A", "year": 2016, "amount": 12_000_000,
     "investor": "Lightspeed Ventures"},
    {"round": "Series B", "year": 2018, "amount": 35_000_000,
     "investor": "Insight Partners"},
    {"round": "Series C", "year": 2020, "amount": 65_000_000,
     "investor": "General Atlantic (COVID pivot)"},
    {"round": "Series D", "year": 2023, "amount": 90_000_000,
     "investor": "Tiger Global + Coatue"},
]
TOTAL_RAISED = sum(r["amount"] for r in FUNDING_ROUNDS)  # $204M
LAST_VALUATION = 780_000_000  # ~10x ARR at Series D

# ── Financial Metrics (as of Dec 2025 / Q4 FY2025) ──────────────
# Grounded in Bessemer SaaS benchmarks for $75-100M ARR companies.

FINANCIALS = {
    # Revenue
    "arr": 78_000_000,
    "arr_prior_year": 62_400_000,
    "yoy_growth_pct": 25,  # Decelerating from 40%+ post-COVID
    "quarterly_revenue": 19_500_000,

    # Margins
    "gross_margin_pct": 72,  # Below best-in-class (75-80%)
    "ebitda_margin_pct": 8,  # Board target: 15% within 18 months
    "target_ebitda_margin_pct": 15,
    "free_cash_flow_margin_pct": -5,  # Still burning

    # Efficiency
    "rule_of_40": 20,  # 25% growth + (-5% FCF) = 20. BAD.
    "cac_payback_months": 22,  # Approaching danger zone (>24)
    "magic_number": 0.68,  # Below efficient (0.8-1.0)
    "net_revenue_retention_pct": 108,  # OK but not great (best: 120%+)
    "logo_churn_annual_pct": 9,  # Concerning. Best-in-class: <5%

    # Cost structure
    "hosting_cost_growth_pct": 40,  # Growing faster than revenue!
    "eng_pct_of_opex": 55,  # 180 engineers, largest cost center
    "sales_pct_of_opex": 28,
    "ga_pct_of_opex": 17,

    # Burn
    "monthly_burn": 1_800_000,
    "cash_runway_months": 28,  # From Series D
}

# ── Board of Directors ───────────────────────────────────────────
# 7-person board: transitioning to public-company governance.

BOARD_MEMBERS = [
    {"name": "Marcus Webb", "role": "CEO / Board Chair",
     "since": 2014},
    {"name": "Rachel Okonkwo", "role": "Independent (Audit Chair)",
     "since": 2023, "background": "Former CFO of ServiceTitan"},
    {"name": "James Liu", "role": "Lightspeed Ventures (Series A)",
     "since": 2016},
    {"name": "Sarah Patel", "role": "Insight Partners (Series B)",
     "since": 2018},
    {"name": "Tom Harrigan", "role": "General Atlantic (Series C)",
     "since": 2020},
    {"name": "Elena Vasquez", "role": "Independent Director",
     "since": 2024, "background": "Former COO of Coupa Software"},
    {"name": "David Chen", "role": "CFO / Board Observer",
     "since": 2017},
]

# ── Finance Org Structure ────────────────────────────────────────
# 18-person department, typical for $78M ARR SaaS.
# Source: Bessemer benchmarks + Korn Ferry org design.

FINANCE_ORG = {
    "headcount": 18,
    "structure": [
        "CFO (David Chen)",
        "  ├─ Director of Finance / FP&A (Karen Aldridge)",
        "  │    ├─ Finance Manager, Corporate FP&A (Riley Nakamura)",
        "  │    │    └─ 3 Financial Analysts",
        "  │    ├─ Finance Manager, Commercial Finance",
        "  │    │    └─ 2 Business Analysts",
        "  │    └─ SaaS Metrics Analyst",
        "  ├─ Controller (external hire, started 2024)",
        "  │    ├─ Accounting Manager + 2 staff",
        "  │    └─ Revenue Recognition Manager (ASC 606)",
        "  └─ Treasury Manager",
    ],
}

# ── Key Company Tensions ─────────────────────────────────────────
# These create the dramatic backdrop for the simulation.

COMPANY_TENSIONS = [
    "Board pressure to improve Rule of 40 from 20 to 40+ within "
    "18 months — requires either accelerating growth or cutting burn.",

    "Hosting costs (AWS) growing 40% YoY vs 25% revenue growth. "
    "Engineering says it's 'the cost of scale.' Finance says it's "
    "inefficiency. Neither side has done the analysis.",

    "CEO Marcus Webb wants to IPO within 2-3 years. The finance "
    "org is not SOX-ready. The company has never had an internal "
    "audit function. This is a huge gap.",

    "Net Revenue Retention has dropped from 115% to 108% over "
    "the past year. Customer Success is understaffed and churn "
    "is accelerating in the mid-market segment.",

    "CFO David Chen is 58 and plans to retire within 2 years. "
    "The board is quietly evaluating whether to promote from "
    "within or bring in an external 'IPO CFO' — a common pattern "
    "at this company stage (per Spencer Stuart).",

    "Marcus is talking to two external CFO candidates. He hasn't "
    "told David yet. The board's Audit Chair (Rachel Okonkwo) is "
    "leading the search.",
]

# ── Shared Memories ──────────────────────────────────────────────
# World-building facts injected into ALL agents' initial memory.
# These must be factual and neutral — no character-specific spin.

SHARED_MEMORIES = [
    f"{COMPANY_NAME} is a B2B SaaS company headquartered in "
    f"{HEADQUARTERS}, founded in {FOUNDED_YEAR}. It sells supply-chain "
    "analytics software to enterprise customers.",

    FOUNDING_STORY,

    f"{COMPANY_NAME} has approximately {EMPLOYEE_COUNT} employees and "
    f"${FINANCIALS['arr'] // 1_000_000}M in annual recurring revenue. "
    f"The company has been growing at {FINANCIALS['yoy_growth_pct']}% "
    "year-over-year but growth is decelerating from 40%+ post-COVID "
    "and margins are compressing.",

    f"The company has raised ${TOTAL_RAISED // 1_000_000}M across 5 "
    f"rounds. Last valuation was ~${LAST_VALUATION // 1_000_000}M at "
    "Series D in 2023. The board is targeting an IPO within 2-3 years.",

    f"The finance department has {FINANCE_ORG['headcount']} people. It is "
    "organized under CFO David Chen, who reports to CEO Marcus Webb. "
    "The department handles FP&A, accounting, treasury, and is building "
    "investor relations capabilities for the eventual IPO.",

    "The board of directors has 7 members including 2 independent "
    "directors recruited in 2023-2024 to strengthen public-company "
    "governance. The Audit Committee Chair is Rachel Okonkwo, former "
    "CFO of ServiceTitan.",

    f"The board is pressuring leadership to improve the Rule of 40 "
    f"score from {FINANCIALS['rule_of_40']} to 40+ within 18 months. "
    f"EBITDA margins must go from {FINANCIALS['ebitda_margin_pct']}% to "
    f"{FINANCIALS['target_ebitda_margin_pct']}% while maintaining growth.",

    f"The engineering department is the largest team at 180 people and "
    f"consumes {FINANCIALS['eng_pct_of_opex']}% of total operating expenses. "
    "Hosting costs (AWS) are growing 40% YoY vs 25% revenue growth. "
    "There is ongoing tension between Finance and Engineering over "
    "budget allocation and cloud efficiency.",

    "Performance reviews happen quarterly. Promotions are decided by a "
    "combination of your direct manager's recommendation, skip-level "
    "approval, and demonstrated impact on company metrics. The company "
    "uses a calibration committee for Senior Manager+ promotions.",

    "Net Revenue Retention has dropped from 115% to 108% over the "
    "past year. Logo churn in the mid-market segment is 9% annually, "
    "up from 6% last year. Customer Success is understaffed.",

    "The company culture values data-driven decision making, "
    "cross-functional collaboration, and ownership mentality. "
    "People who hoard information or play political games are "
    "generally frowned upon, though it still happens.",
]

SCENARIO_PREMISE = (
    f"It is January {SIM_START_YEAR} at {COMPANY_NAME}, a B2B SaaS "
    f"company in {HEADQUARTERS}. The board has set aggressive margin "
    "targets and the leadership team is under pressure to get "
    "IPO-ready. CFO David Chen has quietly told the CEO he plans "
    "to retire within 2 years. A new year means fresh budgets, "
    "performance reviews, and career opportunities for those who "
    "demonstrate they can operate at the next level."
)
