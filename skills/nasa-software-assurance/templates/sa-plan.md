# Software Assurance and Software Safety Plan - <project / component>

> Template for NASA-STD-8739.8B. The SA plan may be stand-alone or part of the SDP/SMP or project SMA plan
> (1.3, p. 6); SWE-013 SA task 2 asks SA to develop and maintain an SA plan including software safety,
> with content defined in NASA-HDBK-2203 (SWEHB, not bundled - consult it and your Center template).
> Cite as `[nasa-software-assurance <locator>, p. N]`.

| Field | Value |
|---|---|
| Version / date | <v> / <yyyy-mm-dd> |
| Software class(es) | <Class X per classification record; SA concurrence (SWE-020 task 1)> |
| Requirements Mapping Matrix | <ref and version> |
| Safety-critical components | <list or "none"; assessment ref> |
| IV&V | <required / not required - SWE-141 rationale; IPEP ref> |
| SMA Technical Authority | <name> |
| Prepared by / approved by / concurrence | <SA lead> / <project manager> / <SMA TA> |

## 1. Purpose, scope and applicable documents
NPR 7150.2D, NASA-STD-8739.8B, project plans, Center procedures.

## 2. Organisation and independence
SA, software safety, IV&V roles; reporting path to the SMA TA; escalation of disagreements (NPR 2.1.6.7).

## 3. Software classification and safety-criticality
- Classification concurrence record.
- Safety-criticality assessment per component (4.2 a-e) - see the assessment template.

## 4. SA/SS task plan (SASS-01, Table 1)
Generated with `python -m agentlib nasa-swe sa-tasks --class <X>`.

| SWE | Task no. | Task | Phase / milestone | Owner (SA / safety / IV&V) | Method | Evidence / record |
|---|---|---|---|---|---|---|
| SWE-013 | 2 | Develop and maintain the SA plan | Formulation | SA lead | Plan | This document |

## 5. Software safety
Hazard analysis participation (Appendix A phases), software safety analysis (SWE-205 task 5), SWE-134
analysis, MC/DC and complexity confirmation (SWE-219, SWE-220), test witnessing (SWE-066 task 2).

## 6. Audits and assessments
| Audit | Basis | Frequency / timing | Criteria |
|---|---|---|---|
| Development processes and practices | SWE-039 task 5 | At least once every two years | <> |
| Peer-review process | SWE-088 task 3 | <> | <> |
| Risk management process | SWE-086 task 2 | <> | <> |

## 7. Reviews and milestones
SA participation in milestone reviews (SWE-037 task 2) and peer reviews (SWE-087).

## 8. Cybersecurity assurance
SWE-156, SWE-154, SWE-159, SWE-185 tasks; independent static analysis where planned.

## 9. Non-conformance and issue tracking
Severity levels (SWE-202), tracking (SWE-201), COTS/OSS assessments (SWE-203), root cause for high
severity (SWE-204); SA discrepancy list (SWE-039 task 7).

## 10. Metrics and reporting
SA metrics, trending (SWE-090 task 2), status reports (SWE-039 task 6), Center repository submissions.

## 11. Schedule and resources
SA schedule (SWE-016 task 2); SA cost estimate incl. safety-critical handling (SWE-015 task 1); training
(SWE-017 task 2).

## 12. IV&V interface (if applicable)
IPEP reference, SMA TA concurrence (4.4.2.3), access arrangements (SWE-178), issue handling (SWE-179).

## 13. Tailoring of SA/SS requirements (4.5; SWE-121 task 2)
| Requirement / task | Tailoring | Rationale and risk | Level (1 class / 2 matrix / 3 SA TA) | SMA TA concurrence |
|---|---|---|---|---|

## 14. Records
Quality records retained (1.3): plans, reports, metrics, analyses, trending results.

_This plan supports, but does not replace, decisions of the SMA Technical Authority._
