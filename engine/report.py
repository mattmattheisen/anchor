"""
Standardized decision reporting for Anchor.

This module packages Anchor's existing analytical outputs
into one stable, machine-readable decision report.

It does not perform new analysis. It consumes conclusions
already produced by the regime, pipeline, allocation,
portfolio, and summary layers.
"""

from dataclasses import dataclass
from typing import List, Optional

from engine.pipeline import PipelineOpportunityResult
from engine.portfolio import PortfolioRecommendation
from engine.summary import DecisionSummary


@dataclass
class DecisionReport:
    headline: str
    recommendation: str

    duration_posture: str
    credit_posture: str
    inflation_posture: str
    liquidity_posture: str

    preferred_exposures: List[str]
    exposures_to_limit: List[str]

    top_security_type: Optional[str]
    top_maturity_years: Optional[float]
    top_classification: Optional[str]

    selected_opportunities: List[PipelineOpportunityResult]

    rationale: List[str]
    cautions: List[str]


def build_decision_report(
    portfolio: PortfolioRecommendation,
    summary: DecisionSummary,
) -> DecisionReport:
    """
    Combine Anchor's portfolio recommendation and
    deterministic summary into one final report object.

    This function intentionally performs no additional
    ranking, risk scoring, regime classification, or
    allocation analysis.
    """

    rationale = []

    rationale.extend(
        summary.rationale
    )

    rationale.extend(
        portfolio.rationale
    )

    rationale = list(
        dict.fromkeys(rationale)
    )

    cautions = list(
        dict.fromkeys(summary.cautions)
    )

    return DecisionReport(
        headline=summary.headline,
        recommendation=summary.recommendation,
        duration_posture=portfolio.duration_posture,
        credit_posture=portfolio.credit_posture,
        inflation_posture=portfolio.inflation_posture,
        liquidity_posture=portfolio.liquidity_posture,
        preferred_exposures=list(
            portfolio.preferred_exposures
        ),
        exposures_to_limit=list(
            portfolio.exposures_to_limit
        ),
        top_security_type=portfolio.top_security_type,
        top_maturity_years=portfolio.top_maturity_years,
        top_classification=portfolio.top_classification,
        selected_opportunities=list(
            portfolio.selected_opportunities
        ),
        rationale=rationale,
        cautions=cautions,
    )
