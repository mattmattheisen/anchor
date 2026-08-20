"""
System-level acceptance tests for Anchor.

These tests evaluate Anchor as a complete deterministic
decision system using realistic groups of competing
fixed-income opportunities.

Unlike unit tests, these tests are concerned with the
coherence of the final decision rather than the behavior
of an individual function.
"""

import json

from engine.models import FixedIncomeOpportunity
from engine.regime import RegimeAssessment
from engine.service import run_anchor


def make_neutral_regime():
    """
    Construct a broadly neutral regime in which Anchor
    should be free to distinguish securities primarily
    through relative value and security-level risk.
    """

    return RegimeAssessment(
        policy="NEUTRAL",
        growth="NEUTRAL",
        inflation="STABLE",
        real_rates="STABLE",
        term_premium="NEUTRAL",
        credit="BENIGN",
        dominant_driver="MIXED",
        confidence="MEDIUM",
    )


def make_realistic_opportunity_set():
    """
    Construct a diversified fixed-income opportunity set.

    The securities intentionally vary across:

    - maturity,
    - security type,
    - nominal yield,
    - credit exposure,
    - inflation protection,
    - callability,
    - relative-value compensation.
    """

    treasury_2y = FixedIncomeOpportunity(
        security_type="TREASURY",
        maturity_years=2.0,
        yield_percent=4.20,
    )

    treasury_5y = FixedIncomeOpportunity(
        security_type="TREASURY",
        maturity_years=5.0,
        yield_percent=4.35,
    )

    tips_5y = FixedIncomeOpportunity(
        security_type="TIPS",
        maturity_years=5.0,
        yield_percent=2.10,
    )

    corporate_5y = FixedIncomeOpportunity(
        security_type="CORPORATE",
        maturity_years=5.0,
        yield_percent=5.30,
        rating="A",
        callable=False,
    )

    callable_corporate_5y = FixedIncomeOpportunity(
        security_type="CORPORATE",
        maturity_years=5.0,
        yield_percent=5.30,
        rating="A",
        callable=True,
    )

    return [
        (treasury_2y, "MODERATE"),
        (treasury_5y, "MODERATE"),
        (tips_5y, "MODERATE"),
        (corporate_5y, "HIGH"),
        (callable_corporate_5y, "HIGH"),
    ]


def test_realistic_fixed_income_scenario_runs_end_to_end():
    result = run_anchor(
        opportunities=make_realistic_opportunity_set(),
        regime=make_neutral_regime(),
    )

    assert isinstance(result, dict)

    encoded = json.dumps(result)

    assert isinstance(encoded, str)


def test_realistic_scenario_produces_three_selections():
    result = run_anchor(
        opportunities=make_realistic_opportunity_set(),
        regime=make_neutral_regime(),
        max_selections=3,
    )

    assert len(
        result["selected_opportunities"]
    ) == 3


def test_realistic_scenario_has_single_top_opportunity():
    result = run_anchor(
        opportunities=make_realistic_opportunity_set(),
        regime=make_neutral_regime(),
    )

    assert result["top_opportunity"] is not None

    assert (
        result["top_opportunity"]["security_type"]
        == result["selected_opportunities"][0][
            "security_type"
        ]
    )

    assert (
        result["top_opportunity"]["maturity_years"]
        == result["selected_opportunities"][0][
            "maturity_years"
        ]
    )


def test_non_callable_corporate_beats_identical_callable_bond():
    result = run_anchor(
        opportunities=make_realistic_opportunity_set(),
        regime=make_neutral_regime(),
        max_selections=5,
    )

    corporate_results = [
        item
        for item in result["selected_opportunities"]
        if (
            item["security_type"] == "CORPORATE"
            and item["maturity_years"] == 5.0
        )
    ]

    assert len(corporate_results) == 2

    non_callable = next(
        item
        for item in corporate_results
        if item["callable"] is False
    )

    callable_bond = next(
        item
        for item in corporate_results
        if item["callable"] is True
    )

    assert (
        non_callable["total_risk_penalty_bps"]
        < callable_bond["total_risk_penalty_bps"]
    )

    assert (
        non_callable["risk_adjusted_yield_percent"]
        > callable_bond["risk_adjusted_yield_percent"]
    )

    assert (
        non_callable["rank"]
        < callable_bond["rank"]
    )


def test_callable_penalty_is_exactly_separated():
    result = run_anchor(
        opportunities=make_realistic_opportunity_set(),
        regime=make_neutral_regime(),
        max_selections=5,
    )

    corporate_results = [
        item
        for item in result["selected_opportunities"]
        if (
            item["security_type"] == "CORPORATE"
            and item["maturity_years"] == 5.0
        )
    ]

    non_callable = next(
        item
        for item in corporate_results
        if item["callable"] is False
    )

    callable_bond = next(
        item
        for item in corporate_results
        if item["callable"] is True
    )

    assert (
        callable_bond["total_risk_penalty_bps"]
        - non_callable["total_risk_penalty_bps"]
        == 30.0
    )


def test_selected_opportunities_remain_rank_ordered():
    result = run_anchor(
        opportunities=make_realistic_opportunity_set(),
        regime=make_neutral_regime(),
        max_selections=5,
    )

    ranks = [
        item["rank"]
        for item in result["selected_opportunities"]
    ]

    assert ranks == sorted(ranks)


def test_risk_adjusted_yield_never_exceeds_stated_yield():
    result = run_anchor(
        opportunities=make_realistic_opportunity_set(),
        regime=make_neutral_regime(),
        max_selections=5,
    )

    for item in result["selected_opportunities"]:
        assert (
            item["risk_adjusted_yield_percent"]
            <= item["stated_yield_percent"]
        )


def test_neutral_regime_produces_coherent_portfolio_posture():
    result = run_anchor(
        opportunities=make_realistic_opportunity_set(),
        regime=make_neutral_regime(),
    )

    posture = result["portfolio_posture"]

    assert set(posture.keys()) == {
        "duration",
        "credit",
        "inflation",
        "liquidity",
    }

    assert all(
        value is not None
        for value in posture.values()
    )


def test_acceptance_output_contains_explanation():
    result = run_anchor(
        opportunities=make_realistic_opportunity_set(),
        regime=make_neutral_regime(),
    )

    assert result["headline"]
    assert result["recommendation"]
    assert result["rationale"]


def test_acceptance_output_preserves_public_contract():
    result = run_anchor(
        opportunities=make_realistic_opportunity_set(),
        regime=make_neutral_regime(),
    )

    assert set(result.keys()) == {
        "headline",
        "recommendation",
        "portfolio_posture",
        "preferred_exposures",
        "exposures_to_limit",
        "top_opportunity",
        "selected_opportunities",
        "rationale",
        "cautions",
    }
