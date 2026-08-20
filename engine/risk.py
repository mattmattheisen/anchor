"""
Risk-adjusted fixed-income analytics for Anchor.

This module applies transparent penalties to headline yield
for duration, credit, callability, and structural complexity.

The result is not an expected return forecast. It is a
deterministic comparison measure designed to prevent Anchor
from simply preferring the highest stated yield.
"""

from dataclasses import dataclass

from engine.models import FixedIncomeOpportunity


CREDIT_PENALTY_BPS = {
    "AAA": 5.0,
    "AA": 10.0,
    "A": 20.0,
    "BBB": 40.0,
    "BB": 80.0,
    "B": 120.0,
    "CCC": 200.0,
}


STRUCTURE_PENALTY_BPS = {
    "TREASURY": 0.0,
    "TIPS": 5.0,
    "CD": 10.0,
    "AGENCY": 10.0,
    "MUNICIPAL": 15.0,
    "CORPORATE": 20.0,
}


@dataclass
class RiskAdjustedAssessment:
    security_type: str
    maturity_years: float
    stated_yield_percent: float
    rating: str | None
    callable: bool

    duration_penalty_bps: float
    credit_penalty_bps: float
    call_penalty_bps: float
    structure_penalty_bps: float

    total_penalty_bps: float
    risk_adjusted_yield_percent: float

    risk_level: str


def duration_penalty_bps(
    maturity_years: float,
) -> float:
    """
    Estimate a first-pass duration penalty from maturity.

    This is intentionally a simple proxy. Anchor will later
    use actual duration when available.
    """
    if maturity_years <= 1:
        return 0.0

    if maturity_years <= 3:
        return 10.0

    if maturity_years <= 7:
        return 25.0

    if maturity_years <= 10:
        return 40.0

    if maturity_years <= 20:
        return 70.0

    return 100.0


def credit_penalty_bps(
    rating: str | None,
    security_type: str,
) -> float:
    """
    Estimate a credit-risk penalty.

    Treasury and TIPS securities receive no credit penalty.
    Unrated non-government securities receive a conservative
    default penalty.
    """
    security_type = security_type.upper()

    if security_type in {"TREASURY", "TIPS"}:
        return 0.0

    if rating is None:
        return 50.0

    return CREDIT_PENALTY_BPS.get(
        rating.upper(),
        75.0,
    )


def call_penalty_bps(
    callable_security: bool,
) -> float:
    """
    Apply a penalty to callable securities.

    Callable bonds expose the investor to reinvestment risk
    when rates fall.
    """
    if callable_security:
        return 30.0

    return 0.0


def structure_penalty_bps(
    security_type: str,
) -> float:
    """
    Apply a first-pass structural/liquidity penalty
    based on security type.
    """
    return STRUCTURE_PENALTY_BPS.get(
        security_type.upper(),
        30.0,
    )


def total_risk_penalty_bps(
    opportunity: FixedIncomeOpportunity,
) -> float:
    """
    Calculate Anchor's combined fixed-income risk penalty.
    """
    duration = duration_penalty_bps(
        opportunity.maturity_years,
    )

    credit = credit_penalty_bps(
        opportunity.rating,
        opportunity.security_type,
    )

    call = call_penalty_bps(
        opportunity.callable,
    )

    structure = structure_penalty_bps(
        opportunity.security_type,
    )

    return round(
        duration
        + credit
        + call
        + structure,
        2,
    )


def calculate_risk_adjusted_yield(
    opportunity: FixedIncomeOpportunity,
) -> float:
    """
    Subtract Anchor's risk penalty from stated yield.

    Example:

        5.30% stated yield
        65 bp total risk penalty

        risk-adjusted yield = 4.65%
    """
    penalty = total_risk_penalty_bps(
        opportunity,
    )

    return round(
        opportunity.yield_percent
        - penalty / 100,
        4,
    )


def classify_risk_level(
    total_penalty_bps: float,
) -> str:
    """
    Classify the magnitude of Anchor's aggregate risk penalty.
    """
    if total_penalty_bps < 25:
        return "LOW"

    if total_penalty_bps < 60:
        return "MODERATE"

    if total_penalty_bps < 100:
        return "ELEVATED"

    return "HIGH"


def assess_risk_adjusted_yield(
    opportunity: FixedIncomeOpportunity,
) -> RiskAdjustedAssessment:
    """
    Create a complete risk-adjusted yield assessment.
    """
    duration = duration_penalty_bps(
        opportunity.maturity_years,
    )

    credit = credit_penalty_bps(
        opportunity.rating,
        opportunity.security_type,
    )

    call = call_penalty_bps(
        opportunity.callable,
    )

    structure = structure_penalty_bps(
        opportunity.security_type,
    )

    total_penalty = round(
        duration
        + credit
        + call
        + structure,
        2,
    )

    adjusted_yield = round(
        opportunity.yield_percent
        - total_penalty / 100,
        4,
    )

    return RiskAdjustedAssessment(
        security_type=opportunity.security_type,
        maturity_years=opportunity.maturity_years,
        stated_yield_percent=opportunity.yield_percent,
        rating=opportunity.rating,
        callable=opportunity.callable,
        duration_penalty_bps=duration,
        credit_penalty_bps=credit,
        call_penalty_bps=call,
        structure_penalty_bps=structure,
        total_penalty_bps=total_penalty,
        risk_adjusted_yield_percent=adjusted_yield,
        risk_level=classify_risk_level(total_penalty),
    )
