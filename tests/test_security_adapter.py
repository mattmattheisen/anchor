from datetime import date

import pytest

from engine.security_adapter import (
    calculate_maturity_years,
    security_data_to_opportunity,
)
from engine.security_data import SecurityData


def make_security(
    security_type="TREASURY",
    maturity_date=date(2030, 8, 21),
    yield_to_maturity_percent=4.25,
    rating=None,
    callable=False,
):
    return SecurityData(
        security_type=security_type,
        maturity_date=maturity_date,
        yield_to_maturity_percent=(
            yield_to_maturity_percent
        ),
        cusip="91282ABC1",
        issuer="Test Issuer",
        coupon_percent=4.00,
        price=99.50,
        rating=rating,
        callable=callable,
        call_date=None,
        minimum_quantity=1000.0,
        source="TEST",
        description="Test security",
    )


def test_calculate_maturity_years_returns_positive_value():
    result = calculate_maturity_years(
        maturity_date=date(2030, 8, 21),
        as_of_date=date(2026, 8, 21),
    )

    assert result > 0


def test_calculate_maturity_years_is_about_four_years():
    result = calculate_maturity_years(
        maturity_date=date(2030, 8, 21),
        as_of_date=date(2026, 8, 21),
    )

    assert result == pytest.approx(
        4.0,
        abs=0.01,
    )


def test_calculate_maturity_years_rejects_same_date():
    with pytest.raises(
        ValueError,
        match="must be after as_of_date",
    ):
        calculate_maturity_years(
            maturity_date=date(2026, 8, 21),
            as_of_date=date(2026, 8, 21),
        )


def test_calculate_maturity_years_rejects_past_date():
    with pytest.raises(
        ValueError,
        match="must be after as_of_date",
    ):
        calculate_maturity_years(
            maturity_date=date(2025, 8, 21),
            as_of_date=date(2026, 8, 21),
        )


def test_calculate_maturity_years_requires_date_inputs():
    with pytest.raises(
        TypeError,
        match="maturity_date must be a date",
    ):
        calculate_maturity_years(
            maturity_date="2030-08-21",
            as_of_date=date(2026, 8, 21),
        )

    with pytest.raises(
        TypeError,
        match="as_of_date must be a date",
    ):
        calculate_maturity_years(
            maturity_date=date(2030, 8, 21),
            as_of_date="2026-08-21",
        )


def test_treasury_converts_to_anchor_opportunity():
    security = make_security(
        security_type="TREASURY",
    )

    opportunity, spread = (
        security_data_to_opportunity(
            security=security,
            spread_compensation="moderate",
            as_of_date=date(2026, 8, 21),
        )
    )

    assert opportunity.security_type == "TREASURY"
    assert opportunity.yield_percent == 4.25
    assert opportunity.rating is None
    assert opportunity.callable is False
    assert spread == "MODERATE"


def test_corporate_preserves_rating_and_callable():
    security = make_security(
        security_type="CORPORATE",
        rating="A",
        callable=True,
    )

    opportunity, spread = (
        security_data_to_opportunity(
            security=security,
            spread_compensation="high",
            as_of_date=date(2026, 8, 21),
        )
    )

    assert opportunity.security_type == "CORPORATE"
    assert opportunity.rating == "A"
    assert opportunity.callable is True
    assert spread == "HIGH"


def test_tips_preserves_security_type():
    security = make_security(
        security_type="TIPS",
    )

    opportunity, _ = (
        security_data_to_opportunity(
            security=security,
            spread_compensation="moderate",
            as_of_date=date(2026, 8, 21),
        )
    )

    assert opportunity.security_type == "TIPS"


def test_cd_preserves_security_type():
    security = make_security(
        security_type="CD",
    )

    opportunity, _ = (
        security_data_to_opportunity(
            security=security,
            spread_compensation="moderate",
            as_of_date=date(2026, 8, 21),
        )
    )

    assert opportunity.security_type == "CD"


def test_adapter_preserves_yield_to_maturity():
    security = make_security(
        yield_to_maturity_percent=5.15,
    )

    opportunity, _ = (
        security_data_to_opportunity(
            security=security,
            spread_compensation="moderate",
            as_of_date=date(2026, 8, 21),
        )
    )

    assert opportunity.yield_percent == 5.15


def test_adapter_normalizes_spread_compensation():
    security = make_security()

    _, spread = (
        security_data_to_opportunity(
            security=security,
            spread_compensation="  high  ",
            as_of_date=date(2026, 8, 21),
        )
    )

    assert spread == "HIGH"


def test_adapter_rejects_blank_spread_compensation():
    security = make_security()

    with pytest.raises(
        ValueError,
        match="cannot be blank",
    ):
        security_data_to_opportunity(
            security=security,
            spread_compensation="   ",
            as_of_date=date(2026, 8, 21),
        )


def test_adapter_rejects_non_string_spread():
    security = make_security()

    with pytest.raises(
        TypeError,
        match="must be a string",
    ):
        security_data_to_opportunity(
            security=security,
            spread_compensation=123,
            as_of_date=date(2026, 8, 21),
        )


def test_adapter_rejects_invalid_security_data():
    security = make_security(
        security_type="CORPORATE",
        rating=None,
    )

    with pytest.raises(
        ValueError,
        match="Corporate securities require a rating",
    ):
        security_data_to_opportunity(
            security=security,
            spread_compensation="HIGH",
            as_of_date=date(2026, 8, 21),
        )


def test_adapter_is_deterministic():
    security = make_security(
        security_type="CORPORATE",
        rating="A",
        callable=False,
    )

    first = security_data_to_opportunity(
        security=security,
        spread_compensation="HIGH",
        as_of_date=date(2026, 8, 21),
    )

    second = security_data_to_opportunity(
        security=security,
        spread_compensation="HIGH",
        as_of_date=date(2026, 8, 21),
    )

    assert first == second
