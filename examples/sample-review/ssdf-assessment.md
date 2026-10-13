# SSDF assessment (fictional example)

Source data: `data/ssdf-assessment.yaml`.

```text
# SSDF v1.1 assessment check

organisation: Acme Payments Ltd (fictional), scope: Acme Checkout API (fictional), commit a1b2c3d, assessor: secure-development-reviewer (AI-assisted), date: 2026-10-13

Validation: PASS - 0 error(s), 0 warning(s).

## Overall

- Coverage: 88.8% (coverage = (implemented + 0.5*partial) / (tasks - not-applicable); unassessed/invalid rows, implemented-without-evidence and not-applicable-without-justification score 0)
- Fully implemented: 82.5% of 40 applicable tasks (42 assessed tasks, 2 not applicable)
- Counts: implemented 33, partial 5, planned 2, not-applicable 2

## By practice group

| Group | Applicable | Implemented | Partial | Planned | Not implemented | Unevidenced | Unassessed | Coverage |
|---|---|---|---|---|---|---|---|---|
| PO Prepare the Organization | 13 | 11 | 2 | 0 | 0 | 0 | 0 | 92.3% |
| PS Protect the Software | 4 | 3 | 0 | 1 | 0 | 0 | 0 | 75.0% |
| PW Produce Well-Secured Software | 14 | 13 | 1 | 0 | 0 | 0 | 0 | 96.4% |
| RV Respond to Vulnerabilities | 9 | 6 | 2 | 1 | 0 | 0 | 0 | 77.8% |

## By practice

| Practice | Tasks | Applicable | Coverage |
|---|---|---|---|
| PO.1 Define Security Requirements for Software Development | 3 | 3 | 100.0% |
| PO.2 Implement Roles and Responsibilities | 3 | 3 | 100.0% |
| PO.3 Implement Supporting Toolchains | 3 | 3 | 100.0% |
| PO.4 Define and Use Criteria for Software Security Checks | 2 | 2 | 50.0% |
| PO.5 Implement and Maintain Secure Environments for Software Development | 2 | 2 | 100.0% |
| PS.1 Protect All Forms of Code from Unauthorized Access and Tampering | 1 | 1 | 100.0% |
| PS.2 Provide a Mechanism for Verifying Software Release Integrity | 1 | 1 | 0.0% |
| PS.3 Archive and Protect Each Software Release | 2 | 2 | 100.0% |
| PW.1 Design Software to Meet Security Requirements and Mitigate Security Risks | 3 | 3 | 100.0% |
| PW.2 Review the Software Design to Verify Compliance with Security Requirements and Risk Information | 1 | 1 | 100.0% |
| PW.4 Reuse Existing, Well-Secured Software When Feasible Instead of Duplicating Functionality | 3 | 3 | 100.0% |
| PW.5 Create Source Code by Adhering to Secure Coding Practices | 1 | 1 | 100.0% |
| PW.6 Configure the Compilation, Interpreter, and Build Processes to Improve Executable Security | 2 | 0 | n/a |
| PW.7 Review and/or Analyze Human-Readable Code to Identify Vulnerabilities and Verify Compliance with Security Requirements | 2 | 2 | 100.0% |
| PW.8 Test Executable Code to Identify Vulnerabilities and Verify Compliance with Security Requirements | 2 | 2 | 75.0% |
| PW.9 Configure Software to Have Secure Settings by Default | 2 | 2 | 100.0% |
| RV.1 Identify and Confirm Vulnerabilities on an Ongoing Basis | 3 | 3 | 83.3% |
| RV.2 Assess, Prioritize, and Remediate Vulnerabilities | 2 | 2 | 100.0% |
| RV.3 Analyze Vulnerabilities to Identify Their Root Causes | 4 | 4 | 62.5% |

## Prioritised gaps

Tool heuristic, not NIST guidance (SSDF practices are not prioritised; PDF p.12): status severity, then number of EO 14028 Section 4e subsections mapped in Appendix A Table 2 (PDF p.33).

| Rank | Tier | Task | Status | EO 14028 4e | Owner | Target | Task text |
|---|---|---|---|---|---|---|---|
| 1 | Low | PS.2.1 | planned | 4e(iii), 4e(x) | Platform security lead | 2026-12-15 | Make software integrity verification information available to software acquirers. |
| 2 | Low | RV.3.4 | planned | - | Platform security lead | 2026-12-15 | Review the SDLC process, and update it if appropriate to prevent (or reduce the likelihood of) the root cause… |
| 3 | Low | RV.1.2 | partial | 4e(iv), 4e(vi), 4e(viii) | AppSec team | - | Review, analyze, and/or test the software’s code to identify or confirm the presence of previously undetected… |
| 4 | Low | PO.4.1 | partial | 4e(iv), 4e(v) | AppSec team | - | Define criteria for software security checks and track throughout the SDLC. |
| 5 | Low | PO.4.2 | partial | 4e(iv), 4e(v) | AppSec team | - | Implement processes, mechanisms, etc. to gather and safeguard the necessary information in support of the cri… |
| 6 | Low | PW.8.2 | partial | 4e(iv), 4e(v) | AppSec team | - | Scope the testing, design the tests, perform the testing, and document the results, including recording and t… |
| 7 | Low | RV.3.3 | partial | 4e(iv), 4e(viii) | AppSec team | - | Review the software for similar vulnerabilities to eradicate a class of vulnerabilities, and proactively fix… |

Self-assessment aid generated from NIST SP 800-218 (SSDF v1.1). It supports, but does not replace, qualified professional judgement, independent assessment or a formal attestation.
```
