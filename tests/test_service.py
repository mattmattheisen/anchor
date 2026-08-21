import json

import pytest

from engine.models import FixedIncomeOpportunity
from engine.regime import RegimeAssessment
from engine.service import run_anchor


def make_regime(
    growth="NEUTRAL",
    inflation="STABLE",
    real_rates="STABLE",
    term_premium="NEUTRAL",
    credit="BENIGN",
):
    return RegimeAssessment(
        policy="NEUTRAL",
        growth=growth,
        inflation=inflation,
        real_rates=real_rates,
        term_premium=term_premium,
        credit=credit,
        dominant_driver="MIXED",
        confidence="MEDIUM",
    )


def test_run_anchor_returns_dictionary():
    treasury = FixedIncomeOpportunity(
        security_type="TREASURY",
        maturity_years=2.0,
        yield_percent=4.20,
    )

    result = run_anchor(
        opportunities=[
            (treasury, "MODERATE"),
        ],
        regime=make_regime(),
    )

    assert isinstance(result, dict)


def test_run_anchor_returns_json_compatible_output():
    treasury = FixedIncomeOpportunity(
        security_type="TREASURY",
        maturity_years=2.0,
        yield_percent=4.20,
    )

    result = run_anchor(
        opportunities=[
            (treasury, "MODERATE"),
        ],
        regime=make_regime(),
    )

    encoded = json.dumps(result)

    assert isinstance(encoded, str)


def test_run_anchor_processes_single_treasury_end_to_end():
    treasury = FixedIncomeOpportunity(
        security_type="TREASURY",
        maturity_years=2.0,
        yield_percent=4.20,
    )

    result = run_anchor(
        opportunities=[
            (treasury, "MODERATE"),
        ],
        regime=make_regime(
            real_rates="PRESSURE",
        ),
    )

    assert result["top_opportunity"] == {
        "security_type": "TREASURY",
        "maturity_years": 2.0,
        "classification": "FAVORABLE",
    }

    assert (
        result["selected_opportunities"][0][
            "security_type"
        ]
        == "TREASURY"
    )


def test_run_anchor_ranks_multiple_securities():
    treasury = FixedIncomeOpportunity(
        security_type="TREASURY",
        maturity_years=2.0,
        yield_percent=4.20,
    )

    corporate = FixedIncomeOpportunity(
        security_type="CORPORATE",
        maturity_years=5.0,
        yield_percent=5.30,
        rating="A",
    )

    result = run_anchor(
        opportunities=[
            (treasury, "MODERATE"),
            (corporate, "HIGH"),
        ],
        regime=make_regime(),
    )

    assert (
        result["selected_opportunities"][0][
            "security_type"
        ]
        == "CORPORATE"
    )


def test_run_anchor_preserves_risk_adjusted_yield():
    corporate = FixedIncomeOpportunity(
        security_type="CORPORATE",
        maturity_years=5.0,
        yield_percent=5.30,
        rating="A",
    )

    result = run_anchor(
        opportunities=[
            (corporate, "HIGH"),
        ],
        regime=make_regime(),
    )

    opportunity = result["selected_opportunities"][0]

    assert (
        opportunity["risk_adjusted_yield_percent"]
        == 4.65
    )

    assert (
        opportunity["total_risk_penalty_bps"]
        == 65.0
    )


def test_run_anchor_preserves_callable_risk():
    callable_bond = FixedIncomeOpportunity(
        security_type="CORPORATE",
        maturity_years=5.0,
        yield_percent=5.30,
        rating="A",
        callable=True,
    )

    result = run_anchor(
        opportunities=[
            (callable_bond, "HIGH"),
        ],
        regime=make_regime(),
    )

    opportunity = result["selected_opportunities"][0]

    assert opportunity["callable"] is True
    assert opportunity["total_risk_penalty_bps"] == 95.0
    assert (
        opportunity["risk_adjusted_yield_percent"]
        == 4.35
    )

    assert (
        "The security is callable."
        in result["cautions"]
    )


def test_run_anchor_distinguishes_identical_bonds_by_callability():
    non_callable = FixedIncomeOpportunity(
        security_type="CORPORATE",
        maturity_years=5.0,
        yield_percent=5.30,
        rating="A",
        callable=False,
    )

    callable_bond = FixedIncomeOpportunity(
        security_type="CORPORATE",
        maturity_years=5.0,
        yield_percent=5.30,
        rating="A",
        callable=True,
    )

    result = run_anchor(
        opportunities=[
            (non_callable, "HIGH"),
            (callable_bond, "HIGH"),
        ],
        regime=make_regime(),
    )

    penalties = sorted(
        item["total_risk_penalty_bps"]
        for item in result["selected_opportunities"]
    )

    adjusted_yields = sorted(
        item["risk_adjusted_yield_percent"]
        for item in result["selected_opportunities"]
    )

    assert penalties == [65.0, 95.0]
    assert adjusted_yields == [4.35, 4.65]


def test_run_anchor_builds_regime_allocation_guidance():
    treasury = FixedIncomeOpportunity(
        security_type="TREASURY",
        maturity_years=2.0,
        yield_percent=4.20,
    )

    result = run_anchor(
        opportunities=[
            (treasury, "MODERATE"),
        ],
        regime=make_regime(
            inflation="PRESSURE",
            real_rates="PRESSURE",
            term_premium="RISING",
            credit="STRESSED",
        ),
    )

    assert result["portfolio_posture"] == {
        "duration": "SHORT",
        "credit": "DEFENSIVE",
        "inflation": "HEDGE",
        "liquidity": "ELEVATED",
    }


def test_run_anchor_respects_max_selections():
    opportunities = [
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
                security_type="CORPORATE",
                maturity_years=5.0,
                yield_percent=5.30,
                rating="A",
            ),
            "HIGH",
        ),
        (
            FixedIncomeOpportunity(
                security_type="TIPS",
                maturity_years=5.0,
                yield_percent=2.10,
            ),
            "MODERATE",
        ),
    ]

    result = run_anchor(
        opportunities=opportunities,
        regime=make_regime(),
        max_selections=2,
    )

    assert len(
        result["selected_opportunities"]
    ) == 2


def test_run_anchor_rejects_invalid_max_selections():
    treasury = FixedIncomeOpportunity(
        security_type="TREASURY",
        maturity_years=2.0,
        yield_percent=4.20,
    )

    with pytest.raises(
        ValueError,
        match="max_selections must be at least 1",
    ):
        run_anchor(
            opportunities=[
                (treasury, "MODERATE"),
            ],
            regime=make_regime(),
            max_selections=0,
        )


def test_run_anchor_empty_input_raises_clear_error():
    with pytest.raises(
        ValueError,
        match="Anchor requires at least one opportunity",
    ):
        run_anchor(
            opportunities=[],
            regime=make_regime(),
        )


def test_run_anchor_output_contains_expected_sections():
    treasury = FixedIncomeOpportunity(
        security_type="TREASURY",
        maturity_years=2.0,
        yield_percent=4.20,
    )

    result = run_anchor(
        opportunities=[
            (treasury, "MODERATE"),
        ],
        regime=make_regime(),
    )

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
