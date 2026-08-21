"""
Production-shaped Anchor runner.

This script combines:

    live FRED market data
        ↓
    deterministic regime construction

with:

    production fixed-income security CSV
        ↓
    SecurityData
        ↓
    FixedIncomeOpportunity

and sends both into Anchor's deterministic decision engine.

This is not a broker integration.

The security CSV remains an explicit input file so that
market-security data can be inspected and audited before
Anchor evaluates it.
"""

import argparse
import json
from datetime import date

from engine.fred_collector import (
    FREDDataError,
    collect_fred_market_data,
)
from engine.market_data import (
    market_data_to_dict,
)
from engine.regime_builder import (
    build_regime_from_market_data,
)
from engine.security_adapter import (
    security_data_to_opportunity,
)
from engine.security_data import (
    security_data_to_dict,
)
from engine.security_import import (
    load_security_data_from_csv,
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


def print_market_summary(
    market_data,
) -> None:
    """
    Print the live market environment.
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

    if market_data.unemployment_rate is not None:
        print(
            f"Unemployment Rate: "
            f"{market_data.unemployment_rate:.2f}%"
        )


def print_regime_summary(
    regime,
) -> None:
    """
    Print Anchor's deterministic regime assessment.
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


def print_security_summary(
    imported_securities,
) -> None:
    """
    Print the production securities supplied to Anchor.
    """

    print()
    print("SECURITIES LOADED")
    print("-----------------")

    for index, item in enumerate(
        imported_securities,
        start=1,
    ):
        security, spread = item

        identifier = (
            security.cusip
            or "NO-CUSIP"
        )

        issuer = (
            security.issuer
            or "Unknown issuer"
        )

        print(
            f"{index}. "
            f"{security.security_type} | "
            f"{identifier} | "
            f"{issuer}"
        )

        print(
            f"   Maturity: "
            f"{security.maturity_date.isoformat()} | "
            f"YTM: "
            f"{security.yield_to_maturity_percent:.2f}% | "
            f"Spread Compensation: {spread}"
        )

        if security.rating is not None:
            print(
                f"   Rating: "
                f"{security.rating}"
            )

        if security.callable:
            call_text = (
                security.call_date.isoformat()
                if security.call_date is not None
                else "unspecified"
            )

            print(
                f"   Callable: YES | "
                f"Call Date: {call_text}"
            )


def print_decision_summary(
    decision,
) -> None:
    """
    Print Anchor's primary decision output.
    """

    print()
    print("ANCHOR DECISION")
    print("---------------")

    print(
        f"Headline: "
        f"{decision['headline']}"
    )

    top = decision[
        "top_opportunity"
    ]

    if top is None:
        print(
            "Top Opportunity: NONE"
        )

    else:
        print(
            f"Top Opportunity: "
            f"{top['maturity_years']:.2f}-year "
            f"{top['security_type']}"
        )

        print(
            f"Classification: "
            f"{top['classification']}"
        )

    print()
    print("SELECTED OPPORTUNITIES")
    print("----------------------")

    for index, opportunity in enumerate(
        decision["selected_opportunities"],
        start=1,
    ):
        print(
            f"{index}. "
            f"{opportunity['maturity_years']:.2f}-year "
            f"{opportunity['security_type']}"
        )

        print(
            f"   Stated Yield: "
            f"{opportunity['stated_yield_percent']:.2f}%"
        )

        print(
            f"   Risk Penalty: "
            f"{opportunity['total_risk_penalty_bps']:.0f} bps"
        )

        print(
            f"   Risk-Adjusted Yield: "
            f"{opportunity['risk_adjusted_yield_percent']:.2f}%"
        )

        print(
            f"   Classification: "
            f"{opportunity['classification']}"
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
            "production-shaped fixed-income security data."
        )
    )

    parser.add_argument(
        "csv_file",
        help=(
            "Path to the production security CSV file."
        ),
    )

    parser.add_argument(
        "--max-selections",
        type=int,
        default=3,
        help=(
            "Maximum number of opportunities to select. "
            "Default: 3."
        ),
    )

    parser.add_argument(
        "--as-of-date",
        type=date.fromisoformat,
        default=None,
        help=(
            "Explicit YYYY-MM-DD date used to calculate "
            "years to maturity. Default: today's date."
        ),
    )

    output_group = (
        parser.add_mutually_exclusive_group()
    )

    output_group.add_argument(
        "--json-only",
        action="store_true",
        help=(
            "Print only machine-readable JSON."
        ),
    )

    output_group.add_argument(
        "--summary-only",
        action="store_true",
        help=(
            "Print only the human-readable summary."
        ),
    )

    args = parser.parse_args()

    as_of_date = (
        args.as_of_date
        or date.today()
    )

    imported_securities = (
        load_security_data_from_csv(
            args.csv_file
        )
    )

    opportunities = []

    for security, spread_compensation in (
        imported_securities
    ):
        opportunities.append(
            security_data_to_opportunity(
                security=security,
                spread_compensation=(
                    spread_compensation
                ),
                as_of_date=as_of_date,
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
        "as_of_date": (
            as_of_date.isoformat()
        ),
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
        "securities": [
            {
                "security": (
                    security_data_to_dict(
                        security
                    )
                ),
                "spread_compensation": spread,
            }
            for security, spread
            in imported_securities
        ],
        "decision": decision,
    }

    if args.json_only:
        print(
            json.dumps(
                output,
                indent=2,
            )
        )

        return

    print()
    print(
        "ANCHOR PRODUCTION RUN"
    )
    print(
        "====================="
    )

    print(
        f"As Of: "
        f"{as_of_date.isoformat()}"
    )

    print_market_summary(
        market_data
    )

    print_regime_summary(
        regime
    )

    print_security_summary(
        imported_securities
    )

    print_decision_summary(
        decision
    )

    if args.summary_only:
        return

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
