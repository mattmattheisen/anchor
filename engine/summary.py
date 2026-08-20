"""
Deterministic decision summaries for Anchor.

This module converts Anchor's integrated fixed-income
pipeline results into concise, human-readable explanations.

The summary layer does not make investment decisions.
It explains decisions already produced by the analytical
pipeline.
"""

from dataclasses import dataclass
from typing import List

from engine.pipeline import (
    PipelineOpportunityResult,
    PipelineResult,
)


@dataclass
class DecisionSummary:
    headline: str
    recommendation: str
    rationale: List[str]
    cautions: List[str]


def _security_label(
    opportunity: PipelineOpportunityResult,
) -> str:
    """
    Build a concise label for a security.
    """
    security_type = opportunity.security_type.upper()

    label = (
        f"{opportunity.maturity_years:g}-year "
        f"{security_type}"
    )

    if opportunity.rating:
        label += f" ({opportunity.rating})"

    if opportunity.callable:
        label += " callable"

    return label


def _build_rationale(
    opportunity: PipelineOpportunityResult,
) -> List[str]:
    """
    Explain the strongest attributes of an opportunity.
    """
    rationale = []

    rationale.append(
        f"Anchor classification: "
        f"{opportunity.classification}."
    )

    rationale.append(
        f"Regime fit: {opportunity.regime_fit}."
    )

    rationale.append(
        f"Spread compensation: "
        f"{opportunity.spread_compensation}."
    )

    rationale.append(
        f"Stated yield: "
        f"{opportunity.stated_yield_percent:.2f}%."
    )

    rationale.append(
        f"Risk-adjusted yield: "
        f"{opportunity.risk_adjusted_yield_percent:.2f}%."
    )

    return rationale


def _build_cautions(
    opportunity: PipelineOpportunityResult,
) -> List[str]:
    """
    Surface material cautions already identified
    by Anchor's deterministic engines.
    """
    cautions = []

    if opportunity.risk_level in {
        "ELEVATED",
        "HIGH",
    }:
        cautions.append(
            f"Risk level is {opportunity.risk_level}."
        )

    if opportunity.total_risk_penalty_bps > 0:
        cautions.append(
            f"Anchor applies a "
            f"{opportunity.total_risk_penalty_bps:.0f} bp "
            f"risk penalty."
        )

    if opportunity.callable:
        cautions.append(
            "The security is callable."
        )

    if opportunity.regime_fit == "CAUTIOUS":
        cautions.append(
            "Current regime conditions warrant caution."
        )

    if opportunity.regime_fit == "UNFAVORABLE":
        cautions.append(
            "Current regime conditions are unfavorable."
        )

    return cautions


def summarize_pipeline(
    result: PipelineResult,
) -> DecisionSummary:
    """
    Produce a deterministic summary of an Anchor
    pipeline result.

    Raises:
        ValueError if the pipeline contains no
        opportunities.
    """
    if not result.opportunities:
        raise ValueError(
            "Cannot summarize an empty pipeline result."
        )

    top = result.opportunities[0]

    label = _security_label(top)

    headline = (
        f"Anchor ranks the {label} first."
    )

    recommendation = (
        f"The {label} receives an Anchor classification "
        f"of {top.classification} with a ranking score "
        f"of {top.ranking_score:.1f}."
    )

    rationale = _build_rationale(top)
    cautions = _build_cautions(top)

    return DecisionSummary(
        headline=headline,
        recommendation=recommendation,
        rationale=rationale,
        cautions=cautions,
    )
