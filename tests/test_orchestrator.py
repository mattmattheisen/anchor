import json

import pytest

from engine.orchestrator import run_decision_process
from engine.pipeline import (
    PipelineOpportunityResult,
    PipelineResult,
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


def make_opportunity(
    rank=1,
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
    opportunities=None,
    regime=None,
):
    if opportunities is None:
        opportunities = [
            make_opportunity()
        ]

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


def test_orchestrator_returns_dictionary():
    result = run_decision_process(
        make_pipeline()
    )

    assert isinstance(result, dict)


def test_orchestrator_returns_json_compatible_output():
    result = run_decision_process(
        make_pipeline()
    )

    encoded = json.dumps(result)

    assert isinstance(encoded, str)


def test_orchestrator_preserves_top_opportunity():
    result = run_decision_process(
        make_pipeline()
    )

    assert result["top_opportunity"] == {
        "security_type": "CORPORATE",
        "maturity_years": 5.0,
        "classification": "ATTRACTIVE",
    }


def test_orchestrator_preserves_security_details():
    result = run_decision_process(
        make_pipeline()
    )

    opportunity = (
        result["selected_opportunities"][0]
    )

    assert opportunity["security_type"] == "CORPORATE"
    assert opportunity["maturity_years"] == 5.0
    assert opportunity["rating"] == "A"
    assert opportunity["ranking_score"] == 33.0
    assert (
        opportunity["risk_adjusted_yield_percent"]
        == 4.65
    )


def test_orchestrator_builds_summary():
    result = run_decision_process(
        make_pipeline()
    )

    assert (
        result["headline"]
        == "Anchor ranks the 5-year CORPORATE (A) first."
    )

    assert "ATTRACTIVE" in result["recommendation"]


def test_orchestrator_builds_allocation_posture():
    regime = make_regime(
        inflation="PRESSURE",
        real_rates="PRESSURE",
        term_premium="RISING",
        credit="STRESSED",
    )

    result = run_decision_process(
        make_pipeline(
            regime=regime
        )
    )

    assert result["portfolio_posture"] == {
        "duration": "SHORT",
        "credit": "DEFENSIVE",
        "inflation": "HEDGE",
        "liquidity": "ELEVATED",
    }


def test_orchestrator_carries_preferred_exposures():
    regime = make_regime(
        inflation="PRESSURE",
        credit="STRESSED",
    )

    result = run_decision_process(
        make_pipeline(
            regime=regime
        )
    )

    assert "TIPS" in result["preferred_exposures"]
    assert (
        "HIGH_QUALITY_GOVERNMENT"
        in result["preferred_exposures"]
    )


def test_orchestrator_respects_max_selections():
    opportunities = [
        make_opportunity(
            rank=1,
            security_type="TREASURY",
            maturity_years=2.0,
            ranking_score=30.0,
            rating=None,
        ),
        make_opportunity(
            rank=2,
            security_type="CORPORATE",
            maturity_years=5.0,
            ranking_score=28.0,
        ),
        make_opportunity(
            rank=3,
            security_type="TIPS",
            maturity_years=5.0,
            ranking_score=25.0,
            rating=None,
        ),
    ]

    result = run_decision_process(
        make_pipeline(opportunities),
        max_selections=2,
    )

    assert len(
        result["selected_opportunities"]
    ) == 2

    assert [
        item["rank"]
        for item in result["selected_opportunities"]
    ] == [1, 2]


def test_orchestrator_does_not_rerank_pipeline():
    first = make_opportunity(
        rank=1,
        security_type="TREASURY",
        maturity_years=2.0,
        ranking_score=10.0,
        rating=None,
    )

    second = make_opportunity(
        rank=2,
        security_type="CORPORATE",
        maturity_years=5.0,
        ranking_score=99.0,
    )

    result = run_decision_process(
        make_pipeline(
            [first, second]
        )
    )

    assert (
        result["selected_opportunities"][0][
            "security_type"
        ]
        == "TREASURY"
    )


def test_callable_security_surfaces_caution():
    opportunity = make_opportunity(
        callable=True,
        total_risk_penalty_bps=95.0,
        risk_adjusted_yield_percent=4.35,
    )

    result = run_decision_process(
        make_pipeline(
            [opportunity]
        )
    )

    assert (
        "The security is callable."
        in result["cautions"]
    )


def test_callable_security_surfaces_portfolio_rationale():
    opportunity = make_opportunity(
        callable=True,
        total_risk_penalty_bps=95.0,
        risk_adjusted_yield_percent=4.35,
    )

    result = run_decision_process(
        make_pipeline(
            [opportunity]
        )
    )

    assert any(
        "highest-ranked security is callable"
        in item
        for item in result["rationale"]
    )


def test_orchestrator_rejects_invalid_max_selections():
    with pytest.raises(
        ValueError,
        match="max_selections must be at least 1",
    ):
        run_decision_process(
            make_pipeline(),
            max_selections=0,
        )


def test_empty_pipeline_cannot_be_summarized():
    pipeline = make_pipeline(
        opportunities=[]
    )

    with pytest.raises(
        ValueError,
        match="Cannot summarize an empty pipeline result",
    ):
        run_decision_process(
            pipeline
        )


def test_orchestrator_output_contains_expected_sections():
    result = run_decision_process(
        make_pipeline()
    )

    assert set(result.keys()) == {
        "schema_version",
        "headline",
        "recommendation",
        "portfolio_posture",
        "preferred_exposures",
        "exposures_to_limit",
        "top_opportunity",
        "selected_opportunities",
        "rationale",
        "cautions",
    }
