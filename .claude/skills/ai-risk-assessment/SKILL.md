---
name: ai-risk-assessment
description: Assess AI product risks using the NIST AI RMF; use for LLM apps, agents and model deployment decisions.
---

# Ai Risk Assessment

## When to use
Assess AI product risks using the NIST AI RMF; use for LLM apps, agents and model deployment decisions.

## Procedure
1. Map the use context, affected users, misuse pathways and consequences.
2. Apply govern/map/measure/manage categories selectively according to risk.
3. Define measured evaluations for accuracy, prompt injection, privacy, fairness and reliability when relevant.
4. Set human oversight boundaries and incident rollback/escalation.
5. Explicitly mark unresolved risks and external compliance reviews.

## Required outputs
model-risk-register.md, eval-plan.md, governance-checklist.md

## Evidence and quality gates
- Cite applicable source IDs from `sources/registry.json` and document specific sections where verified.
- Identify each assumption, unresolved question, owner and review status.
- No fabricated observations, approvals, compliance conclusions or test evidence.
- For safety-critical or regulated decisions, escalate to a qualified human reviewer.

## Primary reference
Source ID: `nist-ai`. Check current edition/version and applicability in `sources/registry.json`.
