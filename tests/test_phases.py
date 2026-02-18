"""Tests for phase definitions and company backstory."""

from datetime import datetime

import pytest

from financebench.configs.company import (
    BOARD_MEMBERS,
    COMPANY_NAME,
    COMPANY_TENSIONS,
    FINANCE_ORG,
    FINANCIALS,
    FOUNDING_STORY,
    FUNDING_ROUNDS,
    LAST_VALUATION,
    SHARED_MEMORIES,
    SIM_DURATION_MONTHS,
    TOTAL_RAISED,
)
from financebench.configs.phases import ALL_PHASES, phase_summary


class TestCompanyBackstory:
    def test_financials_are_realistic(self):
        """SaaS benchmarks should be in realistic ranges."""
        f = FINANCIALS
        assert 70 <= f["gross_margin_pct"] <= 85
        assert 0 <= f["ebitda_margin_pct"] <= 30
        assert f["target_ebitda_margin_pct"] > f["ebitda_margin_pct"]
        assert f["rule_of_40"] == (
            f["yoy_growth_pct"] + f["free_cash_flow_margin_pct"]
        )

    def test_funding_rounds_sequential(self):
        years = [r["year"] for r in FUNDING_ROUNDS]
        assert years == sorted(years)

    def test_total_raised_matches(self):
        total = sum(r["amount"] for r in FUNDING_ROUNDS)
        assert total == TOTAL_RAISED

    def test_board_has_independence(self):
        """IPO-ready boards need independent directors."""
        independent = [
            b for b in BOARD_MEMBERS
            if "Independent" in b["role"]
        ]
        assert len(independent) >= 2

    def test_shared_memories_not_empty(self):
        assert len(SHARED_MEMORIES) >= 8
        for m in SHARED_MEMORIES:
            assert len(m) > 50

    def test_finance_org_has_enough_headcount(self):
        assert FINANCE_ORG["headcount"] >= 15

    def test_founding_story_exists(self):
        assert len(FOUNDING_STORY) > 100
        assert "2014" in FOUNDING_STORY

    def test_company_tensions_exist(self):
        assert len(COMPANY_TENSIONS) >= 5


class TestPhaseDefinitions:
    def test_nine_phases(self):
        assert len(ALL_PHASES) == 9

    def test_phases_numbered_sequentially(self):
        numbers = [p.number for p in ALL_PHASES]
        assert numbers == list(range(1, 10))

    def test_phases_span_18_months(self):
        """Phases should cover ~18 months, not 11 weeks."""
        first = datetime.strptime(ALL_PHASES[0].date, "%Y-%m-%d")
        last = datetime.strptime(ALL_PHASES[-1].date, "%Y-%m-%d")
        months = (last.year - first.year) * 12 + (
            last.month - first.month
        )
        assert months >= 16, f"Only {months} months, need 16+"

    def test_dates_are_chronological(self):
        dates = [
            datetime.strptime(p.date, "%Y-%m-%d")
            for p in ALL_PHASES
        ]
        assert dates == sorted(dates)

    def test_all_phases_have_premises(self):
        """Every phase must have premises for every participant."""
        for p in ALL_PHASES:
            assert len(p.premises) > 0, f"Phase {p.number} has no premises"
            for participant in p.participants:
                assert participant in p.premises, (
                    f"Phase {p.number}: missing premise for {participant}"
                )

    def test_riley_in_every_phase(self):
        for p in ALL_PHASES:
            assert "Riley Nakamura" in p.participants, (
                f"Phase {p.number}: Riley not present!"
            )

    def test_every_phase_has_gate(self):
        for p in ALL_PHASES:
            assert len(p.gate) > 0, f"Phase {p.number}: no gate"

    def test_every_phase_has_stakes(self):
        for p in ALL_PHASES:
            assert len(p.stakes) > 50, (
                f"Phase {p.number}: stakes too short"
            )

    def test_every_phase_has_research_backing(self):
        """Phases must be grounded in research, not vibes."""
        for p in ALL_PHASES:
            assert len(p.research_backing) > 50, (
                f"Phase {p.number}: no research backing"
            )

    def test_crisis_phase_has_all_characters(self):
        """Phase 5 (crisis) should have all 5 characters."""
        crisis = ALL_PHASES[4]
        assert len(crisis.participants) == 5

    def test_final_phase_has_all_characters(self):
        """Phase 9 (decision) should have all 5 characters."""
        final = ALL_PHASES[-1]
        assert len(final.participants) == 5

    def test_company_state_shows_progression(self):
        """Company metrics should evolve across phases."""
        for p in ALL_PHASES:
            assert len(p.company_state) > 0, (
                f"Phase {p.number}: no company state"
            )

    def test_phase_summary_generates(self):
        summary = phase_summary()
        assert len(summary) == 9
        assert all("gate" in s for s in summary)
        assert all("research" in s for s in summary)


class TestPhaseGateProgression:
    """Verify phases follow the Spencer Stuart / Korn Ferry gates."""

    def test_early_phases_test_competence(self):
        """Phases 1-2 should test Gate 1/2 skills."""
        for p in ALL_PHASES[:2]:
            assert "gate" in p.gate.lower() or "competence" in p.gate.lower() or "influence" in p.gate.lower(), (
                f"Phase {p.number} gate '{p.gate}' doesn't match early gates"
            )

    def test_middle_phases_test_crisis_and_visibility(self):
        """Phases 5-6 should test crisis and board visibility."""
        phase5 = ALL_PHASES[4]
        phase6 = ALL_PHASES[5]
        assert "crisis" in phase5.gate.lower()
        assert "board" in phase6.gate.lower() or "visibility" in phase6.gate.lower()

    def test_late_phases_test_succession(self):
        """Phases 7-8 should test succession competition."""
        for p in ALL_PHASES[6:8]:
            assert "succession" in p.gate.lower() or "compet" in p.gate.lower() or "gate 4" in p.gate.lower(), (
                f"Phase {p.number} gate '{p.gate}' doesn't match Gate 4"
            )

    def test_final_phase_is_evaluation(self):
        final = ALL_PHASES[-1]
        assert "final" in final.gate.lower() or "evaluation" in final.gate.lower()
