# Traceability practice notes

Original guidance for this library. The registered source (`nasa-software`, NASA SWEHB) could not
be read in this environment, so nothing here is attributed to it; treat any resemblance to NASA
requirements as *(unverified)* general practice.

## Why bidirectional trace
- **Forward** (requirement → code → test): shows nothing approved was forgotten.
- **Backward** (test/code → requirement): shows nothing is built or tested that no longer has a
  reason to exist (gold-plating, stale tests after a requirement was retired).

## Tag placement conventions supported by `trace_scan.py`
| Where | Example | Linked to |
|---|---|---|
| Python comment / docstring in source | `"""Implements AIOPS-SW-001 ..."""` | code location |
| `@req` marker anywhere | `# @req AIOPS-SW-002` | code or test |
| Python test name | `def test_AIOPS_SW_001_rejects_overlap` | that test |
| Comment/docstring inside a Python test | `# verifies AIOPS-SW-002` | that test |
| JS/TS test title | `it('AIOPS-SW-003 sends reminder', ...)` | that test |
| Comment directly above a JS/TS test | `// AIOPS-SW-003` | that test |
| Module docstring/comment outside tests in a test file | `"""Tests for AIOPS-SW-010"""` | every test in the file |

JUnit matching uses the testcase `name` (parametrised suffixes like `[case1]` are stripped). Jest
titles must be unique within the results for reliable matching.

## Result semantics
- `pass` only when every linked test has a JUnit result and all passed.
- `fail` when any linked test failed or errored; `blocked` when results are skips only.
- `not_tested` otherwise — including partial results. Absence of evidence is not a pass.

## Common traps
- Tagging the whole module in a test file ("covers AIOPS-SW-001..020") — inflates coverage.
  Prefer tags on individual tests.
- Copy-pasted tests carrying the wrong ID — catch with the sample check.
- Requirements verified by inspection or analysis: record them in the V&V matrix
  (`se-verification-validation`) rather than inventing a token test.
- Results from a different commit than the code reviewed — record the commit SHA with the run.
