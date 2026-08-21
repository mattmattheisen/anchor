"""
Canonical broker-field schema for Anchor.

Broker and custodian exports frequently use different
column names for the same fixed-income concepts.

This module defines the canonical field names Anchor
recognizes and the common aliases that may appear in
real-world broker exports.

The schema does not parse files or make investment
decisions.

Its responsibility is:

    broker-specific column name
            ↓
    normalized Anchor field name
            ↓
    SecurityData importer
"""

from typing import Dict, Optional


BROKER_FIELD_ALIASES = {
    "cusip": {
        "cusip",
        "cusip number",
        "cusip_number",
        "security id",
        "security_id",
    },

    "issuer": {
        "issuer",
        "issuer name",
        "issuer_name",
        "company",
        "company name",
        "description",
    },

    "security_type": {
        "security type",
        "security_type",
        "product type",
        "product_type",
        "asset type",
        "asset_type",
    },

    "coupon_percent": {
        "coupon",
        "coupon rate",
        "coupon_rate",
        "coupon percent",
        "coupon_percent",
    },

    "maturity_date": {
        "maturity",
        "maturity date",
        "maturity_date",
        "maturity dt",
        "maturity_dt",
    },

    "yield_percent": {
        "yield",
        "yield percent",
        "yield_percent",
        "yield to maturity",
        "yield_to_maturity",
        "ytm",
        "yield to worst",
        "yield_to_worst",
        "ytw",
    },

    "price": {
        "price",
        "market price",
        "market_price",
        "ask price",
        "ask_price",
    },

    "rating": {
        "rating",
        "credit rating",
        "credit_rating",
        "composite rating",
        "composite_rating",
    },

    "callable": {
        "callable",
        "callable flag",
        "callable_flag",
        "call feature",
        "call_feature",
    },

    "call_date": {
        "call date",
        "call_date",
        "next call date",
        "next_call_date",
        "first call date",
        "first_call_date",
    },

    "minimum_quantity": {
        "minimum quantity",
        "minimum_quantity",
        "minimum qty",
        "minimum_qty",
        "minimum purchase",
        "minimum_purchase",
        "min qty",
        "min_qty",
    },

    "source": {
        "source",
        "data source",
        "data_source",
        "broker",
        "custodian",
    },

    "description": {
        "description",
        "security description",
        "security_description",
        "name",
    },
}


def normalize_column_name(
    column_name: str,
) -> str:
    """
    Normalize a broker-export column name before alias
    matching.

    Normalization:

        strip leading/trailing whitespace
        lowercase
        replace hyphens with spaces
        collapse repeated whitespace
    """

    if not isinstance(
        column_name,
        str,
    ):
        raise TypeError(
            "column_name must be a string."
        )

    normalized = (
        column_name
        .strip()
        .lower()
        .replace("-", " ")
    )

    normalized = " ".join(
        normalized.split()
    )

    return normalized


def canonical_field_for_column(
    column_name: str,
) -> Optional[str]:
    """
    Return Anchor's canonical field name for a broker
    column.

    Returns None when the column is not recognized.
    """

    normalized = normalize_column_name(
        column_name
    )

    for canonical_field, aliases in (
        BROKER_FIELD_ALIASES.items()
    ):
        normalized_aliases = {
            normalize_column_name(alias)
            for alias in aliases
        }

        if normalized in normalized_aliases:
            return canonical_field

    return None


def build_column_mapping(
    columns,
) -> Dict[str, str]:
    """
    Build a mapping from original broker column names to
    Anchor canonical field names.

    Unrecognized columns are ignored.

    Raises:
        ValueError if two source columns map to the same
        canonical Anchor field.
    """

    mapping = {}
    used_canonical_fields = set()

    for column in columns:
        canonical = (
            canonical_field_for_column(
                column
            )
        )

        if canonical is None:
            continue

        if canonical in used_canonical_fields:
            raise ValueError(
                "Multiple broker columns map to "
                f"Anchor field: {canonical}"
            )

        mapping[column] = canonical

        used_canonical_fields.add(
            canonical
        )

    return mapping
