"""
Runnable demonstration of Anchor's public service interface.

This script constructs a small fixed-income opportunity set,
runs the complete Anchor decision process, and prints the
final JSON-compatible result.

It is intended as a simple example for developers and
future interface integrations.
"""

import json

from engine.models import FixedIncomeOpportunity
from engine.regime import RegimeAssessment
from engine.service import run_anchor


def main():
    regime = RegimeAssessment(
        policy="NEUTRAL",
        growth="NEUTRAL",
        inflation="STABLE",
        real_rates="STABLE",
        term_premium="NEUTRAL",
        credit="BENIGN",
        dominant_driver="MIXED",
        confidence="MEDIUM",
    )

    opportunities = [
        (
            FixedIncomeOpportunity(
                security_type="TREASURY",
                maturity_years=2.0,
                yield_percent=4.20,
            ),
            "MODERATE",
        ),
        (
            FixedIncomeOpportunity(
                security_type="TREASURY",
                maturity_years=5.0,
                yield_percent=4.35,
            ),
            "MODERATE",
        ),
        (
            FixedIncomeOpportunity(
                security_type="TIPS",
                maturity_years=5.0,
                yield_percent=2.10,
            ),
            "MODERATE",
        ),
        (
            FixedIncomeOpportunity(
                security_type="CORPORATE",
                maturity_years=5.0,
                yield_percent=5.30,
                rating="A",
                callable=False,
            ),
            "HIGH",
        ),
        (
            FixedIncomeOpportunity(
                security_type="CORPORATE",
                maturity_years=5.0,
                yield_percent=5.30,
                rating="A",
                callable=True,
            ),
            "HIGH",
        ),
    ]

    result = run_anchor(
        opportunities=opportunities,
        regime=regime,
        max_selections=3,
    )

    print(
        json.dumps(
            result,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
