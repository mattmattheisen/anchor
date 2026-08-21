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

The runner prints a concise human-readable summary first,
followed by the complete JSON output for auditability.
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
    Convert RegimeAssessment into a plain dictionary.
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


def _format_optional_percent(
    value,
) -> str:
    """
    Format an optional percentage value for display.
    """

    if value is None:
        return "N/A"

    return f"{value:.2f}%"


def print_market_summary(
    market_data,
) -> None:
    """
    Print Anchor's live market-data snapshot.
    """

    print()
    print("LIVE MARKET SUMMARY")
    print("-------------------")

    print(
        f"Fed Funds: "
        f"{market_data.fed_funds_rate:.2f}%"
    )

    print(
        f"2Y Treasury: "
        f"{market_data.treasury_2y:.2f}%"
    )

    print(
        f"10Y Treasury: "
        f"{market_data.treasury_10y:.2f}%"
    )

    print(
        f"10Y Real Yield: "
        f"{market_data.real_yield_10y:.2f}%"
    )

    print(
        f"10Y Breakeven: "
        f"{market_data.breakeven_10y:.2f}%"
    )

    print(
        f"IG Credit Spread: "
        f"{market_data.credit_spread_ig_bps:.0f} bps"
    )

    print(
        "Unemployment Rate: "
        f"{_format_optional_percent(
            market_data.unemployment_rate
        )}"
    )

    print()
    print("30-DAY MARKET CHANGES")
    print("---------------------")

    print(
        f"2Y Treasury: "
        f"{market_data.treasury_2y_change_bps:+.0f} bps"
    )

    print(
        f"10Y Treasury: "
        f"{market_data.treasury_10y_change_bps:+.0f} bps"
    )

    print(
        f"10Y Real Yield: "
        f"{market_data.real_yield_10y_change_bps:+.0f} bps"
    )

    print(
        f"10Y Breakeven: "
        f"{market_data.breakeven_10y_change_bps:+.0f} bps"
    )

    print(
        f"IG Credit Spread: "
        f"{market_data.credit_spread_ig_change_bps:+.0f} bps"
    )

    if (
        market_data.unemployment_rate_change_pct
        is not None
    ):
        print(
            "Latest Unemployment Change: "
            f"{market_data.unemployment_rate_change_pct:+.2f}%"
        )


def print_regime_summary(
    regime,
) -> None:
    """
    Print the regime generated from live market data.
    """

    print()
    print("ANCHOR REGIME")
    print("-------------")

    print(
        f"Policy: {regime.policy}"
    )

    print(
        f"Growth: {regime.growth}"
    )

    print(
        f"Inflation: {regime.inflation}"
    )

    print(
        f"Real Rates: {regime.real_rates}"
    )

    print(
        f"Term Premium: {regime.term_premium}"
    )

    print(
        f"Credit: {regime.credit}"
    )

    print(
        f"Dominant Driver: "
        f"{regime.dominant_driver}"
    )

    print(
        f"Confidence: "
        f"{regime.confidence}"
    )


def print_decision_summary(
    decision,
) -> None:
    """
    Print the most important fields from Anchor's decision.
    """

    print()
    print("ANCHOR DECISION")
    print("---------------")

    top = decision[
        "top_opportunity"
    ]

    print(
        f"Headline: "
        f"{decision['headline']}"
    )

    print(
        f"Top Opportunity: "
        f"{top['maturity_years']}-year "
        f"{top['security_type']}"
    )

    print(
        f"Classification: "
        f"{top['classification']}"
    )

    selected = decision[
        "selected_opportunities"
    ]

    if selected:
        first = selected[0]

        print(
            f"Stated Yield: "
            f"{first['stated_yield_percent']:.2f}%"
        )

        print(
            f"Risk Penalty: "
            f"{first['total_risk_penalty_bps']:.0f} bps"
        )

        print(
            f"Risk-Adjusted Yield: "
            f"{first['risk_adjusted_yield_percent']:.2f}%"
        )

    posture = decision[
        "portfolio_posture"
    ]

    print()
    print("PORTFOLIO POSTURE")
    print("-----------------")

    print(
        f"Duration: "
        f"{posture['duration']}"
    )

    print(
        f"Credit: "
        f"{posture['credit']}"
    )

    print(
        f"Inflation: "
        f"{posture['inflation']}"
    )

    print(
        f"Liquidity: "
        f"{posture['liquidity']}"
    )


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

    parser.add_argument(
        "--json-only",
        action="store_true",
        help=(
            "Suppress the human-readable summary and print "
            "only JSON."
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

    if not args.json_only:
        print_market_summary(
            market_data
        )

        print_regime_summary(
            regime
        )

        print_decision_summary(
            decision
        )

        print()
        print("FULL JSON OUTPUT")
        print("----------------")

    print(
        json.dumps(
            output,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
