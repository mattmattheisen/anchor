"""
Integrated fixed-income decision pipeline for Anchor.

This module orchestrates Anchor's existing analytical
components into a single deterministic decision process.

It does not replace the underlying curve, rate, credit,
regime, opportunity, risk, or ranking engines. It coordinates
their outputs so they can be consumed as one assessment.
"""

from dataclasses import dataclass
from typing import Iterable, List, Tuple

from engine.models import FixedIncomeOpportunity
from engine.opportunity import (
    OpportunityAssessment,
    assess_opportunity,
)
from engine.ranking import (
    RankedOpportunity,
    rank_opportunities,
)
from engine.regime import RegimeAssessment
from engine.risk import (
    RiskAdjustedAssessment,
    assess_risk_adjusted_yield,
)


@dataclass
class PipelineOpportunityResult:
    rank: int

    security_type: str
    maturity_years: float
    stated_yield_percent: float
    rating: str | None

    spread_compensation: str
    regime_fit: str
    classification: str

    risk_level: str
    total_risk_penalty_bps: float
    risk_adjusted_yield_percent: float

    ranking_score: float

    explanation: str


@dataclass
class PipelineResult:
    regime: RegimeAssessment
    opportunities: List[PipelineOpportunityResult]

    top_security_type: str | None
    top_maturity_years: float | None
    top_classification: str | None


def evaluate_single_opportunity(
    opportunity: FixedIncomeOpportunity,
    spread_compensation: str,
    regime: RegimeAssessment,
) -> Tuple[
    OpportunityAssessment,
    RiskAdjustedAssessment,
]:
    """
    Run one fixed-income opportunity through Anchor's
    opportunity and risk engines.
    """
    opportunity_assessment = assess_opportunity(
        opportunity=opportunity,
        spread_compensation=spread_compensation,
        regime=regime,
    )

    risk_assessment = assess_risk_adjusted_yield(
        opportunity
    )

    return (
        opportunity_assessment,
        risk_assessment,
    )


def build_pipeline_result(
    ranked: RankedOpportunity,
    risk: RiskAdjustedAssessment,
) -> PipelineOpportunityResult:
    """
    Combine ranking, opportunity, and risk outputs
    into one security-level result.
    """
    return PipelineOpportunityResult(
        rank=ranked.rank,
        security_type=ranked.security_type,
        maturity_years=ranked.maturity_years,
        stated_yield_percent=ranked.yield_percent,
        rating=ranked.rating,
        spread_compensation=ranked.spread_compensation,
        regime_fit=ranked.regime_fit,
        classification=ranked.classification,
        risk_level=risk.risk_level,
        total_risk_penalty_bps=risk.total_penalty_bps,
        risk_adjusted_yield_percent=(
            risk.risk_adjusted_yield_percent
        ),
        ranking_score=ranked.score,
        explanation=ranked.explanation,
    )


def run_decision_pipeline(
    opportunities: Iterable[
        Tuple[FixedIncomeOpportunity, str]
    ],
    regime: RegimeAssessment,
) -> PipelineResult:
    """
    Run multiple securities through Anchor's integrated
    fixed-income decision pipeline.

    Each input consists of:

        (
            FixedIncomeOpportunity,
            spread_compensation,
        )

    Example:

        (
            treasury,
            "MODERATE",
        )

    The pipeline:

        1. Assesses regime fit.
        2. Classifies the opportunity.
        3. Calculates risk-adjusted yield.
        4. Ranks all opportunities.
        5. Returns one integrated decision table.
    """
    opportunities = list(opportunities)

    if not opportunities:
        return PipelineResult(
            regime=regime,
            opportunities=[],
            top_security_type=None,
            top_maturity_years=None,
            top_classification=None,
        )

    opportunity_assessments = []
    risk_assessments = []

    for opportunity, spread_compensation in opportunities:
        opportunity_assessment, risk_assessment = (
            evaluate_single_opportunity(
                opportunity=opportunity,
                spread_compensation=spread_compensation,
                regime=regime,
            )
        )

        opportunity_assessments.append(
            opportunity_assessment
        )

        risk_assessments.append(
            risk_assessment
        )

    ranked = rank_opportunities(
        opportunity_assessments
    )

    risk_lookup = {
        (
            risk.security_type,
            risk.maturity_years,
            risk.stated_yield_percent,
            risk.rating,
        ): risk
        for risk in risk_assessments
    }

    integrated_results = []

    for ranked_opportunity in ranked:
        key = (
            ranked_opportunity.security_type,
            ranked_opportunity.maturity_years,
            ranked_opportunity.yield_percent,
            ranked_opportunity.rating,
        )

        risk = risk_lookup[key]

        integrated_results.append(
            build_pipeline_result(
                ranked=ranked_opportunity,
                risk=risk,
            )
        )

    top = integrated_results[0]

    return PipelineResult(
        regime=regime,
        opportunities=integrated_results,
        top_security_type=top.security_type,
        top_maturity_years=top.maturity_years,
        top_classification=top.classification,
    )
