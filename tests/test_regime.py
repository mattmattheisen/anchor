from engine.regime import (
    classify_growth_regime,
    classify_inflation_regime,
    classify_real_rate_regime,
    classify_credit_regime,
    classify_term_premium_regime,
    determine_dominant_driver,
    determine_confidence,
    assess_regime,
)


def test_growth_regimes():
    assert classify_growth_regime("INVERTED") == "WEAKENING"
    assert classify_growth_regime("FLAT") == "CAUTIOUS"
    assert classify_growth_regime("STEEP") == "IMPROVING"
    assert classify_growth_regime("NORMAL") == "NEUTRAL"


def test_inflation_regimes():
    assert classify_inflation_regime("INFLATION") == "PRESSURE"
    assert classify_inflation_regime("REAL_RATE") == "STABLE"
    assert classify_inflation_regime("MIXED") == "MIXED"
    assert classify_inflation_regime("UNCHANGED") == "STABLE"


def test_real_rate_regimes():
    assert classify_real_rate_regime("REAL_RATE") == "PRESSURE"
    assert classify_real_rate_regime("INFLATION") == "STABLE"
    assert classify_real_rate_regime("MIXED") == "MIXED"
    assert classify_real_rate_regime("UNCHANGED") == "STABLE"


def test_credit_regimes():
    assert classify_credit_regime("UNFAVORABLE") == "TIGHT"
    assert classify_credit_regime("THIN") == "TIGHT"
    assert classify_credit_regime("MODERATE") == "BENIGN"
    assert classify_credit_regime("MEANINGFUL") == "WIDENING"
    assert classify_credit_regime("HIGH") == "STRESSED"


def test_unknown_credit_input():
    assert classify_credit_regime("BANANA") == "UNKNOWN"


def test_term_premium_rising():
    assert classify_term_premium_regime(
        "STEEP",
        "REAL_RATE",
    ) == "RISING"


def test_term_premium_low_when_inverted():
    assert classify_term_premium_regime(
        "INVERTED",
        "MIXED",
    ) == "LOW"


def test_credit_stress_has_priority():
    result = determine_dominant_driver(
        growth="WEAKENING",
        inflation="PRESSURE",
        real_rates="PRESSURE",
        term_premium="RISING",
        credit="STRESSED",
    )

    assert result == "CREDIT_STRESS"


def test_real_rate_term_premium_driver():
    result = determine_dominant_driver(
        growth="IMPROVING",
        inflation="STABLE",
        real_rates="PRESSURE",
        term_premium="RISING",
        credit="BENIGN",
    )

    assert result == "REAL_RATE_TERM_PREMIUM"


def test_inflation_driver():
    result = determine_dominant_driver(
        growth="NEUTRAL",
        inflation="PRESSURE",
        real_rates="STABLE",
        term_premium="NEUTRAL",
        credit="BENIGN",
    )

    assert result == "INFLATION_PRESSURE"


def test_growth_slowdown_driver():
    result = determine_dominant_driver(
        growth="WEAKENING",
        inflation="STABLE",
        real_rates="STABLE",
        term_premium="LOW",
        credit="BENIGN",
    )

    assert result == "GROWTH_SLOWDOWN"


def test_mixed_driver_when_no_signal_dominates():
    result = determine_dominant_driver(
        growth="NEUTRAL",
        inflation="STABLE",
        real_rates="STABLE",
        term_premium="NEUTRAL",
        credit="BENIGN",
    )

    assert result == "MIXED"


def test_high_confidence_requires_multiple_supporting_signals():
    confidence = determine_confidence(
        growth="IMPROVING",
        inflation="STABLE",
        real_rates="PRESSURE",
        term_premium="RISING",
        credit="BENIGN",
        dominant_driver="REAL_RATE_TERM_PREMIUM",
    )

    assert confidence == "HIGH"


def test_medium_confidence_single_signal():
    confidence = determine_confidence(
        growth="NEUTRAL",
        inflation="PRESSURE",
        real_rates="STABLE",
        term_premium="NEUTRAL",
        credit="BENIGN",
        dominant_driver="INFLATION_PRESSURE",
    )

    assert confidence == "MEDIUM"


def test_complete_regime_assessment():
    result = assess_regime(
        curve_shape="STEEP",
        rate_driver="REAL_RATE",
        spread_compensation="MODERATE",
    )

    assert result.policy == "NEUTRAL"
    assert result.growth == "IMPROVING"
    assert result.inflation == "STABLE"
    assert result.real_rates == "PRESSURE"
    assert result.term_premium == "RISING"
    assert result.credit == "BENIGN"
    assert result.dominant_driver == "REAL_RATE_TERM_PREMIUM"
    assert result.confidence == "HIGH"


def test_credit_stress_overrides_other_signals():
    result = assess_regime(
        curve_shape="INVERTED",
        rate_driver="INFLATION",
        spread_compensation="HIGH",
    )

    assert result.credit == "STRESSED"
    assert result.dominant_driver == "CREDIT_STRESS"
    assert result.confidence == "MEDIUM"
