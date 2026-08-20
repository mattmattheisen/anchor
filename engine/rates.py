"""
Interest-rate decomposition analytics for Anchor.

This module separates nominal Treasury yields into
real-yield and breakeven-inflation components.
"""

from dataclasses import dataclass

from engine.models import TreasuryPoint, TipsPoint


@dataclass
class RateDecomposition:
    maturity_years: float
    nominal_yield_percent: float
    real_yield_percent: float
    breakeven_inflation_percent: float


def breakeven_inflation(
    nominal_yield_percent: float,
    real_yield_percent: float,
) -> float:
    """
    Estimate breakeven inflation.

    Breakeven inflation is approximated as:

        nominal Treasury yield - TIPS real yield
    """
    return round(
        nominal_yield_percent - real_yield_percent,
        3,
    )


def decompose_rate(
    nominal_point: TreasuryPoint,
    tips_point: TipsPoint,
) -> RateDecomposition:
    """
    Decompose a nominal Treasury yield into its
    real-yield and breakeven-inflation components.

    Both securities must represent the same maturity.
    """
    if nominal_point.maturity_years != tips_point.maturity_years:
        raise ValueError(
            "Nominal Treasury and TIPS maturities must match."
        )

    breakeven = breakeven_inflation(
        nominal_point.yield_percent,
        tips_point.real_yield_percent,
    )

    return RateDecomposition(
        maturity_years=nominal_point.maturity_years,
        nominal_yield_percent=nominal_point.yield_percent,
        real_yield_percent=tips_point.real_yield_percent,
        breakeven_inflation_percent=breakeven,
    )


def rate_change_bps(
    previous_percent: float,
    current_percent: float,
) -> float:
    """
    Calculate a yield change in basis points.
    """
    return round(
        (current_percent - previous_percent) * 100,
        2,
    )


def classify_rate_driver(
    nominal_change_bps: float,
    real_change_bps: float,
    breakeven_change_bps: float,
) -> str:
    """
    Classify the dominant driver of a nominal yield move.

    This is Anchor's first-pass deterministic classification.
    More sophisticated confidence and mixed-regime logic
    will be added later.
    """
    real_magnitude = abs(real_change_bps)
    inflation_magnitude = abs(breakeven_change_bps)

    if real_magnitude == 0 and inflation_magnitude == 0:
        return "UNCHANGED"

    if real_magnitude >= inflation_magnitude * 2:
        return "REAL_RATE"

    if inflation_magnitude >= real_magnitude * 2:
        return "INFLATION"

    return "MIXED"
