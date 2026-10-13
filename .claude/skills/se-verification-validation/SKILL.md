---
name: se-verification-validation
description: Design traceable verification and validation plans and assess objective test evidence.
---

# Se Verification Validation

## When to use
Design traceable verification and validation plans and assess objective test evidence.

## Procedure
1. For every approved requirement define test, analysis, inspection or demonstration and objective acceptance thresholds.
2. Define calibrated measurement method, environment, tolerances, uncertainty and pass/fail rules.
3. Distinguish verification against specifications from validation of real use needs.
4. Record test IDs, run configuration, actual observations and evidence file locations.
5. Report untested, failed or blocked results explicitly; no inference from plans to outcomes.

## Required outputs
verification-matrix.csv, test-plan.md, validation-plan.md, evidence-register.md

## Evidence and quality gates
- Cite applicable source IDs from `sources/registry.json` and document specific sections where verified.
- Identify each assumption, unresolved question, owner and review status.
- No fabricated observations, approvals, compliance conclusions or test evidence.
- For safety-critical or regulated decisions, escalate to a qualified human reviewer.

## Primary reference
Source ID: `nasa-se-realize`. Check current edition/version and applicability in `sources/registry.json`.
