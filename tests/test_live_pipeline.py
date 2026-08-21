import json

from engine.market_data import MarketDataSnapshot
from engine.opportunity_import import load_opportunities_from_csv
from engine.regime_builder import build_regime_from_market_data
from engine.service import run_anchor


def make_market_snapshot():
    return MarketDataSnapshot(
        fed_funds_rate=4.50,
        treasury_2y=4.30,
        treasury_10y=4.45,
        real_yield_10y=2.10,
        breakeven_10y=2.30,
        credit_spread_ig_bps=95.0,
        treasury_2y_change_bps=5.0,
        treasury_10y_change_bps=10.0,
        real_yield_10y_change_bps=20.0,
        breakeven_10y_change_bps=5.0,
        credit_spread_ig_change_bps=2.0,
        unemployment_rate=4.2,
        unemployment_rate_change_pct=0.0,
    )


def write_opportunity_csv(tmp_path):
    path = tmp_path / "opportunities.csv"

    path.write_text(
        (
            "security_type,maturity_years,"
            "yield_percent,rating,callable,"
            "spread_compensation\n"
            "TREASURY,2,4.20,,,MODERATE\n"
            "TREASURY,5,4.35,,,MODERATE\n"
            "TIPS,5,2.10,,,MODERATE\n"
            "CORPORATE,5,5.30,A,FALSE,HIGH\n"
            "CORPORATE,5,5.30,A,TRUE,HIGH\n"
        ),
        encoding="utf-8",
    )

    return path


def test_live_pipeline_builds_regime_from_market_data():
    snapshot = make_market_snapshot()

    regime = build_regime_from_market_data(
        snapshot
    )

    assert regime.real_rates == "PRESSURE"
    assert regime.credit == "BENIGN"
    assert regime.dominant_driver == "REAL_RATES"


def test_live_pipeline_loads_csv_opportunities(
    tmp_path,
):
    path = write_opportunity_csv(
        tmp_path
    )

    opportunities = (
        load_opportunities_from_csv(
            str(path)
        )
    )

    assert len(opportunities) == 5


def test_live_pipeline_runs_end_to_end(
    tmp_path,
):
    snapshot = make_market_snapshot()

    regime = build_regime_from_market_data(
        snapshot
    )

    path = write_opportunity_csv(
        tmp_path
    )

    opportunities = (
        load_opportunities_from_csv(
            str(path)
        )
    )

    result = run_anchor(
        opportunities=opportunities,
        regime=regime,
        max_selections=3,
    )

    assert isinstance(result, dict)
    assert result["schema_version"] == "1.0"

    assert len(
        result["selected_opportunities"]
    ) == 3

    assert result["top_opportunity"] is not None


def test_live_pipeline_preserves_regime_effects(
    tmp_path,
):
    snapshot = make_market_snapshot()

    regime = build_regime_from_market_data(
        snapshot
    )

    path = write_opportunity_csv(
        tmp_path
    )

    opportunities = (
        load_opportunities_from_csv(
            str(path)
        )
    )

    result = run_anchor(
        opportunities=opportunities,
        regime=regime,
        max_selections=3,
    )

    assert result["portfolio_posture"][
        "duration"
    ] == "SHORT"


def test_live_pipeline_output_is_json_serializable(
    tmp_path,
):
    snapshot = make_market_snapshot()

    regime = build_regime_from_market_data(
        snapshot
    )

    path = write_opportunity_csv(
        tmp_path
    )

    opportunities = (
        load_opportunities_from_csv(
            str(path)
        )
    )

    result = run_anchor(
        opportunities=opportunities,
        regime=regime,
        max_selections=3,
    )

    encoded = json.dumps(
        result,
        sort_keys=True,
    )

    decoded = json.loads(
        encoded
    )

    assert decoded == result


def test_live_pipeline_is_deterministic(
    tmp_path,
):
    snapshot = make_market_snapshot()

    regime = build_regime_from_market_data(
        snapshot
    )

    path = write_opportunity_csv(
        tmp_path
    )

    first_opportunities = (
        load_opportunities_from_csv(
            str(path)
        )
    )

    second_opportunities = (
        load_opportunities_from_csv(
            str(path)
        )
    )

    first = run_anchor(
        opportunities=first_opportunities,
        regime=regime,
        max_selections=3,
    )

    second = run_anchor(
        opportunities=second_opportunities,
        regime=regime,
        max_selections=3,
    )

    assert first == second
