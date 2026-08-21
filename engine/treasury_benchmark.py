"""
Deterministic Treasury benchmark selection for Anchor.

This module selects or interpolates the Treasury yield used
as the comparison benchmark for a fixed-income security.

Anchor's current live Treasury curve includes:

    1-year
    2-year
    3-year
    5-year
    7-year
    10-year

For maturities that fall between available Treasury points,
Anchor uses linear interpolation.

If one or more optional Treasury points are unavailable,
the selector falls back to the remaining available points.

Maturities shorter than the shortest available point use
that shortest point.

Maturities longer than the longest available point use
that longest point.

This module does not calculate credit spreads and does not
rank securities.
"""

import math
from dataclasses import dataclass
from typing import List, Tuple

from engine.market_data import MarketDataSnapshot


@dataclass(frozen=True)
class TreasuryBenchmark:
    """
    Treasury benchmark selected for one security.

    benchmark_name:
        Human-readable description of the benchmark.

    benchmark_maturity_years:
        Security maturity being benchmarked when
        interpolation is used, or the Treasury maturity
        when an exact/end-point Treasury is used.

    benchmark_yield_percent:
        Selected or interpolated Treasury yield.
    """

    benchmark_name: str
    benchmark_maturity_years: float
    benchmark_yield_percent: float


CurvePoint = Tuple[
    float,
    float,
    str,
]


def _validate_maturity_years(
    maturity_years: float,
) -> None:
    """
    Validate remaining maturity.
    """

    if isinstance(
        maturity_years,
        bool,
    ):
        raise TypeError(
            "maturity_years must be numeric."
        )

    if not isinstance(
        maturity_years,
        (int, float),
    ):
        raise TypeError(
            "maturity_years must be numeric."
        )

    if not math.isfinite(
        float(maturity_years)
    ):
        raise ValueError(
            "maturity_years must be finite."
        )

    if maturity_years <= 0:
        raise ValueError(
            "maturity_years must be greater than 0."
        )


def _build_available_curve(
    market_data: MarketDataSnapshot,
) -> List[CurvePoint]:
    """
    Build the available nominal Treasury curve.

    Optional curve points that are None are excluded.

    The 2-year and 10-year points remain required by
    MarketDataSnapshot and therefore always participate.
    """

    points: List[
        CurvePoint
    ] = []

    raw_points = [
        (
            1.0,
            market_data.treasury_1y,
            "1Y_TREASURY",
        ),
        (
            2.0,
            market_data.treasury_2y,
            "2Y_TREASURY",
        ),
        (
            3.0,
            market_data.treasury_3y,
            "3Y_TREASURY",
        ),
        (
            5.0,
            market_data.treasury_5y,
            "5Y_TREASURY",
        ),
        (
            7.0,
            market_data.treasury_7y,
            "7Y_TREASURY",
        ),
        (
            10.0,
            market_data.treasury_10y,
            "10Y_TREASURY",
        ),
    ]

    for (
        maturity,
        yield_percent,
        name,
    ) in raw_points:
        if yield_percent is None:
            continue

        points.append(
            (
                maturity,
                yield_percent,
                name,
            )
        )

    points.sort(
        key=lambda item: item[0]
    )

    if not points:
        raise ValueError(
            "No Treasury curve points are available."
        )

    return points


def _interpolate_yield(
    target_maturity: float,
    lower_maturity: float,
    lower_yield: float,
    upper_maturity: float,
    upper_yield: float,
) -> float:
    """
    Linearly interpolate a Treasury yield.

    Formula:

        lower_yield
        +
        maturity_fraction
        *
        (
            upper_yield
            - lower_yield
        )
    """

    maturity_range = (
        upper_maturity
        - lower_maturity
    )

    if maturity_range <= 0:
        raise ValueError(
            "Treasury interpolation requires "
            "increasing maturities."
        )

    maturity_fraction = (
        target_maturity
        - lower_maturity
    ) / maturity_range

    return (
        lower_yield
        + maturity_fraction
        * (
            upper_yield
            - lower_yield
        )
    )


def select_treasury_benchmark(
    maturity_years: float,
    market_data: MarketDataSnapshot,
) -> TreasuryBenchmark:
    """
    Select or interpolate the Treasury benchmark for a
    security.

    Rules
    -----
    Exact maturity:
        Use the matching Treasury point.

    Between curve points:
        Linearly interpolate between adjacent Treasury
        yields.

    Below shortest curve point:
        Use the shortest available Treasury yield.

    Above longest curve point:
        Use the longest available Treasury yield.

    Missing optional curve points:
        Interpolate across the remaining available points.
    """

    _validate_maturity_years(
        maturity_years
    )

    if not isinstance(
        market_data,
        MarketDataSnapshot,
    ):
        raise TypeError(
            "market_data must be a MarketDataSnapshot."
        )

    curve = _build_available_curve(
        market_data
    )

    first_maturity, first_yield, first_name = (
        curve[0]
    )

    if maturity_years <= first_maturity:
        return TreasuryBenchmark(
            benchmark_name=first_name,
            benchmark_maturity_years=(
                first_maturity
            ),
            benchmark_yield_percent=(
                first_yield
            ),
        )

    last_maturity, last_yield, last_name = (
        curve[-1]
    )

    if maturity_years >= last_maturity:
        return TreasuryBenchmark(
            benchmark_name=last_name,
            benchmark_maturity_years=(
                last_maturity
            ),
            benchmark_yield_percent=(
                last_yield
            ),
        )

    for index in range(
        len(curve) - 1
    ):
        (
            lower_maturity,
            lower_yield,
            lower_name,
        ) = curve[index]

        (
            upper_maturity,
            upper_yield,
            upper_name,
        ) = curve[index + 1]

        if (
            maturity_years
            == lower_maturity
        ):
            return TreasuryBenchmark(
                benchmark_name=lower_name,
                benchmark_maturity_years=(
                    lower_maturity
                ),
                benchmark_yield_percent=(
                    lower_yield
                ),
            )

        if (
            maturity_years
            == upper_maturity
        ):
            return TreasuryBenchmark(
                benchmark_name=upper_name,
                benchmark_maturity_years=(
                    upper_maturity
                ),
                benchmark_yield_percent=(
                    upper_yield
                ),
            )

        if (
            lower_maturity
            < maturity_years
            < upper_maturity
        ):
            interpolated_yield = (
                _interpolate_yield(
                    target_maturity=(
                        maturity_years
                    ),
                    lower_maturity=(
                        lower_maturity
                    ),
                    lower_yield=(
                        lower_yield
                    ),
                    upper_maturity=(
                        upper_maturity
                    ),
                    upper_yield=(
                        upper_yield
                    ),
                )
            )

            benchmark_name = (
                f"INTERPOLATED_"
                f"{lower_name}_"
                f"{upper_name}"
            )

            return TreasuryBenchmark(
                benchmark_name=(
                    benchmark_name
                ),
                benchmark_maturity_years=(
                    maturity_years
                ),
                benchmark_yield_percent=(
                    interpolated_yield
                ),
            )

    raise RuntimeError(
        "Unable to select Treasury benchmark."
    )
