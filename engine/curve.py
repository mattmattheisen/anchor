"""
Treasury curve analytics for Anchor.

This module handles basic yield-curve calculations such as
sorting maturities, computing spreads between curve points,
and identifying simple curve-shape characteristics.
"""

from typing import Iterable, List, Dict

from engine.models import TreasuryPoint


def sort_curve(points: Iterable[TreasuryPoint]) -> List[TreasuryPoint]:
    """
    Return Treasury curve points sorted by maturity.
    """
    return sorted(points, key=lambda point: point.maturity_years)


def curve_to_dict(points: Iterable[TreasuryPoint]) -> Dict[float, float]:
    """
    Convert Treasury curve points into a maturity-to-yield mapping.
    """
    return {
        point.maturity_years: point.yield_percent
        for point in sort_curve(points)
    }


def spread_bps(
    short_point: TreasuryPoint,
    long_point: TreasuryPoint,
) -> float:
    """
    Calculate the yield spread between two Treasury maturities
    in basis points.

    Positive result:
        Long maturity yields more than short maturity.

    Negative result:
        Curve is inverted between the two maturities.
    """
    return round(
        (long_point.yield_percent - short_point.yield_percent) * 100,
        2,
    )


def find_point(
    points: Iterable[TreasuryPoint],
    maturity_years: float,
) -> TreasuryPoint:
    """
    Return the Treasury point matching the requested maturity.

    Raises:
        ValueError if the maturity is not present.
    """
    for point in points:
        if point.maturity_years == maturity_years:
            return point

    raise ValueError(
        f"Treasury maturity {maturity_years} years was not found."
    )


def standard_curve_spreads(
    points: Iterable[TreasuryPoint],
) -> Dict[str, float]:
    """
    Calculate Anchor's standard Treasury curve spreads.

    Required maturities:
        2Y, 5Y, 10Y, 30Y
    """
    points = list(points)

    two_year = find_point(points, 2.0)
    five_year = find_point(points, 5.0)
    ten_year = find_point(points, 10.0)
    thirty_year = find_point(points, 30.0)

    return {
        "2s10s": spread_bps(two_year, ten_year),
        "2s30s": spread_bps(two_year, thirty_year),
        "5s10s": spread_bps(five_year, ten_year),
        "5s30s": spread_bps(five_year, thirty_year),
        "10s30s": spread_bps(ten_year, thirty_year),
    }


def classify_curve_shape(
    points: Iterable[TreasuryPoint],
) -> str:
    """
    Provide a simple qualitative classification of the Treasury curve.

    This is intentionally basic. More advanced regime interpretation
    will live in a separate module.
    """
    spreads = standard_curve_spreads(points)

    two_ten = spreads["2s10s"]
    two_thirty = spreads["2s30s"]

    if two_ten < 0 and two_thirty < 0:
        return "INVERTED"

    if two_ten > 50 and two_thirty > 50:
        return "STEEP"

    if abs(two_ten) <= 25 and abs(two_thirty) <= 25:
        return "FLAT"

    return "NORMAL"
