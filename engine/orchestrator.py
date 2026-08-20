"""
End-to-end orchestration for Anchor.

This module coordinates Anchor's existing deterministic
decision layers and produces the final serialized output.

It does not perform independent analysis, scoring,
classification, ranking, or portfolio construction.
"""

from typing import Any, Dict

from engine.allocation import build_allocation_guidance
from engine.pipeline import PipelineResult
from engine.portfolio import build_portfolio_recommendation
from engine.report import build_decision_report
from engine.serialization import serialize_decision_report
from engine.summary import summarize_pipeline


def run_decision_process(
    pipeline: PipelineResult,
    max_selections: int = 3,
) -> Dict[str, Any]:
    """
    Run Anchor's downstream decision process from an
    already-completed PipelineResult.

    Flow:

        PipelineResult
            ↓
        DecisionSummary
            ↓
        AllocationGuidance
            ↓
        PortfolioRecommendation
            ↓
        DecisionReport
            ↓
        JSON-compatible dictionary

    The pipeline remains the authoritative source for
    ranking and security-level analytical conclusions.
    """

    summary = summarize_pipeline(
        pipeline
    )

    allocation = build_allocation_guidance(
        pipeline.regime
    )

    portfolio = build_portfolio_recommendation(
        pipeline,
        max_selections=max_selections,
    )

    # PortfolioRecommendation already derives its posture
    # from Anchor's allocation logic. This explicit call
    # keeps the orchestration flow clear and verifies that
    # allocation guidance can be generated independently.
    _ = allocation

    report = build_decision_report(
        portfolio,
        summary,
    )

    return serialize_decision_report(
        report
    )
