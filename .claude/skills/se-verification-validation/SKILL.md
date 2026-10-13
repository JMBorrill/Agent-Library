---
name: se-verification-validation
description: Plan and audit product verification (did we build it right — against each requirement) and validation (did we build the right thing — against stakeholder needs) with a traceable V&V matrix, objective acceptance criteria and evidence records. Use when writing a verification matrix or test/validation plan, assessing coverage before a TRR/acceptance review, or checking claimed test results for missing evidence, configuration or independent review.
metadata:
  pack: systems-engineering
  version: "1.1.0"
  sources: "nasa-se-realize nasa-se"
---

# Product verification and validation

## Purpose
Give every approved requirement a planned, objective verification activity and every stakeholder need
a validation activity; then keep results honest — each result carries evidence, a run date, the exact
configuration tested and an independent reviewer. Corresponds to the NASA processes *Product
Verification* and *Product Validation* (see References).

## When to use
- After requirements are drafted (`se-requirements`), to build the V&V matrix and test plan.
- Before a test readiness review (TRR) or acceptance/transition, to audit coverage and evidence.
- When someone reports "all tests pass" — to check what was actually tested, on what configuration.
- When a change invalidates prior evidence (pair with `se-change-control`).

**Do not use when:** you are reviewing software unit-test code quality (use `software-code-review`) or
mapping code to requirements (use `software-requirements-traceability`, then feed results here).

## Inputs
Required: requirements register (`se-requirements` format) including stakeholder needs
(`level=stakeholder`); V&V matrix CSV (`assets/templates/verification-matrix.csv`).
Optional: test procedures, evidence files, configuration/version list, facility constraints.

## Procedure
1. **Separate the two questions.** Verification activities (`type=verification`, ID `<P>-VER-NNN`) trace
   to requirements. Validation activities (`type=validation`, `<P>-VAL-NNN`) trace to stakeholder needs
   (`need_id`) and run in the intended or a representative operational environment with real users or
   operators where possible.
2. **Choose the method** per requirement — see Decision criteria. Simulation/modelling counts as
   *analysis*; state the model's own validation basis.
3. **Write acceptance criteria** that a third party could judge pass/fail without the author present:
   measured quantity, threshold, tolerance, sample size, conditions.
4. **Plan the configuration**: name the hardware revision, firmware/software version and test setup
   for each activity. Results on an unidentified configuration are not evidence.
5. **Run the check**: `python3 scripts/vmatrix_check.py --requirements req.csv matrix.csv`
   (add `--include-proposed` before a baseline review). Fix all errors.
6. **Record results only from inspected evidence**: `result` ∈ {not_tested, pass, fail, blocked}, with
   `evidence_ref` (file/log/report path), `run_date`, `configuration`, `performed_by`, `reviewer`.
   A plan, a simulation run on an unverified model, or an expectation is never a `pass`.
7. **Disposition failures**: a `fail` creates a non-conformance (NCR) — repair, retest, or change the
   requirement via `se-change-control`; waivers need the owner's signed approval.
8. **Report** coverage, failed/blocked items and unvalidated needs to `se-review-gates` / the
   independent reviewer.

## Decision criteria
| Situation | Method |
|---|---|
| Quantitative performance measurable in a representative environment | **test** |
| Not testable on the ground / too costly / destructive; validated models exist | **analysis** (state model validation) |
| Physical attribute, document, drawing, label, code property | **inspection** |
| Function observable as yes/no in operation | **demonstration** |
| Safety-critical requirement | test where at all feasible + independent witness; escalate |
| Result exists but evidence or configuration missing | treat as `not_tested` until supplied |
| Requirement verified only by validation | error — add a verification activity |

## Outputs
- `verification-matrix.csv` (template above); `test-plan.md` / `validation-plan.md` (procedures, setup,
  hazards, pass/fail rules); `evidence-register.md` (where each evidence file lives).
- Coverage report: `vmatrix_check.py --json` (schema `assets/schemas/vmatrix-report.schema.json`).

## Validation
`vmatrix_check.py` exit 0 ⇒ every in-scope requirement has a planned verification activity and every
recorded result has evidence, date and configuration. It does **not** show the tests were adequate,
the evidence genuine, or the product fit for purpose. `passed_pct` is a status metric, not a
qualification statement.

## Examples
- `assets/examples/vmatrix-pass.csv` + `assets/examples/requirements.csv` → exit 0; note it still reports
  `DEMO-SYS-002` as failed — integrity checks do not hide failing results.
- `assets/examples/vmatrix-fail.csv` → exit 1: `result-without-evidence`, `no-configuration`,
  `unknown-requirement`, `validation-used-as-verification`, `method`, `result`,
  `unverified-requirement`; warnings `self-review`, `unvalidated-need`.

## Escalation and stop conditions
- Physical tests involving stored energy, motion, pressure, heat, radiation or people need a test
  readiness review and a qualified human authorisation — this skill never authorises a test.
- Stop and ask when acceptance criteria cannot be made objective, or when a requirement appears
  unverifiable (return it to `se-requirements`).
- Author (`vv-engineer`) and reviewer (`independent-reviewer`) must be different agents/people.

## References
- `nasa-se-realize` — Product Verification §5.3, Product Validation §5.4 *(section numbers from secondary
  sources; primary inaccessible in-session — see `sources/audits/nasa-se-realize.md`)*.
- Method guidance and record-keeping notes: [references/vv-methods.md](references/vv-methods.md).
