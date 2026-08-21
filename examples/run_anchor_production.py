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

The production runner also preserves the identity of the
original market security so Anchor's ranked output can be
traced back to:

    CUSIP
    issuer
    maturity date
    stated YTM
    rating
    callable status
    source

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


def build_security_lookup(
    imported_securities,
    as_of_date,
):
    """
    Build a lookup table linking Anchor opportunities back
    to their original production SecurityData records.

    The lookup key uses the fields currently retained by
    FixedIncomeOpportunity.

    A list is stored for each key because two different
    securities may legitimately have identical analytical
    characteristics.
    """

    lookup = {}

    for security, spread in imported_securities:
        opportunity, normalized_spread = (
            security_data_to_opportunity(
                security=security,
                spread_compensation=spread,
                as_of_date=as_of_date,
            )
        )

        key = (
            opportunity.security_type,
            round(
                opportunity.maturity_years,
                8,
            ),
            round(
                opportunity.yield_percent,
                8,
            ),
            opportunity.rating,
            opportunity.callable,
            normalized_spread,
        )

        lookup.setdefault(
            key,
            [],
        ).append(
            security
        )

    return lookup


def find_source_security(
    selected_opportunity,
    imported_securities,
    as_of_date,
):
    """
    Match one serialized Anchor opportunity back to the
    original SecurityData record.

    Matching uses the analytical fields preserved by
    Anchor's current FixedIncomeOpportunity model.

    If more than one production security has identical
    analytical characteristics, the first unmatched-like
    record is returned for display. Full production input
    remains available in JSON for auditability.
    """

    selected_type = (
        selected_opportunity[
            "security_type"
        ]
    )

    selected_maturity = (
        selected_opportunity[
            "maturity_years"
        ]
    )

    selected_yield = (
        selected_opportunity[
            "stated_yield_percent"
        ]
    )

    for security, spread in imported_securities:
        opportunity, _ = (
            security_data_to_opportunity(
                security=security,
                spread_compensation=spread,
                as_of_date=as_of_date,
            )
        )

        if (
            opportunity.security_type
            == selected_type
            and abs(
                opportunity.maturity_years
                - selected_maturity
            ) < 0.0001
            and abs(
                opportunity.yield_percent
                - selected_yield
            ) < 0.0001
            and opportunity.rating
            == selected_opportunity.get(
                "rating"
            )
            and opportunity.callable
            == selected_opportunity.get(
                "callable",
                False,
            )
        ):
            return security

    return None


def print_source_security(
    security,
) -> None:
    """
    Print the identity of one production security.
    """

    if security is None:
        print(
            "   Security Identity: "
            "Unable to match source record."
        )

        return

    print(
        f"   CUSIP: "
        f"{security.cusip or 'N/A'}"
    )

    print(
        f"   Issuer: "
        f"{security.issuer or 'N/A'}"
    )

    print(
        f"   Maturity Date: "
        f"{security.maturity_date.isoformat()}"
    )

    print(
        f"   Market YTM: "
        f"{security.yield_to_maturity_percent:.2f}%"
    )

    if security.coupon_percent is not None:
        print(
            f"   Coupon: "
            f"{security.coupon_percent:.2f}%"
        )

    if security.price is not None:
        print(
            f"   Price: "
            f"{security.price:.2f}"
        )

    if security.rating is not None:
        print(
            f"   Rating: "
            f"{security.rating}"
        )

    print(
        f"   Callable: "
        f"{'YES' if security.callable else 'NO'}"
    )

    if security.call_date is not None:
        print(
            f"   Call Date: "
            f"{security.call_date.isoformat()}"
        )

    if security.minimum_quantity is not None:
        print(
            f"   Minimum Quantity: "
            f"{security.minimum_quantity:.0f}"
        )

    if security.source is not None:
        print(
            f"   Source: "
            f"{security.source}"
        )


def print_decision_summary(
    decision,
    imported_securities,
    as_of_date,
) -> None:
    """
    Print Anchor's primary decision output together with
    the identity of the original production securities.
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

    selected = decision[
        "selected_opportunities"
    ]

    if top is None:
        print(
            "Top Opportunity: NONE"
        )

    else:
        print()
        print("TOP-RANKED SECURITY")
        print("-------------------")

        if selected:
            top_selected = selected[0]

            source_security = (
                find_source_security(
                    selected_opportunity=top_selected,
                    imported_securities=(
                        imported_securities
                    ),
                    as_of_date=as_of_date,
                )
            )

            print_source_security(
                source_security
            )

            print(
                f"   Anchor Classification: "
                f"{top_selected['classification']}"
            )

            print(
                f"   Stated Yield: "
                f"{top_selected['stated_yield_percent']:.2f}%"
            )

            print(
                f"   Risk Penalty: "
                f"{top_selected['total_risk_penalty_bps']:.0f} bps"
            )

            print(
                f"   Risk-Adjusted Yield: "
                f"{top_selected['risk_adjusted_yield_percent']:.2f}%"
            )

            print(
                f"   Ranking Score: "
                f"{top_selected['ranking_score']:.2f}"
            )

    print()
    print("SELECTED OPPORTUNITIES")
    print("----------------------")

    for index, opportunity in enumerate(
        selected,
        start=1,
    ):
        source_security = (
            find_source_security(
                selected_opportunity=opportunity,
                imported_securities=(
                    imported_securities
                ),
                as_of_date=as_of_date,
            )
        )

        print()
        print(
            f"{index}. "
            f"{opportunity['security_type']}"
        )

        print_source_security(
            source_security
        )

        print(
            f"   Classification: "
            f"{opportunity['classification']}"
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
            f"   Ranking Score: "
            f"{opportunity['ranking_score']:.2f}"
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
        decision=decision,
        imported_securities=(
            imported_securities
        ),
        as_of_date=as_of_date,
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
