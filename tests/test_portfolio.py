import pytest

from engine.pipeline import (
    PipelineOpportunityResult,
    PipelineResult,
)
from engine.portfolio import build_portfolio_recommendation
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


def make_opportunity(
    rank,
    security_type,
    maturity_years,
    stated_yield_percent,
    classification,
    ranking_score,
    rating=None,
    callable=False,
    spread_compensation="MODERATE",
    regime_fit="NEUTRAL",
    risk_level="MODERATE",
    total_risk_penalty_bps=25.0,
    risk_adjusted_yield_percent=4.00,
):
    return PipelineOpportunityResult(
        rank=rank,
        security_type=security_type,
        maturity_years=maturity_years,
        stated_yield_percent=stated_yield_percent,
        rating=rating,
        callable=callable,
        spread_compensation=spread_compensation,
        regime_fit=regime_fit,
        classification=classification,
        risk_level=risk_level,
        total_risk_penalty_bps=total_risk_penalty_bps,
        risk_adjusted_yield_percent=risk_adjusted_yield_percent,
        ranking_score=ranking_score,
        explanation="Test explanation.",
    )


def make_pipeline(
    opportunities,
    regime=None,
):
    if regime is None:
        regime = make_regime()

    if opportunities:
        top = opportunities[0]

        return PipelineResult(
            regime=regime,
            opportunities=opportunities,
            top_security_type=top.security_type,
            top_maturity_years=top.maturity_years,
            top_classification=top.classification,
        )

    return PipelineResult(
        regime=regime,
        opportunities=[],
        top_security_type=None,
        top_maturity_years=None,
        top_classification=None,
    )


def test_portfolio_preserves_ranked_order():
    first = make_opportunity(
        rank=1,
        security_type="TREASURY",
        maturity_years=2.0,
        stated_yield_percent=4.20,
        classification="FAVORABLE",
        ranking_score=28.0,
    )

    second = make_opportunity(
        rank=2,
        security_type="CORPORATE",
        maturity_years=5.0,
        stated_yield_percent=5.30,
        classification="ATTRACTIVE",
        ranking_score=33.0,
        rating="A",
    )

    pipeline = make_pipeline(
        [first, second]
    )

    result = build_portfolio_recommendation(
        pipeline
    )

    assert result.selected_opportunities[0] is first
    assert result.selected_opportunities[1] is second


def test_default_maximum_selects_three():
    opportunities = [
        make_opportunity(
            rank=index,
            security_type="TREASURY",
            maturity_years=float(index),
            stated_yield_percent=4.00 + index / 10,
            classification="NEUTRAL",
            ranking_score=20.0 - index,
        )
        for index in range(1, 6)
    ]

    pipeline = make_pipeline(opportunities)

    result = build_portfolio_recommendation(
        pipeline
    )

    assert len(result.selected_opportunities) == 3
    assert [
        item.rank
        for item in result.selected_opportunities
    ] == [1, 2, 3]


def test_custom_maximum_selection_count():
    opportunities = [
        make_opportunity(
            rank=index,
            security_type="TREASURY",
            maturity_years=float(index),
            stated_yield_percent=4.00,
            classification="NEUTRAL",
            ranking_score=20.0,
        )
        for index in range(1, 5)
    ]

    pipeline = make_pipeline(opportunities)

    result = build_portfolio_recommendation(
        pipeline,
        max_selections=2,
    )

    assert len(result.selected_opportunities) == 2


def test_invalid_maximum_selection_raises():
    pipeline = make_pipeline([])

    with pytest.raises(
        ValueError,
        match="max_selections must be at least 1",
    ):
        build_portfolio_recommendation(
            pipeline,
            max_selections=0,
        )


def test_empty_pipeline_returns_no_selected_opportunities():
    pipeline = make_pipeline([])

    result = build_portfolio_recommendation(
        pipeline
    )

    assert result.selected_opportunities == []
    assert result.top_security_type is None
    assert result.top_maturity_years is None
    assert result.top_classification is None


def test_empty_pipeline_has_explanatory_rationale():
    pipeline = make_pipeline([])

    result = build_portfolio_recommendation(
        pipeline
    )

    assert (
        "No individual security opportunities are currently "
        "available for selection."
        in result.rationale
    )


def test_portfolio_carries_allocation_postures():
    regime = make_regime(
        inflation="PRESSURE",
        real_rates="PRESSURE",
        term_premium="RISING",
        credit="STRESSED",
    )

    pipeline = make_pipeline(
        [],
        regime=regime,
    )

    result = build_portfolio_recommendation(
        pipeline
    )

    assert result.duration_posture == "SHORT"
    assert result.credit_posture == "DEFENSIVE"
    assert result.inflation_posture == "HEDGE"
    assert result.liquidity_posture == "ELEVATED"


def test_portfolio_carries_preferred_exposures():
    regime = make_regime(
        inflation="PRESSURE",
        credit="STRESSED",
    )

    pipeline = make_pipeline(
        [],
        regime=regime,
    )

    result = build_portfolio_recommendation(
        pipeline
    )

    assert "TIPS" in result.preferred_exposures
    assert (
        "HIGH_QUALITY_GOVERNMENT"
        in result.preferred_exposures
    )


def test_top_security_metadata_is_preserved():
    top = make_opportunity(
        rank=1,
        security_type="CORPORATE",
        maturity_years=5.0,
        stated_yield_percent=5.30,
        classification="ATTRACTIVE",
        ranking_score=33.0,
        rating="A",
    )

    pipeline = make_pipeline([top])

    result = build_portfolio_recommendation(
        pipeline
    )

    assert result.top_security_type == "CORPORATE"
    assert result.top_maturity_years == 5.0
    assert result.top_classification == "ATTRACTIVE"


def test_rationale_mentions_top_opportunity():
    top = make_opportunity(
        rank=1,
        security_type="TREASURY",
        maturity_years=2.0,
        stated_yield_percent=4.20,
        classification="FAVORABLE",
        ranking_score=28.0,
        risk_adjusted_yield_percent=4.10,
        total_risk_penalty_bps=10.0,
    )

    pipeline = make_pipeline([top])

    result = build_portfolio_recommendation(
        pipeline
    )

    assert any(
        "highest-ranked opportunity is the 2-year TREASURY"
        in item
        for item in result.rationale
    )


def test_rationale_mentions_risk_adjusted_yield():
    top = make_opportunity(
        rank=1,
        security_type="CORPORATE",
        maturity_years=5.0,
        stated_yield_percent=5.30,
        classification="ATTRACTIVE",
        ranking_score=33.0,
        rating="A",
        risk_adjusted_yield_percent=4.65,
        total_risk_penalty_bps=65.0,
    )

    pipeline = make_pipeline([top])

    result = build_portfolio_recommendation(
        pipeline
    )

    assert any(
        "risk-adjusted yield is 4.65%"
        in item
        for item in result.rationale
    )

    assert any(
        "65 bp risk penalty"
        in item
        for item in result.rationale
    )


def test_callable_top_security_adds_call_risk_rationale():
    top = make_opportunity(
        rank=1,
        security_type="CORPORATE",
        maturity_years=5.0,
        stated_yield_percent=5.60,
        classification="ATTRACTIVE",
        ranking_score=33.0,
        rating="A",
        callable=True,
        total_risk_penalty_bps=95.0,
        risk_adjusted_yield_percent=4.65,
    )

    pipeline = make_pipeline([top])

    result = build_portfolio_recommendation(
        pipeline
    )

    assert any(
        "highest-ranked security is callable"
        in item
        for item in result.rationale
    )


def test_non_callable_top_security_does_not_add_call_warning():
    top = make_opportunity(
        rank=1,
        security_type="TREASURY",
        maturity_years=2.0,
        stated_yield_percent=4.20,
        classification="FAVORABLE",
        ranking_score=28.0,
        callable=False,
    )

    pipeline = make_pipeline([top])

    result = build_portfolio_recommendation(
        pipeline
    )

    assert not any(
        "callable"
        in item.lower()
        for item in result.rationale
    )


def test_selection_does_not_re_rank_by_score():
    first = make_opportunity(
        rank=1,
        security_type="TREASURY",
        maturity_years=2.0,
        stated_yield_percent=4.20,
        classification="FAVORABLE",
        ranking_score=10.0,
    )

    second = make_opportunity(
        rank=2,
        security_type="CORPORATE",
        maturity_years=5.0,
        stated_yield_percent=5.30,
        classification="ATTRACTIVE",
        ranking_score=99.0,
        rating="A",
    )

    pipeline = make_pipeline(
        [first, second]
    )

    result = build_portfolio_recommendation(
        pipeline
    )

    assert result.selected_opportunities[0] is first
