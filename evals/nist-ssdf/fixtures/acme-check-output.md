# SSDF v1.1 assessment check

organisation: Acme Payments Ltd, scope: Checkout platform (6 services, web + API), assessor: Internal AppSec team, date: 2026-10-01

Validation: FAIL - 3 error(s), 2 warning(s).

## Overall

- Coverage: 50.0% (coverage = (implemented + 0.5*partial) / (tasks - not-applicable); unassessed/invalid rows, implemented-without-evidence and not-applicable-without-justification score 0)
- Fully implemented: 37.5% of 40 applicable tasks (42 assessed tasks, 2 not applicable)
- Counts: implemented 15, partial 10, planned 5, not-implemented 7, not-applicable 2, unevidenced 1, unassessed 2

## By practice group

| Group | Applicable | Implemented | Partial | Planned | Not implemented | Unevidenced | Unassessed | Coverage |
|---|---|---|---|---|---|---|---|---|
| PO Prepare the Organization | 13 | 5 | 4 | 1 | 2 | 1 | 0 | 53.8% |
| PS Protect the Software | 4 | 2 | 0 | 1 | 1 | 0 | 0 | 50.0% |
| PW Produce Well-Secured Software | 14 | 6 | 4 | 2 | 1 | 0 | 1 | 57.1% |
| RV Respond to Vulnerabilities | 9 | 2 | 2 | 1 | 3 | 0 | 1 | 33.3% |

## By practice

| Practice | Tasks | Applicable | Coverage |
|---|---|---|---|
| PO.1 Define Security Requirements for Software Development | 3 | 3 | 50.0% |
| PO.2 Implement Roles and Responsibilities | 3 | 3 | 66.7% |
| PO.3 Implement Supporting Toolchains | 3 | 3 | 50.0% |
| PO.4 Define and Use Criteria for Software Security Checks | 2 | 2 | 25.0% |
| PO.5 Implement and Maintain Secure Environments for Software Development | 2 | 2 | 75.0% |
| PS.1 Protect All Forms of Code from Unauthorized Access and Tampering | 1 | 1 | 100.0% |
| PS.2 Provide a Mechanism for Verifying Software Release Integrity | 1 | 1 | 0.0% |
| PS.3 Archive and Protect Each Software Release | 2 | 2 | 50.0% |
| PW.1 Design Software to Meet Security Requirements and Mitigate Security Risks | 3 | 3 | 83.3% |
| PW.2 Review the Software Design to Verify Compliance with Security Requirements and Risk Information | 1 | 1 | 50.0% |
| PW.4 Reuse Existing, Well-Secured Software When Feasible Instead of Duplicating Functionality | 3 | 3 | 50.0% |
| PW.5 Create Source Code by Adhering to Secure Coding Practices | 1 | 1 | 100.0% |
| PW.6 Configure the Compilation, Interpreter, and Build Processes to Improve Executable Security | 2 | 0 | n/a |
| PW.7 Review and/or Analyze Human-Readable Code to Identify Vulnerabilities and Verify Compliance with Security Requirements | 2 | 2 | 100.0% |
| PW.8 Test Executable Code to Identify Vulnerabilities and Verify Compliance with Security Requirements | 2 | 2 | 25.0% |
| PW.9 Configure Software to Have Secure Settings by Default | 2 | 2 | 0.0% |
| RV.1 Identify and Confirm Vulnerabilities on an Ongoing Basis | 3 | 3 | 50.0% |
| RV.2 Assess, Prioritize, and Remediate Vulnerabilities | 2 | 2 | 75.0% |
| RV.3 Analyze Vulnerabilities to Identify Their Root Causes | 4 | 4 | 0.0% |

## Findings

| Level | Id | Issue |
|---|---|---|
| error | PO.3.3 | status 'implemented' without evidence |
| error | PW.4.2 | status 'not-applicable' without justification |
| error | RV.3.4 | task missing from assessment |
| warning | PS.3.2 | planned without an owner |
| warning | PS.3.2 | planned without a target_date |

## Prioritised gaps

Tool heuristic, not NIST guidance (SSDF practices are not prioritised; PDF p.12): status severity, then number of EO 14028 Section 4e subsections mapped in Appendix A Table 2 (PDF p.33).

| Rank | Tier | Task | Status | EO 14028 4e | Owner | Target | Task text |
|---|---|---|---|---|---|---|---|
| 1 | High | PO.4.2 | not-implemented | 4e(iv), 4e(v) | - | - | Implement processes, mechanisms, etc. to gather and safeguard the necessary information in support of the cri… |
| 2 | High | PS.2.1 | not-implemented | 4e(iii), 4e(x) | - | - | Make software integrity verification information available to software acquirers. |
| 3 | High | PW.8.2 | not-implemented | 4e(iv), 4e(v) | QA lead | - | Scope the testing, design the tests, perform the testing, and document the results, including recording and t… |
| 4 | High | RV.3.3 | not-implemented | 4e(iv), 4e(viii) | - | - | Review the software for similar vulnerabilities to eradicate a class of vulnerabilities, and proactively fix… |
| 5 | High | PO.1.3 | not-implemented | 4e(vi) | Procurement | - | Communicate requirements to all third parties who will provide commercial software components to the organiza… |
| 6 | High | RV.1.3 | not-implemented | 4e(viii) | - | - | Have a policy that addresses vulnerability disclosure and remediation, and implement the roles, responsibilit… |
| 7 | Medium | PW.4.2 | unassessed | - | - | - | Create and maintain well-secured software components in-house following SDLC processes to meet common interna… |
| 8 | Medium | RV.3.2 | not-implemented | - | - | - | Analyze the root causes over time to identify patterns, such as a particular secure coding practice not being… |
| 9 | Medium | RV.3.4 | unassessed | - | - | - | Review the SDLC process, and update it if appropriate to prevent (or reduce the likelihood of) the root cause… |
| 10 | Medium | PO.3.3 | unevidenced | 4e(i)(F), 4e(ii), 4e(v) | Platform team | - | Configure tools to generate artifacts of their support of secure software development practices as defined by… |
| 11 | Medium | PS.3.2 | planned | 4e(vi), 4e(vii), 4e(x) | - | - | Collect, safeguard, maintain, and share provenance data for all components of each software release (e.g., in… |
| 12 | Low | PW.9.1 | planned | 4e(iv) | Product security | 2027-01-15 | Define a secure baseline by determining how to configure each setting that has an effect on security or a sec… |
| 13 | Low | PW.9.2 | planned | 4e(iv) | Product security | 2027-01-15 | Implement the default settings (or groups of default settings, if applicable), and document each setting for… |
| 14 | Low | PO.2.2 | planned | - | AppSec lead | 2027-02-01 | Provide role-based training for all personnel with responsibilities that contribute to secure development. Pe… |
| 15 | Low | RV.3.1 | planned | - | AppSec lead | 2027-04-30 | Analyze identified vulnerabilities to determine their root causes. |
| 16 | Low | PO.5.2 | partial | 4e(i)(C), 4e(i)(E), 4e(i)(F), 4e(ii), 4e(iii), 4e(v), 4e(vi) | IT | 2026-12-31 | Secure and harden development endpoints (i.e., endpoints for software designers, developers, testers, builder… |
| 17 | Low | PO.3.2 | partial | 4e(i)(F), 4e(ii), 4e(iii), 4e(v), 4e(vi) | Platform team | 2026-11-30 | Follow recommended security practices to deploy, operate, and maintain tools and toolchains. |
| 18 | Low | PW.4.1 | partial | 4e(iii), 4e(vi), 4e(x) | Platform team | - | Acquire and maintain well-secured software components (e.g., software libraries, modules, middleware, framewo… |
| 19 | Low | RV.1.1 | partial | 4e(iv), 4e(vi), 4e(viii) | AppSec lead | - | Gather information from software acquirers, users, and public sources on potential vulnerabilities in the sof… |
| 20 | Low | RV.2.2 | partial | 4e(iv), 4e(v), 4e(viii) | AppSec lead | - | Plan and implement risk responses for vulnerabilities. |
| 21 | Low | PO.4.1 | partial | 4e(iv), 4e(v) | AppSec lead | - | Define criteria for software security checks and track throughout the SDLC. |
| 22 | Low | PW.2.1 | partial | 4e(iv), 4e(v) | Architecture | - | Have 1) a qualified person (or people) who were not involved with the design and/or 2) automated processes in… |
| 23 | Low | PO.1.2 | partial | - | AppSec lead | 2026-12-15 | Identify and document all security requirements for organization-developed software to meet, and maintain the… |
| 24 | Low | PW.1.1 | partial | - | AppSec lead | 2027-03-31 | Use forms of risk modeling – such as threat modeling, attack modeling, or attack surface mapping – to help as… |
| 25 | Low | PW.8.1 | partial | - | QA lead | - | Determine whether executable code testing should be performed to find vulnerabilities not identified by previ… |

Self-assessment aid generated from NIST SP 800-218 (SSDF v1.1). It supports, but does not replace, qualified professional judgement, independent assessment or a formal attestation.
