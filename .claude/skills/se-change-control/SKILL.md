---
name: se-change-control
description: Assess requirement, interface and design changes across the baselined system.
---

# Se Change Control

## When to use
Assess requirement, interface and design changes across the baselined system.

## Procedure
1. Identify changed configuration items and reason for change.
2. Map impacts to requirements, interfaces, hazards, cost/schedule, tests and prior evidence.
3. Document options: accept, revise, defer, reject; do not silently overwrite baselines.
4. Identify tests invalidated by the new configuration and schedule re-verification.
5. Obtain approval from accountable owner before incorporating into controlled baseline.

## Required outputs
change-request.md, impact-assessment.md, baseline-history.md

## Evidence and quality gates
- Cite applicable source IDs from `sources/registry.json` and document specific sections where verified.
- Identify each assumption, unresolved question, owner and review status.
- No fabricated observations, approvals, compliance conclusions or test evidence.
- For safety-critical or regulated decisions, escalate to a qualified human reviewer.

## Primary reference
Source ID: `nasa-se-manage`. Check current edition/version and applicability in `sources/registry.json`.
