---
name: se-requirements
description: Draft, review and trace measurable technical requirements; use when converting missions into verifiable obligations and acceptance tests.
---

# Se Requirements

## When to use
Draft, review and trace measurable technical requirements; use when converting missions into verifiable obligations and acceptance tests.

## Procedure
1. Draft uniquely identified atomic requirements as clear shall-statements only when justified.
2. Record the origin, rationale, units, normal/off-nominal conditions and approval status.
3. Reject ambiguous adjectives like fast, robust or user-friendly unless operationally defined.
4. Assign a verification method and acceptance threshold or mark them unresolved.
5. Build parent-child and requirement-to-test traceability; flag orphan and conflicting items.

## Required outputs
requirements.csv, verification-matrix.csv, requirements-review.md

## Evidence and quality gates
- Cite applicable source IDs from `sources/registry.json` and document specific sections where verified.
- Identify each assumption, unresolved question, owner and review status.
- No fabricated observations, approvals, compliance conclusions or test evidence.
- For safety-critical or regulated decisions, escalate to a qualified human reviewer.

## Primary reference
Source ID: `nasa-se-design`. Check current edition/version and applicability in `sources/registry.json`.
