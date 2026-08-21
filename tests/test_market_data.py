import math

import pytest

from engine.market_data import (
    MarketDataSnapshot,
    market_data_to_dict,
    validate_market_data,
)


def make_snapshot(
    fed_funds_rate=4.50,
    treasury_2y=4.31,
    treasury_10y=4.42,
    real_yield_10y=2.08,
    breakeven_10y=2.34,
    credit_spread_ig_bps=96.0,
    treasury_2y_change_bps=0.0,
    treasury_10y_change_bps=0.0,
    real_yield_10y_change_bps=0.0,
    breakeven_10y_change_bps=0.0,
    credit_spread_ig_change_bps=0.0,
    unemployment_rate=None,
    unemployment_rate_change_pct=None,
):
    return MarketDataSnapshot(
        fed_funds_rate=fed_funds_rate,
        treasury_2y=treasury_2y,
        treasury_10y=treasury_10y,
        real_yield_10y=real_yield_10y,
        breakeven_10y=breakeven_10y,
        credit_spread_ig_bps=credit_spread_ig_bps,
        treasury_2y_change_bps=treasury_2y_change_bps,
        treasury_10y_change_bps=treasury_10y_change_bps,
        real_yield_10y_change_bps=real_yield_10y_change_bps,
        breakeven_10y_change_bps=breakeven_10y_change_bps,
        credit_spread_ig_change_bps=credit_spread_ig_change_bps,
        unemployment_rate=unemployment_rate,
        unemployment_rate_change_pct=(
            unemployment_rate_change_pct
        ),
    )


def test_valid_snapshot_passes_validation():
    validate_market_data(
        make_snapshot()
    )


def test_market_data_to_dict_returns_dictionary():
    result = market_data_to_dict(
        make_snapshot()
    )

    assert isinstance(result, dict)


def test_market_data_to_dict_preserves_values():
    snapshot = make_snapshot(
        fed_funds_rate=4.25,
        treasury_2y=4.10,
        treasury_10y=4.35,
        real_yield_10y=1.95,
        breakeven_10y=2.40,
        credit_spread_ig_bps=88.0,
        unemployment_rate=4.2,
    )

    result = market_data_to_dict(
        snapshot
    )

    assert result["fed_funds_rate"] == 4.25
    assert result["treasury_2y"] == 4.10
    assert result["treasury_10y"] == 4.35
    assert result["real_yield_10y"] == 1.95
    assert result["breakeven_10y"] == 2.40
    assert result["credit_spread_ig_bps"] == 88.0
    assert result["unemployment_rate"] == 4.2


def test_market_data_to_dict_preserves_change_fields():
    snapshot = make_snapshot(
        treasury_2y_change_bps=12.0,
        treasury_10y_change_bps=-8.0,
        real_yield_10y_change_bps=15.0,
        breakeven_10y_change_bps=6.0,
        credit_spread_ig_change_bps=10.0,
    )

    result = market_data_to_dict(
        snapshot
    )

    assert result["treasury_2y_change_bps"] == 12.0
    assert result["treasury_10y_change_bps"] == -8.0
    assert result["real_yield_10y_change_bps"] == 15.0
    assert result["breakeven_10y_change_bps"] == 6.0
    assert result["credit_spread_ig_change_bps"] == 10.0


@pytest.mark.parametrize(
    "field_name",
    [
        "fed_funds_rate",
        "treasury_2y",
        "treasury_10y",
        "real_yield_10y",
        "breakeven_10y",
        "credit_spread_ig_bps",
        "treasury_2y_change_bps",
        "treasury_10y_change_bps",
        "real_yield_10y_change_bps",
        "breakeven_10y_change_bps",
        "credit_spread_ig_change_bps",
    ],
)
def test_non_numeric_required_field_is_rejected(
    field_name,
):
    kwargs = {
        field_name: "NOT_NUMERIC",
    }

    snapshot = make_snapshot(
        **kwargs
    )

    with pytest.raises(
        TypeError,
        match="must be numeric",
    ):
        validate_market_data(
            snapshot
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "fed_funds_rate",
        "treasury_2y",
        "treasury_10y",
        "real_yield_10y",
        "breakeven_10y",
        "credit_spread_ig_bps",
        "treasury_2y_change_bps",
        "treasury_10y_change_bps",
        "real_yield_10y_change_bps",
        "breakeven_10y_change_bps",
        "credit_spread_ig_change_bps",
    ],
)
def test_boolean_required_field_is_rejected(
    field_name,
):
    kwargs = {
        field_name: True,
    }

    snapshot = make_snapshot(
        **kwargs
    )

    with pytest.raises(
        TypeError,
        match="must be numeric",
    ):
        validate_market_data(
            snapshot
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "fed_funds_rate",
        "treasury_2y",
        "treasury_10y",
        "real_yield_10y",
        "breakeven_10y",
        "credit_spread_ig_bps",
        "treasury_2y_change_bps",
        "treasury_10y_change_bps",
        "real_yield_10y_change_bps",
        "breakeven_10y_change_bps",
        "credit_spread_ig_change_bps",
    ],
)
def test_nan_required_field_is_rejected(
    field_name,
):
    kwargs = {
        field_name: math.nan,
    }

    snapshot = make_snapshot(
        **kwargs
    )

    with pytest.raises(
        ValueError,
        match="must be finite",
    ):
        validate_market_data(
            snapshot
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "fed_funds_rate",
        "treasury_2y",
        "treasury_10y",
        "real_yield_10y",
        "breakeven_10y",
        "credit_spread_ig_bps",
        "treasury_2y_change_bps",
        "treasury_10y_change_bps",
        "real_yield_10y_change_bps",
        "breakeven_10y_change_bps",
        "credit_spread_ig_change_bps",
    ],
)
def test_infinite_required_field_is_rejected(
    field_name,
):
    kwargs = {
        field_name: math.inf,
    }

    snapshot = make_snapshot(
        **kwargs
    )

    with pytest.raises(
        ValueError,
        match="must be finite",
    ):
        validate_market_data(
            snapshot
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "fed_funds_rate",
        "treasury_2y",
        "treasury_10y",
        "credit_spread_ig_bps",
    ],
)
def test_negative_nonnegative_fields_are_rejected(
    field_name,
):
    kwargs = {
        field_name: -1.0,
    }

    snapshot = make_snapshot(
        **kwargs
    )

    with pytest.raises(
        ValueError,
    ):
        validate_market_data(
            snapshot
        )


def test_negative_real_yield_is_allowed():
    snapshot = make_snapshot(
        real_yield_10y=-0.50,
    )

    validate_market_data(
        snapshot
    )


def test_negative_breakeven_is_allowed_by_integrity_layer():
    snapshot = make_snapshot(
        breakeven_10y=-0.25,
    )

    validate_market_data(
        snapshot
    )


def test_negative_change_values_are_allowed():
    snapshot = make_snapshot(
        treasury_2y_change_bps=-25.0,
        treasury_10y_change_bps=-15.0,
        real_yield_10y_change_bps=-20.0,
        breakeven_10y_change_bps=-10.0,
        credit_spread_ig_change_bps=-12.0,
    )

    validate_market_data(
        snapshot
    )


def test_optional_unemployment_fields_can_be_none():
    snapshot = make_snapshot(
        unemployment_rate=None,
        unemployment_rate_change_pct=None,
    )

    validate_market_data(
        snapshot
    )


def test_valid_optional_unemployment_fields_pass():
    snapshot = make_snapshot(
        unemployment_rate=4.3,
        unemployment_rate_change_pct=0.2,
    )

    validate_market_data(
        snapshot
    )


def test_negative_unemployment_rate_is_rejected():
    snapshot = make_snapshot(
        unemployment_rate=-1.0,
    )

    with pytest.raises(
        ValueError,
        match="unemployment_rate cannot be negative",
    ):
        validate_market_data(
            snapshot
        )


def test_nan_unemployment_rate_is_rejected():
    snapshot = make_snapshot(
        unemployment_rate=math.nan,
    )

    with pytest.raises(
        ValueError,
        match="must be finite",
    ):
        validate_market_data(
            snapshot
        )


def test_boolean_unemployment_rate_is_rejected():
    snapshot = make_snapshot(
        unemployment_rate=True,
    )

    with pytest.raises(
        TypeError,
        match="must be numeric",
    ):
        validate_market_data(
            snapshot
        )


def test_wrong_snapshot_type_is_rejected():
    with pytest.raises(
        TypeError,
        match="snapshot must be a MarketDataSnapshot",
    ):
        validate_market_data(
            "NOT_A_SNAPSHOT"
        )
