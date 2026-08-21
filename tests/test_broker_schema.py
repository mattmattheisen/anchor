import pytest

from engine.broker_schema import (
    build_column_mapping,
    canonical_field_for_column,
    normalize_column_name,
)


@pytest.mark.parametrize(
    "source,expected",
    [
        ("CUSIP", "cusip"),
        (" cusip ", "cusip"),
        ("Coupon Rate", "coupon rate"),
        ("Coupon-Rate", "coupon rate"),
        ("  Yield   To   Maturity  ", "yield to maturity"),
        ("NEXT-CALL-DATE", "next call date"),
    ],
)
def test_normalize_column_name(
    source,
    expected,
):
    assert (
        normalize_column_name(source)
        == expected
    )


@pytest.mark.parametrize(
    "column,expected",
    [
        ("CUSIP", "cusip"),
        ("CUSIP Number", "cusip"),
        ("Security ID", "cusip"),
        ("Issuer", "issuer"),
        ("Issuer Name", "issuer"),
        ("Security Type", "security_type"),
        ("Product Type", "security_type"),
        ("Coupon", "coupon_percent"),
        ("Coupon Rate", "coupon_percent"),
        ("Maturity", "maturity_date"),
        ("Maturity Date", "maturity_date"),
        ("Yield", "yield_percent"),
        ("Yield To Maturity", "yield_percent"),
        ("YTM", "yield_percent"),
        ("Yield To Worst", "yield_percent"),
        ("YTW", "yield_percent"),
        ("Price", "price"),
        ("Ask Price", "price"),
        ("Rating", "rating"),
        ("Credit Rating", "rating"),
        ("Callable", "callable"),
        ("Callable Flag", "callable"),
        ("Call Date", "call_date"),
        ("Next Call Date", "call_date"),
        ("Minimum Quantity", "minimum_quantity"),
        ("Min Qty", "minimum_quantity"),
        ("Source", "source"),
        ("Custodian", "source"),
        ("Security Description", "description"),
        ("Name", "description"),
    ],
)
def test_canonical_field_aliases(
    column,
    expected,
):
    assert (
        canonical_field_for_column(
            column
        )
        == expected
    )


def test_unknown_column_returns_none():
    assert (
        canonical_field_for_column(
            "Random Broker Field"
        )
        is None
    )


def test_column_matching_is_case_insensitive():
    assert (
        canonical_field_for_column(
            "YIELD TO MATURITY"
        )
        == "yield_percent"
    )


def test_column_matching_handles_hyphens():
    assert (
        canonical_field_for_column(
            "NEXT-CALL-DATE"
        )
        == "call_date"
    )


def test_build_column_mapping():
    columns = [
        "CUSIP",
        "Issuer Name",
        "Coupon Rate",
        "Maturity Date",
        "Yield To Worst",
        "Ask Price",
        "Credit Rating",
        "Callable Flag",
        "Next Call Date",
        "Min Qty",
        "Custodian",
    ]

    result = build_column_mapping(
        columns
    )

    assert result == {
        "CUSIP": "cusip",
        "Issuer Name": "issuer",
        "Coupon Rate": "coupon_percent",
        "Maturity Date": "maturity_date",
        "Yield To Worst": "yield_percent",
        "Ask Price": "price",
        "Credit Rating": "rating",
        "Callable Flag": "callable",
        "Next Call Date": "call_date",
        "Min Qty": "minimum_quantity",
        "Custodian": "source",
    }


def test_build_mapping_ignores_unknown_columns():
    columns = [
        "CUSIP",
        "Some Random Column",
        "Another Unknown Field",
        "Maturity Date",
    ]

    result = build_column_mapping(
        columns
    )

    assert result == {
        "CUSIP": "cusip",
        "Maturity Date": "maturity_date",
    }


def test_duplicate_canonical_mapping_is_rejected():
    columns = [
        "CUSIP",
        "CUSIP Number",
    ]

    with pytest.raises(
        ValueError,
        match=(
            "Multiple broker columns map to "
            "Anchor field: cusip"
        ),
    ):
        build_column_mapping(
            columns
        )


@pytest.mark.parametrize(
    "value",
    [
        None,
        123,
        True,
        4.25,
    ],
)
def test_normalize_column_requires_string(
    value,
):
    with pytest.raises(
        TypeError,
        match="column_name must be a string",
    ):
        normalize_column_name(
            value
        )


def test_mapping_is_deterministic():
    columns = [
        "CUSIP",
        "Issuer",
        "Maturity",
        "YTM",
    ]

    first = build_column_mapping(
        columns
    )

    second = build_column_mapping(
        columns
    )

    assert first == second
