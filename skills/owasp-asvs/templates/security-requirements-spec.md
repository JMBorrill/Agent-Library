# Security requirements specification - <System / feature>

| Field | Value |
|---|---|
| Baseline | OWASP ASVS 5.0.0, Level <n> (cumulative) |
| Applicable chapters/sections | <list>; exclusions with reasons in section 2 |
| Owner / approver | <names> |
| Version / date | <v0.1>, <date> |

## 1. Context

<System purpose, architecture sketch, trust boundaries, data classes, identity model.>

## 2. Applicability

| Chapter / section | Applicable? | Rationale |
|---|---|---|
| | | |

## 3. Documented security decisions

One row per applicable `Vn.1` documentation requirement (decisions must exist before the paired
implementation requirements can be verified [owasp-asvs Documented security decisions, p. 12]).

| ASVS id | Decision required | Decision (summary) | Where documented / enforced (doc or common library) | Owner |
|---|---|---|---|---|
| v5.0.0-6.1.1 | Anti-automation and rate-limit controls for authentication | | | |
| v5.0.0-8.1.1 | Function- and data-level authorization rules | | | |

## 4. Requirements allocation

Generate the baseline with `python -m agentlib asvs checklist --level <n> --chapters <...> --format yaml`.

| ASVS id | Level | Requirement (short) | Component(s) | Approach / approved library | Acceptance test | Owner | Phase |
|---|---|---|---|---|---|---|---|
| v5.0.0-<id> | | | | | | | |

## 5. Not-applicable requirements

| ASVS id | Justification (architecture-based) |
|---|---|

## 6. Additional (non-ASVS) security requirements

<Organisation- or domain-specific requirements, clearly labelled as not ASVS.>

## 7. Traceability and verification

This specification is the verification checklist: statuses are added later and validated with
`python -m agentlib asvs check-assessment`.

---
Requirement text: OWASP ASVS 5.0.0, (c) The OWASP Foundation, CC BY-SA 4.0.
