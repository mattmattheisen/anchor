"""
Structured market-data inputs for Anchor.

This module defines the raw economic and fixed-income
observations used to construct Anchor's deterministic
RegimeAssessment.

It does not fetch external data and it does not classify
the regime.

Those responsibilities remain separate:

    external source
        ↓
    market-data collector
        ↓
    MarketDataSnapshot
        ↓
    deterministic regime builder
        ↓
    RegimeAssessment
"""

import math
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class MarketDataSnapshot:
    """
    Raw market observations used by Anchor's regime builder.

    All yield and spread values are expressed in percentage
    points unless otherwise noted.

    Treasury curve fields currently supported:

        treasury_1y
        treasury_2y
        treasury_3y
        treasury_5y
        treasury_7y
        treasury_10y

    Examples:

        treasury_2y = 4.25
        treasury_10y = 4.45
        real_yield_10y = 2.05
        breakeven_10y = 2.40
        credit_spread_ig_bps = 92.0

    Change fields represent movement over the selected
    comparison window.

    Examples:

        real_yield_10y_change_bps = 18.0
        breakeven_10y_change_bps = -6.0
        credit_spread_ig_change_bps = 12.0
    """

    fed_funds_rate: float

    treasury_2y: float
    treasury_10y: float

    real_yield_10y: float
    breakeven_10y: float

    credit_spread_ig_bps: float

    treasury_1y: Optional[float] = None
    treasury_3y: Optional[float] = None
    treasury_5y: Optional[float] = None
    treasury_7y: Optional[float] = None

    treasury_2y_change_bps: float = 0.0
    treasury_10y_change_bps: float = 0.0

    treasury_1y_change_bps: Optional[float] = None
    treasury_3y_change_bps: Optional[float] = None
    treasury_5y_change_bps: Optional[float] = None
    treasury_7y_change_bps: Optional[float] = None

    real_yield_10y_change_bps: float = 0.0
    breakeven_10y_change_bps: float = 0.0

    credit_spread_ig_change_bps: float = 0.0

    unemployment_rate: Optional[float] = None
    unemployment_rate_change_pct: Optional[float] = None


def _validate_finite(
    value: float,
    field_name: str,
) -> None:
    """
    Require a numeric market observation to be finite.
    """

    if not isinstance(
        value,
        (int, float),
    ):
        raise TypeError(
            f"{field_name} must be numeric."
        )

    if isinstance(
        value,
        bool,
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


def _validate_optional_finite(
    value: Optional[float],
    field_name: str,
) -> None:
    """
    Validate an optional numeric market observation.
    """

    if value is None:
        return

    _validate_finite(
        value,
        field_name,
    )


def _validate_nonnegative_optional(
    value: Optional[float],
    field_name: str,
) -> None:
    """
    Require an optional market observation to be
    nonnegative when supplied.
    """

    if value is None:
        return

    if value < 0:
        raise ValueError(
            f"{field_name} cannot be negative."
        )


def validate_market_data(
    snapshot: MarketDataSnapshot,
) -> None:
    """
    Validate a MarketDataSnapshot before regime analysis.

    This function verifies data integrity only.

    It does not determine whether a value is economically
    high, low, rising, falling, benign, or stressed.
    """

    if not isinstance(
        snapshot,
        MarketDataSnapshot,
    ):
        raise TypeError(
            "snapshot must be a MarketDataSnapshot."
        )

    required_numeric_fields = {
        "fed_funds_rate": snapshot.fed_funds_rate,
        "treasury_2y": snapshot.treasury_2y,
        "treasury_10y": snapshot.treasury_10y,
        "real_yield_10y": snapshot.real_yield_10y,
        "breakeven_10y": snapshot.breakeven_10y,
        "credit_spread_ig_bps": (
            snapshot.credit_spread_ig_bps
        ),
        "treasury_2y_change_bps": (
            snapshot.treasury_2y_change_bps
        ),
        "treasury_10y_change_bps": (
            snapshot.treasury_10y_change_bps
        ),
        "real_yield_10y_change_bps": (
            snapshot.real_yield_10y_change_bps
        ),
        "breakeven_10y_change_bps": (
            snapshot.breakeven_10y_change_bps
        ),
        "credit_spread_ig_change_bps": (
            snapshot.credit_spread_ig_change_bps
        ),
    }

    for field_name, value in (
        required_numeric_fields.items()
    ):
        _validate_finite(
            value,
            field_name,
        )

    optional_numeric_fields = {
        "treasury_1y": snapshot.treasury_1y,
        "treasury_3y": snapshot.treasury_3y,
        "treasury_5y": snapshot.treasury_5y,
        "treasury_7y": snapshot.treasury_7y,
        "treasury_1y_change_bps": (
            snapshot.treasury_1y_change_bps
        ),
        "treasury_3y_change_bps": (
            snapshot.treasury_3y_change_bps
        ),
        "treasury_5y_change_bps": (
            snapshot.treasury_5y_change_bps
        ),
        "treasury_7y_change_bps": (
            snapshot.treasury_7y_change_bps
        ),
        "unemployment_rate": (
            snapshot.unemployment_rate
        ),
        "unemployment_rate_change_pct": (
            snapshot.unemployment_rate_change_pct
        ),
    }

    for field_name, value in (
        optional_numeric_fields.items()
    ):
        _validate_optional_finite(
            value,
            field_name,
        )

    if snapshot.fed_funds_rate < 0:
        raise ValueError(
            "fed_funds_rate cannot be negative."
        )

    if snapshot.treasury_2y < 0:
        raise ValueError(
            "treasury_2y cannot be negative."
        )

    if snapshot.treasury_10y < 0:
        raise ValueError(
            "treasury_10y cannot be negative."
        )

    _validate_nonnegative_optional(
        snapshot.treasury_1y,
        "treasury_1y",
    )

    _validate_nonnegative_optional(
        snapshot.treasury_3y,
        "treasury_3y",
    )

    _validate_nonnegative_optional(
        snapshot.treasury_5y,
        "treasury_5y",
    )

    _validate_nonnegative_optional(
        snapshot.treasury_7y,
        "treasury_7y",
    )

    if snapshot.credit_spread_ig_bps < 0:
        raise ValueError(
            "credit_spread_ig_bps cannot be negative."
        )

    if (
        snapshot.unemployment_rate is not None
        and snapshot.unemployment_rate < 0
    ):
        raise ValueError(
            "unemployment_rate cannot be negative."
        )


def market_data_to_dict(
    snapshot: MarketDataSnapshot,
) -> Dict[str, Optional[float]]:
    """
    Convert MarketDataSnapshot into a plain dictionary.

    This is useful for debugging, logging, and future data
    adapters.
    """

    validate_market_data(
        snapshot
    )

    return {
        "fed_funds_rate": (
            snapshot.fed_funds_rate
        ),
        "treasury_1y": (
            snapshot.treasury_1y
        ),
        "treasury_2y": (
            snapshot.treasury_2y
        ),
        "treasury_3y": (
            snapshot.treasury_3y
        ),
        "treasury_5y": (
            snapshot.treasury_5y
        ),
        "treasury_7y": (
            snapshot.treasury_7y
        ),
        "treasury_10y": (
            snapshot.treasury_10y
        ),
        "real_yield_10y": (
            snapshot.real_yield_10y
        ),
        "breakeven_10y": (
            snapshot.breakeven_10y
        ),
        "credit_spread_ig_bps": (
            snapshot.credit_spread_ig_bps
        ),
        "treasury_1y_change_bps": (
            snapshot.treasury_1y_change_bps
        ),
        "treasury_2y_change_bps": (
            snapshot.treasury_2y_change_bps
        ),
        "treasury_3y_change_bps": (
            snapshot.treasury_3y_change_bps
        ),
        "treasury_5y_change_bps": (
            snapshot.treasury_5y_change_bps
        ),
        "treasury_7y_change_bps": (
            snapshot.treasury_7y_change_bps
        ),
        "treasury_10y_change_bps": (
            snapshot.treasury_10y_change_bps
        ),
        "real_yield_10y_change_bps": (
            snapshot.real_yield_10y_change_bps
        ),
        "breakeven_10y_change_bps": (
            snapshot.breakeven_10y_change_bps
        ),
        "credit_spread_ig_change_bps": (
            snapshot.credit_spread_ig_change_bps
        ),
        "unemployment_rate": (
            snapshot.unemployment_rate
        ),
        "unemployment_rate_change_pct": (
            snapshot.unemployment_rate_change_pct
        ),
    }
