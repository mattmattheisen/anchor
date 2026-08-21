import pytest

from engine.opportunity_import import (
    load_opportunities_from_csv,
)


def write_csv(
    tmp_path,
    content,
):
    path = tmp_path / "opportunities.csv"
    path.write_text(
        content,
        encoding="utf-8",
    )
    return path


def test_load_valid_csv(tmp_path):
    path = write_csv(
        tmp_path,
        (
            "security_type,maturity_years,"
            "yield_percent,rating,callable,"
            "spread_compensation\n"
            "TREASURY,2,4.20,,,MODERATE\n"
            "CORPORATE,5,5.30,A,FALSE,HIGH\n"
        ),
    )

    result = load_opportunities_from_csv(
        str(path)
    )

    assert len(result) == 2


def test_imported_security_types_are_normalized(tmp_path):
    path = write_csv(
        tmp_path,
        (
            "security_type,maturity_years,"
            "yield_percent,rating,callable,"
            "spread_compensation\n"
            "treasury,2,4.20,,,moderate\n"
        ),
    )

    result = load_opportunities_from_csv(
        str(path)
    )

    opportunity, spread = result[0]

    assert (
        opportunity.security_type
        == "TREASURY"
    )

    assert spread == "MODERATE"


def test_numeric_fields_are_parsed(tmp_path):
    path = write_csv(
        tmp_path,
        (
            "security_type,maturity_years,"
            "yield_percent,rating,callable,"
            "spread_compensation\n"
            "TREASURY,2.5,4.27,,,MODERATE\n"
        ),
    )

    result = load_opportunities_from_csv(
        str(path)
    )

    opportunity, _ = result[0]

    assert opportunity.maturity_years == 2.5
    assert opportunity.yield_percent == 4.27


def test_rating_is_normalized(tmp_path):
    path = write_csv(
        tmp_path,
        (
            "security_type,maturity_years,"
            "yield_percent,rating,callable,"
            "spread_compensation\n"
            "CORPORATE,5,5.30,a,FALSE,HIGH\n"
        ),
    )

    result = load_opportunities_from_csv(
        str(path)
    )

    opportunity, _ = result[0]

    assert opportunity.rating == "A"


@pytest.mark.parametrize(
    "value",
    [
        "TRUE",
        "YES",
        "Y",
        "1",
        "true",
        "yes",
    ],
)
def test_callable_true_values(
    tmp_path,
    value,
):
    path = write_csv(
        tmp_path,
        (
            "security_type,maturity_years,"
            "yield_percent,rating,callable,"
            "spread_compensation\n"
            f"CORPORATE,5,5.30,A,{value},HIGH\n"
        ),
    )

    result = load_opportunities_from_csv(
        str(path)
    )

    opportunity, _ = result[0]

    assert opportunity.callable is True


@pytest.mark.parametrize(
    "value",
    [
        "FALSE",
        "NO",
        "N",
        "0",
        "",
        "false",
        "no",
    ],
)
def test_callable_false_values(
    tmp_path,
    value,
):
    path = write_csv(
        tmp_path,
        (
            "security_type,maturity_years,"
            "yield_percent,rating,callable,"
            "spread_compensation\n"
            f"CORPORATE,5,5.30,A,{value},HIGH\n"
        ),
    )

    result = load_opportunities_from_csv(
        str(path)
    )

    opportunity, _ = result[0]

    assert opportunity.callable is False


def test_invalid_callable_value_raises(tmp_path):
    path = write_csv(
        tmp_path,
        (
            "security_type,maturity_years,"
            "yield_percent,rating,callable,"
            "spread_compensation\n"
            "CORPORATE,5,5.30,A,MAYBE,HIGH\n"
        ),
    )

    with pytest.raises(
        ValueError,
        match="callable must be TRUE or FALSE",
    ):
        load_opportunities_from_csv(
            str(path)
        )


def test_missing_required_column_raises(tmp_path):
    path = write_csv(
        tmp_path,
        (
            "security_type,maturity_years,"
            "yield_percent\n"
            "TREASURY,2,4.20\n"
        ),
    )

    with pytest.raises(
        ValueError,
        match="missing required columns",
    ):
        load_opportunities_from_csv(
            str(path)
        )


def test_missing_numeric_value_raises(tmp_path):
    path = write_csv(
        tmp_path,
        (
            "security_type,maturity_years,"
            "yield_percent,rating,callable,"
            "spread_compensation\n"
            "TREASURY,,4.20,,,MODERATE\n"
        ),
    )

    with pytest.raises(
        ValueError,
        match="maturity_years is required",
    ):
        load_opportunities_from_csv(
            str(path)
        )


def test_non_numeric_maturity_raises(tmp_path):
    path = write_csv(
        tmp_path,
        (
            "security_type,maturity_years,"
            "yield_percent,rating,callable,"
            "spread_compensation\n"
            "TREASURY,FIVE,4.20,,,MODERATE\n"
        ),
    )

    with pytest.raises(
        ValueError,
        match="maturity_years must be numeric",
    ):
        load_opportunities_from_csv(
            str(path)
        )


def test_non_numeric_yield_raises(tmp_path):
    path = write_csv(
        tmp_path,
        (
            "security_type,maturity_years,"
            "yield_percent,rating,callable,"
            "spread_compensation\n"
            "TREASURY,2,HIGH,,,MODERATE\n"
        ),
    )

    with pytest.raises(
        ValueError,
        match="yield_percent must be numeric",
    ):
        load_opportunities_from_csv(
            str(path)
        )


def test_empty_csv_raises(tmp_path):
    path = write_csv(
        tmp_path,
        (
            "security_type,maturity_years,"
            "yield_percent,rating,callable,"
            "spread_compensation\n"
        ),
    )

    with pytest.raises(
        ValueError,
        match="contains no opportunities",
    ):
        load_opportunities_from_csv(
            str(path)
        )


def test_blank_rows_are_ignored(tmp_path):
    path = write_csv(
        tmp_path,
        (
            "security_type,maturity_years,"
            "yield_percent,rating,callable,"
            "spread_compensation\n"
            "\n"
            "TREASURY,2,4.20,,,MODERATE\n"
            "\n"
        ),
    )

    result = load_opportunities_from_csv(
        str(path)
    )

    assert len(result) == 1


def test_missing_file_raises():
    with pytest.raises(
        FileNotFoundError,
    ):
        load_opportunities_from_csv(
            "does_not_exist.csv"
        )


def test_imported_output_has_anchor_tuple_shape(
    tmp_path,
):
    path = write_csv(
        tmp_path,
        (
            "security_type,maturity_years,"
            "yield_percent,rating,callable,"
            "spread_compensation\n"
            "TREASURY,2,4.20,,,MODERATE\n"
        ),
    )

    result = load_opportunities_from_csv(
        str(path)
    )

    assert len(result) == 1

    opportunity, spread = result[0]

    assert hasattr(
        opportunity,
        "security_type",
    )

    assert spread == "MODERATE"
