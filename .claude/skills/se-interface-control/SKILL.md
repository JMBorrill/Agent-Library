---
name: se-interface-control
description: Define, baseline and check system interfaces (mechanical, electrical, data, software, thermal, operational, human) in an interface control register with owners on both sides, units, ranges/protocols, failure behaviour and verification links; produce an N-squared matrix. Use when drafting an ICD, integrating subsystems or suppliers, reviewing interface readiness before PDR/CDR/integration, or detecting unit mismatches and unowned interfaces.
metadata:
  pack: systems-engineering
  version: "1.1.0"
  sources: "nasa-se-manage nasa-se"
---

# Interface management

## Purpose
Make every boundary between components explicit, jointly owned and verifiable, so integration
surprises (unit mismatches, undefined failure behaviour, version drift) are caught on paper. Corresponds
to the NASA process *Interface Management* (see References).

## When to use
- After logical decomposition / architecture definition, when components and their exchanges are known.
- Before integration steps (`se-implementation-integration`) and design reviews.
- When a supplier, team or software service owns one side of a boundary.
- When any interface parameter changes (then also run `se-change-control`).

**Do not use when:** defining a public software API's full schema (keep OpenAPI/AsyncAPI as the
detailed source and reference it in `range_or_protocol`), or reviewing internal code structure.

## Inputs
Required: component list (`assets/examples/components.csv` format), ICD register CSV
(`assets/templates/icd.csv`) — one row per interface *parameter*.
Optional: requirements register (for `requirement_ids`), V&V matrix (for `verification_id`),
detailed specs (drawings, protocol docs, pinouts).

## Procedure
1. **Enumerate boundaries** from the architecture: for each pair of components ask what crosses —
   force/structure, power, signals, data, heat, fluid, light/RF, operator actions. Include external
   systems and test equipment (rigs, ground support) as components.
2. **Describe each parameter**: value, units on *both* sides, tolerance, range/protocol (connector,
   message ID, rate, timing), version, and **failure behaviour** (what each side does when the
   parameter is absent or out of range).
3. **Assign owners on both sides**; interfaces are agreed by both owners, never by one.
4. **Link** each interface to the requirement(s) it implements and a verification activity.
5. **Check**: `python3 scripts/icd_check.py icd.csv --components components.csv --n2`
   Resolve all errors; use the N² matrix to spot missing or unexpected exchanges (empty cells where
   physics says something must flow; cells on both sides of the diagonal indicating feedback loops).
6. **Baseline**: move `draft → agreed → baselined` only when both owners agree; changes after baseline go
   through `se-change-control`.
7. **Verify** at integration: interface tests are part of the V&V matrix (`se-verification-validation`).

## Decision criteria
| Situation | Rule |
|---|---|
| Units differ but convertible (V vs mV) | Warning in draft; error when baselined — agree one unit |
| Units of different dimension (A vs V) | Error — the parameter is mis-defined |
| No failure behaviour on an agreed interface | Error — define safe/degraded behaviour |
| Same parameter defined twice | Error — conflicting definitions; keep one row |
| One owner missing | Interface cannot be agreed |
| Interface with safety function (e-stop, power cut) | Requires verification by test and safety review |

## Outputs
`icd.csv` (register), `interface-control.md` (narrative, diagrams, references to detailed specs),
N² matrix (`--n2`), check report (`--json`).

## Validation
`icd_check.py` exit 0 ⇒ register is internally consistent (IDs, owners, units, failure behaviour,
links). It does **not** prove physical, electrical or data compatibility — that needs analysis and
interface tests. Unknown units are reported as `info` for manual review.

## Examples
- `assets/examples/icd-pass.csv` with `components.csv` → exit 0; N² matrix shows four exchanges.
- `assets/examples/icd-fail.csv` → exit 1: `unit-conversion` (baselined V vs mV), `unit-incompatible`
  (A vs V), `duplicate-parameter`, `missing-owner-to`, `no-failure-behaviour`, `no-verification`,
  `self-interface`, `status`, `unknown-component`.

## Escalation and stop conditions
- Interfaces carrying hazardous energy or safety functions → `safety-risk-reviewer`.
- Supplier/contractual interfaces → the human contract owner approves the baseline.
- Stop when a component owner is unknown; record as an open action rather than assigning one.

## References
- `nasa-se-manage` — Interface Management §6.3 *(secondary corroboration only; see
  `sources/audits/nasa-se-manage.md`)*.
- N² diagram practice is general systems-engineering usage; no source text reproduced.
