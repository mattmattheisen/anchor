from engine.models import TreasuryPoint
from engine.curve import (
    sort_curve,
    spread_bps,
    standard_curve_spreads,
    classify_curve_shape,
)


def sample_curve():
    return [
        TreasuryPoint(2.0, 4.218),
        TreasuryPoint(5.0, 4.433),
        TreasuryPoint(10.0, 4.704),
        TreasuryPoint(30.0, 5.256),
    ]


def test_sort_curve():
    points = [
        TreasuryPoint(10.0, 4.704),
        TreasuryPoint(2.0, 4.218),
        TreasuryPoint(5.0, 4.433),
    ]

    sorted_points = sort_curve(points)

    assert [point.maturity_years for point in sorted_points] == [
        2.0,
        5.0,
        10.0,
    ]


def test_spread_bps():
    short_point = TreasuryPoint(2.0, 4.218)
    long_point = TreasuryPoint(10.0, 4.704)

    assert spread_bps(short_point, long_point) == 48.6


def test_standard_curve_spreads():
    spreads = standard_curve_spreads(sample_curve())

    assert spreads["2s10s"] == 48.6
    assert spreads["2s30s"] == 103.8
    assert spreads["5s10s"] == 27.1
    assert spreads["5s30s"] == 82.3
    assert spreads["10s30s"] == 55.2


def test_classify_curve_shape():
    assert classify_curve_shape(sample_curve()) == "NORMAL"
def test_inverted_curve():
    points = [
        TreasuryPoint(2.0, 5.00),
        TreasuryPoint(5.0, 4.80),
        TreasuryPoint(10.0, 4.50),
        TreasuryPoint(30.0, 4.25),
    ]

    assert classify_curve_shape(points) == "INVERTED"


def test_flat_curve():
    points = [
        TreasuryPoint(2.0, 4.50),
        TreasuryPoint(5.0, 4.52),
        TreasuryPoint(10.0, 4.55),
        TreasuryPoint(30.0, 4.60),
    ]

    assert classify_curve_shape(points) == "FLAT"


def test_steep_curve():
    points = [
        TreasuryPoint(2.0, 3.50),
        TreasuryPoint(5.0, 4.00),
        TreasuryPoint(10.0, 4.25),
        TreasuryPoint(30.0, 4.75),
    ]

    assert classify_curve_shape(points) == "STEEP"


def test_missing_required_maturity():
    points = [
        TreasuryPoint(2.0, 4.20),
        TreasuryPoint(5.0, 4.40),
        TreasuryPoint(10.0, 4.70),
    ]

    try:
        standard_curve_spreads(points)
        assert False, "Expected ValueError for missing 30Y Treasury"
    except ValueError as exc:
        assert "30.0 years was not found" in str(exc)


def test_unsorted_input_still_works():
    points = [
        TreasuryPoint(30.0, 5.25),
        TreasuryPoint(2.0, 4.20),
        TreasuryPoint(10.0, 4.70),
        TreasuryPoint(5.0, 4.40),
    ]

    spreads = standard_curve_spreads(points)

    assert spreads["2s10s"] == 50.0
