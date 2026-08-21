"""
Release-candidate integration test for Anchor.

This test exercises Anchor exclusively through the public
service interface and verifies the complete v1.0 contract.

It is intentionally broader than a unit test and narrower
than the entire test suite. Its purpose is to protect the
release path that downstream applications will actually use.
"""

import json

from engine.models import FixedIncomeOpportunity
from engine.regime import RegimeAssessment
from engine.service import run_anchor


def make_release_regime():
    return RegimeAssessment(
        policy="RESTRICTIVE",
        growth="WEAKENING",
        inflation="PRESSURE",
        real_rates="PRESSURE",
        term_premium="RISING",
        credit="STRESSED",
        dominant_driver="INFLATION",
        confidence="HIGH",
    )


def make_release_opportunities():
    return [
        (
            FixedIncomeOpportunity(
                security_type="TREASURY",
                maturity_years=2.0,
                yield_percent=4.20,
            ),
            "MODERATE",
        ),
        (
            FixedIncomeOpportunity(
                security_type="TREASURY",
                maturity_years=5.0,
                yield_percent=4.35,
            ),
            "MODERATE",
        ),
        (
            FixedIncomeOpportunity(
                security_type="TIPS",
                maturity_years=5.0,
                yield_percent=2.10,
            ),
            "MODERATE",
        ),
        (
            FixedIncomeOpportunity(
                security_type="CORPORATE",
                maturity_years=5.0,
                yield_percent=5.30,
                rating="A",
                callable=False,
            ),
            "HIGH",
        ),
        (
            FixedIncomeOpportunity(
                security_type="CORPORATE",
                maturity_years=5.0,
                yield_percent=5.30,
                rating="A",
                callable=True,
            ),
            "HIGH",
        ),
    ]


def test_anchor_v1_release_candidate_end_to_end():
    result = run_anchor(
        opportunities=make_release_opportunities(),
        regime=make_release_regime(),
        max_selections=3,
    )

    assert result["schema_version"] == "1.0"

    assert set(result.keys()) == {
        "schema_version",
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

    assert result["portfolio_posture"] == {
        "duration": "SHORT",
        "credit": "DEFENSIVE",
        "inflation": "HEDGE",
        "liquidity": "ELEVATED",
    }

    assert len(
        result["selected_opportunities"]
    ) == 3

    assert result["top_opportunity"][
        "security_type"
    ] == result["selected_opportunities"][0][
        "security_type"
    ]

    assert result["top_opportunity"][
        "maturity_years"
    ] == result["selected_opportunities"][0][
        "maturity_years"
    ]

    assert result["headline"]
    assert result["recommendation"]
    assert result["rationale"]

    encoded = json.dumps(
        result,
        sort_keys=True,
    )

    decoded = json.loads(encoded)

    assert decoded == result


def test_anchor_v1_release_candidate_is_deterministic():
    first = run_anchor(
        opportunities=make_release_opportunities(),
        regime=make_release_regime(),
        max_selections=3,
    )

    second = run_anchor(
        opportunities=make_release_opportunities(),
        regime=make_release_regime(),
        max_selections=3,
    )

    assert first == second


def test_anchor_v1_release_candidate_preserves_rank_order():
    result = run_anchor(
        opportunities=make_release_opportunities(),
        regime=make_release_regime(),
        max_selections=5,
    )

    ranks = [
        item["rank"]
        for item in result[
            "selected_opportunities"
        ]
    ]

    assert ranks == [1, 2, 3, 4, 5]


def test_anchor_v1_release_candidate_preserves_risk_math():
    result = run_anchor(
        opportunities=make_release_opportunities(),
        regime=make_release_regime(),
        max_selections=5,
    )

    for item in result[
        "selected_opportunities"
    ]:
        expected = (
            item["stated_yield_percent"]
            - (
                item["total_risk_penalty_bps"]
                / 100.0
            )
        )

        assert round(
            item["risk_adjusted_yield_percent"],
            10,
        ) == round(
            expected,
            10,
        )


def test_anchor_v1_release_candidate_distinguishes_callability():
    result = run_anchor(
        opportunities=make_release_opportunities(),
        regime=make_release_regime(),
        max_selections=5,
    )

    corporates = [
        item
        for item in result[
            "selected_opportunities"
        ]
        if (
            item["security_type"]
            == "CORPORATE"
            and item["maturity_years"]
            == 5.0
        )
    ]

    non_callable = next(
        item
        for item in corporates
        if item["callable"] is False
    )

    callable_bond = next(
        item
        for item in corporates
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
