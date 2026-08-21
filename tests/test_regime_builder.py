import pytest

from engine.market_data import MarketDataSnapshot
from engine.regime_builder import (
    build_regime_from_market_data,
    classify_credit,
    classify_growth,
    classify_inflation,
    classify_policy,
    classify_real_rates,
    classify_term_premium,
    determine_confidence,
    determine_dominant_driver,
)


def make_snapshot(
    fed_funds_rate=4.50,
    treasury_2y=4.40,
    treasury_10y=4.50,
    real_yield_10y=1.50,
    breakeven_10y=2.25,
    credit_spread_ig_bps=100.0,
    treasury_2y_change_bps=0.0,
    treasury_10y_change_bps=0.0,
    real_yield_10y_change_bps=0.0,
    breakeven_10y_change_bps=0.0,
    credit_spread_ig_change_bps=0.0,
    unemployment_rate=None,
    unemployment_rate_change_pct=None,
):
    return MarketDataSnapshot(
        fed_funds_rate=fed_funds_rate,
        treasury_2y=treasury_2y,
        treasury_10y=treasury_10y,
        real_yield_10y=real_yield_10y,
        breakeven_10y=breakeven_10y,
        credit_spread_ig_bps=credit_spread_ig_bps,
        treasury_2y_change_bps=treasury_2y_change_bps,
        treasury_10y_change_bps=treasury_10y_change_bps,
        real_yield_10y_change_bps=real_yield_10y_change_bps,
        breakeven_10y_change_bps=breakeven_10y_change_bps,
        credit_spread_ig_change_bps=credit_spread_ig_change_bps,
        unemployment_rate=unemployment_rate,
        unemployment_rate_change_pct=(
            unemployment_rate_change_pct
        ),
    )


def test_policy_restrictive_when_fed_funds_above_two_year():
    snapshot = make_snapshot(
        fed_funds_rate=4.75,
        treasury_2y=4.40,
    )

    assert classify_policy(snapshot) == "RESTRICTIVE"


def test_policy_accommodative_when_fed_funds_below_two_year():
    snapshot = make_snapshot(
        fed_funds_rate=4.00,
        treasury_2y=4.40,
    )

    assert classify_policy(snapshot) == "ACCOMMODATIVE"


def test_policy_neutral_inside_threshold():
    snapshot = make_snapshot(
        fed_funds_rate=4.50,
        treasury_2y=4.40,
    )

    assert classify_policy(snapshot) == "NEUTRAL"


def test_growth_weakening_on_curve_inversion():
    snapshot = make_snapshot(
        treasury_2y=4.75,
        treasury_10y=4.25,
    )

    assert classify_growth(snapshot) == "WEAKENING"


def test_growth_weakening_on_unemployment_deterioration():
    snapshot = make_snapshot(
        treasury_2y=4.20,
        treasury_10y=4.80,
        unemployment_rate_change_pct=0.40,
    )

    assert classify_growth(snapshot) == "WEAKENING"


def test_growth_accelerating_on_steep_curve_without_unemployment_deterioration():
    snapshot = make_snapshot(
        treasury_2y=4.00,
        treasury_10y=4.75,
        unemployment_rate_change_pct=0.0,
    )

    assert classify_growth(snapshot) == "ACCELERATING"


def test_growth_neutral_when_curve_is_neither_inverted_nor_steep():
    snapshot = make_snapshot(
        treasury_2y=4.30,
        treasury_10y=4.50,
    )

    assert classify_growth(snapshot) == "NEUTRAL"


def test_inflation_pressure_on_high_breakeven():
    snapshot = make_snapshot(
        breakeven_10y=2.60,
    )

    assert classify_inflation(snapshot) == "PRESSURE"


def test_inflation_pressure_on_rising_breakeven():
    snapshot = make_snapshot(
        breakeven_10y=2.30,
        breakeven_10y_change_bps=20.0,
    )

    assert classify_inflation(snapshot) == "PRESSURE"


def test_inflation_falling_on_low_and_declining_breakeven():
    snapshot = make_snapshot(
        breakeven_10y=1.90,
        breakeven_10y_change_bps=-20.0,
    )

    assert classify_inflation(snapshot) == "FALLING"


def test_inflation_stable_otherwise():
    snapshot = make_snapshot(
        breakeven_10y=2.25,
        breakeven_10y_change_bps=5.0,
    )

    assert classify_inflation(snapshot) == "STABLE"


def test_real_rates_pressure_on_high_level():
    snapshot = make_snapshot(
        real_yield_10y=2.10,
    )

    assert classify_real_rates(snapshot) == "PRESSURE"


def test_real_rates_pressure_on_large_increase():
    snapshot = make_snapshot(
        real_yield_10y=1.50,
        real_yield_10y_change_bps=20.0,
    )

    assert classify_real_rates(snapshot) == "PRESSURE"


def test_real_rates_falling_on_low_and_declining_level():
    snapshot = make_snapshot(
        real_yield_10y=0.40,
        real_yield_10y_change_bps=-20.0,
    )

    assert classify_real_rates(snapshot) == "FALLING"


def test_real_rates_stable_otherwise():
    snapshot = make_snapshot(
        real_yield_10y=1.25,
        real_yield_10y_change_bps=5.0,
    )

    assert classify_real_rates(snapshot) == "STABLE"


def test_term_premium_rising_when_long_end_rises_faster():
    snapshot = make_snapshot(
        treasury_2y_change_bps=5.0,
        treasury_10y_change_bps=25.0,
    )

    assert classify_term_premium(snapshot) == "RISING"


def test_term_premium_falling_when_long_end_falls_faster():
    snapshot = make_snapshot(
        treasury_2y_change_bps=-5.0,
        treasury_10y_change_bps=-25.0,
    )

    assert classify_term_premium(snapshot) == "FALLING"


def test_term_premium_neutral_when_differential_small():
    snapshot = make_snapshot(
        treasury_2y_change_bps=5.0,
        treasury_10y_change_bps=10.0,
    )

    assert classify_term_premium(snapshot) == "NEUTRAL"


def test_credit_stressed_on_wide_spreads():
    snapshot = make_snapshot(
        credit_spread_ig_bps=160.0,
    )

    assert classify_credit(snapshot) == "STRESSED"


def test_credit_stressed_on_large_spread_widening():
    snapshot = make_snapshot(
        credit_spread_ig_bps=120.0,
        credit_spread_ig_change_bps=30.0,
    )

    assert classify_credit(snapshot) == "STRESSED"


def test_credit_benign_on_tight_stable_spreads():
    snapshot = make_snapshot(
        credit_spread_ig_bps=95.0,
        credit_spread_ig_change_bps=5.0,
    )

    assert classify_credit(snapshot) == "BENIGN"


def test_credit_neutral_between_thresholds():
    snapshot = make_snapshot(
        credit_spread_ig_bps=125.0,
        credit_spread_ig_change_bps=15.0,
    )

    assert classify_credit(snapshot) == "NEUTRAL"


def test_credit_stress_has_driver_priority():
    result = determine_dominant_driver(
        growth="WEAKENING",
        inflation="PRESSURE",
        real_rates="PRESSURE",
        term_premium="RISING",
        credit="STRESSED",
    )

    assert result == "CREDIT_STRESS"


def test_combined_inflation_real_rate_pressure_is_detected():
    result = determine_dominant_driver(
        growth="NEUTRAL",
        inflation="PRESSURE",
        real_rates="PRESSURE",
        term_premium="NEUTRAL",
        credit="BENIGN",
    )

    assert result == "INFLATION_REAL_RATE_PRESSURE"


def test_real_rate_term_premium_driver_is_detected():
    result = determine_dominant_driver(
        growth="NEUTRAL",
        inflation="STABLE",
        real_rates="PRESSURE",
        term_premium="RISING",
        credit="BENIGN",
    )

    assert result == "REAL_RATE_TERM_PREMIUM"


def test_confidence_high_with_four_directional_signals():
    result = determine_confidence(
        growth="WEAKENING",
        inflation="PRESSURE",
        real_rates="PRESSURE",
        term_premium="RISING",
        credit="NEUTRAL",
    )

    assert result == "HIGH"


def test_confidence_medium_with_two_directional_signals():
    result = determine_confidence(
        growth="WEAKENING",
        inflation="PRESSURE",
        real_rates="STABLE",
        term_premium="NEUTRAL",
        credit="NEUTRAL",
    )

    assert result == "MEDIUM"


def test_confidence_low_with_one_directional_signal():
    result = determine_confidence(
        growth="NEUTRAL",
        inflation="PRESSURE",
        real_rates="STABLE",
        term_premium="NEUTRAL",
        credit="NEUTRAL",
    )

    assert result == "LOW"


def test_build_regime_from_market_data_returns_expected_neutral_regime():
    snapshot = make_snapshot()

    regime = build_regime_from_market_data(
        snapshot
    )

    assert regime.policy == "NEUTRAL"
    assert regime.growth == "NEUTRAL"
    assert regime.inflation == "STABLE"
    assert regime.real_rates == "STABLE"
    assert regime.term_premium == "NEUTRAL"
    assert regime.credit == "BENIGN"
    assert regime.dominant_driver == "MIXED"


def test_build_regime_from_adverse_market_data():
    snapshot = make_snapshot(
        fed_funds_rate=5.00,
        treasury_2y=4.50,
        treasury_10y=4.10,
        real_yield_10y=2.25,
        breakeven_10y=2.65,
        credit_spread_ig_bps=170.0,
        treasury_2y_change_bps=5.0,
        treasury_10y_change_bps=25.0,
        real_yield_10y_change_bps=20.0,
        breakeven_10y_change_bps=20.0,
        credit_spread_ig_change_bps=30.0,
        unemployment_rate_change_pct=0.40,
    )

    regime = build_regime_from_market_data(
        snapshot
    )

    assert regime.policy == "RESTRICTIVE"
    assert regime.growth == "WEAKENING"
    assert regime.inflation == "PRESSURE"
    assert regime.real_rates == "PRESSURE"
    assert regime.term_premium == "RISING"
    assert regime.credit == "STRESSED"
    assert regime.dominant_driver == "CREDIT_STRESS"
    assert regime.confidence == "HIGH"


def test_build_regime_is_deterministic():
    snapshot = make_snapshot(
        fed_funds_rate=4.75,
        treasury_2y=4.25,
        treasury_10y=4.60,
        real_yield_10y=2.10,
        breakeven_10y=2.55,
        credit_spread_ig_bps=120.0,
        treasury_2y_change_bps=0.0,
        treasury_10y_change_bps=20.0,
    )

    first = build_regime_from_market_data(
        snapshot
    )

    second = build_regime_from_market_data(
        snapshot
    )

    assert first == second
