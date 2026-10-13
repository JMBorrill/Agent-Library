---
name: se-requirements
description: Draft, lint and baseline traceable technical requirements (shall-statements with rationale, owner, verification method and measurable acceptance criteria) and manage them under change. Use when turning stakeholder needs or a ConOps into system/subsystem/software requirements, reviewing a requirements register for ambiguity, atomicity, TBDs, orphans or broken parent links, or preparing an SRR-style baseline.
metadata:
  pack: systems-engineering
  version: "1.1.0"
  sources: "nasa-se-design nasa-se-manage nasa-se"
---

# Technical requirements definition and management

## Purpose
Produce a requirements register in which every active requirement is uniquely identified, atomic,
necessary, unambiguous, verifiable, traced to a parent need and owned — and keep it that way as the
design evolves. Corresponds to the NASA common technical processes *Technical Requirements Definition*
and *Requirements Management* (see References for verification status).

## When to use
- Converting stakeholder expectations / ConOps (from `se-stakeholder-conops`) into "shall" requirements.
- Reviewing an existing register before a requirements review (SRR-style) or a baseline.
- Allocating system requirements to subsystems, software or suppliers (flow-down).
- Assessing a register after a change (pair with `se-change-control`).

**Do not use when:** the need itself is still unclear (run `se-stakeholder-conops` first); you need
user stories for a software product backlog (use `product-requirements-brief`, then flow verifiable
items here); or you are writing test procedures (use `se-verification-validation`).

## Inputs
Required
- Parent needs: stakeholder needs, mission objectives, ConOps, or higher-level requirements.
- Requirements register CSV in the template format: `assets/templates/requirements.csv`.
Optional
- Constraints: standards, regulations, interfaces (ICDs), budgets, technology limits.
- Project ID prefix and level scheme (default `<PROJECT>-<STK|SYS|SUB|SW|HW>-<NNN>`).

## Procedure
1. **Frame the level.** Decide the level being written (stakeholder → system → subsystem →
   component/software). Each requirement states *what*, never *how*, at that level.
2. **Derive candidates** from each parent need. For every candidate record: `parent`, `rationale`
   (why it exists / where the number came from), `source` (document, analysis or meeting — never
   invented), `owner`.
3. **Write each statement** as: `<subject> shall <verb> <object> <measurable condition> [under <condition>]`.
   One "shall" per requirement. Replace vague adjectives with numbers and units. Put unknown values as
   `TBD` (value unknown) or `TBR` (value proposed, needs confirmation) — never invent precision.
4. **Assign verification**: method ∈ {test, analysis, inspection, demonstration} and an acceptance
   criterion with a pass/fail threshold, plus a planned `verification_id` (`<PROJECT>-VER-NNN`).
5. **Lint** the register:
   `python3 scripts/req_lint.py <register.csv> --tree`
   Fix every `error`. For each `warning` either fix it or record a justification in `notes`.
6. **Check flow-down completeness**: every non-top-level requirement has a parent; every
   approved parent with derived scope has at least one child (inspect the `--tree` output).
7. **Hand over for verification planning**: give the register to `se-verification-validation`
   (`vmatrix_check.py` confirms every approved requirement has planned verification).
8. **Baseline only with human approval**: status moves `proposed → approved` only when the named
   owner approves; record the approval in the baseline log (`se-configuration-management`).
9. **Manage change**: after a baseline, never edit an approved statement in place — raise a change
   request and run `se-change-control` impact analysis. Retired IDs are never reused.

## Decision criteria
| Situation | Rule |
|---|---|
| Requirement contains TBD/TBR | May stay `proposed`; cannot be `approved` (linter error). Record closure owner/date. |
| Statement needs two "shall"s | Split. Atomic requirements trace and verify independently. |
| No measurable threshold possible | Choose inspection/demonstration with observable criteria, or record it as a goal rather than a requirement. |
| Requirement prescribes a design | Keep only if it is a genuine constraint (interface, standard, customer-mandated); record why in rationale. |
| Value has no source | Mark `TBR`, add rationale "engineering estimate — needs analysis", flag to owner. |
| Linter warning judged acceptable | Document justification in `notes`; reviewer decides. |
| Safety/regulatory requirement | Requires a named qualified owner; escalate (see below). |

## Outputs
- `requirements.csv` — register (template `assets/templates/requirements.csv`).
- Lint report (`req_lint.py --json`, schema `assets/schemas/lint-report.schema.json`).
- `requirements-review.md` — open issues, TBD/TBR list with owners, justification of accepted warnings.

## Validation
- `python3 scripts/req_lint.py register.csv --json` → exit 0 means **no structural errors**.
- `--strict` treats warnings as errors (use before a baseline).
- PASS does **not** mean the requirements are correct, complete, feasible or safe; it means they are
  well-formed and traceable. Technical adequacy is judged by the owner and an independent reviewer.

## Examples
- `assets/examples/requirements-pass.csv` — expected: exit 0, one `need-statement` info.
- `assets/examples/requirements-fail.csv` — expected: exit 1 with `duplicate-id`, `id-format`,
  `tbd-in-approved`, `unknown-parent`, `trace-cycle`, `verification-method`,
  `approved-missing-owner`, and ambiguity/atomicity warnings.
- Worked flow-down: `examples/aster-01/` in the library repository.

## Escalation and stop conditions
- **Stop and ask the owner** when a parent need is missing, contradictory, or when a number cannot be
  sourced — do not fill gaps with plausible values.
- **Escalate to a qualified human** for safety-critical, regulatory, contractual or financial
  requirements; mark them `proposed` until signed.
- Hand to `requirements-engineer` (author) and `independent-reviewer` (challenge) — the author must not
  review their own baseline.

## References
- `nasa-se-design` — NASA SE Handbook §4.2 Technical Requirements Definition *(section number
  unverified in-session; see `sources/audits/nasa-se-design.md`)*.
- `nasa-se-manage` — §6.2 Requirements Management *(unverified in-session)*.
- Requirement-quality rules and rationale: [references/requirements-quality.md](references/requirements-quality.md).
