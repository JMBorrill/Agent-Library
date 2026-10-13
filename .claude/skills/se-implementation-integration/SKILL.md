---
name: se-implementation-integration
description: Plan product implementation (make, buy, reuse, with unit-level verification) and an incremental integration sequence in which every step has prerequisites, checks and interface coverage; detect assemblies used before they exist, cycles, unverified components and untested interfaces. Use when planning how components become a working system, preparing an integration plan or test-bed, or reviewing whether an integration sequence is ready to execute.
metadata:
  pack: systems-engineering
  version: "1.1.0"
  sources: "nasa-se-realize nasa-se"
---

# Product implementation and integration

## Purpose
Get from verified parts to a working whole with the fewest surprises: implement or procure each
component with its own acceptance evidence, then integrate in small steps where each step exercises
specific interfaces and has its own checks, so failures are isolated quickly. Corresponds to the NASA
processes *Product Implementation* and *Product Integration* (see References).

## When to use
- Design is stable enough to build/buy components (after CDR-style review for hardware).
- Planning test-bed, harness or software build integration order.
- Reviewing an integration plan before a test readiness review.
- Bringing in COTS or reused components (receiving inspection and acceptance).

**Do not use when:** integrating code continuously in a software repository with automated CI — use
the CI pipeline and `software-code-review`/`sre-production-readiness`; use this skill when software
meets hardware or several systems meet.

## Inputs
Required: component list with source (make/buy/reuse), status and unit-verification state; ICD
(`se-interface-control`); verification activities (`se-verification-validation`).
Template: `assets/templates/integration-plan.json`.

## Procedure
1. **Implementation decision per component**: make, buy, reuse — reference the decision record for
   contested ones (`se-decision-analysis`). For buy/reuse define receiving inspection, documentation
   and acceptance tests; for make define build records and unit tests.
2. **Unit verification first**: each component enters integration only with its unit-level evidence
   (or a recorded, risk-accepted exception).
3. **Design the sequence**: start from the lowest-risk core (often power + control), add one element or
   interface group per step, keep a known-good fallback configuration. Prefer emulators/simulators for
   items not yet available.
4. **For each step** define: items integrated, assembly produced, prerequisite steps, interfaces
   exercised (ICD IDs), checks (verification IDs), instrumentation/logging, hazards and safe state.
5. **Check the plan**: `python3 scripts/integration_check.py plan.json --icd icd.csv`
6. **Execute and record**: configuration of each assembly, check results with evidence, anomalies →
   NCRs; never mark a step done without inspected results.
7. **Feed verification**: completed integration checks become evidence in the V&V matrix.

## Decision criteria
| Situation | Rule |
|---|---|
| Component not unit-verified | Warning — integrate only with recorded risk acceptance |
| Assembly used before its producing step | Error — reorder or add prerequisite |
| Step without checks | Error — every step must prove something |
| ICD interface joined but never listed | Warning — add to the step that first joins those items |
| Step involves hazardous energy | Safe-state procedure + TRR-style check (`se-review-gates`) |
| Integration failure | Revert to last known-good assembly; root cause before proceeding |

## Outputs
`implementation-plan.md` (make/buy/reuse with acceptance), `integration-plan.json`, check report,
`integration-results.md` (executed step records with configuration and evidence).

## Validation
Exit 0 ⇒ sequence is logically executable (every input exists when needed, no cycles, every step has
checks, all components used, final assembly produced). It does not predict integration success.

## Examples
- `assets/examples/integration-pass.json` (+ `icd.csv`) → exit 0; warning: RIG not unit-verified.
- `assets/examples/integration-fail.json` → exit 1: `produced-twice`, `prerequisite-cycle`, `no-checks`,
  `assembly-not-ready`, `unknown-item`, `no-final-assembly`; warnings `interface-not-checked`.

## Escalation and stop conditions
- Steps with stored energy, high voltage, pressure or motion → `safety-risk-reviewer`; physical
  execution requires a qualified human's authorisation.
- Stop integration when an anomaly is unexplained; do not proceed "to see if it goes away".
- Author `vv-engineer`/`systems-engineer`; reviewer `independent-reviewer`.

## References
- `nasa-se-realize` — Product Implementation §5.1, Product Integration §5.2 *(secondary corroboration
  only; see `sources/audits/nasa-se-realize.md`)*.
