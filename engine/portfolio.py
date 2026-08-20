"""
Deterministic portfolio recommendation layer for Anchor.

This module combines Anchor's fixed-income decision pipeline
with its regime-based allocation guidance.

It does not determine client-specific allocation percentages.
Its purpose is to organize Anchor's analytical conclusions
into a portfolio-level recommendation object.
"""

from dataclasses import dataclass
from typing import List, Optional

from engine.allocation import (
    AllocationGuidance,
    build_allocation_guidance,
)
from engine.pipeline import (
    PipelineOpportunityResult,
    PipelineResult,
)


@dataclass
class PortfolioRecommendation:
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


def _select_opportunities(
    pipeline_result: PipelineResult,
    max_selections: int,
) -> List[PipelineOpportunityResult]:
    """
    Select the highest-ranked opportunities from the
    completed Anchor pipeline.

    The pipeline is already responsible for ranking.
    This function preserves that ordering rather than
    independently re-ranking securities.
    """

    if max_selections < 1:
        raise ValueError(
            "max_selections must be at least 1."
        )

    return pipeline_result.opportunities[:max_selections]


def _build_portfolio_rationale(
    pipeline_result: PipelineResult,
    allocation: AllocationGuidance,
    selected: List[PipelineOpportunityResult],
) -> List[str]:
    """
    Combine allocation and security-selection reasoning
    into a portfolio-level rationale.
    """

    rationale = list(allocation.rationale)

    if selected:
        top = selected[0]

        rationale.append(
            f"Anchor's highest-ranked opportunity is the "
            f"{top.maturity_years:g}-year "
            f"{top.security_type.upper()} with a "
            f"{top.classification} classification."
        )

        rationale.append(
            f"Its risk-adjusted yield is "
            f"{top.risk_adjusted_yield_percent:.2f}% "
            f"after a {top.total_risk_penalty_bps:.0f} bp "
            f"risk penalty."
        )

        if top.callable:
            rationale.append(
                "The highest-ranked security is callable, "
                "so call risk remains part of the portfolio "
                "decision."
            )

    else:
        rationale.append(
            "No individual security opportunities are "
            "currently available for selection."
        )

    return rationale


def build_portfolio_recommendation(
    pipeline_result: PipelineResult,
    max_selections: int = 3,
) -> PortfolioRecommendation:
    """
    Build a deterministic portfolio recommendation from
    Anchor's integrated pipeline result.

    The recommendation combines:

    1. regime-based allocation guidance,
    2. ranked security opportunities, and
    3. risk-aware portfolio rationale.

    It intentionally does not assign client-specific
    portfolio percentages.
    """

    allocation = build_allocation_guidance(
        pipeline_result.regime
    )

    selected = _select_opportunities(
        pipeline_result,
        max_selections,
    )

    rationale = _build_portfolio_rationale(
        pipeline_result,
        allocation,
        selected,
    )

    return PortfolioRecommendation(
        duration_posture=allocation.duration_posture,
        credit_posture=allocation.credit_posture,
        inflation_posture=allocation.inflation_posture,
        liquidity_posture=allocation.liquidity_posture,
        preferred_exposures=list(
            allocation.preferred_exposures
        ),
        exposures_to_limit=list(
            allocation.exposures_to_limit
        ),
        top_security_type=pipeline_result.top_security_type,
        top_maturity_years=pipeline_result.top_maturity_years,
        top_classification=pipeline_result.top_classification,
        selected_opportunities=selected,
        rationale=rationale,
    )
