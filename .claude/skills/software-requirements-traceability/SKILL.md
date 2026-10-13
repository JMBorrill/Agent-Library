---
name: software-requirements-traceability
description: Build and check a requirement-to-code-to-test traceability matrix by scanning source and test files for requirement IDs (comments, docstrings, test names, @req markers) and attaching JUnit results per requirement. Use when proving every approved software requirement has a test, finding tests that cite unknown or retired requirement IDs, preparing verification evidence for a review or release, or auditing trace links after a change.
metadata:
  pack: software
  version: "1.0.0"
  sources: "nasa-software"
---

# Software requirements traceability (requirement → code → test)

## Purpose
Show, for every approved software requirement, where it is implemented and which tests verify it,
with the latest test result — and surface the gaps: approved requirements with no test, tests that
cite IDs that do not exist or are retired, code tagged but untested, and failing tests. The
matrix is evidence for a verification review, not a substitute for one.

## When to use
- Before a test readiness / release review, to show requirement-level verification status.
- After requirements change (new, retired, re-worded) to find stale tags in code and tests.
- When onboarding a codebase to a requirements register produced with `se-requirements`.
- When a CI pipeline needs a gate: "no approved requirement without a test".

**Do not use when:** the requirements themselves are not yet written or linted (run
`se-requirements` first); you need system-level V&V planning across hardware/software (use
`se-verification-validation`); or you need to judge whether a test is adequate (human review).

## Inputs
Required
- Requirements register CSV in the `se-requirements` format (`id`, `level`, `status` used here):
  template `assets/templates/requirements.csv`.
- One or more source directories (`--src`) and test directories (`--tests`).
Optional
- JUnit XML results (`--junit`) from the test run being reported (pytest `--junitxml`, Jest
  `jest-junit`, Maven Surefire, etc.).
- A custom ID regex (`--id-pattern`); default `[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-[0-9]{3,}`.

## Procedure
1. **Agree the tagging convention** with the team: requirement IDs appear in a comment or
   docstring at the implementing function, in the test name (`test_AIOPS_SW_001_...` — underscores
   are read as hyphens), in a JS/TS test title, in a comment directly above a test, or as an
   explicit `@req AIOPS-SW-001` marker. Tags at file level in a test file apply to every test in it.
2. **Lint the register first** (`se-requirements`: `req_lint.py`) so IDs and statuses are valid.
3. **Run the tests** and keep the JUnit XML from that run (record commit SHA and date).
4. **Scan**:
   `python3 scripts/trace_scan.py requirements.csv --src src --tests tests --junit results.xml --matrix-csv trace-matrix.csv`
5. **Resolve every error**: write the missing test (`approved-untested`), fix or remove references
   to unknown/retired IDs (`test-unknown-requirement`, `test-retired-requirement`), fix failing
   tests (`test-failed`). Warnings (`code-untested`, `missing-result`, code tags of unknown IDs) need
   a decision recorded in the review notes.
6. **Sample-check links**: open a sample of matrix rows (all safety/security/tenant-isolation
   rows, plus at least 10% of the rest) and confirm the code and test really address the
   requirement. Record the sample in the review notes.
7. **Publish** the matrix CSV with the run identifier and hand it to `se-verification-validation`
   or the release gate.

## Decision criteria
| Situation | Rule |
|---|---|
| Approved code-level requirement, no test | Error — blocks the gate until a test exists or the requirement is re-planned (inspection/analysis recorded in the V&V matrix). |
| Need/stakeholder-level requirement (`level` = mission/stakeholder/business/need) | Not expected in code tests; validated with users (reported with a note). |
| Linked test has no result in the JUnit file | Status stays `not_tested`; never assume pass. |
| Any linked test failed/errored | Requirement `fail`, error. Skipped tests → `blocked`. |
| All linked tests passed | `pass` — means "tests linked by tag passed", not "requirement verified". |
| Test cites retired/unknown ID | Error: the test is verifying something no longer required, or the ID is mistyped. |
| Proposed requirement tagged in code but untested | Warning: implementation ahead of verification. |
| Safety-, security- or regulatory-relevant requirement | Human verification sign-off required regardless of status. |

## Outputs
- `trace-matrix.csv` (`--matrix-csv`; template `assets/templates/trace-matrix.csv`).
- JSON report (`--json`), schema `assets/schemas/trace-report.schema.json`.
- `traceability-review.md` — sample-check record, accepted warnings with justification.

## Validation
- `python3 scripts/trace_scan.py ... --json` → exit 0 = every approved code-level requirement has
  at least one linked test, no test cites unknown/retired IDs and no linked test failed.
  `--strict` also blocks on warnings. Exit 2 = unreadable input or missing directory.
- PASS does **not** mean the requirements are verified: tags can be wrong, tests can be weak, and
  results apply only to the run supplied. Scanning is lexical (Python comments/docstrings via the
  tokenizer; `//`, `/* */`, `--`, `#` comments elsewhere), so IDs in ordinary string literals in
  source code are ignored by design.

## Examples
- `assets/examples/project-pass/` — booking/reminder service, three approved requirements, all
  linked and passing → exit 0:
  `python3 scripts/trace_scan.py assets/examples/project-pass/requirements.csv --src assets/examples/project-pass/src --tests assets/examples/project-pass/tests --junit assets/examples/project-pass/results-junit.xml`
- `assets/examples/project-fail/` — same project with the reminder test missing → exit 1 with one
  `approved-untested` error for `AIOPS-SW-003`.

## Escalation and stop conditions
- **Stop** if the register has unresolved lint errors or duplicate IDs — the matrix would be wrong.
- **Escalate** failing or missing tests on safety-, security- or tenant-isolation requirements to
  the requirement owner and `security-reviewer`/`software-quality-reviewer` before any release.
- Do not mark requirements verified yourself; status changes need the owner's sign-off. Hand the
  matrix to `independent-reviewer` for challenge on high-consequence releases.

## References
- `nasa-software` — NASA Software Engineering and Assurance Handbook (SWEHB). **INACCESSIBLE**
  in this environment (`sources/audits/nasa-software.md`); no SWE requirement number or handbook
  section is cited here. Bidirectional requirement-to-test traceability is presented as general
  software engineering practice; any NASA-specific obligation (e.g. by software class) is
  *(unverified)* and must be checked against NPR 7150.2 by a human. Source ID: `nasa-software`.
- Related library skills: `se-requirements` (register format), `se-verification-validation`.
- Method notes: [references/traceability-practice.md](references/traceability-practice.md).
