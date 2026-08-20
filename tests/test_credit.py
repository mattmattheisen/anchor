import pytest

from engine.models import FixedIncomeOpportunity, TreasuryPoint
from engine.credit import (
    treasury_yield_for_maturity,
    spread_to_treasury_bps,
    classify_spread_compensation,
    compare_opportunity_to_treasury,
)


def sample_treasury_curve():
    return [
        TreasuryPoint(2.0, 4.218),
        TreasuryPoint(5.0, 4.433),
        TreasuryPoint(10.0, 4.704),
        TreasuryPoint(30.0, 5.256),
    ]


def test_treasury_yield_lookup():
    result = treasury_yield_for_maturity(
        sample_treasury_curve(),
        5.0,
    )

    assert result == 4.433


def test_spread_to_treasury():
    opportunity = FixedIncomeOpportunity(
        security_type="CORPORATE",
        maturity_years=5.0,
        yield_percent=5.300,
        rating="A",
    )

    spread = spread_to_treasury_bps(
        opportunity,
        sample_treasury_curve(),
    )

    assert spread == 86.7


def test_meaningful_spread_classification():
    assert classify_spread_compensation(86.7) == "MEANINGFUL"


def test_spread_classification_boundaries():
    assert classify_spread_compensation(-1.0) == "UNFAVORABLE"
    assert classify_spread_compensation(0.0) == "THIN"
    assert classify_spread_compensation(24.99) == "THIN"
    assert classify_spread_compensation(25.0) == "MODERATE"
    assert classify_spread_compensation(74.99) == "MODERATE"
    assert classify_spread_compensation(75.0) == "MEANINGFUL"
    assert classify_spread_compensation(149.99) == "MEANINGFUL"
    assert classify_spread_compensation(150.0) == "HIGH"


def test_negative_spread_is_unfavorable():
    opportunity = FixedIncomeOpportunity(
        security_type="CORPORATE",
        maturity_years=5.0,
        yield_percent=4.20,
        rating="AAA",
    )

    spread = spread_to_treasury_bps(
        opportunity,
        sample_treasury_curve(),
    )

    assert spread == -23.3
    assert classify_spread_compensation(spread) == "UNFAVORABLE"


def test_missing_treasury_maturity_rejected():
    opportunity = FixedIncomeOpportunity(
        security_type="CORPORATE",
        maturity_years=7.0,
        yield_percent=5.10,
        rating="A",
    )

    with pytest.raises(
        ValueError,
        match="Treasury maturity 7.0 years was not found",
    ):
        spread_to_treasury_bps(
            opportunity,
            sample_treasury_curve(),
        )


def test_full_opportunity_comparison():
    opportunity = FixedIncomeOpportunity(
        security_type="CORPORATE",
        maturity_years=5.0,
        yield_percent=5.300,
        rating="A",
        issuer="Example Corporation",
    )

    result = compare_opportunity_to_treasury(
        opportunity,
        sample_treasury_curve(),
    )

    assert result["security_type"] == "CORPORATE"
    assert result["maturity_years"] == 5.0
    assert result["yield_percent"] == 5.300
    assert result["rating"] == "A"
    assert result["spread_to_treasury_bps"] == 86.7
    assert result["spread_compensation"] == "MEANINGFUL"
