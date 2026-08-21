import math

import pytest

from engine.market_data import MarketDataSnapshot
from engine.treasury_benchmark import (
    TreasuryBenchmark,
    select_treasury_benchmark,
)


def make_market_data(
    treasury_1y=4.10,
    treasury_2y=4.20,
    treasury_3y=4.25,
    treasury_5y=4.35,
    treasury_7y=4.50,
    treasury_10y=4.65,
):
    return MarketDataSnapshot(
        fed_funds_rate=3.75,
        treasury_1y=treasury_1y,
        treasury_2y=treasury_2y,
        treasury_3y=treasury_3y,
        treasury_5y=treasury_5y,
        treasury_7y=treasury_7y,
        treasury_10y=treasury_10y,
        real_yield_10y=2.25,
        breakeven_10y=2.30,
        credit_spread_ig_bps=85.0,
    )


def test_exact_two_year_maturity_uses_two_year_treasury():
    result = select_treasury_benchmark(
        maturity_years=2.0,
        market_data=make_market_data(),
    )

    assert isinstance(
        result,
        TreasuryBenchmark,
    )

    assert (
        result.benchmark_name
        == "2Y_TREASURY"
    )

    assert (
        result.benchmark_maturity_years
        == 2.0
    )

    assert (
        result.benchmark_yield_percent
        == 4.20
    )


def test_exact_five_year_maturity_uses_five_year_treasury():
    result = select_treasury_benchmark(
        maturity_years=5.0,
        market_data=make_market_data(),
    )

    assert (
        result.benchmark_name
        == "5Y_TREASURY"
    )

    assert (
        result.benchmark_maturity_years
        == 5.0
    )

    assert (
        result.benchmark_yield_percent
        == 4.35
    )


def test_exact_seven_year_maturity_uses_seven_year_treasury():
    result = select_treasury_benchmark(
        maturity_years=7.0,
        market_data=make_market_data(),
    )

    assert (
        result.benchmark_name
        == "7Y_TREASURY"
    )

    assert (
        result.benchmark_yield_percent
        == 4.50
    )


def test_exact_ten_year_maturity_uses_ten_year_treasury():
    result = select_treasury_benchmark(
        maturity_years=10.0,
        market_data=make_market_data(),
    )

    assert (
        result.benchmark_name
        == "10Y_TREASURY"
    )

    assert (
        result.benchmark_yield_percent
        == 4.65
    )


def test_maturity_below_one_year_uses_one_year_treasury():
    result = select_treasury_benchmark(
        maturity_years=0.50,
        market_data=make_market_data(),
    )

    assert (
        result.benchmark_name
        == "1Y_TREASURY"
    )

    assert (
        result.benchmark_maturity_years
        == 1.0
    )

    assert (
        result.benchmark_yield_percent
        == 4.10
    )


def test_maturity_above_ten_years_uses_ten_year_treasury():
    result = select_treasury_benchmark(
        maturity_years=12.0,
        market_data=make_market_data(),
    )

    assert (
        result.benchmark_name
        == "10Y_TREASURY"
    )

    assert (
        result.benchmark_maturity_years
        == 10.0
    )

    assert (
        result.benchmark_yield_percent
        == 4.65
    )


def test_interpolates_between_one_and_two_year():
    result = select_treasury_benchmark(
        maturity_years=1.5,
        market_data=make_market_data(
            treasury_1y=4.00,
            treasury_2y=4.20,
        ),
    )

    assert (
        result.benchmark_name
        == "INTERPOLATED_1Y_TREASURY_2Y_TREASURY"
    )

    assert (
        result.benchmark_maturity_years
        == 1.5
    )

    assert (
        result.benchmark_yield_percent
        == pytest.approx(
            4.10
        )
    )


def test_interpolates_between_two_and_three_year():
    result = select_treasury_benchmark(
        maturity_years=2.5,
        market_data=make_market_data(
            treasury_2y=4.20,
            treasury_3y=4.30,
        ),
    )

    assert (
        result.benchmark_name
        == "INTERPOLATED_2Y_TREASURY_3Y_TREASURY"
    )

    assert (
        result.benchmark_yield_percent
        == pytest.approx(
            4.25
        )
    )


def test_interpolates_between_three_and_five_year():
    result = select_treasury_benchmark(
        maturity_years=4.0,
        market_data=make_market_data(
            treasury_3y=4.20,
            treasury_5y=4.40,
        ),
    )

    assert (
        result.benchmark_name
        == "INTERPOLATED_3Y_TREASURY_5Y_TREASURY"
    )

    assert (
        result.benchmark_yield_percent
        == pytest.approx(
            4.30
        )
    )


def test_interpolates_between_five_and_seven_year():
    result = select_treasury_benchmark(
        maturity_years=6.0,
        market_data=make_market_data(
            treasury_5y=4.30,
            treasury_7y=4.50,
        ),
    )

    assert (
        result.benchmark_name
        == "INTERPOLATED_5Y_TREASURY_7Y_TREASURY"
    )

    assert (
        result.benchmark_yield_percent
        == pytest.approx(
            4.40
        )
    )


def test_interpolates_between_seven_and_ten_year():
    result = select_treasury_benchmark(
        maturity_years=8.0,
        market_data=make_market_data(
            treasury_7y=4.50,
            treasury_10y=4.80,
        ),
    )

    assert (
        result.benchmark_name
        == "INTERPOLATED_7Y_TREASURY_10Y_TREASURY"
    )

    assert (
        result.benchmark_yield_percent
        == pytest.approx(
            4.60
        )
    )


def test_selector_uses_live_three_year_yield():
    result = select_treasury_benchmark(
        maturity_years=3.0,
        market_data=make_market_data(
            treasury_3y=4.33,
        ),
    )

    assert (
        result.benchmark_yield_percent
        == 4.33
    )


def test_selector_uses_live_seven_year_yield():
    result = select_treasury_benchmark(
        maturity_years=7.0,
        market_data=make_market_data(
            treasury_7y=4.71,
        ),
    )

    assert (
        result.benchmark_yield_percent
        == 4.71
    )


def test_missing_three_year_point_interpolates_two_to_five():
    result = select_treasury_benchmark(
        maturity_years=4.0,
        market_data=make_market_data(
            treasury_2y=4.20,
            treasury_3y=None,
            treasury_5y=4.40,
        ),
    )

    assert (
        result.benchmark_name
        == "INTERPOLATED_2Y_TREASURY_5Y_TREASURY"
    )

    assert (
        result.benchmark_yield_percent
        == pytest.approx(
            4.3333333333,
        )
    )


def test_missing_optional_curve_points_falls_back_to_two_and_ten():
    result = select_treasury_benchmark(
        maturity_years=6.0,
        market_data=make_market_data(
            treasury_1y=None,
            treasury_3y=None,
            treasury_5y=None,
            treasury_7y=None,
            treasury_2y=4.20,
            treasury_10y=4.60,
        ),
    )

    assert (
        result.benchmark_name
        == "INTERPOLATED_2Y_TREASURY_10Y_TREASURY"
    )

    assert (
        result.benchmark_yield_percent
        == pytest.approx(
            4.40
        )
    )


@pytest.mark.parametrize(
    "value",
    [
        0.0,
        -1.0,
        -10.0,
    ],
)
def test_nonpositive_maturity_is_rejected(
    value,
):
    with pytest.raises(
        ValueError,
        match="must be greater than 0",
    ):
        select_treasury_benchmark(
            maturity_years=value,
            market_data=make_market_data(),
        )


@pytest.mark.parametrize(
    "value",
    [
        math.nan,
        math.inf,
        -math.inf,
    ],
)
def test_nonfinite_maturity_is_rejected(
    value,
):
    with pytest.raises(
        ValueError,
        match="must be finite",
    ):
        select_treasury_benchmark(
            maturity_years=value,
            market_data=make_market_data(),
        )


@pytest.mark.parametrize(
    "value",
    [
        "5.0",
        None,
        True,
        False,
    ],
)
def test_nonnumeric_maturity_is_rejected(
    value,
):
    with pytest.raises(
        TypeError,
        match="must be numeric",
    ):
        select_treasury_benchmark(
            maturity_years=value,
            market_data=make_market_data(),
        )


def test_wrong_market_data_type_is_rejected():
    with pytest.raises(
        TypeError,
        match="market_data must be a MarketDataSnapshot",
    ):
        select_treasury_benchmark(
            maturity_years=5.0,
            market_data="NOT_MARKET_DATA",
        )


def test_selector_is_deterministic():
    market_data = make_market_data()

    first = select_treasury_benchmark(
        maturity_years=6.25,
        market_data=market_data,
    )

    second = select_treasury_benchmark(
        maturity_years=6.25,
        market_data=market_data,
    )

    assert first == second
