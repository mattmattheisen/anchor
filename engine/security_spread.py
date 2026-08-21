"""
Automatic spread-compensation assessment for production
SecurityData records.

This module combines:

    SecurityData
        ↓
    remaining maturity
        ↓
    Treasury benchmark selection
        ↓
    spread calculation
        ↓
    deterministic compensation classification

The result can be passed directly into Anchor's existing
FixedIncomeOpportunity workflow without requiring a human
to pre-label spread compensation.
"""

from dataclasses import dataclass
from datetime import date

from engine.market_data import MarketDataSnapshot
from engine.security_adapter import (
    calculate_maturity_years,
)
from engine.security_data import (
    SecurityData,
    validate_security_data,
)
from engine.spread_calculator import (
    SpreadAssessment,
    assess_spread_compensation,
)
from engine.treasury_benchmark import (
    TreasuryBenchmark,
    select_treasury_benchmark,
)


@dataclass(frozen=True)
class SecuritySpreadAssessment:
    """
    Complete spread assessment for one production security.
    """

    security_type: str
    maturity_years: float

    benchmark: TreasuryBenchmark
    spread: SpreadAssessment


def assess_security_spread(
    security: SecurityData,
    market_data: MarketDataSnapshot,
    as_of_date: date,
) -> SecuritySpreadAssessment:
    """
    Derive spread compensation for one production security.

    Treasury and TIPS securities are treated specially:

        TREASURY
            benchmark spread = 0 bps
            compensation = MODERATE

        TIPS
            benchmark spread = 0 bps
            compensation = MODERATE

    Corporate bonds and CDs are compared to the selected
    Treasury benchmark using current yield to maturity.
    """

    validate_security_data(
        security
    )

    if not isinstance(
        market_data,
        MarketDataSnapshot,
    ):
        raise TypeError(
            "market_data must be a MarketDataSnapshot."
        )

    if not isinstance(
        as_of_date,
        date,
    ):
        raise TypeError(
            "as_of_date must be a date."
        )

    maturity_years = (
        calculate_maturity_years(
            maturity_date=security.maturity_date,
            as_of_date=as_of_date,
        )
    )

    benchmark = (
        select_treasury_benchmark(
            maturity_years=maturity_years,
            market_data=market_data,
        )
    )

    if security.security_type in {
        "TREASURY",
        "TIPS",
    }:
        spread = SpreadAssessment(
            security_yield_percent=(
                security.yield_to_maturity_percent
            ),
            benchmark_yield_percent=(
                security.yield_to_maturity_percent
            ),
            spread_bps=0.0,
            compensation="MODERATE",
        )

        return SecuritySpreadAssessment(
            security_type=(
                security.security_type
            ),
            maturity_years=maturity_years,
            benchmark=benchmark,
            spread=spread,
        )

    spread = (
        assess_spread_compensation(
            security_yield_percent=(
                security.yield_to_maturity_percent
            ),
            benchmark_yield_percent=(
                benchmark.benchmark_yield_percent
            ),
        )
    )

    return SecuritySpreadAssessment(
        security_type=security.security_type,
        maturity_years=maturity_years,
        benchmark=benchmark,
        spread=spread,
    )
