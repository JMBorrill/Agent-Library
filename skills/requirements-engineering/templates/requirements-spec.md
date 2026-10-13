# Requirements specification: <Product / system name>

> Rules: one "shall" per statement; active voice; measurable with tolerances; no unverifiable or ambiguous
> terms; rationale for every requirement; verification method from Test / Analysis / Inspection /
> Demonstration [nasa-se C, p. 249-252; Table 4.2-2, p. 83]. Lint before review:
> `python -m agentlib nasa-se lint-requirements <this file>` (the linter reads the table below).

| Field | Value |
|---|---|
| Document id / version / date | |
| Product layer (system / segment / subsystem / component) | |
| Parent document(s) | <e.g. stakeholder NGOs, MRD, parent SRD> |
| Owner | |
| Baseline status | Draft / Baselined at <review> (CCB controlled thereafter) |

## 1. Scope and context
Purpose of the product, boundaries, link to the ConOps and stakeholder expectations.

## 2. Requirements

| ID | Requirement | Rationale | Parent | Verification method | Verification level | Owner |
|---|---|---|---|---|---|---|
| <SYS-001> | The <product> shall <verb> <object> <measurable criterion with tolerance> <conditions>. | <why; assumptions; link to ConOps/trade> | <parent id or self-derived> | <Test / Analysis / Inspection / Demonstration> | <system> | <name> |

Requirement areas to check for completeness (C.4, p. 250): functional, performance, interface, environment
(development, manufacturing, test, transport, storage, operations), facility, transportation, training,
personnel, operability, safety, security, appearance and physical characteristics, design.

## 3. TBD / TBR list

| ID | Item | Best estimate (TBR) | Rationale | Action to resolve | Responsible | Due |
|---|---|---|---|---|---|---|

## 4. Key Driving Requirements
Requirements with large cost or schedule impact [nasa-se 4.2.1.2.3, p. 81-82].

## 5. Assumptions
All assumptions stated and confirmed before baselining [nasa-se C.3, p. 250].

## 6. Lint and trace results
Paste the summary lines of `lint-requirements` and `trace` and the disposition of each remaining warning.
