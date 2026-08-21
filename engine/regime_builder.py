"""
Deterministic market-data regime builder for Anchor.

This module translates validated MarketDataSnapshot values
into Anchor's existing RegimeAssessment vocabulary.

It does not fetch market data.

Its only responsibility is:

    MarketDataSnapshot
        ↓
    explicit deterministic thresholds
        ↓
    RegimeAssessment

The thresholds in this module are intentionally visible and
testable. They can be refined later without changing the
market-data collection layer or Anchor's core decision engine.
"""

from engine.market_data import (
    MarketDataSnapshot,
    validate_market_data,
)
from engine.regime import RegimeAssessment


# ---------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------

POLICY_DIFFERENCE_BPS = 25.0

GROWTH_INVERSION_BPS = -25.0
GROWTH_STEEP_BPS = 50.0
UNEMPLOYMENT_WEAKENING_CHANGE = 0.30

INFLATION_PRESSURE_LEVEL = 2.50
INFLATION_FALLING_LEVEL = 2.00
INFLATION_CHANGE_BPS = 15.0

REAL_RATE_PRESSURE_LEVEL = 2.00
REAL_RATE_FALLING_LEVEL = 0.50
REAL_RATE_CHANGE_BPS = 15.0

TERM_PREMIUM_CHANGE_BPS = 15.0

CREDIT_STRESS_LEVEL_BPS = 150.0
CREDIT_BENIGN_LEVEL_BPS = 110.0
CREDIT_STRESS_CHANGE_BPS = 25.0
CREDIT_BENIGN_CHANGE_BPS = 10.0


def classify_policy(
    snapshot: MarketDataSnapshot,
) -> str:
    """
    Classify policy using the relationship between the
    effective policy rate and the 2-year Treasury yield.

    If the policy rate is materially above the 2-year yield,
    policy is treated as restrictive.

    If the policy rate is materially below the 2-year yield,
    policy is treated as accommodative.

    Otherwise policy is neutral.
    """

    difference_bps = (
        snapshot.fed_funds_rate
        - snapshot.treasury_2y
    ) * 100.0

    if difference_bps >= POLICY_DIFFERENCE_BPS:
        return "RESTRICTIVE"

    if difference_bps <= -POLICY_DIFFERENCE_BPS:
        return "ACCOMMODATIVE"

    return "NEUTRAL"


def classify_growth(
    snapshot: MarketDataSnapshot,
) -> str:
    """
    Classify growth using Treasury-curve shape with optional
    unemployment confirmation.

    The curve spread is:

        10-year Treasury yield
        minus
        2-year Treasury yield
    """

    curve_spread_bps = (
        snapshot.treasury_10y
        - snapshot.treasury_2y
    ) * 100.0

    if (
        snapshot.unemployment_rate_change_pct
        is not None
        and (
            snapshot.unemployment_rate_change_pct
            >= UNEMPLOYMENT_WEAKENING_CHANGE
        )
    ):
        return "WEAKENING"

    if curve_spread_bps <= GROWTH_INVERSION_BPS:
        return "WEAKENING"

    if curve_spread_bps >= GROWTH_STEEP_BPS:
        if (
            snapshot.unemployment_rate_change_pct
            is None
            or snapshot.unemployment_rate_change_pct
            <= 0.0
        ):
            return "ACCELERATING"

    return "NEUTRAL"


def classify_inflation(
    snapshot: MarketDataSnapshot,
) -> str:
    """
    Classify inflation using the 10-year breakeven level and
    its recent change.
    """

    if (
        snapshot.breakeven_10y
        >= INFLATION_PRESSURE_LEVEL
        or snapshot.breakeven_10y_change_bps
        >= INFLATION_CHANGE_BPS
    ):
        return "PRESSURE"

    if (
        snapshot.breakeven_10y
        <= INFLATION_FALLING_LEVEL
        and snapshot.breakeven_10y_change_bps
        <= -INFLATION_CHANGE_BPS
    ):
        return "FALLING"

    return "STABLE"


def classify_real_rates(
    snapshot: MarketDataSnapshot,
) -> str:
    """
    Classify real-rate pressure from the 10-year real yield
    and its recent change.
    """

    if (
        snapshot.real_yield_10y
        >= REAL_RATE_PRESSURE_LEVEL
        or snapshot.real_yield_10y_change_bps
        >= REAL_RATE_CHANGE_BPS
    ):
        return "PRESSURE"

    if (
        snapshot.real_yield_10y
        <= REAL_RATE_FALLING_LEVEL
        and snapshot.real_yield_10y_change_bps
        <= -REAL_RATE_CHANGE_BPS
    ):
        return "FALLING"

    return "STABLE"


def classify_term_premium(
    snapshot: MarketDataSnapshot,
) -> str:
    """
    Infer term-premium direction using differential movement
    between long- and short-maturity Treasury yields.

    Anchor does not yet ingest a dedicated term-premium
    series, so this is an explicit proxy.

    Positive differential movement means the 10-year yield
    is rising faster than the 2-year yield.

    Negative differential movement means the 10-year yield
    is falling faster than the 2-year yield.
    """

    differential_change_bps = (
        snapshot.treasury_10y_change_bps
        - snapshot.treasury_2y_change_bps
    )

    if (
        differential_change_bps
        >= TERM_PREMIUM_CHANGE_BPS
    ):
        return "RISING"

    if (
        differential_change_bps
        <= -TERM_PREMIUM_CHANGE_BPS
    ):
        return "FALLING"

    return "NEUTRAL"


def classify_credit(
    snapshot: MarketDataSnapshot,
) -> str:
    """
    Classify investment-grade credit conditions using both
    spread level and recent spread movement.
    """

    if (
        snapshot.credit_spread_ig_bps
        >= CREDIT_STRESS_LEVEL_BPS
        or snapshot.credit_spread_ig_change_bps
        >= CREDIT_STRESS_CHANGE_BPS
    ):
        return "STRESSED"

    if (
        snapshot.credit_spread_ig_bps
        <= CREDIT_BENIGN_LEVEL_BPS
        and snapshot.credit_spread_ig_change_bps
        <= CREDIT_BENIGN_CHANGE_BPS
    ):
        return "BENIGN"

    return "NEUTRAL"


def determine_dominant_driver(
    growth: str,
    inflation: str,
    real_rates: str,
    term_premium: str,
    credit: str,
) -> str:
    """
    Determine the dominant fixed-income regime driver.

    Priority is given to conditions that can create the
    largest portfolio-level fixed-income consequences.
    """

    if credit == "STRESSED":
        return "CREDIT_STRESS"

    if (
        inflation == "PRESSURE"
        and real_rates == "PRESSURE"
    ):
        return "INFLATION_REAL_RATE_PRESSURE"

    if (
        real_rates == "PRESSURE"
        and term_premium == "RISING"
    ):
        return "REAL_RATE_TERM_PREMIUM"

    if inflation == "PRESSURE":
        return "INFLATION"

    if real_rates == "PRESSURE":
        return "REAL_RATES"

    if growth == "WEAKENING":
        return "GROWTH"

    if term_premium == "RISING":
        return "TERM_PREMIUM"

    return "MIXED"


def determine_confidence(
    growth: str,
    inflation: str,
    real_rates: str,
    term_premium: str,
    credit: str,
) -> str:
    """
    Estimate regime confidence from the number of
    non-neutral directional signals.

    This is deliberately simple and deterministic.
    """

    directional_signals = 0

    if growth != "NEUTRAL":
        directional_signals += 1

    if inflation != "STABLE":
        directional_signals += 1

    if real_rates != "STABLE":
        directional_signals += 1

    if term_premium != "NEUTRAL":
        directional_signals += 1

    if credit != "NEUTRAL":
        directional_signals += 1

    if directional_signals >= 4:
        return "HIGH"

    if directional_signals >= 2:
        return "MEDIUM"

    return "LOW"


def build_regime_from_market_data(
    snapshot: MarketDataSnapshot,
) -> RegimeAssessment:
    """
    Build Anchor's RegimeAssessment from raw market data.

    The snapshot is validated before any classification
    occurs.
    """

    validate_market_data(
        snapshot
    )

    policy = classify_policy(
        snapshot
    )

    growth = classify_growth(
        snapshot
    )

    inflation = classify_inflation(
        snapshot
    )

    real_rates = classify_real_rates(
        snapshot
    )

    term_premium = classify_term_premium(
        snapshot
    )

    credit = classify_credit(
        snapshot
    )

    dominant_driver = determine_dominant_driver(
        growth=growth,
        inflation=inflation,
        real_rates=real_rates,
        term_premium=term_premium,
        credit=credit,
    )

    confidence = determine_confidence(
        growth=growth,
        inflation=inflation,
        real_rates=real_rates,
        term_premium=term_premium,
        credit=credit,
    )

    return RegimeAssessment(
        policy=policy,
        growth=growth,
        inflation=inflation,
        real_rates=real_rates,
        term_premium=term_premium,
        credit=credit,
        dominant_driver=dominant_driver,
        confidence=confidence,
    )
