# Tailoring, customisation and the SEMP

Source: NASA SE Handbook, NASA/SP-2016-6105 Rev 2 (`nasa-se`), Section 3.11 (PDF pp. 52-62) and
Appendix J (PDF pp. 282-293). PDF pages.

## Tailoring vs customisation (3.11.1, PDF p. 52)

| | Tailoring | Customisation |
|---|---|---|
| Definition (NPR 7123.1, quoted by the handbook) | "the process used to seek relief from SE NPR requirements consistent with program or project objectives, allowable risk, and constraints" | "the modification of recommended SE practices that are used to accomplish the SE requirements" |
| Approval | Results in deviations or waivers; documented in the next SEMP revision, e.g. via the Compliance Matrix | No waiver/deviation; significant customisation should be documented in the SEMP |

An acceptable risk posture must be understood and agreed by the project, customer/stakeholders, Center
management and independent reviewers (PDF p. 52).

## Criteria that drive how much tailoring is acceptable (3.11.2, PDF p. 53)

Type of mission; criticality to the Agency Strategic Plan; acceptable risk level; national significance;
complexity; mission lifetime; cost; launch constraints. NPR 8705.4 risk classification is a starting point.

## Ways to tailor or customise (3.11.4, PDF p. 55)

Tailoring: (1) eliminate a requirement that does not apply; (2) eliminate one that is overly burdensome
(cost of implementing adds more risk than not complying); (3) scale a requirement to balance cost and risk.
Customising: adjust how each of the 17 SE processes is implemented; adjust formality and timing of reviews.

- Non-applicable requirements: e.g. contract requirements for an in-house project, software requirements
  for a system without software (PDF p. 55).
- Scope: the SE NPR requires no additional stand-alone documents; small projects can put plans in the
  project plan or SEMP; a waiver is only needed if the governing PM directive requires a stand-alone
  document (PDF p. 55).
- Reviews: criteria in NPR 7123.1 Appendix G are expected to be customised; combining SRR and SDR/MDR is
  allowed if both intents are met; omitting a required review needs a waiver/deviation (PDF pp. 55-56).
- Table 3.11-1 (types A-F) and Table 3.11-2 (example of tailoring required project products, e.g. SEMP
  "Tailor" for types D-F) illustrate scaling (PDF pp. 56-60); Table 3.11-3 shows a Compliance Matrix
  (PDF p. 62). Approvals: deviations/waivers go to the requirement owners or in bulk via the NPR 7123.1
  appendix H Compliance Matrix (3.11.6, PDF p. 60).

## SEMP (Appendix J)

Purpose: the foundation document for the technical effort; documents which technical processes will be
used, how, by whom and with what resources, and serves as an agreement within the project on how technical
work is conducted (PDF p. 282). Three general sections: technical program planning and control; systems
engineering processes (incl. tailoring); engineering specialty integration (PDF p. 282).

Annotated outline headings (J.3, PDF pp. 284-292):

1.0 Purpose and Scope - 2.0 Applicable Documents - 3.0 Technical Summary (3.1 System Description, 3.2
System Structure, 3.3 Product Integration, 3.4 Planning Context, 3.5 Boundary of Technical Effort, 3.6
Cross References) - 4.0 Technical Effort Integration (4.1 Responsibility and Authority, 4.2 Contractor
Integration, 4.3 Analytical Tools that Support Integration) - 5.0 Common Technical Processes
Implementation - 6.0 Technology Insertion - 7.0 Additional SE Functions and Activities (7.1 System Safety,
7.2 Engineering Methods and Tools, 7.3 Specialty Engineering, 7.4 Technical Performance Measures, 7.5
Heritage, 7.6 Other) - 8.0 Integration with the Project Plan and Technical Resource Allocation - 9.0
Compliance Matrices - Appendices, Templates, References.

Notable content rules:

- Section 5.0 describes, for each of the 17 processes, resources, responsibility (e.g. RACI), training,
  configuration control of work products, stakeholder involvement, monitoring, metrics, adherence
  evaluation and management review, plus project-specific tailoring (PDF pp. 288-289).
- 7.4 TPMs: the minimally required TPMs per NPR 7123.1 are mass margins (hardware projects), power margins
  (powered projects) and review trends incl. closure of review actions; other suggested trends cover
  requirements, interfaces, verification, software, problem reports, cost, schedule and staffing (PDF p. 291).
- 9.0 Compliance Matrix: each NPR requirement marked compliant / partially compliant / noncompliant, with
  the process that achieves compliance or the rationale for noncompliance (PDF p. 292).
- Table J-1 gives SEMP scope by life-cycle phase (PDF p. 293). The SEMP is preliminary at MCR and baselined at
  SRR (projects) or MDR/SDR (uncoupled/loosely coupled programs) (Table 3.0-1, PDF p. 35).

Template: [../templates/semp-outline.md](../templates/semp-outline.md).
