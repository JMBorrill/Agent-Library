# Review of the ASVS 5.0.0 Level 1 assessment (V2, V5) - Customer portal 3.2

I ran `python -m agentlib asvs check-assessment fixtures/assessment-l1.yaml` (target Level 1, chapters
V2 and V5; 8 requirements in scope because levels are cumulative and only L1 applies). Exit code 1:
the assessment is **invalid and incomplete, so it cannot be reported yet**.

## Errors to fix

| Item | Problem | Fix |
|---|---|---|
| 2.2.2 | `fail` without a finding reference | Raise a finding (client-side-only price validation) and record its id |
| 2.3.1 | Invalid status `partially` | ASVS verification is pass/fail; skippable checkout steps means `fail` with a finding |
| 2.1.4 | Unknown id - V2.1 has only 2.1.1-2.1.3 in ASVS 5.0.0 | Correct the id (likely 2.1.2 or 2.1.3; check with `asvs show`) or remove it |
| 5.3.1 | `not-applicable` without a justification | Justify (e.g. uploads never stored in a public folder) or verify it |
| 5.2.2 | In-scope requirement with no result | Verify file extension and content checks and record the status |

## Warning

- 5.4.3 is a Level 2 requirement. At a Level 1 target it is a recommendation: keep finding F-07, but
  report it separately and leave it out of the Level 1 result.

## Current figures (from the tool, not final)

| Chapter | In scope | Pass | Fail | N/A | Missing | Compliance |
|---|---|---|---|---|---|---|
| V2 Validation and Business Logic | 4 | 2 | 1 | 0 | 0 | 50.0% |
| V5 File Handling | 4 | 2 | 0 | 1 | 1 | 66.7% |

Overall 57.1% (pass / (in scope - N/A)). These figures will change once the errors are fixed.
Once 2.3.1 is recorded as a fail, Level 1 is not achieved for this scope.

Next step: correct the file and re-run the check until it exits 0. Then draft the report with
`skills/owasp-asvs/templates/verification-report.md`.
