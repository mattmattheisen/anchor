"""
Production security CSV importer for Anchor.

This module reads richer fixed-income market records from CSV
and converts them into:

    (
        SecurityData,
        spread_compensation,
    )

tuples.

It does not perform investment analysis.

Flow:

    production CSV
        ↓
    parsing
        ↓
    SecurityData
        ↓
    validation
        ↓
    security adapter
        ↓
    FixedIncomeOpportunity
        ↓
    Anchor
"""

import csv
from datetime import date
from pathlib import Path
from typing import List, Optional, Tuple

from engine.security_data import (
    SecurityData,
    validate_security_data,
)


SecurityImportTuple = Tuple[
    SecurityData,
    str,
]


REQUIRED_COLUMNS = {
    "security_type",
    "maturity_date",
    "yield_to_maturity_percent",
    "spread_compensation",
}


def _parse_optional_text(
    value: Optional[str],
) -> Optional[str]:
    """
    Normalize optional text fields.
    """

    if value is None:
        return None

    normalized = value.strip()

    if normalized == "":
        return None

    return normalized


def _parse_optional_upper_text(
    value: Optional[str],
) -> Optional[str]:
    """
    Normalize optional text and uppercase it.
    """

    normalized = _parse_optional_text(
        value
    )

    if normalized is None:
        return None

    return normalized.upper()


def _parse_required_float(
    value: Optional[str],
    field_name: str,
    row_number: int,
) -> float:
    """
    Parse a required numeric field.
    """

    if value is None or value.strip() == "":
        raise ValueError(
            f"Row {row_number}: "
            f"{field_name} is required."
        )

    try:
        return float(
            value.strip()
        )

    except ValueError as exc:
        raise ValueError(
            f"Row {row_number}: "
            f"{field_name} must be numeric."
        ) from exc


def _parse_optional_float(
    value: Optional[str],
    field_name: str,
    row_number: int,
) -> Optional[float]:
    """
    Parse an optional numeric field.
    """

    if value is None or value.strip() == "":
        return None

    try:
        return float(
            value.strip()
        )

    except ValueError as exc:
        raise ValueError(
            f"Row {row_number}: "
            f"{field_name} must be numeric."
        ) from exc


def _parse_required_date(
    value: Optional[str],
    field_name: str,
    row_number: int,
) -> date:
    """
    Parse a required ISO date.

    Expected format:

        YYYY-MM-DD
    """

    if value is None or value.strip() == "":
        raise ValueError(
            f"Row {row_number}: "
            f"{field_name} is required."
        )

    try:
        return date.fromisoformat(
            value.strip()
        )

    except ValueError as exc:
        raise ValueError(
            f"Row {row_number}: "
            f"{field_name} must use YYYY-MM-DD."
        ) from exc


def _parse_optional_date(
    value: Optional[str],
    field_name: str,
    row_number: int,
) -> Optional[date]:
    """
    Parse an optional ISO date.
    """

    if value is None or value.strip() == "":
        return None

    try:
        return date.fromisoformat(
            value.strip()
        )

    except ValueError as exc:
        raise ValueError(
            f"Row {row_number}: "
            f"{field_name} must use YYYY-MM-DD."
        ) from exc


def _parse_callable(
    value: Optional[str],
    row_number: int,
) -> bool:
    """
    Parse callable values.

    Accepted true values:

        TRUE
        YES
        Y
        1

    Accepted false values:

        FALSE
        NO
        N
        0
        blank
    """

    if value is None:
        return False

    normalized = (
        value.strip()
        .upper()
    )

    if normalized == "":
        return False

    if normalized in {
        "TRUE",
        "YES",
        "Y",
        "1",
    }:
        return True

    if normalized in {
        "FALSE",
        "NO",
        "N",
        "0",
    }:
        return False

    raise ValueError(
        f"Row {row_number}: "
        "callable must be TRUE or FALSE."
    )


def _validate_columns(
    fieldnames,
) -> None:
    """
    Verify required production columns exist.
    """

    if not fieldnames:
        raise ValueError(
            "CSV file does not contain a header row."
        )

    normalized = {
        field.strip()
        for field in fieldnames
        if field is not None
    }

    missing = (
        REQUIRED_COLUMNS
        - normalized
    )

    if missing:
        missing_list = ", ".join(
            sorted(missing)
        )

        raise ValueError(
            "CSV file is missing required columns: "
            f"{missing_list}"
        )


def _build_security(
    row: dict,
    row_number: int,
) -> SecurityImportTuple:
    """
    Convert one CSV row into SecurityData plus its
    spread-compensation label.
    """

    security_type = (
        row["security_type"]
        .strip()
        .upper()
    )

    if not security_type:
        raise ValueError(
            f"Row {row_number}: "
            "security_type is required."
        )

    maturity_date = (
        _parse_required_date(
            row.get("maturity_date"),
            "maturity_date",
            row_number,
        )
    )

    yield_to_maturity_percent = (
        _parse_required_float(
            row.get(
                "yield_to_maturity_percent"
            ),
            "yield_to_maturity_percent",
            row_number,
        )
    )

    spread_compensation = (
        row["spread_compensation"]
        .strip()
        .upper()
    )

    if not spread_compensation:
        raise ValueError(
            f"Row {row_number}: "
            "spread_compensation is required."
        )

    callable_value = _parse_callable(
        row.get("callable"),
        row_number,
    )

    security = SecurityData(
        cusip=_parse_optional_text(
            row.get("cusip")
        ),
        issuer=_parse_optional_text(
            row.get("issuer")
        ),
        security_type=security_type,
        coupon_percent=(
            _parse_optional_float(
                row.get("coupon_percent"),
                "coupon_percent",
                row_number,
            )
        ),
        maturity_date=maturity_date,
        yield_to_maturity_percent=(
            yield_to_maturity_percent
        ),
        price=_parse_optional_float(
            row.get("price"),
            "price",
            row_number,
        ),
        rating=_parse_optional_upper_text(
            row.get("rating")
        ),
        callable=callable_value,
        call_date=_parse_optional_date(
            row.get("call_date"),
            "call_date",
            row_number,
        ),
        minimum_quantity=(
            _parse_optional_float(
                row.get("minimum_quantity"),
                "minimum_quantity",
                row_number,
            )
        ),
        source=_parse_optional_upper_text(
            row.get("source")
        ),
        description=_parse_optional_text(
            row.get("description")
        ),
    )

    validate_security_data(
        security
    )

    return (
        security,
        spread_compensation,
    )


def load_security_data_from_csv(
    file_path: str,
) -> List[SecurityImportTuple]:
    """
    Load production fixed-income security records from CSV.

    Required columns
    ----------------
    security_type
    maturity_date
    yield_to_maturity_percent
    spread_compensation

    Optional columns
    ----------------
    cusip
    issuer
    coupon_percent
    price
    rating
    callable
    call_date
    minimum_quantity
    source
    description
    """

    path = Path(
        file_path
    )

    if not path.exists():
        raise FileNotFoundError(
            f"CSV file not found: {file_path}"
        )

    if not path.is_file():
        raise ValueError(
            f"CSV path is not a file: {file_path}"
        )

    results: List[
        SecurityImportTuple
    ] = []

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        reader = csv.DictReader(
            csv_file
        )

        _validate_columns(
            reader.fieldnames
        )

        for row_number, row in enumerate(
            reader,
            start=2,
        ):
            if not any(
                value
                and value.strip()
                for value in row.values()
                if isinstance(
                    value,
                    str,
                )
            ):
                continue

            results.append(
                _build_security(
                    row=row,
                    row_number=row_number,
                )
            )

    if not results:
        raise ValueError(
            "CSV file contains no securities."
        )

    return results
