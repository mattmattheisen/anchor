import math

import pytest

from engine.spread_calculator import (
    SpreadAssessment,
    assess_spread_compensation,
    calculate_spread_bps,
    classify_spread_compensation,
)


def test_calculate_spread_bps_positive():
    result = calculate_spread_bps(
        security_yield_percent=5.25,
        benchmark_yield_percent=4.25,
    )

    assert result == pytest.approx(
        100.0
    )


def test_calculate_spread_bps_negative():
    result = calculate_spread_bps(
        security_yield_percent=4.00,
        benchmark_yield_percent=4.25,
    )

    assert result == pytest.approx(
        -25.0
    )


def test_calculate_spread_bps_zero():
    result = calculate_spread_bps(
        security_yield_percent=4.25,
        benchmark_yield_percent=4.25,
    )

    assert result == pytest.approx(
        0.0
    )


@pytest.mark.parametrize(
    "value,expected",
    [
        (-25.0, "LOW"),
        (0.0, "LOW"),
        (49.99, "LOW"),
        (50.0, "MODERATE"),
        (75.0, "MODERATE"),
        (99.99, "MODERATE"),
        (100.0, "MEANINGFUL"),
        (125.0, "MEANINGFUL"),
        (149.99, "MEANINGFUL"),
        (150.0, "HIGH"),
        (250.0, "HIGH"),
    ],
)
def test_classify_spread_compensation_thresholds(
    value,
    expected,
):
    result = classify_spread_compensation(
        value
    )

    assert result == expected


def test_assess_spread_compensation_returns_assessment():
    result = assess_spread_compensation(
        security_yield_percent=5.50,
        benchmark_yield_percent=4.25,
    )

    assert isinstance(
        result,
        SpreadAssessment,
    )


def test_assess_spread_compensation_preserves_inputs():
    result = assess_spread_compensation(
        security_yield_percent=5.50,
        benchmark_yield_percent=4.25,
    )

    assert (
        result.security_yield_percent
        == 5.50
    )

    assert (
        result.benchmark_yield_percent
        == 4.25
    )


def test_assess_spread_compensation_calculates_spread():
    result = assess_spread_compensation(
        security_yield_percent=5.50,
        benchmark_yield_percent=4.25,
    )

    assert result.spread_bps == pytest.approx(
        125.0
    )


def test_assess_spread_compensation_classifies_result():
    result = assess_spread_compensation(
        security_yield_percent=5.50,
        benchmark_yield_percent=4.25,
    )

    assert (
        result.compensation
        == "MEANINGFUL"
    )


@pytest.mark.parametrize(
    "security_yield,benchmark_yield",
    [
        (math.nan, 4.25),
        (math.inf, 4.25),
        (-math.inf, 4.25),
        (5.00, math.nan),
        (5.00, math.inf),
        (5.00, -math.inf),
    ],
)
def test_calculate_spread_rejects_non_finite_values(
    security_yield,
    benchmark_yield,
):
    with pytest.raises(
        ValueError,
        match="must be finite",
    ):
        calculate_spread_bps(
            security_yield_percent=(
                security_yield
            ),
            benchmark_yield_percent=(
                benchmark_yield
            ),
        )


@pytest.mark.parametrize(
    "security_yield,benchmark_yield",
    [
        ("5.00", 4.25),
        (5.00, "4.25"),
        (None, 4.25),
        (5.00, None),
    ],
)
def test_calculate_spread_rejects_non_numeric_values(
    security_yield,
    benchmark_yield,
):
    with pytest.raises(
        TypeError,
        match="must be numeric",
    ):
        calculate_spread_bps(
            security_yield_percent=(
                security_yield
            ),
            benchmark_yield_percent=(
                benchmark_yield
            ),
        )


@pytest.mark.parametrize(
    "security_yield,benchmark_yield",
    [
        (True, 4.25),
        (5.00, True),
        (False, 4.25),
        (5.00, False),
    ],
)
def test_calculate_spread_rejects_boolean_values(
    security_yield,
    benchmark_yield,
):
    with pytest.raises(
        TypeError,
        match="must be numeric",
    ):
        calculate_spread_bps(
            security_yield_percent=(
                security_yield
            ),
            benchmark_yield_percent=(
                benchmark_yield
            ),
        )


@pytest.mark.parametrize(
    "value",
    [
        math.nan,
        math.inf,
        -math.inf,
    ],
)
def test_classification_rejects_non_finite_values(
    value,
):
    with pytest.raises(
        ValueError,
        match="must be finite",
    ):
        classify_spread_compensation(
            value
        )


@pytest.mark.parametrize(
    "value",
    [
        "100",
        None,
        True,
        False,
    ],
)
def test_classification_rejects_non_numeric_values(
    value,
):
    with pytest.raises(
        TypeError,
        match="must be numeric",
    ):
        classify_spread_compensation(
            value
        )


def test_assessment_is_deterministic():
    first = assess_spread_compensation(
        security_yield_percent=5.35,
        benchmark_yield_percent=4.20,
    )

    second = assess_spread_compensation(
        security_yield_percent=5.35,
        benchmark_yield_percent=4.20,
    )

    assert first == second
