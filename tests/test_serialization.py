import json

from engine.pipeline import PipelineOpportunityResult
from engine.report import DecisionReport
from engine.serialization import (
    serialize_decision_report,
    serialize_opportunity,
)


def make_opportunity():
    return PipelineOpportunityResult(
        rank=1,
        security_type="CORPORATE",
        maturity_years=5.0,
        stated_yield_percent=5.30,
        rating="A",
        callable=True,
        spread_compensation="HIGH",
        regime_fit="NEUTRAL",
        classification="ATTRACTIVE",
        risk_level="ELEVATED",
        total_risk_penalty_bps=95.0,
        risk_adjusted_yield_percent=4.35,
        ranking_score=33.0,
        explanation="Test explanation.",
    )


def make_report():
    opportunity = make_opportunity()

    return DecisionReport(
        headline="Anchor ranks the 5-year CORPORATE first.",
        recommendation="Favor the highest-ranked opportunity.",
        duration_posture="SHORT",
        credit_posture="SELECTIVE",
        inflation_posture="HEDGE",
        liquidity_posture="NORMAL",
        preferred_exposures=[
            "SHORT_INTERMEDIATE_TREASURIES",
            "TIPS",
        ],
        exposures_to_limit=[
            "LONG_DURATION_NOMINAL_BONDS",
        ],
        top_security_type="CORPORATE",
        top_maturity_years=5.0,
        top_classification="ATTRACTIVE",
        selected_opportunities=[
            opportunity
        ],
        rationale=[
            "Test rationale.",
        ],
        cautions=[
            "The security is callable.",
        ],
    )


def test_serialize_opportunity_returns_dictionary():
    result = serialize_opportunity(
        make_opportunity()
    )

    assert isinstance(result, dict)


def test_serialize_opportunity_preserves_all_fields():
    result = serialize_opportunity(
        make_opportunity()
    )

    assert result["rank"] == 1
    assert result["security_type"] == "CORPORATE"
    assert result["maturity_years"] == 5.0
    assert result["stated_yield_percent"] == 5.30
    assert result["rating"] == "A"
    assert result["callable"] is True
    assert result["spread_compensation"] == "HIGH"
    assert result["regime_fit"] == "NEUTRAL"
    assert result["classification"] == "ATTRACTIVE"
    assert result["risk_level"] == "ELEVATED"
    assert result["total_risk_penalty_bps"] == 95.0
    assert result["risk_adjusted_yield_percent"] == 4.35
    assert result["ranking_score"] == 33.0
    assert result["explanation"] == "Test explanation."


def test_report_serialization_preserves_headline():
    result = serialize_decision_report(
        make_report()
    )

    assert result["headline"] == (
        "Anchor ranks the 5-year CORPORATE first."
    )


def test_report_serialization_preserves_recommendation():
    result = serialize_decision_report(
        make_report()
    )

    assert result["recommendation"] == (
        "Favor the highest-ranked opportunity."
    )


def test_report_serialization_builds_portfolio_posture():
    result = serialize_decision_report(
        make_report()
    )

    assert result["portfolio_posture"] == {
        "duration": "SHORT",
        "credit": "SELECTIVE",
        "inflation": "HEDGE",
        "liquidity": "NORMAL",
    }


def test_report_serialization_builds_top_opportunity():
    result = serialize_decision_report(
        make_report()
    )

    assert result["top_opportunity"] == {
        "security_type": "CORPORATE",
        "maturity_years": 5.0,
        "classification": "ATTRACTIVE",
    }


def test_report_serialization_contains_selected_opportunities():
    result = serialize_decision_report(
        make_report()
    )

    assert len(
        result["selected_opportunities"]
    ) == 1

    opportunity = (
        result["selected_opportunities"][0]
    )

    assert opportunity["security_type"] == "CORPORATE"
    assert opportunity["callable"] is True
    assert (
        opportunity["risk_adjusted_yield_percent"]
        == 4.35
    )


def test_report_serialization_preserves_exposures():
    result = serialize_decision_report(
        make_report()
    )

    assert result["preferred_exposures"] == [
        "SHORT_INTERMEDIATE_TREASURIES",
        "TIPS",
    ]

    assert result["exposures_to_limit"] == [
        "LONG_DURATION_NOMINAL_BONDS",
    ]


def test_report_serialization_preserves_rationale_and_cautions():
    result = serialize_decision_report(
        make_report()
    )

    assert result["rationale"] == [
        "Test rationale.",
    ]

    assert result["cautions"] == [
        "The security is callable.",
    ]


def test_serialized_report_can_be_encoded_as_json():
    result = serialize_decision_report(
        make_report()
    )

    encoded = json.dumps(result)

    assert isinstance(encoded, str)
    assert "CORPORATE" in encoded


def test_serialization_uses_plain_python_types():
    result = serialize_decision_report(
        make_report()
    )

    assert isinstance(result, dict)
    assert isinstance(
        result["portfolio_posture"],
        dict,
    )
    assert isinstance(
        result["selected_opportunities"],
        list,
    )
    assert isinstance(
        result["selected_opportunities"][0],
        dict,
    )


def test_empty_selected_opportunities_serialize_cleanly():
    report = make_report()

    report.selected_opportunities = []
    report.top_security_type = None
    report.top_maturity_years = None
    report.top_classification = None

    result = serialize_decision_report(
        report
    )

    assert result["selected_opportunities"] == []

    assert result["top_opportunity"] == {
        "security_type": None,
        "maturity_years": None,
        "classification": None,
    }


def test_serialized_lists_are_independent_copies():
    report = make_report()

    result = serialize_decision_report(
        report
    )

    result["preferred_exposures"].append(
        "TEST_EXPOSURE"
    )

    result["rationale"].append(
        "TEST_RATIONALE"
    )

    assert (
        "TEST_EXPOSURE"
        not in report.preferred_exposures
    )

    assert (
        "TEST_RATIONALE"
        not in report.rationale
    )
