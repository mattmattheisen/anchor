from engine.models import FixedIncomeOpportunity
from engine.risk import (
    duration_penalty_bps,
    credit_penalty_bps,
    call_penalty_bps,
    structure_penalty_bps,
    total_risk_penalty_bps,
    calculate_risk_adjusted_yield,
    classify_risk_level,
    assess_risk_adjusted_yield,
)


def test_duration_penalty_boundaries():
    assert duration_penalty_bps(1.0) == 0.0
    assert duration_penalty_bps(3.0) == 10.0
    assert duration_penalty_bps(7.0) == 25.0
    assert duration_penalty_bps(10.0) == 40.0
    assert duration_penalty_bps(20.0) == 70.0
    assert duration_penalty_bps(30.0) == 100.0


def test_treasury_has_no_credit_penalty():
    assert credit_penalty_bps(
        rating=None,
        security_type="TREASURY",
    ) == 0.0


def test_tips_has_no_credit_penalty():
    assert credit_penalty_bps(
        rating=None,
        security_type="TIPS",
    ) == 0.0


def test_credit_rating_penalties():
    assert credit_penalty_bps("AAA", "CORPORATE") == 5.0
    assert credit_penalty_bps("AA", "CORPORATE") == 10.0
    assert credit_penalty_bps("A", "CORPORATE") == 20.0
    assert credit_penalty_bps("BBB", "CORPORATE") == 40.0
    assert credit_penalty_bps("BB", "CORPORATE") == 80.0
    assert credit_penalty_bps("B", "CORPORATE") == 120.0
    assert credit_penalty_bps("CCC", "CORPORATE") == 200.0


def test_unrated_non_government_penalty():
    assert credit_penalty_bps(
        rating=None,
        security_type="CORPORATE",
    ) == 50.0


def test_unknown_rating_gets_conservative_penalty():
    assert credit_penalty_bps(
        rating="BANANA",
        security_type="CORPORATE",
    ) == 75.0


def test_callable_security_penalty():
    assert call_penalty_bps(True) == 30.0
    assert call_penalty_bps(False) == 0.0


def test_structure_penalties():
    assert structure_penalty_bps("TREASURY") == 0.0
    assert structure_penalty_bps("TIPS") == 5.0
    assert structure_penalty_bps("CD") == 10.0
    assert structure_penalty_bps("AGENCY") == 10.0
    assert structure_penalty_bps("MUNICIPAL") == 15.0
    assert structure_penalty_bps("CORPORATE") == 20.0


def test_unknown_structure_gets_default_penalty():
    assert structure_penalty_bps("BANANA_BOND") == 30.0


def test_five_year_treasury_total_penalty():
    opportunity = FixedIncomeOpportunity(
        security_type="TREASURY",
        maturity_years=5.0,
        yield_percent=4.433,
    )

    assert total_risk_penalty_bps(opportunity) == 25.0


def test_five_year_a_corporate_total_penalty():
    opportunity = FixedIncomeOpportunity(
        security_type="CORPORATE",
        maturity_years=5.0,
        yield_percent=5.30,
        rating="A",
    )

    assert total_risk_penalty_bps(opportunity) == 65.0


def test_callable_a_corporate_total_penalty():
    opportunity = FixedIncomeOpportunity(
        security_type="CORPORATE",
        maturity_years=5.0,
        yield_percent=5.60,
        rating="A",
        callable=True,
    )

    assert total_risk_penalty_bps(opportunity) == 95.0


def test_risk_adjusted_treasury_yield():
    opportunity = FixedIncomeOpportunity(
        security_type="TREASURY",
        maturity_years=5.0,
        yield_percent=4.433,
    )

    assert calculate_risk_adjusted_yield(
        opportunity
    ) == 4.183


def test_risk_adjusted_corporate_yield():
    opportunity = FixedIncomeOpportunity(
        security_type="CORPORATE",
        maturity_years=5.0,
        yield_percent=5.30,
        rating="A",
    )

    assert calculate_risk_adjusted_yield(
        opportunity
    ) == 4.65


def test_risk_level_boundaries():
    assert classify_risk_level(0.0) == "LOW"
    assert classify_risk_level(24.99) == "LOW"
    assert classify_risk_level(25.0) == "MODERATE"
    assert classify_risk_level(59.99) == "MODERATE"
    assert classify_risk_level(60.0) == "ELEVATED"
    assert classify_risk_level(99.99) == "ELEVATED"
    assert classify_risk_level(100.0) == "HIGH"


def test_complete_risk_adjusted_assessment():
    opportunity = FixedIncomeOpportunity(
        security_type="CORPORATE",
        maturity_years=5.0,
        yield_percent=5.30,
        rating="A",
        callable=False,
    )

    result = assess_risk_adjusted_yield(
        opportunity
    )

    assert result.security_type == "CORPORATE"
    assert result.maturity_years == 5.0
    assert result.stated_yield_percent == 5.30
    assert result.rating == "A"
    assert result.callable is False

    assert result.duration_penalty_bps == 25.0
    assert result.credit_penalty_bps == 20.0
    assert result.call_penalty_bps == 0.0
    assert result.structure_penalty_bps == 20.0

    assert result.total_penalty_bps == 65.0
    assert result.risk_adjusted_yield_percent == 4.65
    assert result.risk_level == "ELEVATED"


def test_high_yield_does_not_guarantee_high_adjusted_yield():
    risky = FixedIncomeOpportunity(
        security_type="CORPORATE",
        maturity_years=30.0,
        yield_percent=7.00,
        rating="B",
        callable=True,
    )

    safer = FixedIncomeOpportunity(
        security_type="TREASURY",
        maturity_years=5.0,
        yield_percent=4.50,
    )

    assert calculate_risk_adjusted_yield(
        risky
    ) < risky.yield_percent

    assert calculate_risk_adjusted_yield(
        safer
    ) < safer.yield_percent
