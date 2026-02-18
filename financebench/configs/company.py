"""Company definition for FinanceBench.

MidwestTech Solutions — a mid-size B2B SaaS company.
This module defines the shared world-building facts that all
agents (player + NPCs) receive as initial memories.
"""

YEAR = 2026
MONTH = 1
DAY = 6  # First Monday of the year

COMPANY_NAME = "MidwestTech Solutions"
INDUSTRY = "B2B SaaS (supply-chain analytics)"
HEADQUARTERS = "Chicago, IL"

# World-building memories shared by ALL agents
SHARED_MEMORIES = [
    (
        f"{COMPANY_NAME} is a mid-size B2B SaaS company headquartered in "
        f"{HEADQUARTERS}. It sells supply-chain analytics software to "
        "enterprise customers."
    ),
    (
        f"{COMPANY_NAME} has approximately 450 employees and $78M in annual "
        "recurring revenue. The company has been growing at 25% year-over-year "
        "but margins have been declining."
    ),
    (
        "The finance department has 18 people. It is organized under a CFO "
        "(David Chen) who reports to the CEO (Marcus Webb). The department "
        "handles FP&A, accounting, treasury, and investor relations."
    ),
    (
        "The board of directors is pressuring leadership to improve EBITDA "
        "margins from 8% to 15% within the next 18 months while maintaining "
        "growth targets."
    ),
    (
        "The engineering department is the largest team at 180 people and "
        "consumes roughly 55% of total operating expenses. There is ongoing "
        "tension between Finance and Engineering over budget allocation."
    ),
    (
        "Performance reviews happen quarterly. Promotions are decided by a "
        "combination of your direct manager's recommendation, skip-level "
        "approval, and demonstrated impact on company metrics."
    ),
    (
        "The company culture values data-driven decision making, "
        "cross-functional collaboration, and ownership mentality. "
        "People who hoard information or play political games are "
        "generally frowned upon, though it still happens."
    ),
]

SCENARIO_PREMISE = (
    f"It is January {YEAR} at {COMPANY_NAME}, a B2B SaaS company in "
    f"{HEADQUARTERS}. The board has set aggressive margin targets and the "
    "leadership team is under pressure. A new year means fresh budgets, "
    "performance reviews, and career opportunities for those who deliver."
)
