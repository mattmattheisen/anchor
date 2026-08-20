import pytest

from engine.models import TreasuryPoint
from engine.curve import interpolated_yield


def sample_curve():
    return [
        TreasuryPoint(2.0, 4.218),
        TreasuryPoint(5.0, 4.433),
        TreasuryPoint(10.0, 4.704),
        TreasuryPoint(30.0, 5.256),
    ]


def test_exact_maturity_returns_exact_yield():
    assert interpolated_yield(
        sample_curve(),
        5.0,
    ) == 4.433


def test_interpolates_between_2y_and_5y():
    result = interpolated_yield(
        sample_curve(),
        3.5,
    )

    assert result == 4.3255


def test_interpolates_between_5y_and_10y():
    result = interpolated_yield(
        sample_curve(),
        7.5,
    )

    assert result == 4.5685


def test_interpolates_unsorted_curve():
    points = [
        TreasuryPoint(10.0, 4.704),
        TreasuryPoint(2.0, 4.218),
        TreasuryPoint(30.0, 5.256),
        TreasuryPoint(5.0, 4.433),
    ]

    assert interpolated_yield(
        points,
        7.5,
    ) == 4.5685


def test_empty_curve_rejected():
    with pytest.raises(
        ValueError,
        match="Treasury curve is empty",
    ):
        interpolated_yield([], 5.0)


def test_below_curve_rejected():
    with pytest.raises(
        ValueError,
        match="below the available Treasury curve",
    ):
        interpolated_yield(
            sample_curve(),
            1.0,
        )


def test_above_curve_rejected():
    with pytest.raises(
        ValueError,
        match="above the available Treasury curve",
    ):
        interpolated_yield(
            sample_curve(),
            40.0,
        )
