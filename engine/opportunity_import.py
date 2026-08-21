"""
CSV opportunity import utilities for Anchor.

This module converts structured CSV rows into the
FixedIncomeOpportunity tuples expected by Anchor's public
service interface.

The importer does not perform investment analysis.

Its responsibilities are limited to:

- reading CSV data,
- parsing field values,
- converting rows into Anchor objects,
- surfacing clear input errors.

Anchor's existing validation layer remains authoritative
for determining whether the resulting opportunities are
acceptable to the decision engine.
"""

import csv
from pathlib import Path
from typing import List, Optional, Tuple

from engine.models import FixedIncomeOpportunity


OpportunityTuple = Tuple[
    FixedIncomeOpportunity,
    str,
]


REQUIRED_COLUMNS = {
    "security_type",
    "maturity_years",
    "yield_percent",
    "spread_compensation",
}

OPTIONAL_COLUMNS = {
    "rating",
    "callable",
}


def _parse_float(
    value: str,
    field_name: str,
    row_number: int,
) -> float:
    """
    Parse a required numeric CSV value.

    Raises:
        ValueError if the value cannot be converted to a
        floating-point number.
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


def _parse_optional_string(
    value: Optional[str],
) -> Optional[str]:
    """
    Normalize an optional text field.

    Empty values become None.
    """

    if value is None:
        return None

    normalized = value.strip()

    if normalized == "":
        return None

    return normalized.upper()


def _parse_callable(
    value: Optional[str],
    row_number: int,
) -> bool:
    """
    Parse a CSV callable field into a boolean.

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

    Raises:
        ValueError for any unsupported value.
    """

    if value is None:
        return False

    normalized = value.strip().upper()

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
        f"callable must be TRUE or FALSE."
    )


def _validate_columns(
    fieldnames: Optional[List[str]],
) -> None:
    """
    Verify that the CSV contains Anchor's required columns.
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


def _build_opportunity(
    row: dict,
    row_number: int,
) -> OpportunityTuple:
    """
    Convert one CSV row into an Anchor opportunity tuple.
    """

    security_type = (
        row["security_type"]
        .strip()
        .upper()
    )

    maturity_years = _parse_float(
        row["maturity_years"],
        "maturity_years",
        row_number,
    )

    yield_percent = _parse_float(
        row["yield_percent"],
        "yield_percent",
        row_number,
    )

    spread_compensation = (
        row["spread_compensation"]
        .strip()
        .upper()
    )

    if not security_type:
        raise ValueError(
            f"Row {row_number}: "
            "security_type is required."
        )

    if not spread_compensation:
        raise ValueError(
            f"Row {row_number}: "
            "spread_compensation is required."
        )

    rating = _parse_optional_string(
        row.get("rating")
    )

    callable_value = _parse_callable(
        row.get("callable"),
        row_number,
    )

    opportunity = FixedIncomeOpportunity(
        security_type=security_type,
        maturity_years=maturity_years,
        yield_percent=yield_percent,
        rating=rating,
        callable=callable_value,
    )

    return (
        opportunity,
        spread_compensation,
    )


def load_opportunities_from_csv(
    file_path: str,
) -> List[OpportunityTuple]:
    """
    Load fixed-income opportunities from a CSV file.

    Parameters
    ----------
    file_path:
        Path to a CSV file containing fixed-income
        opportunity data.

    Required columns
    ----------------
    security_type
    maturity_years
    yield_percent
    spread_compensation

    Optional columns
    ----------------
    rating
    callable

    Returns
    -------
    list
        List of:

            (
                FixedIncomeOpportunity,
                spread_compensation,
            )

    Raises
    ------
    FileNotFoundError
        If the CSV file does not exist.

    ValueError
        If the CSV structure or row values are malformed.
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

    opportunities: List[
        OpportunityTuple
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

            opportunities.append(
                _build_opportunity(
                    row=row,
                    row_number=row_number,
                )
            )

    if not opportunities:
        raise ValueError(
            "CSV file contains no opportunities."
        )

    return opportunities
