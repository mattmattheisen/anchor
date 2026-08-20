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
