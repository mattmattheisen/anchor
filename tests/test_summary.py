import pytest

from engine.pipeline import (
    PipelineOpportunityResult,
    PipelineResult,
)
from engine.regime import RegimeAssessment
from engine.summary import summarize_pipeline


def make_regime():
    return RegimeAssessment(
        policy="NEUTRAL",
        growth="NEUTRAL",
        inflation="STABLE",
        real_rates="STABLE",
        term_premium="NEUTRAL",
        credit="BENIGN",
        dominant_driver="MIXED",
        confidence="MEDIUM",
    )


def make_opportunity(
    security_type="CORPORATE",
    maturity_years=5.0,
    stated_yield_percent=5.30,
    rating="A",
    callable=False,
    spread_compensation="HIGH",
    regime_fit="NEUTRAL",
    classification="ATTRACTIVE",
    risk_level="ELEVATED",
    total_risk_penalty_bps=65.0,
    risk_adjusted_yield_percent=4.65,
    ranking_score=33.0,
):
    return PipelineOpportunityResult(
        rank=1,
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


def test_summary_headline_identifies_top_security():
    opportunity = make_opportunity()

    result = PipelineResult(
        regime=make_regime(),
        opportunities=[opportunity],
        top_security_type="CORPORATE",
        top_maturity_years=5.0,
        top_classification="ATTRACTIVE",
    )

    summary = summarize_pipeline(result)

    assert summary.headline == (
        "Anchor ranks the 5-year CORPORATE (A) first."
    )


def test_summary_recommendation_contains_classification_and_score():
    opportunity = make_opportunity()

    result = PipelineResult(
        regime=make_regime(),
        opportunities=[opportunity],
        top_security_type="CORPORATE",
        top_maturity_years=5.0,
        top_classification="ATTRACTIVE",
    )

    summary = summarize_pipeline(result)

    assert "ATTRACTIVE" in summary.recommendation
    assert "33.0" in summary.recommendation


def test_summary_contains_core_rationale():
    opportunity = make_opportunity()

    result = PipelineResult(
        regime=make_regime(),
        opportunities=[opportunity],
        top_security_type="CORPORATE",
        top_maturity_years=5.0,
        top_classification="ATTRACTIVE",
    )

    summary = summarize_pipeline(result)

    assert "Anchor classification: ATTRACTIVE." in summary.rationale
    assert "Regime fit: NEUTRAL." in summary.rationale
    assert "Spread compensation: HIGH." in summary.rationale
    assert "Stated yield: 5.30%." in summary.rationale
    assert "Risk-adjusted yield: 4.65%." in summary.rationale


def test_elevated_risk_is_included_in_cautions():
    opportunity = make_opportunity(
        risk_level="ELEVATED",
    )

    result = PipelineResult(
        regime=make_regime(),
        opportunities=[opportunity],
        top_security_type="CORPORATE",
        top_maturity_years=5.0,
        top_classification="ATTRACTIVE",
    )

    summary = summarize_pipeline(result)

    assert "Risk level is ELEVATED." in summary.cautions


def test_risk_penalty_is_included_in_cautions():
    opportunity = make_opportunity(
        total_risk_penalty_bps=65.0,
    )

    result = PipelineResult(
        regime=make_regime(),
        opportunities=[opportunity],
        top_security_type="CORPORATE",
        top_maturity_years=5.0,
        top_classification="ATTRACTIVE",
    )

    summary = summarize_pipeline(result)

    assert "Anchor applies a 65 bp risk penalty." in summary.cautions


def test_callable_security_is_identified():
    opportunity = make_opportunity(
        callable=True,
    )

    result = PipelineResult(
        regime=make_regime(),
        opportunities=[opportunity],
        top_security_type="CORPORATE",
        top_maturity_years=5.0,
        top_classification="ATTRACTIVE",
    )

    summary = summarize_pipeline(result)

    assert (
        "Anchor ranks the 5-year CORPORATE (A) callable first."
        == summary.headline
    )

    assert "The security is callable." in summary.cautions


def test_cautious_regime_is_identified():
    opportunity = make_opportunity(
        regime_fit="CAUTIOUS",
    )

    result = PipelineResult(
        regime=make_regime(),
        opportunities=[opportunity],
        top_security_type="CORPORATE",
        top_maturity_years=5.0,
        top_classification="SELECTIVE",
    )

    summary = summarize_pipeline(result)

    assert (
        "Current regime conditions warrant caution."
        in summary.cautions
    )


def test_unfavorable_regime_is_identified():
    opportunity = make_opportunity(
        security_type="TREASURY",
        maturity_years=30.0,
        rating=None,
        regime_fit="UNFAVORABLE",
        classification="AVOID",
        risk_level="HIGH",
        total_risk_penalty_bps=100.0,
        risk_adjusted_yield_percent=4.20,
        ranking_score=-1.0,
    )

    result = PipelineResult(
        regime=make_regime(),
        opportunities=[opportunity],
        top_security_type="TREASURY",
        top_maturity_years=30.0,
        top_classification="AVOID",
    )

    summary = summarize_pipeline(result)

    assert (
        "Current regime conditions are unfavorable."
        in summary.cautions
    )


def test_low_risk_zero_penalty_has_no_cautions():
    opportunity = make_opportunity(
        security_type="TREASURY",
        maturity_years=1.0,
        rating=None,
        risk_level="LOW",
        total_risk_penalty_bps=0.0,
        callable=False,
        regime_fit="NEUTRAL",
    )

    result = PipelineResult(
        regime=make_regime(),
        opportunities=[opportunity],
        top_security_type="TREASURY",
        top_maturity_years=1.0,
        top_classification="NEUTRAL",
    )

    summary = summarize_pipeline(result)

    assert summary.cautions == []


def test_summary_uses_first_ranked_opportunity():
    first = make_opportunity(
        security_type="TREASURY",
        maturity_years=2.0,
        rating=None,
        classification="FAVORABLE",
        ranking_score=28.0,
    )

    second = make_opportunity(
        security_type="CORPORATE",
        maturity_years=5.0,
        rating="A",
        classification="ATTRACTIVE",
        ranking_score=33.0,
    )

    result = PipelineResult(
        regime=make_regime(),
        opportunities=[first, second],
        top_security_type="TREASURY",
        top_maturity_years=2.0,
        top_classification="FAVORABLE",
    )

    summary = summarize_pipeline(result)

    assert "2-year TREASURY" in summary.headline


def test_empty_pipeline_cannot_be_summarized():
    result = PipelineResult(
        regime=make_regime(),
        opportunities=[],
        top_security_type=None,
        top_maturity_years=None,
        top_classification=None,
    )

    with pytest.raises(
        ValueError,
        match="Cannot summarize an empty pipeline result",
    ):
        summarize_pipeline(result)
