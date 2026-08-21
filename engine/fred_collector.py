"""
FRED market-data collector for Anchor.

This module retrieves public economic and fixed-income
observations from the Federal Reserve Bank of St. Louis
FRED graph CSV interface.

It converts those observations into Anchor's existing
MarketDataSnapshot structure.

The collector does not classify the economic regime and
does not perform investment analysis.

Flow:

    FRED
      ↓
    raw series observations
      ↓
    normalization
      ↓
    MarketDataSnapshot
      ↓
    regime_builder.py
"""

import csv
import io
from datetime import date, timedelta
from typing import List, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from engine.market_data import (
    MarketDataSnapshot,
    validate_market_data,
)


FRED_GRAPH_CSV_URL = (
    "https://fred.stlouisfed.org/graph/fredgraph.csv"
)


SERIES_FED_FUNDS = "DFF"

SERIES_TREASURY_1Y = "DGS1"
SERIES_TREASURY_2Y = "DGS2"
SERIES_TREASURY_3Y = "DGS3"
SERIES_TREASURY_5Y = "DGS5"
SERIES_TREASURY_7Y = "DGS7"
SERIES_TREASURY_10Y = "DGS10"

SERIES_REAL_YIELD_10Y = "DFII10"
SERIES_BREAKEVEN_10Y = "T10YIE"
SERIES_CREDIT_IG_OAS = "BAMLC0A0CM"
SERIES_UNEMPLOYMENT = "UNRATE"


DAILY_LOOKBACK_DAYS = 30
DAILY_DOWNLOAD_WINDOW_DAYS = 90
UNEMPLOYMENT_DOWNLOAD_WINDOW_DAYS = 365


Observation = Tuple[
    date,
    float,
]


class FREDDataError(RuntimeError):
    """
    Raised when FRED data cannot be retrieved or parsed
    into a usable Anchor market-data observation.
    """


def _build_fred_url(
    series_id: str,
    start_date: date,
) -> str:
    """
    Build the FRED graph CSV URL for one series.
    """

    query = urlencode(
        {
            "id": series_id,
            "cosd": start_date.isoformat(),
        }
    )

    return (
        f"{FRED_GRAPH_CSV_URL}?{query}"
    )


def _download_series_csv(
    series_id: str,
    start_date: date,
) -> str:
    """
    Download CSV text for one FRED series.

    Raises:
        FREDDataError when the request fails.
    """

    url = _build_fred_url(
        series_id=series_id,
        start_date=start_date,
    )

    try:
        with urlopen(
            url,
            timeout=15,
        ) as response:
            payload = response.read()

    except (
        HTTPError,
        URLError,
        TimeoutError,
    ) as exc:
        raise FREDDataError(
            f"Unable to retrieve FRED series "
            f"{series_id}."
        ) from exc

    try:
        return payload.decode(
            "utf-8"
        )

    except UnicodeDecodeError as exc:
        raise FREDDataError(
            f"Unable to decode FRED series "
            f"{series_id}."
        ) from exc


def _parse_series_csv(
    csv_text: str,
    series_id: str,
) -> List[Observation]:
    """
    Parse FRED graph CSV text into dated observations.

    Missing FRED observations represented by '.' or blank
    values are ignored.
    """

    reader = csv.DictReader(
        io.StringIO(
            csv_text
        )
    )

    if not reader.fieldnames:
        raise FREDDataError(
            f"FRED series {series_id} "
            "contains no header."
        )

    date_column = (
        "DATE"
        if "DATE" in reader.fieldnames
        else "observation_date"
    )

    if date_column not in reader.fieldnames:
        raise FREDDataError(
            f"FRED series {series_id} "
            "contains no date column."
        )

    if series_id not in reader.fieldnames:
        raise FREDDataError(
            f"FRED series {series_id} "
            "contains no matching value column."
        )

    observations: List[
        Observation
    ] = []

    for row in reader:
        raw_date = row.get(
            date_column
        )

        raw_value = row.get(
            series_id
        )

        if (
            raw_date is None
            or raw_value is None
        ):
            continue

        raw_date = (
            raw_date.strip()
        )

        raw_value = (
            raw_value.strip()
        )

        if (
            not raw_date
            or not raw_value
            or raw_value == "."
        ):
            continue

        try:
            observation_date = (
                date.fromisoformat(
                    raw_date
                )
            )

            value = float(
                raw_value
            )

        except ValueError as exc:
            raise FREDDataError(
                f"Unable to parse FRED series "
                f"{series_id}."
            ) from exc

        observations.append(
            (
                observation_date,
                value,
            )
        )

    if not observations:
        raise FREDDataError(
            f"FRED series {series_id} "
            "contains no usable observations."
        )

    observations.sort(
        key=lambda item: item[0]
    )

    return observations


def fetch_fred_series(
    series_id: str,
    window_days: int,
) -> List[Observation]:
    """
    Retrieve and parse one FRED series.
    """

    if (
        not isinstance(
            window_days,
            int,
        )
        or isinstance(
            window_days,
            bool,
        )
        or window_days < 1
    ):
        raise ValueError(
            "window_days must be a positive integer."
        )

    start_date = (
        date.today()
        - timedelta(
            days=window_days
        )
    )

    csv_text = (
        _download_series_csv(
            series_id=series_id,
            start_date=start_date,
        )
    )

    return _parse_series_csv(
        csv_text=csv_text,
        series_id=series_id,
    )


def _latest_value(
    observations: List[Observation],
) -> float:
    """
    Return the latest usable observation.
    """

    if not observations:
        raise FREDDataError(
            "Cannot select a value from "
            "an empty observation set."
        )

    return observations[-1][1]


def _change_from_lookback(
    observations: List[Observation],
    lookback_days: int,
) -> float:
    """
    Calculate the change between the latest observation
    and the most recent observation on or before the
    requested calendar lookback date.

    If no observation exists that far back, the earliest
    available observation is used.
    """

    if not observations:
        raise FREDDataError(
            "Cannot calculate change from "
            "an empty observation set."
        )

    latest_date, latest_value = (
        observations[-1]
    )

    target_date = (
        latest_date
        - timedelta(
            days=lookback_days
        )
    )

    comparison_value = (
        observations[0][1]
    )

    for observation_date, value in observations:
        if observation_date <= target_date:
            comparison_value = value
        else:
            break

    return (
        latest_value
        - comparison_value
    )


def _latest_monthly_change(
    observations: List[Observation],
) -> float:
    """
    Calculate the change between the two latest available
    monthly observations.
    """

    if len(observations) < 2:
        raise FREDDataError(
            "At least two unemployment observations "
            "are required."
        )

    return (
        observations[-1][1]
        - observations[-2][1]
    )


def collect_fred_market_data() -> MarketDataSnapshot:
    """
    Collect the FRED series required by Anchor and return
    a validated MarketDataSnapshot.

    Treasury nominal-curve observations currently include:

        1-year
        2-year
        3-year
        5-year
        7-year
        10-year

    Daily change fields use a 30-calendar-day comparison
    window.

    The ICE BofA corporate OAS series is published by FRED
    in percentage points, while Anchor stores corporate
    spreads in basis points. It is therefore multiplied by
    100 during normalization.
    """

    fed_funds = fetch_fred_series(
        SERIES_FED_FUNDS,
        DAILY_DOWNLOAD_WINDOW_DAYS,
    )

    treasury_1y = fetch_fred_series(
        SERIES_TREASURY_1Y,
        DAILY_DOWNLOAD_WINDOW_DAYS,
    )

    treasury_2y = fetch_fred_series(
        SERIES_TREASURY_2Y,
        DAILY_DOWNLOAD_WINDOW_DAYS,
    )

    treasury_3y = fetch_fred_series(
        SERIES_TREASURY_3Y,
        DAILY_DOWNLOAD_WINDOW_DAYS,
    )

    treasury_5y = fetch_fred_series(
        SERIES_TREASURY_5Y,
        DAILY_DOWNLOAD_WINDOW_DAYS,
    )

    treasury_7y = fetch_fred_series(
        SERIES_TREASURY_7Y,
        DAILY_DOWNLOAD_WINDOW_DAYS,
    )

    treasury_10y = fetch_fred_series(
        SERIES_TREASURY_10Y,
        DAILY_DOWNLOAD_WINDOW_DAYS,
    )

    real_yield_10y = fetch_fred_series(
        SERIES_REAL_YIELD_10Y,
        DAILY_DOWNLOAD_WINDOW_DAYS,
    )

    breakeven_10y = fetch_fred_series(
        SERIES_BREAKEVEN_10Y,
        DAILY_DOWNLOAD_WINDOW_DAYS,
    )

    credit_ig_oas = fetch_fred_series(
        SERIES_CREDIT_IG_OAS,
        DAILY_DOWNLOAD_WINDOW_DAYS,
    )

    unemployment = fetch_fred_series(
        SERIES_UNEMPLOYMENT,
        UNEMPLOYMENT_DOWNLOAD_WINDOW_DAYS,
    )

    snapshot = MarketDataSnapshot(
        fed_funds_rate=(
            _latest_value(
                fed_funds
            )
        ),
        treasury_1y=(
            _latest_value(
                treasury_1y
            )
        ),
        treasury_2y=(
            _latest_value(
                treasury_2y
            )
        ),
        treasury_3y=(
            _latest_value(
                treasury_3y
            )
        ),
        treasury_5y=(
            _latest_value(
                treasury_5y
            )
        ),
        treasury_7y=(
            _latest_value(
                treasury_7y
            )
        ),
        treasury_10y=(
            _latest_value(
                treasury_10y
            )
        ),
        real_yield_10y=(
            _latest_value(
                real_yield_10y
            )
        ),
        breakeven_10y=(
            _latest_value(
                breakeven_10y
            )
        ),
        credit_spread_ig_bps=(
            _latest_value(
                credit_ig_oas
            )
            * 100.0
        ),
        treasury_1y_change_bps=(
            _change_from_lookback(
                treasury_1y,
                DAILY_LOOKBACK_DAYS,
            )
            * 100.0
        ),
        treasury_2y_change_bps=(
            _change_from_lookback(
                treasury_2y,
                DAILY_LOOKBACK_DAYS,
            )
            * 100.0
        ),
        treasury_3y_change_bps=(
            _change_from_lookback(
                treasury_3y,
                DAILY_LOOKBACK_DAYS,
            )
            * 100.0
        ),
        treasury_5y_change_bps=(
            _change_from_lookback(
                treasury_5y,
                DAILY_LOOKBACK_DAYS,
            )
            * 100.0
        ),
        treasury_7y_change_bps=(
            _change_from_lookback(
                treasury_7y,
                DAILY_LOOKBACK_DAYS,
            )
            * 100.0
        ),
        treasury_10y_change_bps=(
            _change_from_lookback(
                treasury_10y,
                DAILY_LOOKBACK_DAYS,
            )
            * 100.0
        ),
        real_yield_10y_change_bps=(
            _change_from_lookback(
                real_yield_10y,
                DAILY_LOOKBACK_DAYS,
            )
            * 100.0
        ),
        breakeven_10y_change_bps=(
            _change_from_lookback(
                breakeven_10y,
                DAILY_LOOKBACK_DAYS,
            )
            * 100.0
        ),
        credit_spread_ig_change_bps=(
            _change_from_lookback(
                credit_ig_oas,
                DAILY_LOOKBACK_DAYS,
            )
            * 100.0
        ),
        unemployment_rate=(
            _latest_value(
                unemployment
            )
        ),
        unemployment_rate_change_pct=(
            _latest_monthly_change(
                unemployment
            )
        ),
    )

    validate_market_data(
        snapshot
    )

    return snapshot
