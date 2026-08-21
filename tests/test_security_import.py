from datetime import date

import pytest

from engine.security_import import (
    load_security_data_from_csv,
)


def write_csv(
    tmp_path,
    content,
):
    path = tmp_path / "securities.csv"

    path.write_text(
        content,
        encoding="utf-8",
    )

    return path


def test_load_valid_production_security_csv(
    tmp_path,
):
    path = write_csv(
        tmp_path,
        (
            "cusip,issuer,security_type,"
            "coupon_percent,maturity_date,"
            "yield_to_maturity_percent,"
            "price,rating,callable,call_date,"
            "minimum_quantity,source,"
            "description,spread_compensation\n"
            "91282ABC1,U.S. Treasury,TREASURY,"
            "4.00,2030-08-21,4.25,"
            "99.50,,FALSE,,1000,SCHWAB,"
            "US Treasury Note,MODERATE\n"
            "123456AB7,Example Corporation,"
            "CORPORATE,5.00,2031-06-15,"
            "5.35,101.20,A,FALSE,,5000,"
            "SCHWAB,Example Corp Senior Note,HIGH\n"
        ),
    )

    result = load_security_data_from_csv(
        str(path)
    )

    assert len(result) == 2


def test_import_preserves_treasury_fields(
    tmp_path,
):
    path = write_csv(
        tmp_path,
        (
            "cusip,issuer,security_type,"
            "coupon_percent,maturity_date,"
            "yield_to_maturity_percent,"
            "price,rating,callable,call_date,"
            "minimum_quantity,source,"
            "description,spread_compensation\n"
            "91282ABC1,U.S. Treasury,TREASURY,"
            "4.00,2030-08-21,4.25,"
            "99.50,,FALSE,,1000,SCHWAB,"
            "US Treasury Note,MODERATE\n"
        ),
    )

    result = load_security_data_from_csv(
        str(path)
    )

    security, spread = result[0]

    assert security.cusip == "91282ABC1"
    assert security.issuer == "U.S. Treasury"
    assert security.security_type == "TREASURY"
    assert security.coupon_percent == 4.00
    assert security.maturity_date == date(
        2030,
        8,
        21,
    )
    assert (
        security.yield_to_maturity_percent
        == 4.25
    )
    assert security.price == 99.50
    assert security.callable is False
    assert security.minimum_quantity == 1000.0
    assert security.source == "SCHWAB"
    assert spread == "MODERATE"


def test_import_normalizes_security_type(
    tmp_path,
):
    path = write_csv(
        tmp_path,
        (
            "security_type,maturity_date,"
            "yield_to_maturity_percent,"
            "spread_compensation\n"
            "treasury,2030-08-21,4.25,moderate\n"
        ),
    )

    result = load_security_data_from_csv(
        str(path)
    )

    security, spread = result[0]

    assert security.security_type == "TREASURY"
    assert spread == "MODERATE"


def test_import_normalizes_rating(
    tmp_path,
):
    path = write_csv(
        tmp_path,
        (
            "security_type,maturity_date,"
            "yield_to_maturity_percent,"
            "rating,spread_compensation\n"
            "CORPORATE,2031-06-15,"
            "5.35,a,HIGH\n"
        ),
    )

    result = load_security_data_from_csv(
        str(path)
    )

    security, _ = result[0]

    assert security.rating == "A"


def test_import_normalizes_source(
    tmp_path,
):
    path = write_csv(
        tmp_path,
        (
            "security_type,maturity_date,"
            "yield_to_maturity_percent,"
            "source,spread_compensation\n"
            "TREASURY,2030-08-21,"
            "4.25,schwab,MODERATE\n"
        ),
    )

    result = load_security_data_from_csv(
        str(path)
    )

    security, _ = result[0]

    assert security.source == "SCHWAB"


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
            "security_type,maturity_date,"
            "yield_to_maturity_percent,"
            "rating,callable,call_date,"
            "spread_compensation\n"
            f"CORPORATE,2031-06-15,"
            f"5.35,A,{value},2029-06-15,HIGH\n"
        ),
    )

    result = load_security_data_from_csv(
        str(path)
    )

    security, _ = result[0]

    assert security.callable is True


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
            "security_type,maturity_date,"
            "yield_to_maturity_percent,"
            "rating,callable,"
            "spread_compensation\n"
            f"CORPORATE,2031-06-15,"
            f"5.35,A,{value},HIGH\n"
        ),
    )

    result = load_security_data_from_csv(
        str(path)
    )

    security, _ = result[0]

    assert security.callable is False


def test_import_parses_call_date(
    tmp_path,
):
    path = write_csv(
        tmp_path,
        (
            "security_type,maturity_date,"
            "yield_to_maturity_percent,"
            "rating,callable,call_date,"
            "spread_compensation\n"
            "CORPORATE,2032-09-01,"
            "5.65,A,TRUE,2029-09-01,HIGH\n"
        ),
    )

    result = load_security_data_from_csv(
        str(path)
    )

    security, _ = result[0]

    assert security.call_date == date(
        2029,
        9,
        1,
    )


def test_invalid_callable_raises(
    tmp_path,
):
    path = write_csv(
        tmp_path,
        (
            "security_type,maturity_date,"
            "yield_to_maturity_percent,"
            "rating,callable,"
            "spread_compensation\n"
            "CORPORATE,2031-06-15,"
            "5.35,A,MAYBE,HIGH\n"
        ),
    )

    with pytest.raises(
        ValueError,
        match="callable must be TRUE or FALSE",
    ):
        load_security_data_from_csv(
            str(path)
        )


def test_missing_required_column_raises(
    tmp_path,
):
    path = write_csv(
        tmp_path,
        (
            "security_type,maturity_date,"
            "yield_to_maturity_percent\n"
            "TREASURY,2030-08-21,4.25\n"
        ),
    )

    with pytest.raises(
        ValueError,
        match="missing required columns",
    ):
        load_security_data_from_csv(
            str(path)
        )


def test_missing_maturity_date_raises(
    tmp_path,
):
    path = write_csv(
        tmp_path,
        (
            "security_type,maturity_date,"
            "yield_to_maturity_percent,"
            "spread_compensation\n"
            "TREASURY,,4.25,MODERATE\n"
        ),
    )

    with pytest.raises(
        ValueError,
        match="maturity_date is required",
    ):
        load_security_data_from_csv(
            str(path)
        )


def test_invalid_maturity_date_format_raises(
    tmp_path,
):
    path = write_csv(
        tmp_path,
        (
            "security_type,maturity_date,"
            "yield_to_maturity_percent,"
            "spread_compensation\n"
            "TREASURY,08/21/2030,"
            "4.25,MODERATE\n"
        ),
    )

    with pytest.raises(
        ValueError,
        match="must use YYYY-MM-DD",
    ):
        load_security_data_from_csv(
            str(path)
        )


def test_non_numeric_yield_raises(
    tmp_path,
):
    path = write_csv(
        tmp_path,
        (
            "security_type,maturity_date,"
            "yield_to_maturity_percent,"
            "spread_compensation\n"
            "TREASURY,2030-08-21,"
            "HIGH,MODERATE\n"
        ),
    )

    with pytest.raises(
        ValueError,
        match="yield_to_maturity_percent must be numeric",
    ):
        load_security_data_from_csv(
            str(path)
        )


def test_non_numeric_coupon_raises(
    tmp_path,
):
    path = write_csv(
        tmp_path,
        (
            "security_type,coupon_percent,"
            "maturity_date,"
            "yield_to_maturity_percent,"
            "spread_compensation\n"
            "TREASURY,FOUR,2030-08-21,"
            "4.25,MODERATE\n"
        ),
    )

    with pytest.raises(
        ValueError,
        match="coupon_percent must be numeric",
    ):
        load_security_data_from_csv(
            str(path)
        )


def test_non_numeric_price_raises(
    tmp_path,
):
    path = write_csv(
        tmp_path,
        (
            "security_type,maturity_date,"
            "yield_to_maturity_percent,"
            "price,spread_compensation\n"
            "TREASURY,2030-08-21,"
            "4.25,PAR,MODERATE\n"
        ),
    )

    with pytest.raises(
        ValueError,
        match="price must be numeric",
    ):
        load_security_data_from_csv(
            str(path)
        )


def test_corporate_without_rating_raises(
    tmp_path,
):
    path = write_csv(
        tmp_path,
        (
            "security_type,maturity_date,"
            "yield_to_maturity_percent,"
            "spread_compensation\n"
            "CORPORATE,2031-06-15,"
            "5.35,HIGH\n"
        ),
    )

    with pytest.raises(
        ValueError,
        match="Corporate securities require a rating",
    ):
        load_security_data_from_csv(
            str(path)
        )


def test_non_callable_with_call_date_raises(
    tmp_path,
):
    path = write_csv(
        tmp_path,
        (
            "security_type,maturity_date,"
            "yield_to_maturity_percent,"
            "callable,call_date,"
            "spread_compensation\n"
            "TREASURY,2030-08-21,"
            "4.25,FALSE,2029-08-21,MODERATE\n"
        ),
    )

    with pytest.raises(
        ValueError,
        match="Non-callable securities cannot have a call_date",
    ):
        load_security_data_from_csv(
            str(path)
        )


def test_call_date_after_maturity_raises(
    tmp_path,
):
    path = write_csv(
        tmp_path,
        (
            "security_type,maturity_date,"
            "yield_to_maturity_percent,"
            "rating,callable,call_date,"
            "spread_compensation\n"
            "CORPORATE,2031-06-15,"
            "5.35,A,TRUE,2032-06-15,HIGH\n"
        ),
    )

    with pytest.raises(
        ValueError,
        match="call_date cannot be after maturity_date",
    ):
        load_security_data_from_csv(
            str(path)
        )


def test_blank_rows_are_ignored(
    tmp_path,
):
    path = write_csv(
        tmp_path,
        (
            "security_type,maturity_date,"
            "yield_to_maturity_percent,"
            "spread_compensation\n"
            "\n"
            "TREASURY,2030-08-21,"
            "4.25,MODERATE\n"
            "\n"
        ),
    )

    result = load_security_data_from_csv(
        str(path)
    )

    assert len(result) == 1


def test_empty_csv_raises(
    tmp_path,
):
    path = write_csv(
        tmp_path,
        (
            "security_type,maturity_date,"
            "yield_to_maturity_percent,"
            "spread_compensation\n"
        ),
    )

    with pytest.raises(
        ValueError,
        match="contains no securities",
    ):
        load_security_data_from_csv(
            str(path)
        )


def test_missing_file_raises():
    with pytest.raises(
        FileNotFoundError,
    ):
        load_security_data_from_csv(
            "does_not_exist.csv"
        )
