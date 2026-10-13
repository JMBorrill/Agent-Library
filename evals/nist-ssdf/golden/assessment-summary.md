# SSDF v1.1 gap assessment summary - Acme Payments Ltd (checkout platform)

## Scope and method

Self-assessment by the internal AppSec team (2026-10-01) of the checkout platform (6 services, web + API)
against the 42 tasks of NIST SP 800-218, SSDF v1.1, Table 1 (PDF pp.14-28). Figures below are copied from
`python -m agentlib ssdf check-assessment` (reference date 2026-10-13); they are not recomputed by hand.

## Overall result

- Self-assessed coverage: **50.0%** (formula: (implemented + 0.5 x partial) / applicable tasks; unevidenced
  "implemented" rows and unjustified "not-applicable" rows earn no credit).
- Fully implemented: 37.5% of 40 applicable tasks.
- Counts: implemented 15, partial 10, planned 5, not-implemented 7, not-applicable 2, implemented without
  evidence 1, unassessed 2.
- Validation: **FAIL** - 3 errors and 2 warnings must be fixed before this worksheet is used externally.

This is a self-assessed coverage figure. SSDF is not a checklist and this result is not a compliance or
certification statement.

## Results by practice group

| Group | Applicable | Coverage |
|---|---|---|
| PO Prepare the Organization | 13 | 53.8% |
| PS Protect the Software | 4 | 50.0% |
| PW Produce Well-Secured Software | 14 | 57.1% |
| RV Respond to Vulnerabilities | 9 | 33.3% |

RV is the weakest group: no vulnerability disclosure policy (RV.1.3) and no root-cause analysis practice
(RV.3.2, RV.3.3; RV.3.4 not assessed).

## Validation issues

| Task | Issue | Fix |
|---|---|---|
| PO.3.3 (p.16) | `implemented` without evidence | Attach the scan-result retention configuration and audit-trail location, or downgrade to `partial` |
| PW.4.2 (p.21) | `not-applicable` without justification | Justify (e.g. no in-house shared components) or assess it |
| RV.3.4 (p.27) | Task missing from the worksheet | Add the row and assess it |
| PS.3.2 (p.19) | `planned` with no owner and no target date (warning) | Name an owner and date |

Reviewer note: PW.6.1 and PW.6.2 are marked not applicable because the services are interpreted. PW.6
covers "compiler, interpreter, and build tools", so the N/A should be reconsidered; at least the build tool
and interpreter configuration is in scope.

## Prioritised gaps

The ordering starts from the tool heuristic (status severity, then the number of EO 14028 Section 4e
subsections that SP 800-218 Appendix A Table 2 maps to the task). SSDF itself does not prioritise practices
(PDF p.12), so this is our heuristic, adjusted for context.

| Rank | Task | Status | Why it matters | Proposed action | Owner | Target |
|---|---|---|---|---|---|---|
| 1 | PS.2.1 (p.19) | not-implemented | Acquirers cannot verify release integrity | Publish release hashes; sign images with a verifiable certificate | Platform team | 2026-12-31 |
| 2 | PW.8.2 (p.24) | not-implemented | No DAST or fuzzing for a public payments API | Add DAST to CI for public APIs; record and triage results | QA lead | 2027-01-31 |
| 3 | RV.1.3 (p.26) | not-implemented | No route for researchers to report issues | Publish a disclosure policy and PSIRT process | AppSec lead | 2026-12-15 |
| 4 | PO.4.2 (p.17) | not-implemented | Security check data is not gathered or protected | Retain gate results immutably and automate decisions | AppSec lead | 2027-01-31 |
| 5 | RV.3.3 (p.27) | not-implemented | Vulnerability classes are not eradicated proactively | Variant analysis after each confirmed vulnerability | AppSec lead | 2027-03-31 |
| 6 | PO.1.3 (p.14) | not-implemented | Supplier contracts lack security requirements | Add security clauses and provenance requirements | Procurement | 2027-03-31 |
| 7 | PS.3.2 (p.19) | planned (no owner) | No SBOM/provenance for releases | Generate, protect and share SBOMs per release | Platform team | 2027-01-31 |
| 8 | RV.3.2, RV.3.4 | not-implemented / unassessed | Root causes are not analysed over time | Start root-cause records and quarterly review | AppSec lead | 2027-04-30 |

## Roadmap

- **0-30 days**: fix validation issues; publish a disclosure policy (RV.1.3); assign owner for PS.3.2.
- **31-90 days**: release hashes and signing (PS.2.1); immutable retention of check results (PO.4.2); DAST for
  public APIs (PW.8.2).
- **3-12 months**: SBOM programme (PS.3.2), supplier requirements (PO.1.3), root-cause process (RV.3.x).

## Limitations

Self-assessment with sampled evidence. The coverage formula and prioritisation are tool heuristics, not NIST
guidance. This summary supports, but does not replace, qualified professional judgement, independent
assessment or a formal attestation by an accountable officer.
