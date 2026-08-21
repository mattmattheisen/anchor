"""
Adversarial boundary tests for Anchor.

These tests deliberately supply malformed, extreme, or
otherwise problematic inputs to Anchor's public service
interface.

The objective is to verify that bad inputs fail clearly
rather than silently contaminating the decision process.
"""

import math

import pytest

from engine.models import FixedIncomeOpportunity
from engine.regime import RegimeAssessment
from engine.service import run_anchor


def make_regime():
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


def make_treasury(
    maturity_years=2.0,
    yield_percent=4.20,
):
    return FixedIncomeOpportunity(
        security_type="TREASURY",
        maturity_years=maturity_years,
        yield_percent=yield_percent,
    )


def test_empty_opportunity_set_is_rejected():
    with pytest.raises(ValueError):
        run_anchor(
            opportunities=[],
            regime=make_regime(),
        )


def test_zero_maturity_is_rejected():
    opportunity = make_treasury(
        maturity_years=0.0,
    )

    with pytest.raises(ValueError):
        run_anchor(
            opportunities=[
                (opportunity, "MODERATE"),
            ],
            regime=make_regime(),
        )


def test_negative_maturity_is_rejected():
    opportunity = make_treasury(
        maturity_years=-1.0,
    )

    with pytest.raises(ValueError):
        run_anchor(
            opportunities=[
                (opportunity, "MODERATE"),
            ],
            regime=make_regime(),
        )


def test_negative_yield_is_rejected():
    opportunity = make_treasury(
        yield_percent=-0.50,
    )

    with pytest.raises(ValueError):
        run_anchor(
            opportunities=[
                (opportunity, "MODERATE"),
            ],
            regime=make_regime(),
        )


def test_nan_yield_is_rejected():
    opportunity = make_treasury(
        yield_percent=math.nan,
    )

    with pytest.raises(ValueError):
        run_anchor(
            opportunities=[
                (opportunity, "MODERATE"),
            ],
            regime=make_regime(),
        )


def test_infinite_yield_is_rejected():
    opportunity = make_treasury(
        yield_percent=math.inf,
    )

    with pytest.raises(ValueError):
        run_anchor(
            opportunities=[
                (opportunity, "MODERATE"),
            ],
            regime=make_regime(),
        )


def test_nan_maturity_is_rejected():
    opportunity = make_treasury(
        maturity_years=math.nan,
    )

    with pytest.raises(ValueError):
        run_anchor(
            opportunities=[
                (opportunity, "MODERATE"),
            ],
            regime=make_regime(),
        )


def test_infinite_maturity_is_rejected():
    opportunity = make_treasury(
        maturity_years=math.inf,
    )

    with pytest.raises(ValueError):
        run_anchor(
            opportunities=[
                (opportunity, "MODERATE"),
            ],
            regime=make_regime(),
        )


def test_invalid_spread_compensation_is_rejected():
    opportunity = make_treasury()

    with pytest.raises(ValueError):
        run_anchor(
            opportunities=[
                (opportunity, "EXTREME"),
            ],
            regime=make_regime(),
        )


def test_invalid_security_type_is_rejected():
    opportunity = FixedIncomeOpportunity(
        security_type="CRYPTO",
        maturity_years=2.0,
        yield_percent=4.20,
    )

    with pytest.raises(ValueError):
        run_anchor(
            opportunities=[
                (opportunity, "MODERATE"),
            ],
            regime=make_regime(),
        )


def test_corporate_without_rating_is_rejected():
    opportunity = FixedIncomeOpportunity(
        security_type="CORPORATE",
        maturity_years=5.0,
        yield_percent=5.30,
    )

    with pytest.raises(ValueError):
        run_anchor(
            opportunities=[
                (opportunity, "HIGH"),
            ],
            regime=make_regime(),
        )


def test_invalid_regime_value_is_rejected():
    regime = RegimeAssessment(
        policy="NEUTRAL",
        growth="IMPOSSIBLE",
        inflation="STABLE",
        real_rates="STABLE",
        term_premium="NEUTRAL",
        credit="BENIGN",
        dominant_driver="MIXED",
        confidence="MEDIUM",
    )

    opportunity = make_treasury()

    with pytest.raises(ValueError):
        run_anchor(
            opportunities=[
                (opportunity, "MODERATE"),
            ],
            regime=regime,
        )


def test_zero_max_selections_is_rejected():
    opportunity = make_treasury()

    with pytest.raises(ValueError):
        run_anchor(
            opportunities=[
                (opportunity, "MODERATE"),
            ],
            regime=make_regime(),
            max_selections=0,
        )


def test_negative_max_selections_is_rejected():
    opportunity = make_treasury()

    with pytest.raises(ValueError):
        run_anchor(
            opportunities=[
                (opportunity, "MODERATE"),
            ],
            regime=make_regime(),
            max_selections=-1,
        )


def test_generator_input_is_consumed_safely():
    opportunities = (
        (make_treasury(), "MODERATE")
        for _ in range(1)
    )

    result = run_anchor(
        opportunities=opportunities,
        regime=make_regime(),
    )

    assert result["top_opportunity"][
        "security_type"
    ] == "TREASURY"


def test_valid_input_still_runs_after_boundary_checks():
    result = run_anchor(
        opportunities=[
            (
                make_treasury(),
                "MODERATE",
            ),
        ],
        regime=make_regime(),
    )

    assert result["schema_version"] == "1.0"
    assert result["selected_opportunities"]
