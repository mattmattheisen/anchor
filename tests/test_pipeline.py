from engine.models import FixedIncomeOpportunity
from engine.pipeline import (
    evaluate_single_opportunity,
    run_decision_pipeline,
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


def test_single_opportunity_runs_through_both_engines():
    opportunity = FixedIncomeOpportunity(
        security_type="CORPORATE",
        maturity_years=5.0,
        yield_percent=5.30,
        rating="A",
    )

    regime = make_regime(
        growth="WEAKENING",
    )

    opportunity_result, risk_result = evaluate_single_opportunity(
        opportunity=opportunity,
        spread_compensation="HIGH",
        regime=regime,
    )

    assert opportunity_result.regime_fit == "CAUTIOUS"
    assert opportunity_result.classification == "SELECTIVE"

    assert risk_result.total_penalty_bps == 65.0
    assert risk_result.risk_adjusted_yield_percent == 4.65
    assert risk_result.risk_level == "ELEVATED"


def test_empty_pipeline_returns_empty_result():
    regime = make_regime()

    result = run_decision_pipeline(
        opportunities=[],
        regime=regime,
    )

    assert result.opportunities == []
    assert result.top_security_type is None
    assert result.top_maturity_years is None
    assert result.top_classification is None


def test_pipeline_ranks_multiple_securities():
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

    long_treasury = FixedIncomeOpportunity(
        security_type="TREASURY",
        maturity_years=30.0,
        yield_percent=5.20,
    )

    regime = make_regime(
        real_rates="PRESSURE",
        term_premium="RISING",
    )

    result = run_decision_pipeline(
        opportunities=[
            (treasury, "MODERATE"),
            (corporate, "HIGH"),
            (long_treasury, "HIGH"),
        ],
        regime=regime,
    )

    assert len(result.opportunities) == 3

    assert result.opportunities[0].security_type == "CORPORATE"
    assert result.opportunities[0].maturity_years == 5.0
    assert result.opportunities[0].ranking_score == 33.0

    assert result.opportunities[1].security_type == "TREASURY"
    assert result.opportunities[1].maturity_years == 2.0
    assert result.opportunities[1].ranking_score == 28.0

    assert result.opportunities[2].security_type == "TREASURY"
    assert result.opportunities[2].maturity_years == 30.0
    assert result.opportunities[2].classification == "AVOID"

    assert result.top_security_type == "CORPORATE"
    assert result.top_maturity_years == 5.0
    assert result.top_classification == "ATTRACTIVE"


def test_pipeline_preserves_risk_adjusted_yield():
    corporate = FixedIncomeOpportunity(
        security_type="CORPORATE",
        maturity_years=5.0,
        yield_percent=5.30,
        rating="A",
    )

    regime = make_regime()

    result = run_decision_pipeline(
        opportunities=[
            (corporate, "MEANINGFUL"),
        ],
        regime=regime,
    )

    security = result.opportunities[0]

    assert security.stated_yield_percent == 5.30
    assert security.total_risk_penalty_bps == 65.0
    assert security.risk_adjusted_yield_percent == 4.65
    assert security.risk_level == "ELEVATED"


def test_pipeline_preserves_ranking_score():
    treasury = FixedIncomeOpportunity(
        security_type="TREASURY",
        maturity_years=2.0,
        yield_percent=4.20,
    )

    regime = make_regime(
        real_rates="PRESSURE",
    )

    result = run_decision_pipeline(
        opportunities=[
            (treasury, "MODERATE"),
        ],
        regime=regime,
    )

    security = result.opportunities[0]

    assert security.regime_fit == "FAVORABLE"
    assert security.classification == "FAVORABLE"
    assert security.ranking_score == 28.0


def test_pipeline_retains_security_rating():
    corporate = FixedIncomeOpportunity(
        security_type="CORPORATE",
        maturity_years=7.0,
        yield_percent=5.10,
        rating="A",
    )

    regime = make_regime()

    result = run_decision_pipeline(
        opportunities=[
            (corporate, "MEANINGFUL"),
        ],
        regime=regime,
    )

    assert result.opportunities[0].rating == "A"


def test_credit_stress_changes_pipeline_classification():
    corporate = FixedIncomeOpportunity(
        security_type="CORPORATE",
        maturity_years=5.0,
        yield_percent=6.50,
        rating="BBB",
    )

    regime = make_regime(
        credit="STRESSED",
    )

    result = run_decision_pipeline(
        opportunities=[
            (corporate, "HIGH"),
        ],
        regime=regime,
    )

    security = result.opportunities[0]

    assert security.regime_fit == "CAUTIOUS"
    assert security.classification == "SELECTIVE"


def test_inflation_pressure_favors_tips():
    tips = FixedIncomeOpportunity(
        security_type="TIPS",
        maturity_years=5.0,
        yield_percent=2.10,
    )

    treasury = FixedIncomeOpportunity(
        security_type="TREASURY",
        maturity_years=10.0,
        yield_percent=4.70,
    )

    regime = make_regime(
        inflation="PRESSURE",
    )

    result = run_decision_pipeline(
        opportunities=[
            (tips, "MODERATE"),
            (treasury, "HIGH"),
        ],
        regime=regime,
    )

    tips_result = next(
        item
        for item in result.opportunities
        if item.security_type == "TIPS"
    )

    treasury_result = next(
        item
        for item in result.opportunities
        if item.security_type == "TREASURY"
    )

    assert tips_result.regime_fit == "FAVORABLE"
    assert treasury_result.regime_fit == "UNFAVORABLE"
    assert treasury_result.classification == "AVOID"


def test_pipeline_rank_numbers_are_sequential():
    opportunities = [
        (
            FixedIncomeOpportunity(
                security_type="TREASURY",
                maturity_years=2.0,
                yield_percent=4.20,
            ),
            "MODERATE",
        ),
        (
            FixedIncomeOpportunity(
                security_type="CORPORATE",
                maturity_years=5.0,
                yield_percent=5.30,
                rating="A",
            ),
            "HIGH",
        ),
        (
            FixedIncomeOpportunity(
                security_type="TIPS",
                maturity_years=5.0,
                yield_percent=2.10,
            ),
            "MODERATE",
        ),
    ]

    regime = make_regime(
        inflation="PRESSURE",
    )

    result = run_decision_pipeline(
        opportunities=opportunities,
        regime=regime,
    )

    assert [
        item.rank
        for item in result.opportunities
    ] == [1, 2, 3]


def test_pipeline_explanations_survive_integration():
    treasury = FixedIncomeOpportunity(
        security_type="TREASURY",
        maturity_years=2.0,
        yield_percent=4.20,
    )

    regime = make_regime(
        real_rates="PRESSURE",
    )

    result = run_decision_pipeline(
        opportunities=[
            (treasury, "MODERATE"),
        ],
        regime=regime,
    )

    explanation = result.opportunities[0].explanation

    assert "TREASURY" in explanation
    assert "FAVORABLE" in explanation


def test_identical_bonds_with_different_callability_keep_separate_risk():
    non_callable = FixedIncomeOpportunity(
        security_type="CORPORATE",
        maturity_years=5.0,
        yield_percent=5.30,
        rating="A",
        callable=False,
    )

    callable_bond = FixedIncomeOpportunity(
        security_type="CORPORATE",
        maturity_years=5.0,
        yield_percent=5.30,
        rating="A",
        callable=True,
    )

    regime = make_regime()

    result = run_decision_pipeline(
        opportunities=[
            (non_callable, "HIGH"),
            (callable_bond, "HIGH"),
        ],
        regime=regime,
    )

    adjusted_yields = sorted(
        item.risk_adjusted_yield_percent
        for item in result.opportunities
    )

    penalties = sorted(
        item.total_risk_penalty_bps
        for item in result.opportunities
    )

    callable_flags = [
        item.callable
        for item in result.opportunities
    ]

    assert adjusted_yields == [4.35, 4.65]
    assert penalties == [65.0, 95.0]
    assert callable_flags == [False, True]
