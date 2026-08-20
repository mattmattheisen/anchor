"""
Fixed-income opportunity evaluation for Anchor.

This module combines relative value with regime context
to produce a first-pass qualitative assessment of an
investable fixed-income opportunity.
"""

from dataclasses import dataclass

from engine.models import FixedIncomeOpportunity
from engine.regime import RegimeAssessment


@dataclass
class OpportunityAssessment:
    security_type: str
    maturity_years: float
    yield_percent: float
    rating: str | None

    spread_compensation: str
    regime_fit: str
    classification: str

    explanation: str


def classify_regime_fit(
    opportunity: FixedIncomeOpportunity,
    regime: RegimeAssessment,
) -> str:
    """
    Determine whether an opportunity broadly fits
    Anchor's current fixed-income regime.
    """
    security_type = opportunity.security_type.upper()

    if regime.credit == "STRESSED":
        if security_type in {"TREASURY", "TIPS", "CD"}:
            return "FAVORABLE"

        if security_type == "CORPORATE":
            return "CAUTIOUS"

    if regime.inflation == "PRESSURE":
        if security_type == "TIPS":
            return "FAVORABLE"

        if security_type == "TREASURY" and opportunity.maturity_years >= 10:
            return "UNFAVORABLE"

    if regime.real_rates == "PRESSURE":
        if opportunity.maturity_years >= 10:
            return "UNFAVORABLE"

        if opportunity.maturity_years <= 3:
            return "FAVORABLE"

    if regime.growth == "WEAKENING":
        if security_type == "TREASURY":
            return "FAVORABLE"

        if security_type == "CORPORATE":
            return "CAUTIOUS"

    if regime.term_premium == "RISING":
        if opportunity.maturity_years >= 10:
            return "UNFAVORABLE"

    return "NEUTRAL"


def classify_opportunity(
    spread_compensation: str,
    regime_fit: str,
) -> str:
    """
    Combine relative-value compensation and regime fit
    into a first-pass opportunity classification.
    """
    if regime_fit == "UNFAVORABLE":
        return "AVOID"

    if regime_fit == "FAVORABLE":
        if spread_compensation in {"MEANINGFUL", "HIGH"}:
            return "ATTRACTIVE"

        if spread_compensation == "MODERATE":
            return "FAVORABLE"

        return "NEUTRAL"

    if regime_fit == "CAUTIOUS":
        if spread_compensation == "HIGH":
            return "SELECTIVE"

        return "CAUTIOUS"

    if spread_compensation == "HIGH":
        return "ATTRACTIVE"

    if spread_compensation == "MEANINGFUL":
        return "FAVORABLE"

    if spread_compensation == "MODERATE":
        return "NEUTRAL"

    return "UNATTRACTIVE"


def build_explanation(
    opportunity: FixedIncomeOpportunity,
    spread_compensation: str,
    regime_fit: str,
    classification: str,
) -> str:
    """
    Build a concise explanation for Anchor's assessment.
    """
    return (
        f"{opportunity.security_type} with "
        f"{opportunity.maturity_years:.1f}-year maturity "
        f"has {spread_compensation.lower()} relative-value compensation "
        f"and a {regime_fit.lower()} fit with the current regime. "
        f"Anchor classifies the opportunity as {classification}."
    )


def assess_opportunity(
    opportunity: FixedIncomeOpportunity,
    spread_compensation: str,
    regime: RegimeAssessment,
) -> OpportunityAssessment:
    """
    Create Anchor's first-pass assessment of an
    investable fixed-income opportunity.
    """
    regime_fit = classify_regime_fit(
        opportunity,
        regime,
    )

    classification = classify_opportunity(
        spread_compensation,
        regime_fit,
    )

    explanation = build_explanation(
        opportunity,
        spread_compensation,
        regime_fit,
        classification,
    )

    return OpportunityAssessment(
        security_type=opportunity.security_type,
        maturity_years=opportunity.maturity_years,
        yield_percent=opportunity.yield_percent,
        rating=opportunity.rating,
        spread_compensation=spread_compensation,
        regime_fit=regime_fit,
        classification=classification,
        explanation=explanation,
    )
