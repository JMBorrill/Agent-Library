---
name: se-review-gates
description: Conduct independent SRR/PDR/CDR/TRR-inspired engineering reviews and present readiness risks.
---

# Se Review Gates

## When to use
Conduct independent SRR/PDR/CDR/TRR-inspired engineering reviews and present readiness risks.

## Procedure
1. Select a review appropriate to phase and project risk; avoid pretending that every NASA review is mandatory.
2. Check entrance criteria, approved scope, requirement coverage, open risks, interface control and test readiness.
3. Independently challenge assumptions, design feasibility and missing evidence.
4. Write actions with owners, due dates, severity and required closure evidence.
5. Recommend GO, conditional GO or NO-GO; require project-owner signoff for final decisions.

## Required outputs
review-checklist.md, review-findings.md, gate-disposition.md

## Evidence and quality gates
- Cite applicable source IDs from `sources/registry.json` and document specific sections where verified.
- Identify each assumption, unresolved question, owner and review status.
- No fabricated observations, approvals, compliance conclusions or test evidence.
- For safety-critical or regulated decisions, escalate to a qualified human reviewer.

## Primary reference
Source ID: `nasa-se-manage`. Check current edition/version and applicability in `sources/registry.json`.
