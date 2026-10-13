# Software Development / Management Plan - <project / CSCI name>

> Template aligned to NPR 7150.2D (SWE-013 requires software plans covering the entire life cycle and the
> NPR requirements with approved tailoring). Content recommendations for each plan are in NASA-HDBK-2203
> (SWEHB, not bundled) - check it and your Center's template before baselining. Replace every `<...>`.
> Cite requirements as `[nasa-software-requirements SWE-nnn, p. N]`.

| Field | Value |
|---|---|
| Document id / version | <id> / <version> |
| Software classification | Class <A-F> per classification record <ref> (SWE-020, SWE-176) |
| Safety-critical | <yes/no/pending> per SWE-205 determination <ref> |
| IV&V required | <yes/no> (SWE-141 categories) |
| Requirements Mapping Matrix | <ref> (SWE-125), generated with `nasa-swe matrix --class <X>` |
| Approvals | Project manager, Engineering TA, SMA TA, <CIO for Class F / 3.11> |

## 1. Scope and system overview
- Systems/subsystems containing software and the class of each.
- Software life-cycle model and how it maps to project milestone reviews (NPR does not mandate a model).

## 2. Acquisition approach (SWE-033, SWE-027)
- Options assessed (acquire, develop internally, by contract, enhance, reuse, external source) and decision record.
- COTS/GOTS/MOTS/OSS/reused components: requirements, documentation, licences (with IP counsel), support,
  V&V level, vendor defect monitoring.

## 3. Organisation, responsibilities and training (SWE-017)
- Roles (project manager, software lead, SA, safety, IV&V, CM, test).
- Project-specific training plan and tracking (including SA personnel).

## 4. Processes, deliverables and Government actions (SWE-036, SWE-037, SWE-039, SWE-040, SWE-042)
| Deliverable / electronic product | Owner | Due milestone | Government action (review/approve) |
|---|---|---|---|
| <SRS> | <> | <SRR/PDR> | <approve> |

- Milestones at which developer progress is reviewed and audited.
- Developer status reporting and insight provided to the PM and SA.
- Electronic access to products, traceability, change/non-conformance data, metrics and modifiable source code.

## 5. Cost and schedule (SWE-015, SWE-151, SWE-174, SWE-016, SWE-018, SWE-046)
- Cost model(s) used (number required depends on class and size) and parameters; SA support costs included.
- Software schedule coordinated with the project schedule; dependencies; review cadence.

## 6. Tracking and corrective action (SWE-024)
- Measures compared against plan; corrective actions and commitment changes managed to closure.

## 7. Engineering approach
- Requirements (SWE-050, SWE-051, SWE-184, SWE-053, SWE-054, SWE-055).
- Architecture and design (SWE-057, SWE-143 if Category 1/2, SWE-058).
- Implementation: coding standard, static analysis, unit test, version descriptions, tool accreditation
  (SWE-060, SWE-061, SWE-135, SWE-062, SWE-186, SWE-063, SWE-136).
- Auto-generated code approach if applicable (SWE-146, SWE-206).
- Testing - see the Software Test Plan (SWE-065 ... SWE-211).
- Bi-directional traceability links required for the class (SWE-052, Table 1).

## 8. Safety-critical software (SWE-205, SWE-023, SWE-134, SWE-219, SWE-220)
- Components determined safety-critical, hazard report references, implementation of SWE-134 a-l,
  MC/DC coverage approach, cyclomatic complexity limit and waiver process.

## 9. Cybersecurity (SWE-156, SWE-154, SWE-157, SWE-159, SWE-207, SWE-185, SWE-210)
- Assessment, risks and mitigations, secure coding standard, static analysis, mitigation testing,
  adversarial-action detection requirements, SAISO involvement.

## 10. Supporting processes
- Configuration management - reference the SCM plan (SWE-079 ... SWE-085, SWE-045).
- Risk management (SWE-086).
- Peer reviews/inspections: items reviewed, checklists, criteria, measurements (SWE-087, SWE-088, SWE-089).
- Measurement and analysis (SWE-090, SWE-093, SWE-094, SWE-199, SWE-200).
- Non-conformance management and severity levels (SWE-201 ... SWE-204).

## 11. Software assurance, safety and IV&V interfaces (SWE-022, SWE-131, SWE-178, SWE-179)
- Reference the SA plan; artefacts and access provided to SA and IV&V; issue response process.

## 12. CMMI rating (Class A/B only, SWE-032)
- Developer organisation, rating, appraisal date / disclosure statement.

## 13. Operations, maintenance and retirement (SWE-075, SWE-077, SWE-194, SWE-195, SWE-196)

## 14. Reuse (SWE-147, SWE-148)

## 15. Tailoring
| SWE | Tailoring / relief | Rationale and risk | Approving Authority (Appendix C) | Status |
|---|---|---|---|---|

_This plan supports, but does not replace, the decisions of the accountable NASA authorities._
