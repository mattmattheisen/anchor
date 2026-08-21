import pytest

from engine.models import FixedIncomeOpportunity
from engine.regime import RegimeAssessment
from engine.validation import (
    validate_anchor_inputs,
    validate_opportunity,
    validate_regime,
)


def make_regime(
    policy="NEUTRAL",
    growth="NEUTRAL",
    inflation="STABLE",
    real_rates="STABLE",
    term_premium="NEUTRAL",
    credit="BENIGN",
    confidence="MEDIUM",
):
    return RegimeAssessment(
        policy=policy,
        growth=growth,
        inflation=inflation,
        real_rates=real_rates,
        term_premium=term_premium,
        credit=credit,
        dominant_driver="MIXED",
        confidence=confidence,
    )


def test_valid_treasury_passes_validation():
    opportunity = FixedIncomeOpportunity(
        security_type="TREASURY",
        maturity_years=2.0,
        yield_percent=4.20,
    )

    validate_opportunity(opportunity)


def test_valid_corporate_passes_validation():
    opportunity = FixedIncomeOpportunity(
        security_type="CORPORATE",
        maturity_years=5.0,
        yield_percent=5.30,
        rating="A",
    )

    validate_opportunity(opportunity)


def test_unsupported_security_type_raises():
    opportunity = FixedIncomeOpportunity(
        security_type="MUNICIPAL",
        maturity_years=5.0,
        yield_percent=4.00,
    )

    with pytest.raises(
        ValueError,
        match="Unsupported security_type",
    ):
        validate_opportunity(opportunity)


def test_zero_maturity_raises():
    opportunity = FixedIncomeOpportunity(
        security_type="TREASURY",
        maturity_years=0.0,
        yield_percent=4.20,
    )

    with pytest.raises(
        ValueError,
        match="maturity_years must be greater than 0",
    ):
        validate_opportunity(opportunity)


def test_negative_maturity_raises():
    opportunity = FixedIncomeOpportunity(
        security_type="TREASURY",
        maturity_years=-1.0,
        yield_percent=4.20,
    )

    with pytest.raises(
        ValueError,
        match="maturity_years must be greater than 0",
    ):
        validate_opportunity(opportunity)


def test_negative_yield_raises():
    opportunity = FixedIncomeOpportunity(
        security_type="TREASURY",
        maturity_years=2.0,
        yield_percent=-0.25,
    )

    with pytest.raises(
        ValueError,
        match="yield_percent cannot be negative",
    ):
        validate_opportunity(opportunity)


def test_corporate_without_rating_raises():
    opportunity = FixedIncomeOpportunity(
        security_type="CORPORATE",
        maturity_years=5.0,
        yield_percent=5.30,
    )

    with pytest.raises(
        ValueError,
        match="Corporate opportunities require a rating",
    ):
        validate_opportunity(opportunity)


def test_non_boolean_callable_raises():
    opportunity = FixedIncomeOpportunity(
        security_type="CORPORATE",
        maturity_years=5.0,
        yield_percent=5.30,
        rating="A",
        callable="YES",
    )

    with pytest.raises(
        ValueError,
        match="callable must be a boolean",
    ):
        validate_opportunity(opportunity)


def test_valid_regime_passes_validation():
    validate_regime(
        make_regime()
    )


@pytest.mark.parametrize(
    "field,value,error_text",
    [
        (
            "policy",
            "UNKNOWN",
            "Unsupported policy value",
        ),
        (
            "growth",
            "UNKNOWN",
            "Unsupported growth value",
        ),
        (
            "inflation",
            "UNKNOWN",
            "Unsupported inflation value",
        ),
        (
            "real_rates",
            "UNKNOWN",
            "Unsupported real_rates value",
        ),
        (
            "term_premium",
            "UNKNOWN",
            "Unsupported term_premium value",
        ),
        (
            "credit",
            "UNKNOWN",
            "Unsupported credit value",
        ),
        (
            "confidence",
            "UNKNOWN",
            "Unsupported confidence value",
        ),
    ],
)
def test_invalid_regime_values_raise(
    field,
    value,
    error_text,
):
    kwargs = {
        field: value,
    }

    regime = make_regime(
        **kwargs
    )

    with pytest.raises(
        ValueError,
        match=error_text,
    ):
        validate_regime(regime)


def test_empty_opportunity_set_raises():
    with pytest.raises(
        ValueError,
        match="Anchor requires at least one opportunity",
    ):
        validate_anchor_inputs(
            opportunities=[],
            regime=make_regime(),
        )


def test_invalid_spread_compensation_raises():
    opportunity = FixedIncomeOpportunity(
        security_type="TREASURY",
        maturity_years=2.0,
        yield_percent=4.20,
    )

    with pytest.raises(
        ValueError,
        match="Unsupported spread_compensation",
    ):
        validate_anchor_inputs(
            opportunities=[
                (opportunity, "EXTREME"),
            ],
            regime=make_regime(),
        )


def test_validate_anchor_inputs_returns_list():
    opportunity = FixedIncomeOpportunity(
        security_type="TREASURY",
        maturity_years=2.0,
        yield_percent=4.20,
    )

    result = validate_anchor_inputs(
        opportunities=[
            (opportunity, "MODERATE"),
        ],
        regime=make_regime(),
    )

    assert isinstance(result, list)
    assert len(result) == 1


def test_generator_inputs_are_materialized_safely():
    opportunity = FixedIncomeOpportunity(
        security_type="TREASURY",
        maturity_years=2.0,
        yield_percent=4.20,
    )

    opportunities = (
        item
        for item in [
            (opportunity, "MODERATE"),
        ]
    )

    result = validate_anchor_inputs(
        opportunities=opportunities,
        regime=make_regime(),
    )

    assert len(result) == 1
    assert result[0][0] is opportunity


def test_multiple_valid_opportunities_pass():
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

    result = validate_anchor_inputs(
        opportunities=[
            (treasury, "MODERATE"),
            (corporate, "HIGH"),
        ],
        regime=make_regime(),
    )

    assert len(result) == 2
