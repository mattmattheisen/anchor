from datetime import date

import pytest

from engine.fred_collector import (
    FREDDataError,
    _build_fred_url,
    _change_from_lookback,
    _latest_monthly_change,
    _latest_value,
    _parse_series_csv,
)


def test_build_fred_url_contains_series_id():
    url = _build_fred_url(
        series_id="DGS10",
        start_date=date(2026, 1, 1),
    )

    assert "DGS10" in url
    assert "2026-01-01" in url


def test_parse_series_csv_reads_valid_rows():
    csv_text = (
        "observation_date,DGS10\n"
        "2026-08-01,4.20\n"
        "2026-08-02,4.25\n"
        "2026-08-03,4.30\n"
    )

    result = _parse_series_csv(
        csv_text=csv_text,
        series_id="DGS10",
    )

    assert result == [
        (
            date(2026, 8, 1),
            4.20,
        ),
        (
            date(2026, 8, 2),
            4.25,
        ),
        (
            date(2026, 8, 3),
            4.30,
        ),
    ]


def test_parse_series_csv_supports_date_column():
    csv_text = (
        "DATE,DGS2\n"
        "2026-08-01,4.10\n"
        "2026-08-02,4.15\n"
    )

    result = _parse_series_csv(
        csv_text=csv_text,
        series_id="DGS2",
    )

    assert result[-1][1] == 4.15


def test_parse_series_csv_ignores_missing_values():
    csv_text = (
        "observation_date,DGS10\n"
        "2026-08-01,4.20\n"
        "2026-08-02,.\n"
        "2026-08-03,\n"
        "2026-08-04,4.35\n"
    )

    result = _parse_series_csv(
        csv_text=csv_text,
        series_id="DGS10",
    )

    assert result == [
        (
            date(2026, 8, 1),
            4.20,
        ),
        (
            date(2026, 8, 4),
            4.35,
        ),
    ]


def test_parse_series_csv_sorts_observations():
    csv_text = (
        "observation_date,DGS10\n"
        "2026-08-03,4.30\n"
        "2026-08-01,4.20\n"
        "2026-08-02,4.25\n"
    )

    result = _parse_series_csv(
        csv_text=csv_text,
        series_id="DGS10",
    )

    assert [
        item[0]
        for item in result
    ] == [
        date(2026, 8, 1),
        date(2026, 8, 2),
        date(2026, 8, 3),
    ]


def test_parse_series_csv_rejects_missing_header():
    with pytest.raises(
        FREDDataError,
    ):
        _parse_series_csv(
            csv_text="",
            series_id="DGS10",
        )


def test_parse_series_csv_rejects_missing_date_column():
    csv_text = (
        "WRONG,DGS10\n"
        "2026-08-01,4.20\n"
    )

    with pytest.raises(
        FREDDataError,
        match="contains no date column",
    ):
        _parse_series_csv(
            csv_text=csv_text,
            series_id="DGS10",
        )


def test_parse_series_csv_rejects_missing_series_column():
    csv_text = (
        "observation_date,DGS2\n"
        "2026-08-01,4.20\n"
    )

    with pytest.raises(
        FREDDataError,
        match="contains no matching value column",
    ):
        _parse_series_csv(
            csv_text=csv_text,
            series_id="DGS10",
        )


def test_parse_series_csv_rejects_bad_numeric_value():
    csv_text = (
        "observation_date,DGS10\n"
        "2026-08-01,NOT_NUMERIC\n"
    )

    with pytest.raises(
        FREDDataError,
        match="Unable to parse FRED series",
    ):
        _parse_series_csv(
            csv_text=csv_text,
            series_id="DGS10",
        )


def test_latest_value_returns_last_observation():
    observations = [
        (
            date(2026, 8, 1),
            4.10,
        ),
        (
            date(2026, 8, 2),
            4.20,
        ),
    ]

    assert _latest_value(
        observations
    ) == 4.20


def test_latest_value_rejects_empty_observations():
    with pytest.raises(
        FREDDataError,
    ):
        _latest_value(
            []
        )


def test_change_from_lookback_uses_previous_observation():
    observations = [
        (
            date(2026, 7, 1),
            4.00,
        ),
        (
            date(2026, 7, 15),
            4.10,
        ),
        (
            date(2026, 8, 1),
            4.30,
        ),
    ]

    change = _change_from_lookback(
        observations=observations,
        lookback_days=17,
    )

    assert change == pytest.approx(
        0.20
    )


def test_change_from_lookback_uses_earliest_when_needed():
    observations = [
        (
            date(2026, 8, 1),
            4.00,
        ),
        (
            date(2026, 8, 10),
            4.30,
        ),
    ]

    change = _change_from_lookback(
        observations=observations,
        lookback_days=30,
    )

    assert change == pytest.approx(
        0.30
    )


def test_change_from_lookback_rejects_empty_observations():
    with pytest.raises(
        FREDDataError,
    ):
        _change_from_lookback(
            observations=[],
            lookback_days=30,
        )


def test_latest_monthly_change():
    observations = [
        (
            date(2026, 6, 1),
            4.1,
        ),
        (
            date(2026, 7, 1),
            4.2,
        ),
        (
            date(2026, 8, 1),
            4.4,
        ),
    ]

    change = _latest_monthly_change(
        observations
    )

    assert change == pytest.approx(
        0.2
    )


def test_latest_monthly_change_requires_two_observations():
    observations = [
        (
            date(2026, 8, 1),
            4.4,
        ),
    ]

    with pytest.raises(
        FREDDataError,
        match="At least two unemployment observations",
    ):
        _latest_monthly_change(
            observations
        )
