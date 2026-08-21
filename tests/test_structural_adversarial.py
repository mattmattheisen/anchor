"""
Structural adversarial tests for Anchor.

These tests deliberately supply malformed object types,
tuple structures, and public-service arguments.

The objective is to verify that Anchor rejects invalid
structural inputs clearly rather than failing unpredictably
inside the analytical engine.
"""

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


def make_treasury():
    return FixedIncomeOpportunity(
        security_type="TREASURY",
        maturity_years=2.0,
        yield_percent=4.20,
    )


def test_none_regime_is_rejected():
    with pytest.raises(
        (TypeError, ValueError, AttributeError),
    ):
        run_anchor(
            opportunities=[
                (
                    make_treasury(),
                    "MODERATE",
                ),
            ],
            regime=None,
        )


def test_wrong_opportunity_object_type_is_rejected():
    with pytest.raises(
        (TypeError, ValueError, AttributeError),
    ):
        run_anchor(
            opportunities=[
                (
                    "NOT_AN_OPPORTUNITY",
                    "MODERATE",
                ),
            ],
            regime=make_regime(),
        )


def test_opportunity_tuple_missing_spread_is_rejected():
    with pytest.raises(
        (TypeError, ValueError),
    ):
        run_anchor(
            opportunities=[
                (
                    make_treasury(),
                ),
            ],
            regime=make_regime(),
        )


def test_opportunity_tuple_with_extra_values_is_rejected():
    with pytest.raises(
        (TypeError, ValueError),
    ):
        run_anchor(
            opportunities=[
                (
                    make_treasury(),
                    "MODERATE",
                    "EXTRA",
                ),
            ],
            regime=make_regime(),
        )


def test_non_string_spread_compensation_is_rejected():
    with pytest.raises(
        (TypeError, ValueError),
    ):
        run_anchor(
            opportunities=[
                (
                    make_treasury(),
                    123,
                ),
            ],
            regime=make_regime(),
        )


def test_none_spread_compensation_is_rejected():
    with pytest.raises(
        (TypeError, ValueError),
    ):
        run_anchor(
            opportunities=[
                (
                    make_treasury(),
                    None,
                ),
            ],
            regime=make_regime(),
        )


def test_string_instead_of_opportunity_iterable_is_rejected():
    with pytest.raises(
        (TypeError, ValueError, AttributeError),
    ):
        run_anchor(
            opportunities="NOT_VALID",
            regime=make_regime(),
        )


def test_none_opportunity_iterable_is_rejected():
    with pytest.raises(
        (TypeError, ValueError),
    ):
        run_anchor(
            opportunities=None,
            regime=make_regime(),
        )


def test_float_max_selections_is_rejected():
    with pytest.raises(
        (TypeError, ValueError),
    ):
        run_anchor(
            opportunities=[
                (
                    make_treasury(),
                    "MODERATE",
                ),
            ],
            regime=make_regime(),
            max_selections=2.5,
        )


def test_string_max_selections_is_rejected():
    with pytest.raises(
        (TypeError, ValueError),
    ):
        run_anchor(
            opportunities=[
                (
                    make_treasury(),
                    "MODERATE",
                ),
            ],
            regime=make_regime(),
            max_selections="3",
        )


def test_boolean_max_selections_is_rejected():
    with pytest.raises(
        (TypeError, ValueError),
    ):
        run_anchor(
            opportunities=[
                (
                    make_treasury(),
                    "MODERATE",
                ),
            ],
            regime=make_regime(),
            max_selections=True,
        )


def test_duplicate_valid_opportunities_do_not_crash():
    opportunity = make_treasury()

    result = run_anchor(
        opportunities=[
            (
                opportunity,
                "MODERATE",
            ),
            (
                opportunity,
                "MODERATE",
            ),
        ],
        regime=make_regime(),
        max_selections=2,
    )

    assert len(
        result["selected_opportunities"]
    ) == 2


def test_generator_with_multiple_items_is_consumed_once():
    opportunities = (
        item
        for item in [
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
        ]
    )

    result = run_anchor(
        opportunities=opportunities,
        regime=make_regime(),
        max_selections=2,
    )

    assert len(
        result["selected_opportunities"]
    ) == 2


def test_valid_structural_input_still_runs():
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
