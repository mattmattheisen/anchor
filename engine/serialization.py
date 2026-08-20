"""
Serialization utilities for Anchor.

This module converts Anchor's final decision objects into
plain Python dictionaries that can be safely consumed by
JSON encoders, APIs, dashboards, saved reports, or other
external interfaces.

No analytical decisions are made here.
"""

from typing import Any, Dict, List

from engine.pipeline import PipelineOpportunityResult
from engine.report import DecisionReport


def serialize_opportunity(
    opportunity: PipelineOpportunityResult,
) -> Dict[str, Any]:
    """
    Convert a pipeline opportunity into a plain dictionary.
    """

    return {
        "rank": opportunity.rank,
        "security_type": opportunity.security_type,
        "maturity_years": opportunity.maturity_years,
        "stated_yield_percent": (
            opportunity.stated_yield_percent
        ),
        "rating": opportunity.rating,
        "callable": opportunity.callable,
        "spread_compensation": (
            opportunity.spread_compensation
        ),
        "regime_fit": opportunity.regime_fit,
        "classification": opportunity.classification,
        "risk_level": opportunity.risk_level,
        "total_risk_penalty_bps": (
            opportunity.total_risk_penalty_bps
        ),
        "risk_adjusted_yield_percent": (
            opportunity.risk_adjusted_yield_percent
        ),
        "ranking_score": opportunity.ranking_score,
        "explanation": opportunity.explanation,
    }


def serialize_decision_report(
    report: DecisionReport,
) -> Dict[str, Any]:
    """
    Convert Anchor's final DecisionReport into a
    JSON-compatible dictionary.

    The resulting structure contains only standard Python
    primitives:

    - dictionaries
    - lists
    - strings
    - numbers
    - booleans
    - None

    This keeps the analytical engine independent from any
    particular presentation or transport layer.
    """

    selected_opportunities: List[Dict[str, Any]] = [
        serialize_opportunity(opportunity)
        for opportunity in report.selected_opportunities
    ]

    return {
        "headline": report.headline,
        "recommendation": report.recommendation,
        "portfolio_posture": {
            "duration": report.duration_posture,
            "credit": report.credit_posture,
            "inflation": report.inflation_posture,
            "liquidity": report.liquidity_posture,
        },
        "preferred_exposures": list(
            report.preferred_exposures
        ),
        "exposures_to_limit": list(
            report.exposures_to_limit
        ),
        "top_opportunity": {
            "security_type": report.top_security_type,
            "maturity_years": report.top_maturity_years,
            "classification": report.top_classification,
        },
        "selected_opportunities": selected_opportunities,
        "rationale": list(report.rationale),
        "cautions": list(report.cautions),
    }
