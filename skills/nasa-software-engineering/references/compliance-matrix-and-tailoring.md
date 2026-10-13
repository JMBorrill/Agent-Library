# Requirements Mapping Matrix (compliance matrix) and tailoring

Page numbers are PDF pages of NPR 7150.2D (identical to the printed "Page N of 89").

## What the matrix is

- Each project manager with software components maintains one or more requirements mapping matrices
  against the NPR, including requirements delegated to other parties or met through contracts or Space
  Act Agreements (SWE-125, p. 22). Multiple matrices are allowed for multiple components (Note, p. 22).
- The project complies with the requirements marked `X` in Appendix C for its class (SWE-139, p. 22) and
  documents approved tailoring in the plans or procedures that control the affected software (SWE-121,
  p. 22).
- Appendix C (pp. 55-78) lists, for each Chapter 3-5 requirement: section, SWE id, statement, the
  Authority for Classes A-E, `X`/blank for Classes A-E, the Class F Authority and `X`/blank for Class F.
  `X` = invoked consistent with the class and may be tailored with TA approval; blank = optional / not
  invoked (C.3, p. 55; 2.2.4, p. 18). NPR 7150.2D uses no other notation (no "P(Center)").
- Each requirement marked `X` for the project's class should be addressed in the matrix; requirements
  that do not apply (for example IV&V) are tailored out with justification (C.3, p. 55).
- Chapter 2 requirements are not part of the matrix (1.3.1, p. 9).
- Programs/projects may substitute a matrix mapped to their Center's implementation of NPR 7150.2 (C.1,
  p. 55).

## Authorities (Appendix C "Authority" column)

| Authority value | Requirements | Meaning |
|---|---|---|
| Center | 98 of the 100 Chapter 3-5 requirements | Center Director or designated ETA, designated SMA TA, and the CHMO-designated Health and Medical TA (C.3, p. 55). |
| HQ OSMA | SWE-141 (IV&V) | NASA HQ; the NASA Chief, SMA makes the final decision on tailoring of SWE-141 (SWE-223, p. 12). |
| HQ OCE and HQ OSMA | SWE-032 (CMMI rating) | NASA HQ designates the TA for SWE-032 and SWE-141 (Note to 2.1.8.1, p. 16). |
| CIO (Class F column) | Class F rows | The NASA CIO or designee has institutional authority on all Class F projects and joint responsibility on 3.11 cybersecurity requirements (C.2 d, p. 55). |

(Counts computed from `catalog/npr-7150-2d.json`.)

## Tailoring rules

- Tailoring is the process of seeking relief from NPR requirements consistent with objectives, acceptable
  risk and constraints; the responsible program/project/operations manager formally accepts the
  tailoring risk; for human-safety risk the actual risk takers agree to assume it (2.2.1, pp. 17-18).
- Approval of the Authority designated in Appendix C is required for all tailoring of `X` requirements
  (2.2.5, p. 18). A relief request includes the rationale, a risk evaluation and reference to supporting
  material; the dispositioning organization obtains concurrence of organizations that could be affected
  (Note to 2.2.5, pp. 18-19).
- Relief may be requested in the streamlined form of the matrix, with engineering, NASA CIO and SMA
  signatures; the designated SAISO signs for relief of cybersecurity requirements (2.2.6, p. 19).
- The engineering, CIO and SMA authorities review and agree with any tailored requirement per the
  matrix Authority column (SWE-150, p. 19).
- Technical/institutional authorities check the classification, evaluate commitments, confirm that
  "Not-Applicable" entries really do not apply, judge risks and mitigations, approve or disapprove relief,
  and archive approved matrices (SWE-126, pp. 16-17). Approval is shown by signature(s) in the matrix
  (SWE-126 b, p. 17). Tailoring a requirement marked HQ TA needs NASA HQ approval (Note, p. 17).
- Relief from Section 3.11 cybersecurity requirements needs agreement from the SAISO or Center CISO
  (Note to SWE-140, p. 12).

## Status vocabulary used by `nasa-swe`

| Status | Use when | Needs |
|---|---|---|
| Compliant | Requirement is met | Evidence |
| Partially Compliant | Partly met | Evidence and rationale (with the risk of the gap) |
| Non-Compliant | Not met and no relief | Rationale and corrective action |
| Planned | Will be met; work not yet done | Plan reference (evidence later) |
| Tailored | Relief approved or requested | Rationale, risk evaluation, approver per Authority column |
| Not Applicable | Requirement cannot apply (e.g. no IV&V) | Rationale; TA confirms (SWE-126 a(3)) |

This vocabulary is a library convention mapped to the NPR's concepts (commitment, tailoring/relief,
"Not-Applicable"); the NPR does not prescribe status labels. `check-matrix` accepts common aliases
(`N/A`, `waived`, `partial` ...).

## Procedure

```sh
python -m agentlib nasa-swe matrix --class C --safety-critical --format csv -o rmm.csv
# fill Status, Tailoring rationale, Approval, Evidence (keep the swe_id column)
python -m agentlib nasa-swe check-matrix rmm.csv --class C        # exit 1 while errors remain
python -m agentlib nasa-swe check-matrix rmm.csv --class C --format json -o rmm-check.json
```

`check-matrix` reports:

- ERROR: unknown SWE ids, malformed ids, duplicates, an `X` requirement for the class missing from the
  matrix, missing or invalid status, Compliant/Partially Compliant without evidence, Tailored /
  Not Applicable / Non-Compliant / Partially Compliant without rationale.
- WARNING: Tailored without an approval entry; HQ-authority requirement tailored without HQ approval;
  3.11 cybersecurity relief without SAISO/CISO; Chapter 2 requirement listed; class unknown.
- INFO: a listed requirement that is blank (optional) for the class.
- Summary: rows, applicable count, missing applicable, status counts, evidence coverage, percentage
  Compliant of applicable.

## Typical evidence by area

| Area | Evidence examples |
|---|---|
| Planning (3.1) | Approved SDP/SMP, acceptance criteria, milestone list, status reports |
| Cost/schedule (3.2-3.3) | Cost model outputs and parameters, integrated schedule, review minutes |
| Classification (3.5) | Classification record with SA concurrence, archived matrix |
| Safety-critical (3.7) | Hazard reports, SWE-134 design analysis, MC/DC coverage report, complexity report |
| Cybersecurity (3.11) | Cybersecurity assessment, secure coding standard, static analysis results, mitigation test reports |
| Traceability (3.12) | Trace matrix covering the Table 1 links for the class |
| Requirements/design (4.1-4.3) | SRS, architecture description, design description, review records |
| Implementation/test (4.4-4.5) | Coding standard, static analysis, unit test results, test plans/procedures/reports, coverage data |
| CM/risk/peer review (5.1-5.3) | SCM plan, change records, audits, risk register, inspection records with measurements |
| Measurement/defects (5.4-5.5) | Metrics reports, requirements volatility, non-conformance database, severity definitions |
