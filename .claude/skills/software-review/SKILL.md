---
name: software-review
description: Review code with Google engineering principles, test design and security awareness.
---

# Software Review

## When to use
Review code with Google engineering principles, test design and security awareness.

## Procedure
1. Inspect actual diffs and surrounding code before drawing conclusions.
2. Check design, functional correctness, simplicity, tests, names, documentation and failure behavior.
3. Classify findings by severity and cite file paths and lines.
4. Recommend focused fixes and executable tests; avoid changing unrelated behavior.
5. Report what was run and what could not be verified.

## Required outputs
code-review.md, regression-test-plan.md

## Evidence and quality gates
- Cite applicable source IDs from `sources/registry.json` and document specific sections where verified.
- Identify each assumption, unresolved question, owner and review status.
- No fabricated observations, approvals, compliance conclusions or test evidence.
- For safety-critical or regulated decisions, escalate to a qualified human reviewer.

## Primary reference
Source ID: `google-review`. Check current edition/version and applicability in `sources/registry.json`.
