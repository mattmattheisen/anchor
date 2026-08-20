"""
Deterministic fixed-income allocation guidance for Anchor.

This module translates Anchor's regime assessment into broad
portfolio positioning guidance.

It does not select individual securities or determine client-
specific allocations. Individual securities remain the
responsibility of the opportunity, risk, ranking, and pipeline
engines.
"""

from dataclasses import dataclass
from typing import List

from engine.regime import RegimeAssessment


@dataclass
class AllocationGuidance:
    duration_posture: str
    credit_posture: str
    inflation_posture: str
    liquidity_posture: str
    preferred_exposures: List[str]
    exposures_to_limit: List[str]
    rationale: List[str]


def build_allocation_guidance(
    regime: RegimeAssessment,
) -> AllocationGuidance:
    """
    Convert an Anchor regime assessment into deterministic
    fixed-income allocation guidance.
    """

    duration_posture = "NEUTRAL"
    credit_posture = "NEUTRAL"
    inflation_posture = "NEUTRAL"
    liquidity_posture = "NORMAL"

    preferred_exposures = []
    exposures_to_limit = []
    rationale = []

    # ---------------------------------------------------------
    # Duration
    # ---------------------------------------------------------

    if (
        regime.real_rates == "PRESSURE"
        or regime.term_premium == "RISING"
    ):
        duration_posture = "SHORT"
        preferred_exposures.append(
            "SHORT_INTERMEDIATE_TREASURIES"
        )
        exposures_to_limit.append(
            "LONG_DURATION_NOMINAL_BONDS"
        )
        rationale.append(
            "Real-rate or term-premium pressure argues "
            "against extending duration."
        )

    elif (
        regime.growth == "WEAKENING"
        and regime.inflation != "PRESSURE"
    ):
        duration_posture = "EXTEND"
        preferred_exposures.append(
            "INTERMEDIATE_LONG_TREASURIES"
        )
        rationale.append(
            "Weakening growth without inflation pressure "
            "supports selective duration extension."
        )

    else:
        preferred_exposures.append(
            "INTERMEDIATE_TREASURIES"
        )
        rationale.append(
            "Rate conditions support a neutral duration "
            "posture."
        )

    # ---------------------------------------------------------
    # Credit
    # ---------------------------------------------------------

    if regime.credit == "STRESSED":
        credit_posture = "DEFENSIVE"
        preferred_exposures.append(
            "HIGH_QUALITY_GOVERNMENT"
        )
        exposures_to_limit.append(
            "LOWER_QUALITY_CREDIT"
        )
        rationale.append(
            "Credit stress favors higher-quality fixed "
            "income."
        )

    elif regime.credit == "BENIGN":
        credit_posture = "SELECTIVE"
        preferred_exposures.append(
            "INVESTMENT_GRADE_CREDIT"
        )
        rationale.append(
            "Benign credit conditions permit selective "
            "investment-grade exposure."
        )

    # ---------------------------------------------------------
    # Inflation
    # ---------------------------------------------------------

    if regime.inflation == "PRESSURE":
        inflation_posture = "HEDGE"
        preferred_exposures.append(
            "TIPS"
        )
        exposures_to_limit.append(
            "LONG_NOMINAL_DURATION"
        )
        rationale.append(
            "Inflation pressure increases the value of "
            "inflation-protected exposure."
        )

    elif regime.inflation == "FALLING":
        inflation_posture = "NOMINAL"
        preferred_exposures.append(
            "NOMINAL_TREASURIES"
        )
        rationale.append(
            "Falling inflation improves the relative "
            "case for nominal bonds."
        )

    # ---------------------------------------------------------
    # Liquidity
    # ---------------------------------------------------------

    if (
        regime.credit == "STRESSED"
        or regime.growth == "WEAKENING"
    ):
        liquidity_posture = "ELEVATED"
        preferred_exposures.append(
            "TREASURY_BILLS_AND_CASH"
        )
        rationale.append(
            "Economic or credit weakness supports "
            "maintaining additional liquidity."
        )

    # Remove duplicates while preserving order.
    preferred_exposures = list(
        dict.fromkeys(preferred_exposures)
    )

    exposures_to_limit = list(
        dict.fromkeys(exposures_to_limit)
    )

    return AllocationGuidance(
        duration_posture=duration_posture,
        credit_posture=credit_posture,
        inflation_posture=inflation_posture,
        liquidity_posture=liquidity_posture,
        preferred_exposures=preferred_exposures,
        exposures_to_limit=exposures_to_limit,
        rationale=rationale,
    )
