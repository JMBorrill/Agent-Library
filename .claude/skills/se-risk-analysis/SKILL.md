---
name: se-risk-analysis
description: Identify and mitigate technical risks and draft FMEA-style analyses; use during design, tests and changes.
---

# Se Risk Analysis

## When to use
Identify and mitigate technical risks and draft FMEA-style analyses; use during design, tests and changes.

## Procedure
1. Identify hazards, failure modes, root causes, effects and detection methods.
2. Distinguish observed failures from plausible failure hypotheses.
3. Score likelihood/severity using an explicitly described ordinal rubric; do not present score as a calibrated probability.
4. Assign mitigation owner, trigger threshold, verification action and residual risk.
5. Escalate safety-critical hazards to qualified human review and withhold automatic release approval.

## Required outputs
risk-register.csv, hazard-analysis.md, mitigations.md

## Evidence and quality gates
- Cite applicable source IDs from `sources/registry.json` and document specific sections where verified.
- Identify each assumption, unresolved question, owner and review status.
- No fabricated observations, approvals, compliance conclusions or test evidence.
- For safety-critical or regulated decisions, escalate to a qualified human reviewer.

## Primary reference
Source ID: `nasa-se-manage`. Check current edition/version and applicability in `sources/registry.json`.
