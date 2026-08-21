"""
Deterministic Treasury benchmark selection for Anchor.

This module selects the Treasury yield used as the
comparison benchmark for a fixed-income security.

The first production implementation uses Anchor's current
live Treasury inputs:

    2-year Treasury
    10-year Treasury

and selects between them based on the security's remaining
maturity.

This is intentionally simple and explicit.

Future versions can extend the benchmark curve with
additional Treasury maturities without changing the spread
calculation interface.
"""

import math
from dataclasses import dataclass

from engine.market_data import MarketDataSnapshot


@dataclass(frozen=True)
class TreasuryBenchmark:
    """
    Selected Treasury benchmark for one security.
    """

    benchmark_name: str
    benchmark_maturity_years: float
    benchmark_yield_percent: float


SHORT_BENCHMARK_MAX_YEARS = 5.0


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


def select_treasury_benchmark(
    maturity_years: float,
    market_data: MarketDataSnapshot,
) -> TreasuryBenchmark:
    """
    Select the Treasury benchmark for a security.

    Initial rule:

        maturity <= 5 years
            use 2-year Treasury

        maturity > 5 years
            use 10-year Treasury

    This deliberately favors a small number of explicit
    benchmark buckets over interpolation in the first
    implementation.
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

    if maturity_years <= SHORT_BENCHMARK_MAX_YEARS:
        return TreasuryBenchmark(
            benchmark_name="2Y_TREASURY",
            benchmark_maturity_years=2.0,
            benchmark_yield_percent=(
                market_data.treasury_2y
            ),
        )

    return TreasuryBenchmark(
        benchmark_name="10Y_TREASURY",
        benchmark_maturity_years=10.0,
        benchmark_yield_percent=(
            market_data.treasury_10y
        ),
    )
