import pytest

from engine.opportunity import OpportunityAssessment
from engine.ranking import (
    opportunity_score,
    rank_opportunities,
    top_opportunity,
)


def make_assessment(
    security_type,
    maturity_years,
    yield_percent,
    classification,
    regime_fit,
    spread_compensation,
    rating=None,
):
    return OpportunityAssessment(
        security_type=security_type,
        maturity_years=maturity_years,
        yield_percent=yield_percent,
        rating=rating,
        spread_compensation=spread_compensation,
        regime_fit=regime_fit,
        classification=classification,
        explanation=f"{security_type} test assessment.",
    )


def test_opportunity_score():
    assessment = make_assessment(
        security_type="TREASURY",
        maturity_years=2.0,
        yield_percent=4.20,
        classification="FAVORABLE",
        regime_fit="FAVORABLE",
        spread_compensation="MODERATE",
    )

    assert opportunity_score(assessment) == 28.0


def test_attractive_scores_above_favorable():
    attractive = make_assessment(
        security_type="TIPS",
        maturity_years=5.0,
        yield_percent=2.10,
        classification="ATTRACTIVE",
        regime_fit="FAVORABLE",
        spread_compensation="HIGH",
    )

    favorable = make_assessment(
        security_type="TREASURY",
        maturity_years=2.0,
        yield_percent=4.20,
        classification="FAVORABLE",
        regime_fit="FAVORABLE",
        spread_compensation="MODERATE",
    )

    assert opportunity_score(attractive) > opportunity_score(favorable)


def test_rank_opportunities_highest_score_first():
    assessments = [
        make_assessment(
            security_type="CORPORATE",
            maturity_years=5.0,
            yield_percent=5.30,
            classification="SELECTIVE",
            regime_fit="CAUTIOUS",
            spread_compensation="HIGH",
            rating="A",
        ),
        make_assessment(
            security_type="TREASURY",
            maturity_years=2.0,
            yield_percent=4.20,
            classification="FAVORABLE",
            regime_fit="FAVORABLE",
            spread_compensation="MODERATE",
        ),
        make_assessment(
            security_type="TREASURY",
            maturity_years=30.0,
            yield_percent=5.20,
            classification="AVOID",
            regime_fit="UNFAVORABLE",
            spread_compensation="HIGH",
        ),
    ]

    ranked = rank_opportunities(assessments)

    assert ranked[0].security_type == "TREASURY"
    assert ranked[0].maturity_years == 2.0
    assert ranked[0].score == 28.0

    assert ranked[1].security_type == "CORPORATE"
    assert ranked[1].score == 21.0

    assert ranked[2].maturity_years == 30.0
    assert ranked[2].score == -1.0


def test_rank_numbers_are_sequential():
    assessments = [
        make_assessment(
            "TREASURY",
            2.0,
            4.20,
            "FAVORABLE",
            "FAVORABLE",
            "MODERATE",
        ),
        make_assessment(
            "CORPORATE",
            5.0,
            5.30,
            "SELECTIVE",
            "CAUTIOUS",
            "HIGH",
        ),
        make_assessment(
            "TIPS",
            5.0,
            2.10,
            "ATTRACTIVE",
            "FAVORABLE",
            "HIGH",
        ),
    ]

    ranked = rank_opportunities(assessments)

    assert [item.rank for item in ranked] == [1, 2, 3]


def test_tie_breaker_prefers_higher_yield():
    low_yield = make_assessment(
        "TREASURY",
        5.0,
        4.40,
        "NEUTRAL",
        "NEUTRAL",
        "MODERATE",
    )

    high_yield = make_assessment(
        "CD",
        5.0,
        4.60,
        "NEUTRAL",
        "NEUTRAL",
        "MODERATE",
    )

    ranked = rank_opportunities(
        [low_yield, high_yield]
    )

    assert ranked[0].security_type == "CD"


def test_tie_breaker_prefers_shorter_maturity():
    longer = make_assessment(
        "TREASURY",
        7.0,
        4.50,
        "NEUTRAL",
        "NEUTRAL",
        "MODERATE",
    )

    shorter = make_assessment(
        "TREASURY",
        5.0,
        4.50,
        "NEUTRAL",
        "NEUTRAL",
        "MODERATE",
    )

    ranked = rank_opportunities(
        [longer, shorter]
    )

    assert ranked[0].maturity_years == 5.0


def test_final_tie_breaker_is_alphabetical():
    treasury = make_assessment(
        "TREASURY",
        5.0,
        4.50,
        "NEUTRAL",
        "NEUTRAL",
        "MODERATE",
    )

    agency = make_assessment(
        "AGENCY",
        5.0,
        4.50,
        "NEUTRAL",
        "NEUTRAL",
        "MODERATE",
    )

    ranked = rank_opportunities(
        [treasury, agency]
    )

    assert ranked[0].security_type == "AGENCY"


def test_empty_rankings_return_empty_list():
    assert rank_opportunities([]) == []


def test_top_opportunity():
    assessments = [
        make_assessment(
            "CORPORATE",
            5.0,
            5.30,
            "SELECTIVE",
            "CAUTIOUS",
            "HIGH",
        ),
        make_assessment(
            "TREASURY",
            2.0,
            4.20,
            "FAVORABLE",
            "FAVORABLE",
            "MODERATE",
        ),
    ]

    result = top_opportunity(assessments)

    assert result.security_type == "TREASURY"
    assert result.maturity_years == 2.0


def test_top_opportunity_rejects_empty_input():
    with pytest.raises(
        ValueError,
        match="No fixed-income opportunities were supplied",
    ):
        top_opportunity([])


def test_unknown_labels_do_not_crash_scoring():
    assessment = make_assessment(
        security_type="BANANA_BOND",
        maturity_years=5.0,
        yield_percent=9.99,
        classification="MYSTERY",
        regime_fit="WHAT",
        spread_compensation="WHO_KNOWS",
    )

    assert opportunity_score(assessment) == 0.0
