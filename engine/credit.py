"""
Credit-spread and relative-value analytics for Anchor.

This module compares non-Treasury fixed-income yields
with maturity-matched Treasury yields to estimate
incremental compensation for credit and structure risk.
"""

from typing import Iterable

from engine.models import FixedIncomeOpportunity, TreasuryPoint
from engine.curve import interpolated_yield


def treasury_yield_for_maturity(
    treasury_curve: Iterable[TreasuryPoint],
    maturity_years: float,
) -> float:
    """
    Return the Treasury yield for a requested maturity.

    Exact curve points are returned directly. Maturities
    between observed Treasury points are estimated using
    linear interpolation.

    Raises:
        ValueError if the maturity falls outside the
        available Treasury curve.
    """
    return interpolated_yield(
        treasury_curve,
        maturity_years,
    )


def spread_to_treasury_bps(
    opportunity: FixedIncomeOpportunity,
    treasury_curve: Iterable[TreasuryPoint],
) -> float:
    """
    Calculate the opportunity's yield spread to a
    maturity-matched Treasury in basis points.
    """
    treasury_yield = treasury_yield_for_maturity(
        treasury_curve,
        opportunity.maturity_years,
    )

    return round(
        (opportunity.yield_percent - treasury_yield) * 100,
        2,
    )


def classify_spread_compensation(
    spread_bps: float,
) -> str:
    """
    Provide a first-pass qualitative classification
    of incremental spread compensation.

    These thresholds are placeholders for Anchor's
    deterministic prototype. Historical percentile
    analysis will replace simple static thresholds later.
    """
    if spread_bps < 0:
        return "UNFAVORABLE"

    if spread_bps < 25:
        return "THIN"

    if spread_bps < 75:
        return "MODERATE"

    if spread_bps < 150:
        return "MEANINGFUL"

    return "HIGH"


def compare_opportunity_to_treasury(
    opportunity: FixedIncomeOpportunity,
    treasury_curve: Iterable[TreasuryPoint],
) -> dict:
    """
    Return Anchor's basic relative-value comparison
    for a fixed-income opportunity.
    """
    treasury_yield = treasury_yield_for_maturity(
        treasury_curve,
        opportunity.maturity_years,
    )

    spread = spread_to_treasury_bps(
        opportunity,
        treasury_curve,
    )

    return {
        "security_type": opportunity.security_type,
        "maturity_years": opportunity.maturity_years,
        "yield_percent": opportunity.yield_percent,
        "rating": opportunity.rating,
        "treasury_yield_percent": treasury_yield,
        "spread_to_treasury_bps": spread,
        "spread_compensation": classify_spread_compensation(spread),
    }
