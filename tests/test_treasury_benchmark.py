import math

import pytest

from engine.market_data import MarketDataSnapshot
from engine.treasury_benchmark import (
    TreasuryBenchmark,
    select_treasury_benchmark,
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


def test_short_maturity_uses_two_year_treasury():
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


def test_five_year_maturity_uses_two_year_treasury():
    result = select_treasury_benchmark(
        maturity_years=5.0,
        market_data=make_market_data(),
    )

    assert (
        result.benchmark_name
        == "2Y_TREASURY"
    )


def test_maturity_above_five_years_uses_ten_year_treasury():
    result = select_treasury_benchmark(
        maturity_years=5.01,
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


def test_long_maturity_uses_ten_year_treasury():
    result = select_treasury_benchmark(
        maturity_years=12.0,
        market_data=make_market_data(),
    )

    assert (
        result.benchmark_name
        == "10Y_TREASURY"
    )


def test_selector_preserves_live_two_year_yield():
    result = select_treasury_benchmark(
        maturity_years=3.0,
        market_data=make_market_data(
            treasury_2y=4.33,
        ),
    )

    assert (
        result.benchmark_yield_percent
        == 4.33
    )


def test_selector_preserves_live_ten_year_yield():
    result = select_treasury_benchmark(
        maturity_years=8.0,
        market_data=make_market_data(
            treasury_10y=4.71,
        ),
    )

    assert (
        result.benchmark_yield_percent
        == 4.71
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
        maturity_years=7.0,
        market_data=market_data,
    )

    second = select_treasury_benchmark(
        maturity_years=7.0,
        market_data=market_data,
    )

    assert first == second
