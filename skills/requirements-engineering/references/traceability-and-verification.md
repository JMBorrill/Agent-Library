# Traceability and verification planning

Source: NASA SE Handbook, NASA/SP-2016-6105 Rev 2 (`nasa-se`); PDF pages.

## Bidirectional traceability (6.2, PDF pp. 163-165)

- Definitions box (PDF p. 163): *traceability* is a discernible association between logical entities such as
  requirements, system elements, verifications or tasks; *bidirectional traceability* is the ability to trace
  any requirement/expectation to its parent and to its allocated children.
- Requirements Management maintains bidirectional traceability between stakeholder expectations, customer
  requirements, technical product requirements, product component requirements, design documents and test
  plans and procedures (PDF p. 165).
- Record traceability as each requirement is documented; each requirement traces to a parent/source in a
  baselined document **or is identified as self-derived** with concurrence sought from the next higher level
  (e.g. locally adopted good practice, design decisions) (PDF p. 165).
- Evaluate the trace independently where possible: does the child fully address its parent? If not, other
  requirements must complete it. Ensure all top-level parent requirements are allocated to lower levels.
  No parent and not acceptably self-derived => flawed trace or **gold plating** to eliminate. Resolve
  duplication between levels (PDF p. 165).
- Product verification reports include each verified requirement and its bidirectional traceability
  (PDF p. 127); bidirectional traceability status is a requirements management work product (PDF p. 168).

### How `nasa-se trace` implements this

| Check | Severity | Meaning |
|---|---|---|
| orphan | error | No parent, not top level, not self-derived |
| dangling-parent / dangling-child | error | Link to an undefined ID (use `--external PREFIX` for baselined parent documents such as NGO-, MRD-) |
| cycle, self-reference, duplicate-id, missing-id | error | Structural defects |
| no-verification-method / invalid-verification-method | error | Must be Test, Analysis, Inspection or Demonstration |
| one-way-link | warning | Parent lists a child that does not trace back, or vice versa (when `children` are declared) |
| not-allocated | warning | Top-level requirement with no children in a multi-level set |
| self-derived | info | Needs concurrence from the next higher level |

Top level = `--top-level` values, else the level of the first requirement in the file; without levels,
requirements with children but no parent are roots. Coverage stats: % with parent, % with a valid method,
counts per method, % verified (status pass/verified/closed).

## Change control (PDF pp. 166-167)

After requirements are validated and reviewed at SRR they go under formal configuration control; changes
need CCB (or equivalent) approval with impacts on cost, schedule, architecture, design, interfaces, ConOps and
higher/lower requirements assessed (PDF p. 166). Requirements creep countermeasures: a good, agreed ConOps;
flush out unstated requirements early; strict change assessment; official change channels; measure each
change's impact against the risk of not approving it; deny changes that do not fit resource margins
(PDF p. 167).

## Verification methods (box, PDF p. 121)

| Method | Use (paraphrase) |
|---|---|
| Analysis | Mathematical modelling and analytical techniques predict suitability from calculated data or lower-level verification data; includes modelling and simulation and verification by similarity of heritage products. Used when hardware is not available. |
| Demonstration | Showing that use of the end product achieves the requirement; basic confirmation of capability without detailed data gathering (e.g. operator tasks in a mockup). |
| Inspection | Visual examination of the realized product (physical features, markings) incl. inspection of drawings, documents or records. |
| Test | Use of the end product to obtain detailed data under controlled conditions; most resource-intensive; "test as you fly, and fly as you test". |

Humans must be properly represented when operator interaction is involved (human-in-the-loop) (PDF p. 121).
Verification is complete with documented objective evidence of compliance (or waiver) and closure of all
discrepancy and nonconformance reports (PDF p. 128). Verification procedures and reports content: Table 5.3-1
(PDF p. 122).

## Requirements Verification Matrix (Appendix D, PDF pp. 253-255)

Only "shall" requirements are included; each identified by unique ID and source document (PDF p. 253).
Table D-1 columns: Requirement No.; Document; Paragraph; Shall Statement; Verification Success Criteria;
Verification Method; Facility or Lab; Phase; Acceptance Requirement?; Preflight Acceptance?; Performing
Organization; Results (PDF p. 254). Example phases (footnote, PDF p. 255): (1) Pre-Declared Development,
(2) Formal Box-Level Functional, (3) Formal Box-Level Environmental, (4) Formal System-Level Environmental,
(5) Formal System-Level Functional, (6) Formal End-to-End Functional, (7) Integrated Vehicle Functional,
(8) On-Orbit Functional. The matrix is appendix C of the V&V Plan outline (Appendix I, PDF p. 272).

Templates: [../templates/verification-matrix.md](../templates/verification-matrix.md),
[../templates/traceability-matrix.md](../templates/traceability-matrix.md).
