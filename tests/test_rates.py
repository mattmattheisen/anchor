import pytest

from engine.models import TreasuryPoint, TipsPoint
from engine.rates import (
    breakeven_inflation,
    decompose_rate,
    rate_change_bps,
    classify_rate_driver,
)


def test_breakeven_inflation():
    assert breakeven_inflation(4.70, 2.17) == 2.53


def test_decompose_rate():
    nominal = TreasuryPoint(10.0, 4.70)
    tips = TipsPoint(10.0, 2.17)

    result = decompose_rate(nominal, tips)

    assert result.maturity_years == 10.0
    assert result.nominal_yield_percent == 4.70
    assert result.real_yield_percent == 2.17
    assert result.breakeven_inflation_percent == 2.53


def test_rate_change_bps():
    assert rate_change_bps(4.40, 4.70) == 30.0


def test_real_rate_driver():
    assert classify_rate_driver(
        nominal_change_bps=30.0,
        real_change_bps=27.0,
        breakeven_change_bps=3.0,
    ) == "REAL_RATE"


def test_inflation_driver():
    assert classify_rate_driver(
        nominal_change_bps=30.0,
        real_change_bps=4.0,
        breakeven_change_bps=26.0,
    ) == "INFLATION"


def test_mixed_driver():
    assert classify_rate_driver(
        nominal_change_bps=30.0,
        real_change_bps=17.0,
        breakeven_change_bps=13.0,
    ) == "MIXED"


def test_unchanged_driver():
    assert classify_rate_driver(
        nominal_change_bps=0.0,
        real_change_bps=0.0,
        breakeven_change_bps=0.0,
    ) == "UNCHANGED"


def test_mismatched_maturities_rejected():
    nominal = TreasuryPoint(10.0, 4.70)
    tips = TipsPoint(5.0, 2.00)

    with pytest.raises(
        ValueError,
        match="Nominal Treasury and TIPS maturities must match",
    ):
        decompose_rate(nominal, tips)


def test_falling_real_rates_are_still_real_rate_driven():
    assert classify_rate_driver(
        nominal_change_bps=-30.0,
        real_change_bps=-27.0,
        breakeven_change_bps=-3.0,
    ) == "REAL_RATE"


def test_falling_breakevens_are_still_inflation_driven():
    assert classify_rate_driver(
        nominal_change_bps=-30.0,
        real_change_bps=-4.0,
        breakeven_change_bps=-26.0,
    ) == "INFLATION"
