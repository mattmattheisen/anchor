"""
Deterministic spread-compensation calculations for Anchor.

This module derives the amount of yield compensation a
fixed-income security provides relative to a Treasury
benchmark.

It does not rank securities.
It does not determine portfolio posture.
It does not classify the economic regime.

Its responsibility is:

    security yield
        ↓
    Treasury benchmark yield
        ↓
    yield spread
        ↓
    deterministic compensation classification

The resulting classification can be supplied to Anchor's
existing decision engine.
"""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class SpreadAssessment:
    """
    Result of a deterministic spread calculation.
    """

    security_yield_percent: float
    benchmark_yield_percent: float
    spread_bps: float
    compensation: str


def calculate_spread_bps(
    security_yield_percent: float,
    benchmark_yield_percent: float,
) -> float:
    """
    Calculate yield spread in basis points.

    Example:

        security yield = 5.25%
        Treasury yield = 4.25%

        spread = 100 bps
    """

    for value, field_name in (
        (
            security_yield_percent,
            "security_yield_percent",
        ),
        (
            benchmark_yield_percent,
            "benchmark_yield_percent",
        ),
    ):
        if isinstance(value, bool):
            raise TypeError(
                f"{field_name} must be numeric."
            )

        if not isinstance(
            value,
            (int, float),
        ):
            raise TypeError(
                f"{field_name} must be numeric."
            )

        if not math.isfinite(
            float(value)
        ):
            raise ValueError(
                f"{field_name} must be finite."
            )

    return (
        security_yield_percent
        - benchmark_yield_percent
    ) * 100.0


def classify_spread_compensation(
    spread_bps: float,
) -> str:
    """
    Convert a calculated yield spread into Anchor's
    deterministic spread-compensation categories.

    Initial production thresholds:

        < 50 bps      LOW
        50-99 bps     MODERATE
        100-149 bps   MEANINGFUL
        >= 150 bps    HIGH

    These thresholds are explicit rather than inferred so
    they can be tested, audited, and revised deliberately.
    """

    if isinstance(
        spread_bps,
        bool,
    ):
        raise TypeError(
            "spread_bps must be numeric."
        )

    if not isinstance(
        spread_bps,
        (int, float),
    ):
        raise TypeError(
            "spread_bps must be numeric."
        )

    if not math.isfinite(
        float(spread_bps)
    ):
        raise ValueError(
            "spread_bps must be finite."
        )

    if spread_bps < 50:
        return "LOW"

    if spread_bps < 100:
        return "MODERATE"

    if spread_bps < 150:
        return "MEANINGFUL"

    return "HIGH"


def assess_spread_compensation(
    security_yield_percent: float,
    benchmark_yield_percent: float,
) -> SpreadAssessment:
    """
    Calculate and classify spread compensation.
    """

    spread_bps = calculate_spread_bps(
        security_yield_percent=(
            security_yield_percent
        ),
        benchmark_yield_percent=(
            benchmark_yield_percent
        ),
    )

    compensation = (
        classify_spread_compensation(
            spread_bps
        )
    )

    return SpreadAssessment(
        security_yield_percent=(
            security_yield_percent
        ),
        benchmark_yield_percent=(
            benchmark_yield_percent
        ),
        spread_bps=spread_bps,
        compensation=compensation,
    )
