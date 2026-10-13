---
name: se-architecture-trades
description: Decompose functions, compare architectures and record trade-study decisions for engineering systems.
---

# Se Architecture Trades

## When to use
Decompose functions, compare architectures and record trade-study decisions for engineering systems.

## Procedure
1. Map required functions without presupposing implementation.
2. Generate at least two feasible alternatives when trade-offs matter, including build/buy/reuse.
3. State evaluation criteria, weights, assumptions and sensitivity to their variation.
4. Use calculations or test data where possible; distinguish estimated performance from evidence.
5. Record owner-approved decisions and open investigations.

## Required outputs
architecture.md, function-tree.md, trade-study.md, decision-log.md

## Evidence and quality gates
- Cite applicable source IDs from `sources/registry.json` and document specific sections where verified.
- Identify each assumption, unresolved question, owner and review status.
- No fabricated observations, approvals, compliance conclusions or test evidence.
- For safety-critical or regulated decisions, escalate to a qualified human reviewer.

## Primary reference
Source ID: `nasa-se-design`. Check current edition/version and applicability in `sources/registry.json`.
