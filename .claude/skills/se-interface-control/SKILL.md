---
name: se-interface-control
description: Define and review system interfaces, boundaries, ownership and compatibility tests.
---

# Se Interface Control

## When to use
Define and review system interfaces, boundaries, ownership and compatibility tests.

## Procedure
1. Enumerate mechanical, electrical, data, software, operational and human interfaces as relevant.
2. Define each interface owner, endpoints, units, ranges, connectors, protocol, latency and failure behavior.
3. Flag missing fields, incompatible units and version mismatches.
4. Draft ICD contracts and assign interface verification evidence.
5. Assess downstream changes whenever an interface evolves.

## Required outputs
interface-control.md, interface-test-matrix.csv

## Evidence and quality gates
- Cite applicable source IDs from `sources/registry.json` and document specific sections where verified.
- Identify each assumption, unresolved question, owner and review status.
- No fabricated observations, approvals, compliance conclusions or test evidence.
- For safety-critical or regulated decisions, escalate to a qualified human reviewer.

## Primary reference
Source ID: `nasa-se-manage`. Check current edition/version and applicability in `sources/registry.json`.
