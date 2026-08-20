"""
Regime classification logic for Anchor.

This module combines Treasury-curve shape, rate-driver
classification, and credit conditions into a qualitative
fixed-income regime assessment.
"""

from dataclasses import dataclass


@dataclass
class RegimeAssessment:
    policy: str
    growth: str
    inflation: str
    real_rates: str
    term_premium: str
    credit: str

    dominant_driver: str
    confidence: str


def classify_growth_regime(
    curve_shape: str,
) -> str:
    """
    Infer a first-pass growth signal from Treasury curve shape.

    This is intentionally simple and will later be augmented
    with economic and market data.
    """
    if curve_shape == "INVERTED":
        return "WEAKENING"

    if curve_shape == "FLAT":
        return "CAUTIOUS"

    if curve_shape == "STEEP":
        return "IMPROVING"

    return "NEUTRAL"


def classify_inflation_regime(
    rate_driver: str,
) -> str:
    """
    Infer inflation pressure from Anchor's rate-driver classification.
    """
    if rate_driver == "INFLATION":
        return "PRESSURE"

    if rate_driver == "REAL_RATE":
        return "STABLE"

    if rate_driver == "MIXED":
        return "MIXED"

    return "STABLE"


def classify_real_rate_regime(
    rate_driver: str,
) -> str:
    """
    Infer real-rate pressure from Anchor's rate-driver classification.
    """
    if rate_driver == "REAL_RATE":
        return "PRESSURE"

    if rate_driver == "INFLATION":
        return "STABLE"

    if rate_driver == "MIXED":
        return "MIXED"

    return "STABLE"


def classify_credit_regime(
    spread_compensation: str,
) -> str:
    """
    Translate credit-spread compensation into a broad
    credit-environment signal.
    """
    if spread_compensation in {"UNFAVORABLE", "THIN"}:
        return "TIGHT"

    if spread_compensation == "MODERATE":
        return "BENIGN"

    if spread_compensation == "MEANINGFUL":
        return "WIDENING"

    if spread_compensation == "HIGH":
        return "STRESSED"

    return "UNKNOWN"


def classify_term_premium_regime(
    curve_shape: str,
    rate_driver: str,
) -> str:
    """
    Infer a first-pass term-premium signal.

    This is only a proxy. Anchor will later incorporate
    an explicit term-premium data series.
    """
    if curve_shape == "STEEP" and rate_driver == "REAL_RATE":
        return "RISING"

    if curve_shape == "INVERTED":
        return "LOW"

    return "NEUTRAL"


def determine_dominant_driver(
    growth: str,
    inflation: str,
    real_rates: str,
    term_premium: str,
    credit: str,
) -> str:
    """
    Determine Anchor's dominant fixed-income regime driver.
    """
    if credit == "STRESSED":
        return "CREDIT_STRESS"

    if real_rates == "PRESSURE" and term_premium == "RISING":
        return "REAL_RATE_TERM_PREMIUM"

    if inflation == "PRESSURE":
        return "INFLATION_PRESSURE"

    if real_rates == "PRESSURE":
        return "REAL_RATE_PRESSURE"

    if growth == "WEAKENING":
        return "GROWTH_SLOWDOWN"

    if credit == "WIDENING":
        return "CREDIT_DETERIORATION"

    return "MIXED"


def determine_confidence(
    growth: str,
    inflation: str,
    real_rates: str,
    term_premium: str,
    credit: str,
    dominant_driver: str,
) -> str:
    """
    Estimate confidence based on how many signals support
    the dominant regime.
    """
    supporting_signals = 0

    if dominant_driver == "CREDIT_STRESS":
        supporting_signals += credit == "STRESSED"

    elif dominant_driver == "REAL_RATE_TERM_PREMIUM":
        supporting_signals += real_rates == "PRESSURE"
        supporting_signals += term_premium == "RISING"

    elif dominant_driver == "INFLATION_PRESSURE":
        supporting_signals += inflation == "PRESSURE"

    elif dominant_driver == "REAL_RATE_PRESSURE":
        supporting_signals += real_rates == "PRESSURE"

    elif dominant_driver == "GROWTH_SLOWDOWN":
        supporting_signals += growth == "WEAKENING"

    elif dominant_driver == "CREDIT_DETERIORATION":
        supporting_signals += credit == "WIDENING"

    if supporting_signals >= 2:
        return "HIGH"

    if supporting_signals == 1:
        return "MEDIUM"

    return "LOW"


def assess_regime(
    curve_shape: str,
    rate_driver: str,
    spread_compensation: str,
) -> RegimeAssessment:
    """
    Create Anchor's first-pass fixed-income regime assessment.
    """
    growth = classify_growth_regime(curve_shape)
    inflation = classify_inflation_regime(rate_driver)
    real_rates = classify_real_rate_regime(rate_driver)
    credit = classify_credit_regime(spread_compensation)

    term_premium = classify_term_premium_regime(
        curve_shape,
        rate_driver,
    )

    dominant_driver = determine_dominant_driver(
        growth,
        inflation,
        real_rates,
        term_premium,
        credit,
    )

    confidence = determine_confidence(
        growth,
        inflation,
        real_rates,
        term_premium,
        credit,
        dominant_driver,
    )

    return RegimeAssessment(
        policy="NEUTRAL",
        growth=growth,
        inflation=inflation,
        real_rates=real_rates,
        term_premium=term_premium,
        credit=credit,
        dominant_driver=dominant_driver,
        confidence=confidence,
    )
