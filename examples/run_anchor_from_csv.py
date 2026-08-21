"""
Run Anchor using fixed-income opportunities loaded from CSV.

This script demonstrates the v1.1 opportunity-ingestion path:

    CSV file
        ↓
    CSV importer
        ↓
    FixedIncomeOpportunity objects
        ↓
    Anchor validation
        ↓
    run_anchor()
        ↓
    JSON decision output

The economic regime is still supplied explicitly here.
Automatic regime collection will be added separately.
"""

import argparse
import json

from engine.opportunity_import import (
    load_opportunities_from_csv,
)
from engine.regime import RegimeAssessment
from engine.service import run_anchor


def build_demo_regime() -> RegimeAssessment:
    """
    Build the temporary explicit regime used by this runner.

    This remains manual for now. A later v1.1 step will
    replace this with a data-driven regime builder.
    """

    return RegimeAssessment(
        policy="NEUTRAL",
        growth="NEUTRAL",
        inflation="STABLE",
        real_rates="STABLE",
        term_premium="NEUTRAL",
        credit="BENIGN",
        dominant_driver="MIXED",
        confidence="MEDIUM",
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Run Anchor using fixed-income opportunities "
            "loaded from a CSV file."
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

    opportunities = load_opportunities_from_csv(
        args.csv_file
    )

    regime = build_demo_regime()

    result = run_anchor(
        opportunities=opportunities,
        regime=regime,
        max_selections=args.max_selections,
    )

    print(
        json.dumps(
            result,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
