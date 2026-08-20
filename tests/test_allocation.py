from engine.allocation import build_allocation_guidance
from engine.regime import RegimeAssessment


def make_regime(
    growth="NEUTRAL",
    inflation="STABLE",
    real_rates="STABLE",
    term_premium="NEUTRAL",
    credit="BENIGN",
):
    return RegimeAssessment(
        policy="NEUTRAL",
        growth=growth,
        inflation=inflation,
        real_rates=real_rates,
        term_premium=term_premium,
        credit=credit,
        dominant_driver="MIXED",
        confidence="MEDIUM",
    )


def test_real_rate_pressure_shortens_duration():
    regime = make_regime(
        real_rates="PRESSURE",
    )

    result = build_allocation_guidance(regime)

    assert result.duration_posture == "SHORT"
    assert (
        "SHORT_INTERMEDIATE_TREASURIES"
        in result.preferred_exposures
    )
    assert (
        "LONG_DURATION_NOMINAL_BONDS"
        in result.exposures_to_limit
    )


def test_rising_term_premium_shortens_duration():
    regime = make_regime(
        term_premium="RISING",
    )

    result = build_allocation_guidance(regime)

    assert result.duration_posture == "SHORT"


def test_weakening_growth_can_extend_duration():
    regime = make_regime(
        growth="WEAKENING",
        inflation="STABLE",
    )

    result = build_allocation_guidance(regime)

    assert result.duration_posture == "EXTEND"
    assert (
        "INTERMEDIATE_LONG_TREASURIES"
        in result.preferred_exposures
    )


def test_inflation_pressure_blocks_growth_duration_extension():
    regime = make_regime(
        growth="WEAKENING",
        inflation="PRESSURE",
    )

    result = build_allocation_guidance(regime)

    assert result.duration_posture == "NEUTRAL"


def test_credit_stress_is_defensive():
    regime = make_regime(
        credit="STRESSED",
    )

    result = build_allocation_guidance(regime)

    assert result.credit_posture == "DEFENSIVE"
    assert (
        "HIGH_QUALITY_GOVERNMENT"
        in result.preferred_exposures
    )
    assert (
        "LOWER_QUALITY_CREDIT"
        in result.exposures_to_limit
    )


def test_benign_credit_is_selective():
    regime = make_regime(
        credit="BENIGN",
    )

    result = build_allocation_guidance(regime)

    assert result.credit_posture == "SELECTIVE"
    assert (
        "INVESTMENT_GRADE_CREDIT"
        in result.preferred_exposures
    )


def test_inflation_pressure_prefers_tips():
    regime = make_regime(
        inflation="PRESSURE",
    )

    result = build_allocation_guidance(regime)

    assert result.inflation_posture == "HEDGE"
    assert "TIPS" in result.preferred_exposures
    assert (
        "LONG_NOMINAL_DURATION"
        in result.exposures_to_limit
    )


def test_falling_inflation_prefers_nominals():
    regime = make_regime(
        inflation="FALLING",
    )

    result = build_allocation_guidance(regime)

    assert result.inflation_posture == "NOMINAL"
    assert (
        "NOMINAL_TREASURIES"
        in result.preferred_exposures
    )


def test_credit_stress_elevates_liquidity():
    regime = make_regime(
        credit="STRESSED",
    )

    result = build_allocation_guidance(regime)

    assert result.liquidity_posture == "ELEVATED"
    assert (
        "TREASURY_BILLS_AND_CASH"
        in result.preferred_exposures
    )


def test_weakening_growth_elevates_liquidity():
    regime = make_regime(
        growth="WEAKENING",
    )

    result = build_allocation_guidance(regime)

    assert result.liquidity_posture == "ELEVATED"


def test_neutral_regime_uses_intermediate_treasuries():
    regime = make_regime(
        credit="UNKNOWN",
    )

    result = build_allocation_guidance(regime)

    assert result.duration_posture == "NEUTRAL"
    assert (
        "INTERMEDIATE_TREASURIES"
        in result.preferred_exposures
    )
    assert result.liquidity_posture == "NORMAL"


def test_stressed_inflationary_real_rate_regime_combines_signals():
    regime = make_regime(
        growth="WEAKENING",
        inflation="PRESSURE",
        real_rates="PRESSURE",
        term_premium="RISING",
        credit="STRESSED",
    )

    result = build_allocation_guidance(regime)

    assert result.duration_posture == "SHORT"
    assert result.credit_posture == "DEFENSIVE"
    assert result.inflation_posture == "HEDGE"
    assert result.liquidity_posture == "ELEVATED"

    assert (
        "SHORT_INTERMEDIATE_TREASURIES"
        in result.preferred_exposures
    )
    assert (
        "HIGH_QUALITY_GOVERNMENT"
        in result.preferred_exposures
    )
    assert "TIPS" in result.preferred_exposures
    assert (
        "TREASURY_BILLS_AND_CASH"
        in result.preferred_exposures
    )


def test_preferred_exposures_do_not_contain_duplicates():
    regime = make_regime(
        growth="WEAKENING",
        credit="STRESSED",
    )

    result = build_allocation_guidance(regime)

    assert len(result.preferred_exposures) == len(
        set(result.preferred_exposures)
    )


def test_exposures_to_limit_do_not_contain_duplicates():
    regime = make_regime(
        inflation="PRESSURE",
        real_rates="PRESSURE",
        term_premium="RISING",
    )

    result = build_allocation_guidance(regime)

    assert len(result.exposures_to_limit) == len(
        set(result.exposures_to_limit)
    )


def test_allocation_guidance_contains_rationale():
    regime = make_regime(
        credit="STRESSED",
    )

    result = build_allocation_guidance(regime)

    assert len(result.rationale) > 0
    assert any(
        "Credit stress" in item
        for item in result.rationale
    )
