from engine.pipeline import PipelineOpportunityResult
from engine.portfolio import PortfolioRecommendation
from engine.report import build_decision_report
from engine.summary import DecisionSummary


def make_opportunity(
    rank=1,
    security_type="TREASURY",
    maturity_years=2.0,
    classification="FAVORABLE",
    callable=False,
):
    return PipelineOpportunityResult(
        rank=rank,
        security_type=security_type,
        maturity_years=maturity_years,
        stated_yield_percent=4.20,
        rating=None,
        callable=callable,
        spread_compensation="MODERATE",
        regime_fit="FAVORABLE",
        classification=classification,
        risk_level="LOW",
        total_risk_penalty_bps=10.0,
        risk_adjusted_yield_percent=4.10,
        ranking_score=28.0,
        explanation="Test explanation.",
    )


def make_portfolio(
    opportunities=None,
):
    if opportunities is None:
        opportunities = [make_opportunity()]

    top = opportunities[0] if opportunities else None

    return PortfolioRecommendation(
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
        top_security_type=(
            top.security_type if top else None
        ),
        top_maturity_years=(
            top.maturity_years if top else None
        ),
        top_classification=(
            top.classification if top else None
        ),
        selected_opportunities=opportunities,
        rationale=[
            "Portfolio rationale.",
            "Shared rationale.",
        ],
    )


def make_summary():
    return DecisionSummary(
        headline="Anchor Fixed-Income Decision",
        recommendation="Favor shorter-duration exposure.",
        rationale=[
            "Summary rationale.",
            "Shared rationale.",
        ],
        cautions=[
            "Inflation remains elevated.",
            "Credit spreads should be monitored.",
        ],
    )


def test_report_preserves_headline():
    report = build_decision_report(
        make_portfolio(),
        make_summary(),
    )

    assert (
        report.headline
        == "Anchor Fixed-Income Decision"
    )


def test_report_preserves_recommendation():
    report = build_decision_report(
        make_portfolio(),
        make_summary(),
    )

    assert (
        report.recommendation
        == "Favor shorter-duration exposure."
    )


def test_report_preserves_portfolio_postures():
    report = build_decision_report(
        make_portfolio(),
        make_summary(),
    )

    assert report.duration_posture == "SHORT"
    assert report.credit_posture == "SELECTIVE"
    assert report.inflation_posture == "HEDGE"
    assert report.liquidity_posture == "NORMAL"


def test_report_preserves_preferred_exposures():
    report = build_decision_report(
        make_portfolio(),
        make_summary(),
    )

    assert (
        "SHORT_INTERMEDIATE_TREASURIES"
        in report.preferred_exposures
    )
    assert "TIPS" in report.preferred_exposures


def test_report_preserves_exposures_to_limit():
    report = build_decision_report(
        make_portfolio(),
        make_summary(),
    )

    assert (
        "LONG_DURATION_NOMINAL_BONDS"
        in report.exposures_to_limit
    )


def test_report_preserves_top_security_metadata():
    report = build_decision_report(
        make_portfolio(),
        make_summary(),
    )

    assert report.top_security_type == "TREASURY"
    assert report.top_maturity_years == 2.0
    assert report.top_classification == "FAVORABLE"


def test_report_preserves_selected_opportunities():
    opportunity = make_opportunity()

    portfolio = make_portfolio(
        [opportunity]
    )

    report = build_decision_report(
        portfolio,
        make_summary(),
    )

    assert len(report.selected_opportunities) == 1
    assert report.selected_opportunities[0] is opportunity


def test_report_combines_rationale():
    report = build_decision_report(
        make_portfolio(),
        make_summary(),
    )

    assert "Summary rationale." in report.rationale
    assert "Portfolio rationale." in report.rationale


def test_report_removes_duplicate_rationale():
    report = build_decision_report(
        make_portfolio(),
        make_summary(),
    )

    assert report.rationale.count(
        "Shared rationale."
    ) == 1


def test_report_preserves_rationale_order():
    report = build_decision_report(
        make_portfolio(),
        make_summary(),
    )

    assert report.rationale == [
        "Summary rationale.",
        "Shared rationale.",
        "Portfolio rationale.",
    ]


def test_report_preserves_cautions():
    report = build_decision_report(
        make_portfolio(),
        make_summary(),
    )

    assert report.cautions == [
        "Inflation remains elevated.",
        "Credit spreads should be monitored.",
    ]


def test_report_removes_duplicate_cautions():
    summary = DecisionSummary(
        headline="Test",
        recommendation="Test",
        rationale=[],
        cautions=[
            "Watch inflation.",
            "Watch inflation.",
        ],
    )

    report = build_decision_report(
        make_portfolio(),
        summary,
    )

    assert report.cautions == [
        "Watch inflation."
    ]


def test_report_handles_empty_opportunity_list():
    report = build_decision_report(
        make_portfolio([]),
        make_summary(),
    )

    assert report.selected_opportunities == []
    assert report.top_security_type is None
    assert report.top_maturity_years is None
    assert report.top_classification is None


def test_report_copies_mutable_lists():
    portfolio = make_portfolio()
    summary = make_summary()

    report = build_decision_report(
        portfolio,
        summary,
    )

    report.preferred_exposures.append(
        "TEST_EXPOSURE"
    )

    report.selected_opportunities.clear()

    assert (
        "TEST_EXPOSURE"
        not in portfolio.preferred_exposures
    )
    assert len(portfolio.selected_opportunities) == 1
