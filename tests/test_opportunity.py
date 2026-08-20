from engine.models import FixedIncomeOpportunity
from engine.opportunity import (
    classify_regime_fit,
    classify_opportunity,
    build_explanation,
    assess_opportunity,
)
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


def test_tips_favored_during_inflation_pressure():
    opportunity = FixedIncomeOpportunity(
        security_type="TIPS",
        maturity_years=5.0,
        yield_percent=2.10,
    )

    regime = make_regime(
        inflation="PRESSURE",
    )

    assert classify_regime_fit(
        opportunity,
        regime,
    ) == "FAVORABLE"


def test_long_treasury_unfavorable_during_inflation_pressure():
    opportunity = FixedIncomeOpportunity(
        security_type="TREASURY",
        maturity_years=10.0,
        yield_percent=4.70,
    )

    regime = make_regime(
        inflation="PRESSURE",
    )

    assert classify_regime_fit(
        opportunity,
        regime,
    ) == "UNFAVORABLE"


def test_short_duration_favored_during_real_rate_pressure():
    opportunity = FixedIncomeOpportunity(
        security_type="TREASURY",
        maturity_years=2.0,
        yield_percent=4.20,
    )

    regime = make_regime(
        real_rates="PRESSURE",
    )

    assert classify_regime_fit(
        opportunity,
        regime,
    ) == "FAVORABLE"


def test_long_duration_unfavorable_during_real_rate_pressure():
    opportunity = FixedIncomeOpportunity(
        security_type="TREASURY",
        maturity_years=30.0,
        yield_percent=5.20,
    )

    regime = make_regime(
        real_rates="PRESSURE",
    )

    assert classify_regime_fit(
        opportunity,
        regime,
    ) == "UNFAVORABLE"


def test_treasury_favored_during_growth_slowdown():
    opportunity = FixedIncomeOpportunity(
        security_type="TREASURY",
        maturity_years=5.0,
        yield_percent=4.40,
    )

    regime = make_regime(
        growth="WEAKENING",
    )

    assert classify_regime_fit(
        opportunity,
        regime,
    ) == "FAVORABLE"


def test_corporate_cautious_during_growth_slowdown():
    opportunity = FixedIncomeOpportunity(
        security_type="CORPORATE",
        maturity_years=5.0,
        yield_percent=5.30,
        rating="A",
    )

    regime = make_regime(
        growth="WEAKENING",
    )

    assert classify_regime_fit(
        opportunity,
        regime,
    ) == "CAUTIOUS"


def test_corporate_cautious_during_credit_stress():
    opportunity = FixedIncomeOpportunity(
        security_type="CORPORATE",
        maturity_years=5.0,
        yield_percent=6.50,
        rating="BBB",
    )

    regime = make_regime(
        credit="STRESSED",
    )

    assert classify_regime_fit(
        opportunity,
        regime,
    ) == "CAUTIOUS"


def test_treasury_favored_during_credit_stress():
    opportunity = FixedIncomeOpportunity(
        security_type="TREASURY",
        maturity_years=5.0,
        yield_percent=4.40,
    )

    regime = make_regime(
        credit="STRESSED",
    )

    assert classify_regime_fit(
        opportunity,
        regime,
    ) == "FAVORABLE"


def test_unfavorable_regime_overrides_high_spread():
    assert classify_opportunity(
        spread_compensation="HIGH",
        regime_fit="UNFAVORABLE",
    ) == "AVOID"


def test_favorable_regime_plus_high_compensation_is_attractive():
    assert classify_opportunity(
        spread_compensation="HIGH",
        regime_fit="FAVORABLE",
    ) == "ATTRACTIVE"


def test_cautious_regime_plus_high_compensation_is_selective():
    assert classify_opportunity(
        spread_compensation="HIGH",
        regime_fit="CAUTIOUS",
    ) == "SELECTIVE"


def test_neutral_regime_plus_meaningful_compensation_is_favorable():
    assert classify_opportunity(
        spread_compensation="MEANINGFUL",
        regime_fit="NEUTRAL",
    ) == "FAVORABLE"


def test_thin_compensation_is_unattractive_when_regime_is_neutral():
    assert classify_opportunity(
        spread_compensation="THIN",
        regime_fit="NEUTRAL",
    ) == "UNATTRACTIVE"


def test_complete_opportunity_assessment():
    opportunity = FixedIncomeOpportunity(
        security_type="CORPORATE",
        maturity_years=5.0,
        yield_percent=5.30,
        rating="A",
    )

    regime = make_regime(
        growth="WEAKENING",
    )

    result = assess_opportunity(
        opportunity=opportunity,
        spread_compensation="HIGH",
        regime=regime,
    )

    assert result.security_type == "CORPORATE"
    assert result.maturity_years == 5.0
    assert result.yield_percent == 5.30
    assert result.rating == "A"
    assert result.spread_compensation == "HIGH"
    assert result.regime_fit == "CAUTIOUS"
    assert result.classification == "SELECTIVE"

    assert "Anchor classifies the opportunity as SELECTIVE" in (
        result.explanation
    )


def test_unknown_security_type_defaults_to_neutral():
    opportunity = FixedIncomeOpportunity(
        security_type="BANANA_BOND",
        maturity_years=5.0,
        yield_percent=9.99,
    )

    regime = make_regime()

    assert classify_regime_fit(
        opportunity,
        regime,
    ) == "NEUTRAL"


def test_explanation_contains_core_fields():
    opportunity = FixedIncomeOpportunity(
        security_type="CORPORATE",
        maturity_years=7.0,
        yield_percent=5.10,
        rating="A",
    )

    explanation = build_explanation(
        opportunity=opportunity,
        spread_compensation="MEANINGFUL",
        regime_fit="NEUTRAL",
        classification="FAVORABLE",
    )

    assert "CORPORATE" in explanation
    assert "7.0-year maturity" in explanation
    assert "meaningful" in explanation
    assert "neutral" in explanation
    assert "FAVORABLE" in explanation
