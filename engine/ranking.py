"""
Comparative ranking logic for Anchor.

This module converts qualitative opportunity assessments
into deterministic ranking scores so multiple fixed-income
alternatives can be compared consistently.
"""

from dataclasses import dataclass
from typing import Iterable, List

from engine.opportunity import OpportunityAssessment


CLASSIFICATION_SCORES = {
    "ATTRACTIVE": 5,
    "FAVORABLE": 4,
    "SELECTIVE": 3,
    "NEUTRAL": 2,
    "CAUTIOUS": 1,
    "UNATTRACTIVE": 0,
    "AVOID": -1,
}


REGIME_FIT_SCORES = {
    "FAVORABLE": 3,
    "NEUTRAL": 2,
    "CAUTIOUS": 1,
    "UNFAVORABLE": 0,
}


SPREAD_COMPENSATION_SCORES = {
    "HIGH": 4,
    "MEANINGFUL": 3,
    "MODERATE": 2,
    "THIN": 1,
    "UNFAVORABLE": 0,
}


@dataclass
class RankedOpportunity:
    rank: int

    security_type: str
    maturity_years: float
    yield_percent: float
    rating: str | None
    callable: bool

    classification: str
    regime_fit: str
    spread_compensation: str

    score: float
    explanation: str


def opportunity_score(
    assessment: OpportunityAssessment,
) -> float:
    """
    Convert Anchor's qualitative assessment into
    a deterministic comparison score.

    Classification receives the greatest weight because
    it already combines regime fit and relative value.
    """
    classification_score = CLASSIFICATION_SCORES.get(
        assessment.classification,
        0,
    )

    regime_score = REGIME_FIT_SCORES.get(
        assessment.regime_fit,
        0,
    )

    spread_score = SPREAD_COMPENSATION_SCORES.get(
        assessment.spread_compensation,
        0,
    )

    score = (
        classification_score * 5
        + regime_score * 2
        + spread_score
    )

    return float(score)


def rank_opportunities(
    assessments: Iterable[OpportunityAssessment],
) -> List[RankedOpportunity]:
    """
    Rank multiple fixed-income opportunities from highest
    to lowest Anchor score.

    Ties are broken by:
        1. Higher yield
        2. Shorter maturity
        3. Non-callable before callable
        4. Security type alphabetically

    This keeps the ranking deterministic.
    """
    assessments = list(assessments)

    scored = [
        (
            opportunity_score(assessment),
            assessment,
        )
        for assessment in assessments
    ]

    scored.sort(
        key=lambda item: (
            -item[0],
            -item[1].yield_percent,
            item[1].maturity_years,
            item[1].callable,
            item[1].security_type,
        )
    )

    ranked = []

    for index, (score, assessment) in enumerate(
        scored,
        start=1,
    ):
        ranked.append(
            RankedOpportunity(
                rank=index,
                security_type=assessment.security_type,
                maturity_years=assessment.maturity_years,
                yield_percent=assessment.yield_percent,
                rating=assessment.rating,
                callable=assessment.callable,
                classification=assessment.classification,
                regime_fit=assessment.regime_fit,
                spread_compensation=assessment.spread_compensation,
                score=score,
                explanation=assessment.explanation,
            )
        )

    return ranked


def top_opportunity(
    assessments: Iterable[OpportunityAssessment],
) -> RankedOpportunity:
    """
    Return Anchor's highest-ranked opportunity.

    Raises:
        ValueError if no opportunities are supplied.
    """
    ranked = rank_opportunities(assessments)

    if not ranked:
        raise ValueError("No fixed-income opportunities were supplied.")

    return ranked[0]
