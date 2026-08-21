"""
Run Anchor using live FRED market data and fixed-income
opportunities supplied through CSV.

This script demonstrates Anchor's complete v1.1
data-driven decision path:

    FRED
      ↓
    MarketDataSnapshot
      ↓
    deterministic RegimeAssessment
      ↓
    Anchor

and:

    CSV
      ↓
    FixedIncomeOpportunity objects
      ↓
    Anchor

The decision engine itself remains unchanged.
"""

import argparse
import json

from engine.fred_collector import (
    FREDDataError,
    collect_fred_market_data,
)
from engine.market_data import (
    market_data_to_dict,
)
from engine.opportunity_import import (
    load_opportunities_from_csv,
)
from engine.regime_builder import (
    build_regime_from_market_data,
)
from engine.service import run_anchor


def regime_to_dict(
    regime,
):
    """
    Convert RegimeAssessment into a plain dictionary for
    display alongside Anchor's decision output.
    """

    return {
        "policy": regime.policy,
        "growth": regime.growth,
        "inflation": regime.inflation,
        "real_rates": regime.real_rates,
        "term_premium": regime.term_premium,
        "credit": regime.credit,
        "dominant_driver": regime.dominant_driver,
        "confidence": regime.confidence,
    }


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Run Anchor using live FRED market data and "
            "fixed-income opportunities loaded from CSV."
        )
    )

    parser.add_argument(
        "csv_file",
        help=(
            "Path to the CSV file containing fixed-income "
            "opportunities."
        ),
    )

    parser.add_argument(
        "--max-selections",
        type=int,
        default=3,
        help=(
            "Maximum number of ranked opportunities to "
            "include in the result. Default: 3."
        ),
    )

    args = parser.parse_args()

    opportunities = (
        load_opportunities_from_csv(
            args.csv_file
        )
    )

    try:
        market_data = (
            collect_fred_market_data()
        )

    except FREDDataError as exc:
        raise SystemExit(
            f"Unable to build live Anchor regime: {exc}"
        ) from exc

    regime = (
        build_regime_from_market_data(
            market_data
        )
    )

    decision = run_anchor(
        opportunities=opportunities,
        regime=regime,
        max_selections=args.max_selections,
    )

    output = {
        "market_data": (
            market_data_to_dict(
                market_data
            )
        ),
        "regime": (
            regime_to_dict(
                regime
            )
        ),
        "decision": decision,
    }

    print(
        json.dumps(
            output,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
