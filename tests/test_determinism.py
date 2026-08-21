"""
Determinism and invariant tests for Anchor.

These tests verify that Anchor produces stable output for
identical inputs and preserves key internal relationships
across repeated runs.

The goal is to prove that Anchor behaves like a deterministic
decision system.
"""

import copy
import json

from engine.models import FixedIncomeOpportunity
from engine.regime import RegimeAssessment
from engine.service import run_anchor


def make_regime():
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


def make_opportunities():
    return [
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


def test_identical_inputs_produce_identical_outputs():
    opportunities = make_opportunities()
    regime = make_regime()

    first = run_anchor(
        opportunities=opportunities,
        regime=regime,
        max_selections=3,
    )

    second = run_anchor(
        opportunities=opportunities,
        regime=regime,
        max_selections=3,
    )

    assert first == second


def test_identical_inputs_produce_identical_json():
    opportunities = make_opportunities()
    regime = make_regime()

    first = run_anchor(
        opportunities=opportunities,
        regime=regime,
        max_selections=3,
    )

    second = run_anchor(
        opportunities=opportunities,
        regime=regime,
        max_selections=3,
    )

    first_json = json.dumps(
        first,
        sort_keys=True,
    )

    second_json = json.dumps(
        second,
        sort_keys=True,
    )

    assert first_json == second_json


def test_repeated_runs_do_not_mutate_opportunity_inputs():
    opportunities = make_opportunities()
    original = copy.deepcopy(
        opportunities
    )

    run_anchor(
        opportunities=opportunities,
        regime=make_regime(),
        max_selections=3,
    )

    assert opportunities == original


def test_repeated_runs_do_not_mutate_regime_input():
    regime = make_regime()
    original = copy.deepcopy(
        regime
    )

    run_anchor(
        opportunities=make_opportunities(),
        regime=regime,
        max_selections=3,
    )

    assert regime == original


def test_top_opportunity_matches_first_selected_opportunity():
    result = run_anchor(
        opportunities=make_opportunities(),
        regime=make_regime(),
        max_selections=3,
    )

    top = result["top_opportunity"]
    first = result[
        "selected_opportunities"
    ][0]

    assert (
        top["security_type"]
        == first["security_type"]
    )

    assert (
        top["maturity_years"]
        == first["maturity_years"]
    )

    assert (
        top["classification"]
        == first["classification"]
    )


def test_selected_opportunities_are_rank_ordered():
    result = run_anchor(
        opportunities=make_opportunities(),
        regime=make_regime(),
        max_selections=5,
    )

    ranks = [
        item["rank"]
        for item in result[
            "selected_opportunities"
        ]
    ]

    assert ranks == sorted(ranks)


def test_ranks_are_unique():
    result = run_anchor(
        opportunities=make_opportunities(),
        regime=make_regime(),
        max_selections=5,
    )

    ranks = [
        item["rank"]
        for item in result[
            "selected_opportunities"
        ]
    ]

    assert len(ranks) == len(set(ranks))


def test_rank_sequence_starts_at_one():
    result = run_anchor(
        opportunities=make_opportunities(),
        regime=make_regime(),
        max_selections=5,
    )

    ranks = [
        item["rank"]
        for item in result[
            "selected_opportunities"
        ]
    ]

    assert ranks[0] == 1


def test_max_selections_only_limits_output_count():
    full = run_anchor(
        opportunities=make_opportunities(),
        regime=make_regime(),
        max_selections=5,
    )

    limited = run_anchor(
        opportunities=make_opportunities(),
        regime=make_regime(),
        max_selections=2,
    )

    assert (
        limited["selected_opportunities"]
        == full["selected_opportunities"][:2]
    )


def test_max_selections_does_not_change_top_opportunity():
    one = run_anchor(
        opportunities=make_opportunities(),
        regime=make_regime(),
        max_selections=1,
    )

    five = run_anchor(
        opportunities=make_opportunities(),
        regime=make_regime(),
        max_selections=5,
    )

    assert (
        one["top_opportunity"]
        == five["top_opportunity"]
    )


def test_risk_adjusted_yield_matches_penalty_math():
    result = run_anchor(
        opportunities=make_opportunities(),
        regime=make_regime(),
        max_selections=5,
    )

    for item in result[
        "selected_opportunities"
    ]:
        expected = (
            item["stated_yield_percent"]
            - (
                item["total_risk_penalty_bps"]
                / 100.0
            )
        )

        assert (
            round(
                item[
                    "risk_adjusted_yield_percent"
                ],
                10,
            )
            == round(
                expected,
                10,
            )
        )


def test_callable_bond_has_higher_penalty_than_identical_non_callable():
    result = run_anchor(
        opportunities=make_opportunities(),
        regime=make_regime(),
        max_selections=5,
    )

    corporates = [
        item
        for item in result[
            "selected_opportunities"
        ]
        if (
            item["security_type"]
            == "CORPORATE"
            and item["maturity_years"]
            == 5.0
        )
    ]

    non_callable = next(
        item
        for item in corporates
        if item["callable"] is False
    )

    callable_bond = next(
        item
        for item in corporates
        if item["callable"] is True
    )

    assert (
        callable_bond[
            "total_risk_penalty_bps"
        ]
        > non_callable[
            "total_risk_penalty_bps"
        ]
    )


def test_callable_bond_has_lower_adjusted_yield_than_identical_non_callable():
    result = run_anchor(
        opportunities=make_opportunities(),
        regime=make_regime(),
        max_selections=5,
    )

    corporates = [
        item
        for item in result[
            "selected_opportunities"
        ]
        if (
            item["security_type"]
            == "CORPORATE"
            and item["maturity_years"]
            == 5.0
        )
    ]

    non_callable = next(
        item
        for item in corporates
        if item["callable"] is False
    )

    callable_bond = next(
        item
        for item in corporates
        if item["callable"] is True
    )

    assert (
        callable_bond[
            "risk_adjusted_yield_percent"
        ]
        < non_callable[
            "risk_adjusted_yield_percent"
        ]
    )


def test_schema_version_is_stable_across_runs():
    first = run_anchor(
        opportunities=make_opportunities(),
        regime=make_regime(),
    )

    second = run_anchor(
        opportunities=make_opportunities(),
        regime=make_regime(),
    )

    assert first["schema_version"] == "1.0"
    assert second["schema_version"] == "1.0"


def test_public_output_key_order_is_stable():
    first = run_anchor(
        opportunities=make_opportunities(),
        regime=make_regime(),
    )

    second = run_anchor(
        opportunities=make_opportunities(),
        regime=make_regime(),
    )

    assert list(first.keys()) == list(
        second.keys()
    )
