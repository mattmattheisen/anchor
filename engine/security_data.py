"""
Production fixed-income security data for Anchor.

This module defines the richer market-data structure used
to represent real investable fixed-income securities.

It is intentionally separate from FixedIncomeOpportunity.

SecurityData describes the security as it exists in the
market.

FixedIncomeOpportunity describes the smaller set of fields
Anchor currently needs for deterministic analysis.

Flow:

    broker / custodian / market-data source
                    ↓
               SecurityData
                    ↓
          security-data validation
                    ↓
      opportunity adapter / normalization
                    ↓
         FixedIncomeOpportunity
                    ↓
                 Anchor
"""

import math
from dataclasses import dataclass
from datetime import date
from typing import Optional


VALID_SECURITY_DATA_TYPES = {
    "TREASURY",
    "TIPS",
    "CORPORATE",
    "CD",
}


@dataclass(frozen=True)
class SecurityData:
    """
    Rich fixed-income security record.

    Fields
    ------
    cusip:
        CUSIP identifier when available.

    issuer:
        Security issuer or obligor.

    security_type:
        Current supported values:

            TREASURY
            TIPS
            CORPORATE
            CD

    coupon_percent:
        Annual stated coupon rate.

    maturity_date:
        Contractual maturity date.

    yield_to_maturity_percent:
        Current yield to maturity.

    price:
        Current clean or quoted price, normally expressed
        per 100 of par value.

    rating:
        Credit rating when applicable.

    callable:
        Whether the security may be called before maturity.

    call_date:
        Earliest or relevant call date when available.

    minimum_quantity:
        Minimum purchase quantity or par amount when known.

    source:
        Origin of the security data, such as SCHWAB,
        TREASURYDIRECT, CSV, or another provider.

    description:
        Optional human-readable security description.
    """

    security_type: str
    maturity_date: date
    yield_to_maturity_percent: float

    cusip: Optional[str] = None
    issuer: Optional[str] = None
    coupon_percent: Optional[float] = None
    price: Optional[float] = None
    rating: Optional[str] = None

    callable: bool = False
    call_date: Optional[date] = None

    minimum_quantity: Optional[float] = None

    source: Optional[str] = None
    description: Optional[str] = None


def _validate_finite_number(
    value,
    field_name: str,
) -> None:
    """
    Require a numeric value to be finite.
    """

    if isinstance(
        value,
        bool,
    ):
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


def _normalize_optional_text(
    value: Optional[str],
) -> Optional[str]:
    """
    Normalize optional text fields for validation.
    """

    if value is None:
        return None

    if not isinstance(
        value,
        str,
    ):
        raise TypeError(
            "Text fields must be strings."
        )

    normalized = value.strip()

    if normalized == "":
        return None

    return normalized


def validate_security_data(
    security: SecurityData,
) -> None:
    """
    Validate one production fixed-income security record.

    This function checks structural and market-data
    integrity only.

    It does not decide whether the security is attractive.
    """

    if not isinstance(
        security,
        SecurityData,
    ):
        raise TypeError(
            "security must be a SecurityData instance."
        )

    if (
        security.security_type
        not in VALID_SECURITY_DATA_TYPES
    ):
        raise ValueError(
            "Unsupported security_type: "
            f"{security.security_type}"
        )

    if not isinstance(
        security.maturity_date,
        date,
    ):
        raise TypeError(
            "maturity_date must be a date."
        )

    _validate_finite_number(
        security.yield_to_maturity_percent,
        "yield_to_maturity_percent",
    )

    if (
        security.yield_to_maturity_percent
        < 0
    ):
        raise ValueError(
            "yield_to_maturity_percent "
            "cannot be negative."
        )

    if security.coupon_percent is not None:
        _validate_finite_number(
            security.coupon_percent,
            "coupon_percent",
        )

        if security.coupon_percent < 0:
            raise ValueError(
                "coupon_percent cannot be negative."
            )

    if security.price is not None:
        _validate_finite_number(
            security.price,
            "price",
        )

        if security.price <= 0:
            raise ValueError(
                "price must be greater than 0."
            )

    if security.minimum_quantity is not None:
        _validate_finite_number(
            security.minimum_quantity,
            "minimum_quantity",
        )

        if security.minimum_quantity <= 0:
            raise ValueError(
                "minimum_quantity must be "
                "greater than 0."
            )

    if not isinstance(
        security.callable,
        bool,
    ):
        raise TypeError(
            "callable must be a boolean."
        )

    if (
        security.call_date is not None
        and not isinstance(
            security.call_date,
            date,
        )
    ):
        raise TypeError(
            "call_date must be a date."
        )

    if (
        security.call_date is not None
        and security.call_date
        > security.maturity_date
    ):
        raise ValueError(
            "call_date cannot be after "
            "maturity_date."
        )

    if (
        not security.callable
        and security.call_date is not None
    ):
        raise ValueError(
            "Non-callable securities cannot "
            "have a call_date."
        )

    rating = _normalize_optional_text(
        security.rating
    )

    if (
        security.security_type == "CORPORATE"
        and rating is None
    ):
        raise ValueError(
            "Corporate securities require "
            "a rating."
        )

    _normalize_optional_text(
        security.cusip
    )

    _normalize_optional_text(
        security.issuer
    )

    _normalize_optional_text(
        security.source
    )

    _normalize_optional_text(
        security.description
    )


def security_data_to_dict(
    security: SecurityData,
) -> dict:
    """
    Convert SecurityData into a plain dictionary.

    Useful for audit logs, debugging, exports, and future
    adapters.
    """

    validate_security_data(
        security
    )

    return {
        "cusip": security.cusip,
        "issuer": security.issuer,
        "security_type": (
            security.security_type
        ),
        "coupon_percent": (
            security.coupon_percent
        ),
        "maturity_date": (
            security.maturity_date.isoformat()
        ),
        "yield_to_maturity_percent": (
            security.yield_to_maturity_percent
        ),
        "price": security.price,
        "rating": security.rating,
        "callable": security.callable,
        "call_date": (
            security.call_date.isoformat()
            if security.call_date is not None
            else None
        ),
        "minimum_quantity": (
            security.minimum_quantity
        ),
        "source": security.source,
        "description": (
            security.description
        ),
    }
