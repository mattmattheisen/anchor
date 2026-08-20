"""
Core data models for Anchor.

These models define the information Anchor receives,
analyzes, and returns. Keeping the data structures
separate from the calculation logic makes the system
easier to test, extend, and audit.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TreasuryPoint:
    maturity_years: float
    yield_percent: float


@dataclass
class TipsPoint:
    maturity_years: float
    real_yield_percent: float


@dataclass
class CreditSpreadPoint:
    rating: str
    maturity_years: float
    spread_bps: float


@dataclass
class FixedIncomeOpportunity:
    security_type: str
    maturity_years: float
    yield_percent: float

    rating: Optional[str] = None
    callable: bool = False
    coupon_percent: Optional[float] = None
    price: Optional[float] = None
    cusip: Optional[str] = None
    issuer: Optional[str] = None
    tax_status: Optional[str] = None


@dataclass
class PerimeterSignal:
    regime: str
    risk_state: str
    trend: str
    confidence: Optional[str] = None


@dataclass
class RegimeState:
    policy: str
    growth: str
    inflation: str
    real_rates: str
    term_premium: str
    credit: str

    dominant_driver: str
    confidence: str


@dataclass
class AnchorAssessment:
    classification: str
    relative_value_score: float
    regime_fit_score: float
    credit_compensation_score: Optional[float]
    structure_score: float
    liquidity_score: float

    explanation: str
