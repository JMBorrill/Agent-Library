---
name: se-implementation-integration
description: Plan make/buy/reuse implementation, subsystem integration sequence and compatibility testing.
---

# Se Implementation Integration

## When to use
Plan make/buy/reuse implementation, subsystem integration sequence and compatibility testing.

## Procedure
1. Link implementation choices to approved requirements and justified trade decisions.
2. Specify integration prerequisites, dependencies, fixtures, interfaces and version configuration.
3. Prefer low-risk incremental integration; isolate interface failures at subsystem boundaries.
4. Specify instrumentation and data logging for each integration step.
5. Do not imply integration succeeded until evidence is inspected.

## Required outputs
implementation-plan.md, integration-plan.md, integration-results.md

## Evidence and quality gates
- Cite applicable source IDs from `sources/registry.json` and document specific sections where verified.
- Identify each assumption, unresolved question, owner and review status.
- No fabricated observations, approvals, compliance conclusions or test evidence.
- For safety-critical or regulated decisions, escalate to a qualified human reviewer.

## Primary reference
Source ID: `nasa-se-realize`. Check current edition/version and applicability in `sources/registry.json`.
