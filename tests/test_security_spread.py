from datetime import date

import pytest

from engine.market_data import MarketDataSnapshot
from engine.security_data import SecurityData
from engine.security_spread import (
    SecuritySpreadAssessment,
    assess_security_spread,
)


AS_OF_DATE = date(
    2026,
    8,
    21,
)


def make_market_data(
    treasury_2y=4.20,
    treasury_10y=4.65,
):
    return MarketDataSnapshot(
        fed_funds_rate=3.75,
        treasury_2y=treasury_2y,
        treasury_10y=treasury_10y,
        real_yield_10y=2.25,
        breakeven_10y=2.30,
        credit_spread_ig_bps=85.0,
    )


def make_security(
    security_type="CORPORATE",
    maturity_date=date(
        2030,
        8,
        21,
    ),
    yield_to_maturity_percent=5.20,
    rating="A",
):
    return SecurityData(
        security_type=security_type,
        maturity_date=maturity_date,
        yield_to_maturity_percent=(
            yield_to_maturity_percent
        ),
        cusip="123456AB7",
        issuer="Test Issuer",
        coupon_percent=5.00,
        price=100.00,
        rating=rating,
        callable=False,
        call_date=None,
        minimum_quantity=1000.0,
        source="TEST",
        description="Test security",
    )


def test_assessment_returns_expected_type():
    result = assess_security_spread(
        security=make_security(),
        market_data=make_market_data(),
        as_of_date=AS_OF_DATE,
    )

    assert isinstance(
        result,
        SecuritySpreadAssessment,
    )


def test_short_corporate_uses_two_year_benchmark():
    result = assess_security_spread(
        security=make_security(
            maturity_date=date(
                2030,
                8,
                21,
            ),
        ),
        market_data=make_market_data(),
        as_of_date=AS_OF_DATE,
    )

    assert (
        result.benchmark.benchmark_name
        == "2Y_TREASURY"
    )

    assert (
        result.benchmark.benchmark_yield_percent
        == 4.20
    )


def test_long_corporate_uses_ten_year_benchmark():
    result = assess_security_spread(
        security=make_security(
            maturity_date=date(
                2033,
                8,
                21,
            ),
        ),
        market_data=make_market_data(),
        as_of_date=AS_OF_DATE,
    )

    assert (
        result.benchmark.benchmark_name
        == "10Y_TREASURY"
    )

    assert (
        result.benchmark.benchmark_yield_percent
        == 4.65
    )


def test_corporate_spread_is_calculated():
    result = assess_security_spread(
        security=make_security(
            yield_to_maturity_percent=5.20,
        ),
        market_data=make_market_data(
            treasury_2y=4.20,
        ),
        as_of_date=AS_OF_DATE,
    )

    assert (
        result.spread.spread_bps
        == pytest.approx(
            100.0
        )
    )


def test_corporate_compensation_is_derived():
    result = assess_security_spread(
        security=make_security(
            yield_to_maturity_percent=5.20,
        ),
        market_data=make_market_data(
            treasury_2y=4.20,
        ),
        as_of_date=AS_OF_DATE,
    )

    assert (
        result.spread.compensation
        == "MEANINGFUL"
    )


def test_cd_spread_is_calculated():
    security = make_security(
        security_type="CD",
        yield_to_maturity_percent=4.95,
        rating=None,
    )

    result = assess_security_spread(
        security=security,
        market_data=make_market_data(
            treasury_2y=4.20,
        ),
        as_of_date=AS_OF_DATE,
    )

    assert (
        result.spread.spread_bps
        == pytest.approx(
            75.0
        )
    )

    assert (
        result.spread.compensation
        == "MODERATE"
    )


def test_treasury_has_zero_spread():
    security = make_security(
        security_type="TREASURY",
        yield_to_maturity_percent=4.25,
        rating=None,
    )

    result = assess_security_spread(
        security=security,
        market_data=make_market_data(),
        as_of_date=AS_OF_DATE,
    )

    assert (
        result.spread.spread_bps
        == 0.0
    )

    assert (
        result.spread.compensation
        == "MODERATE"
    )


def test_tips_has_zero_spread():
    security = make_security(
        security_type="TIPS",
        yield_to_maturity_percent=2.15,
        rating=None,
    )

    result = assess_security_spread(
        security=security,
        market_data=make_market_data(),
        as_of_date=AS_OF_DATE,
    )

    assert (
        result.spread.spread_bps
        == 0.0
    )

    assert (
        result.spread.compensation
        == "MODERATE"
    )


def test_maturity_years_are_calculated():
    result = assess_security_spread(
        security=make_security(
            maturity_date=date(
                2030,
                8,
                21,
            ),
        ),
        market_data=make_market_data(),
        as_of_date=AS_OF_DATE,
    )

    assert (
        result.maturity_years
        == pytest.approx(
            4.0,
            abs=0.01,
        )
    )


def test_security_type_is_preserved():
    result = assess_security_spread(
        security=make_security(
            security_type="CORPORATE",
        ),
        market_data=make_market_data(),
        as_of_date=AS_OF_DATE,
    )

    assert (
        result.security_type
        == "CORPORATE"
    )


def test_invalid_corporate_is_rejected():
    security = make_security(
        security_type="CORPORATE",
        rating=None,
    )

    with pytest.raises(
        ValueError,
        match=(
            "Corporate securities require "
            "a rating"
        ),
    ):
        assess_security_spread(
            security=security,
            market_data=make_market_data(),
            as_of_date=AS_OF_DATE,
        )


def test_wrong_market_data_type_is_rejected():
    with pytest.raises(
        TypeError,
        match=(
            "market_data must be "
            "a MarketDataSnapshot"
        ),
    ):
        assess_security_spread(
            security=make_security(),
            market_data="NOT_MARKET_DATA",
            as_of_date=AS_OF_DATE,
        )


def test_wrong_as_of_date_type_is_rejected():
    with pytest.raises(
        TypeError,
        match="as_of_date must be a date",
    ):
        assess_security_spread(
            security=make_security(),
            market_data=make_market_data(),
            as_of_date="2026-08-21",
        )


def test_matured_security_is_rejected():
    security = make_security(
        maturity_date=date(
            2026,
            8,
            21,
        ),
    )

    with pytest.raises(
        ValueError,
        match=(
            "maturity_date must be after "
            "as_of_date"
        ),
    ):
        assess_security_spread(
            security=security,
            market_data=make_market_data(),
            as_of_date=AS_OF_DATE,
        )


def test_assessment_is_deterministic():
    security = make_security()
    market_data = make_market_data()

    first = assess_security_spread(
        security=security,
        market_data=market_data,
        as_of_date=AS_OF_DATE,
    )

    second = assess_security_spread(
        security=security,
        market_data=market_data,
        as_of_date=AS_OF_DATE,
    )

    assert first == second
