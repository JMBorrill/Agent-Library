# Software Test Plan - <project / CSCI>

> Supports NPR 7150.2D 4.5 Software Testing (PDF pp. 35-37). SWE-065 requires test plans, procedures,
> tests (including test code) and reports. Check NASA-HDBK-2203 and Center templates for full content.

| Field | Value |
|---|---|
| Software class / safety-critical | <Class X> / <yes/no> |
| Test levels | unit / integration / system / acceptance / regression |
| Independent test organisation | <name or n/a> (best practice for Classes A-C per Note to SWE-066) |

## 1. Test items and configuration (SWE-187)
- Items under CM before testing, including test tools, models, simulations, ground support software, COTS/OSS.

## 2. Requirements coverage (SWE-066, SWE-071, SWE-052)
| Requirement id | Test case(s) | Method (test/analysis/inspection) | Hazard trace (SWE-192) | Cyber mitigation (SWE-159) |
|---|---|---|---|---|

## 3. Test environment and platform (SWE-073, SWE-070)
- Target platform or high-fidelity simulation; validation/accreditation status of models and simulations.

## 4. Unit testing (SWE-062, SWE-186)
- Approach, repeatability, safety-critical components per 3.7.4.

## 5. Code coverage (SWE-189, SWE-190, SWE-219)
- Coverage measures selected; coverage measured from test execution; MC/DC = 100 % for safety-critical
  components; disposition of uncovered code (missing requirement, missing test, dead code, deactivated code).

## 6. Off-nominal, hazard and security tests (SWE-192, SWE-159, SWE-134)

## 7. Acceptance tests for loaded/uplinked data, rules and code (SWE-193)

## 8. COTS/GOTS/MOTS/OSS/reused components (SWE-211)

## 9. Regression testing (SWE-191)

## 10. Results evaluation and reporting (SWE-068)
- Pass/fail criteria, non-conformance recording (SWE-201), severity (SWE-202), test report content.

## 11. Pre-delivery verification (SWE-194)

## 12. Software assurance participation
- SA tasks: `python -m agentlib nasa-swe sa-tasks --swe SWE-066` (e.g. test witnessing for safety-critical software).

_Supports, but does not replace, formal verification approval by the accountable authorities._
