"""
Adapter from production SecurityData records into Anchor's
existing FixedIncomeOpportunity model.

This module is intentionally narrow.

It does not fetch market data.
It does not rank securities.
It does not classify the regime.

Its responsibility is:

    SecurityData
        ↓
    deterministic normalization
        ↓
    FixedIncomeOpportunity
        ↓
    Anchor
"""

from datetime import date
from typing import Tuple

from engine.models import FixedIncomeOpportunity
from engine.security_data import (
    SecurityData,
    validate_security_data,
)


OpportunityTuple = Tuple[
    FixedIncomeOpportunity,
    str,
]


def calculate_maturity_years(
    maturity_date: date,
    as_of_date: date,
) -> float:
    """
    Convert a maturity date into decimal years from an
    explicit as-of date.

    A 365.25-day year is used to account for leap years.

    Raises:
        TypeError for non-date inputs.
        ValueError when maturity is not after as_of_date.
    """

    if not isinstance(
        maturity_date,
        date,
    ):
        raise TypeError(
            "maturity_date must be a date."
        )

    if not isinstance(
        as_of_date,
        date,
    ):
        raise TypeError(
            "as_of_date must be a date."
        )

    days_to_maturity = (
        maturity_date
        - as_of_date
    ).days

    if days_to_maturity <= 0:
        raise ValueError(
            "maturity_date must be after as_of_date."
        )

    return (
        days_to_maturity
        / 365.25
    )


def security_data_to_opportunity(
    security: SecurityData,
    spread_compensation: str,
    as_of_date: date,
) -> OpportunityTuple:
    """
    Convert one validated SecurityData record into the
    FixedIncomeOpportunity tuple expected by Anchor.

    SecurityData fields retained by the current Anchor
    decision model:

        security_type
        maturity
        yield to maturity
        rating
        callable

    Richer production fields such as CUSIP, issuer, coupon,
    price, call date, source, and minimum quantity remain
    available on SecurityData for auditability and future
    engine expansion.
    """

    validate_security_data(
        security
    )

    if not isinstance(
        spread_compensation,
        str,
    ):
        raise TypeError(
            "spread_compensation must be a string."
        )

    normalized_spread = (
        spread_compensation
        .strip()
        .upper()
    )

    if not normalized_spread:
        raise ValueError(
            "spread_compensation cannot be blank."
        )

    maturity_years = (
        calculate_maturity_years(
            maturity_date=security.maturity_date,
            as_of_date=as_of_date,
        )
    )

    anchor_security_type = (
        security.security_type
    )

    if anchor_security_type == "CD":
        anchor_security_type = "CORPORATE"

    opportunity = FixedIncomeOpportunity(
        security_type=anchor_security_type,
        maturity_years=maturity_years,
        yield_percent=(
            security.yield_to_maturity_percent
        ),
        rating=security.rating,
        callable=security.callable,
    )

    return (
        opportunity,
        normalized_spread,
    )
