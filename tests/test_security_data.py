from datetime import date

import math
import pytest

from engine.security_data import (
    SecurityData,
    security_data_to_dict,
    validate_security_data,
)


def make_security(
    security_type="TREASURY",
    maturity_date=date(2030, 8, 21),
    yield_to_maturity_percent=4.25,
    cusip="91282ABC1",
    issuer="U.S. Treasury",
    coupon_percent=4.00,
    price=99.50,
    rating=None,
    callable=False,
    call_date=None,
    minimum_quantity=1000.0,
    source="CSV",
    description="Test security",
):
    return SecurityData(
        security_type=security_type,
        maturity_date=maturity_date,
        yield_to_maturity_percent=(
            yield_to_maturity_percent
        ),
        cusip=cusip,
        issuer=issuer,
        coupon_percent=coupon_percent,
        price=price,
        rating=rating,
        callable=callable,
        call_date=call_date,
        minimum_quantity=minimum_quantity,
        source=source,
        description=description,
    )


def test_valid_treasury_passes_validation():
    validate_security_data(
        make_security()
    )


def test_valid_corporate_passes_validation():
    security = make_security(
        security_type="CORPORATE",
        issuer="Example Corporation",
        rating="A",
    )

    validate_security_data(
        security
    )


def test_security_data_to_dict_returns_dictionary():
    result = security_data_to_dict(
        make_security()
    )

    assert isinstance(result, dict)


def test_security_data_to_dict_preserves_core_fields():
    result = security_data_to_dict(
        make_security()
    )

    assert result["cusip"] == "91282ABC1"
    assert result["issuer"] == "U.S. Treasury"
    assert result["security_type"] == "TREASURY"
    assert result["coupon_percent"] == 4.00
    assert result["maturity_date"] == "2030-08-21"
    assert (
        result["yield_to_maturity_percent"]
        == 4.25
    )
    assert result["price"] == 99.50
    assert result["callable"] is False
    assert result["minimum_quantity"] == 1000.0
    assert result["source"] == "CSV"


def test_callable_security_with_valid_call_date_passes():
    security = make_security(
        security_type="CORPORATE",
        rating="A",
        callable=True,
        call_date=date(2028, 8, 21),
    )

    validate_security_data(
        security
    )


def test_callable_security_serializes_call_date():
    security = make_security(
        security_type="CORPORATE",
        rating="A",
        callable=True,
        call_date=date(2028, 8, 21),
    )

    result = security_data_to_dict(
        security
    )

    assert result["call_date"] == "2028-08-21"


def test_invalid_security_type_is_rejected():
    security = make_security(
        security_type="CRYPTO",
    )

    with pytest.raises(
        ValueError,
        match="Unsupported security_type",
    ):
        validate_security_data(
            security
        )


def test_maturity_date_must_be_date():
    security = make_security(
        maturity_date="2030-08-21",
    )

    with pytest.raises(
        TypeError,
        match="maturity_date must be a date",
    ):
        validate_security_data(
            security
        )


def test_negative_yield_is_rejected():
    security = make_security(
        yield_to_maturity_percent=-0.50,
    )

    with pytest.raises(
        ValueError,
        match="cannot be negative",
    ):
        validate_security_data(
            security
        )


def test_nan_yield_is_rejected():
    security = make_security(
        yield_to_maturity_percent=math.nan,
    )

    with pytest.raises(
        ValueError,
        match="must be finite",
    ):
        validate_security_data(
            security
        )


def test_infinite_yield_is_rejected():
    security = make_security(
        yield_to_maturity_percent=math.inf,
    )

    with pytest.raises(
        ValueError,
        match="must be finite",
    ):
        validate_security_data(
            security
        )


def test_boolean_yield_is_rejected():
    security = make_security(
        yield_to_maturity_percent=True,
    )

    with pytest.raises(
        TypeError,
        match="must be numeric",
    ):
        validate_security_data(
            security
        )


def test_negative_coupon_is_rejected():
    security = make_security(
        coupon_percent=-1.0,
    )

    with pytest.raises(
        ValueError,
        match="coupon_percent cannot be negative",
    ):
        validate_security_data(
            security
        )


def test_nan_coupon_is_rejected():
    security = make_security(
        coupon_percent=math.nan,
    )

    with pytest.raises(
        ValueError,
        match="must be finite",
    ):
        validate_security_data(
            security
        )


def test_zero_price_is_rejected():
    security = make_security(
        price=0.0,
    )

    with pytest.raises(
        ValueError,
        match="price must be greater than 0",
    ):
        validate_security_data(
            security
        )


def test_negative_price_is_rejected():
    security = make_security(
        price=-99.0,
    )

    with pytest.raises(
        ValueError,
        match="price must be greater than 0",
    ):
        validate_security_data(
            security
        )


def test_nan_price_is_rejected():
    security = make_security(
        price=math.nan,
    )

    with pytest.raises(
        ValueError,
        match="must be finite",
    ):
        validate_security_data(
            security
        )


def test_zero_minimum_quantity_is_rejected():
    security = make_security(
        minimum_quantity=0.0,
    )

    with pytest.raises(
        ValueError,
        match="minimum_quantity must be greater than 0",
    ):
        validate_security_data(
            security
        )


def test_negative_minimum_quantity_is_rejected():
    security = make_security(
        minimum_quantity=-1000.0,
    )

    with pytest.raises(
        ValueError,
        match="minimum_quantity must be greater than 0",
    ):
        validate_security_data(
            security
        )


def test_callable_must_be_boolean():
    security = make_security(
        callable="YES",
    )

    with pytest.raises(
        TypeError,
        match="callable must be a boolean",
    ):
        validate_security_data(
            security
        )


def test_call_date_must_be_date():
    security = make_security(
        security_type="CORPORATE",
        rating="A",
        callable=True,
        call_date="2028-08-21",
    )

    with pytest.raises(
        TypeError,
        match="call_date must be a date",
    ):
        validate_security_data(
            security
        )


def test_call_date_after_maturity_is_rejected():
    security = make_security(
        security_type="CORPORATE",
        rating="A",
        callable=True,
        maturity_date=date(2030, 8, 21),
        call_date=date(2031, 8, 21),
    )

    with pytest.raises(
        ValueError,
        match="call_date cannot be after maturity_date",
    ):
        validate_security_data(
            security
        )


def test_non_callable_security_cannot_have_call_date():
    security = make_security(
        callable=False,
        call_date=date(2028, 8, 21),
    )

    with pytest.raises(
        ValueError,
        match="Non-callable securities cannot have a call_date",
    ):
        validate_security_data(
            security
        )


def test_corporate_requires_rating():
    security = make_security(
        security_type="CORPORATE",
        rating=None,
    )

    with pytest.raises(
        ValueError,
        match="Corporate securities require a rating",
    ):
        validate_security_data(
            security
        )


def test_optional_text_fields_must_be_strings():
    security = make_security(
        cusip=123456789,
    )

    with pytest.raises(
        TypeError,
        match="Text fields must be strings",
    ):
        validate_security_data(
            security
        )


def test_wrong_object_type_is_rejected():
    with pytest.raises(
        TypeError,
        match="security must be a SecurityData instance",
    ):
        validate_security_data(
            "NOT_SECURITY_DATA"
        )


def test_cd_security_is_supported():
    security = make_security(
        security_type="CD",
        issuer="Example Bank",
        rating=None,
    )

    validate_security_data(
        security
    )


def test_tips_security_is_supported():
    security = make_security(
        security_type="TIPS",
        issuer="U.S. Treasury",
    )

    validate_security_data(
        security
    )
