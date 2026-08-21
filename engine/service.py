"""
Public service interface for Anchor.

This module provides the primary entry point for running
Anchor's deterministic fixed-income decision process.

External callers should use run_anchor() rather than
calling the internal analytical layers individually.
"""

from typing import Any, Dict, Iterable, Tuple

from engine.models import FixedIncomeOpportunity
from engine.orchestrator import run_decision_process
from engine.pipeline import run_decision_pipeline
from engine.regime import RegimeAssessment
from engine.validation import validate_anchor_inputs


def run_anchor(
    opportunities: Iterable[
        Tuple[FixedIncomeOpportunity, str]
    ],
    regime: RegimeAssessment,
    max_selections: int = 3,
) -> Dict[str, Any]:
    """
    Run Anchor's complete deterministic decision process.

    Parameters
    ----------
    opportunities:
        Iterable containing tuples of:

            (
                FixedIncomeOpportunity,
                spread_compensation,
            )

    regime:
        Completed RegimeAssessment describing the current
        fixed-income environment.

    max_selections:
        Maximum number of ranked opportunities to include
        in the final portfolio recommendation.

    Returns
    -------
    dict
        JSON-compatible serialized Anchor decision report.

    Raises
    ------
    TypeError
        If max_selections is not a true integer.

    ValueError
        If max_selections is less than 1 or if the supplied
        opportunities or regime fail Anchor's input
        validation rules.

    Flow
    ----

        External structured inputs
                ↓
        Public argument validation
                ↓
        Input validation
                ↓
        Fixed-income pipeline
                ↓
        Decision orchestration
                ↓
        Serialized decision report
    """

    if isinstance(max_selections, bool):
        raise TypeError(
            "max_selections must be an integer."
        )

    if not isinstance(max_selections, int):
        raise TypeError(
            "max_selections must be an integer."
        )

    if max_selections < 1:
        raise ValueError(
            "max_selections must be at least 1."
        )

    validated_opportunities = validate_anchor_inputs(
        opportunities=opportunities,
        regime=regime,
    )

    pipeline = run_decision_pipeline(
        opportunities=validated_opportunities,
        regime=regime,
    )

    return run_decision_process(
        pipeline=pipeline,
        max_selections=max_selections,
    )
