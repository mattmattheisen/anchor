"""
Public service interface for Anchor.

This module provides the primary programmatic entry point
into Anchor's deterministic fixed-income decision system.

External applications should be able to provide:

1. a regime assessment,
2. fixed-income opportunities,
3. relative-value compensation assessments,

and receive Anchor's final JSON-compatible decision output.

No independent analytical logic belongs in this module.
"""

from typing import Any, Dict, Iterable, Tuple

from engine.models import FixedIncomeOpportunity
from engine.orchestrator import run_decision_process
from engine.pipeline import run_decision_pipeline
from engine.regime import RegimeAssessment


def run_anchor(
    opportunities: Iterable[
        Tuple[FixedIncomeOpportunity, str]
    ],
    regime: RegimeAssessment,
    max_selections: int = 3,
) -> Dict[str, Any]:
    """
    Run Anchor's complete fixed-income decision process.

    Parameters
    ----------
    opportunities:
        Iterable of tuples containing:

            (
                FixedIncomeOpportunity,
                spread_compensation,
            )

    regime:
        Anchor's completed deterministic regime assessment.

    max_selections:
        Maximum number of ranked securities to include
        in the final portfolio recommendation.

    Returns
    -------
    dict
        JSON-compatible Anchor decision output.

    Flow
    ----

        FixedIncomeOpportunity inputs
                ↓
        Fixed-Income Decision Pipeline
                ↓
        PipelineResult
                ↓
        Decision Orchestrator
                ↓
        JSON-compatible decision output
    """

    pipeline = run_decision_pipeline(
        opportunities=opportunities,
        regime=regime,
    )

    return run_decision_process(
        pipeline=pipeline,
        max_selections=max_selections,
    )
