"""
Input validation for Anchor.

This module validates structured inputs before they enter
Anchor's deterministic fixed-income decision engine.

Validation belongs at the system boundary. Analytical
modules should be able to assume that their inputs are
well-formed.
"""

from typing import Iterable, List, Tuple

from engine.models import FixedIncomeOpportunity
from engine.regime import RegimeAssessment


VALID_SECURITY_TYPES = {
    "TREASURY",
    "TIPS",
    "CORPORATE",
}

VALID_SPREAD_COMPENSATION = {
    "LOW",
    "MODERATE",
    "MEANINGFUL",
    "HIGH",
}

VALID_POLICY = {
    "ACCOMMODATIVE",
    "NEUTRAL",
    "RESTRICTIVE",
}

VALID_GROWTH = {
    "ACCELERATING",
    "NEUTRAL",
    "WEAKENING",
}

VALID_INFLATION = {
    "FALLING",
    "STABLE",
    "PRESSURE",
}

VALID_REAL_RATES = {
    "FALLING",
    "STABLE",
    "PRESSURE",
}

VALID_TERM_PREMIUM = {
    "FALLING",
    "NEUTRAL",
    "RISING",
}

VALID_CREDIT = {
    "BENIGN",
    "NEUTRAL",
    "STRESSED",
}

VALID_CONFIDENCE = {
    "LOW",
    "MEDIUM",
    "HIGH",
}


def validate_opportunity(
    opportunity: FixedIncomeOpportunity,
) -> None:
    """
    Validate one fixed-income opportunity.

    Raises:
        ValueError when a field is invalid.
    """

    if opportunity.security_type not in VALID_SECURITY_TYPES:
        raise ValueError(
            f"Unsupported security_type: "
            f"{opportunity.security_type}"
        )

    if opportunity.maturity_years <= 0:
        raise ValueError(
            "maturity_years must be greater than 0."
        )

    if opportunity.yield_percent < 0:
        raise ValueError(
            "yield_percent cannot be negative."
        )

    if (
        opportunity.security_type == "CORPORATE"
        and not opportunity.rating
    ):
        raise ValueError(
            "Corporate opportunities require a rating."
        )

    if not isinstance(
        opportunity.callable,
        bool,
    ):
        raise ValueError(
            "callable must be a boolean."
        )


def validate_regime(
    regime: RegimeAssessment,
) -> None:
    """
    Validate a completed regime assessment.
    """

    if regime.policy not in VALID_POLICY:
        raise ValueError(
            f"Unsupported policy value: {regime.policy}"
        )

    if regime.growth not in VALID_GROWTH:
        raise ValueError(
            f"Unsupported growth value: {regime.growth}"
        )

    if regime.inflation not in VALID_INFLATION:
        raise ValueError(
            f"Unsupported inflation value: "
            f"{regime.inflation}"
        )

    if regime.real_rates not in VALID_REAL_RATES:
        raise ValueError(
            f"Unsupported real_rates value: "
            f"{regime.real_rates}"
        )

    if regime.term_premium not in VALID_TERM_PREMIUM:
        raise ValueError(
            f"Unsupported term_premium value: "
            f"{regime.term_premium}"
        )

    if regime.credit not in VALID_CREDIT:
        raise ValueError(
            f"Unsupported credit value: {regime.credit}"
        )

    if regime.confidence not in VALID_CONFIDENCE:
        raise ValueError(
            f"Unsupported confidence value: "
            f"{regime.confidence}"
        )


def validate_anchor_inputs(
    opportunities: Iterable[
        Tuple[FixedIncomeOpportunity, str]
    ],
    regime: RegimeAssessment,
) -> List[
    Tuple[FixedIncomeOpportunity, str]
]:
    """
    Validate Anchor's complete structured input set.

    The opportunities iterable is materialized into a list
    so generators can be validated once and then safely
    passed downstream.

    Returns:
        Validated opportunity tuples as a list.
    """

    validated = list(opportunities)

    if not validated:
        raise ValueError(
            "Anchor requires at least one opportunity."
        )

    validate_regime(regime)

    for opportunity, spread_compensation in validated:
        validate_opportunity(opportunity)

        if (
            spread_compensation
            not in VALID_SPREAD_COMPENSATION
        ):
            raise ValueError(
                "Unsupported spread_compensation: "
                f"{spread_compensation}"
            )

    return validated
