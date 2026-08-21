# Anchor

## Fixed-Income Decision System

Anchor is a deterministic fixed-income decision engine designed to evaluate whether an investor is being adequately compensated for the risks they are taking.

It analyzes structured fixed-income opportunities within a defined economic regime and produces a ranked, risk-adjusted, portfolio-level decision.

Anchor is designed to work alongside Perimeter and Sentinel.

## Core Question

> Where is an investor being adequately compensated for the fixed-income risk they are taking?

Anchor is built around that question.

The system does not simply compare stated yields. It evaluates relative value after accounting for security structure, regime fit, risk penalties, and portfolio posture.

---

## What Anchor Does

Anchor evaluates fixed-income opportunities across several layers:

1. Security characteristics
2. Yield and maturity
3. Credit quality
4. Callability
5. Spread compensation
6. Economic regime fit
7. Risk-adjusted yield
8. Opportunity classification
9. Cross-security ranking
10. Portfolio allocation guidance
11. Portfolio recommendation
12. Decision reporting

The result is a deterministic decision object that can be consumed by a CLI, dashboard, API, report generator, or other application.

---

## Architecture

Anchor separates analytical logic from presentation logic.

```text
Structured Security Inputs
          ↓
     Input Validation
          ↓
 Opportunity Assessment
          ↓
   Risk Adjustment
          ↓
       Ranking
          ↓
 Decision Pipeline
          ↓
       Summary
          ↓
 Allocation Guidance
          ↓
Portfolio Recommendation
          ↓
   Decision Report
          ↓
    Serialization
          ↓
JSON-Compatible Output
