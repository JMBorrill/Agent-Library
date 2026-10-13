# Life cycle, Key Decision Points and technical reviews

Source: NASA SE Handbook, NASA/SP-2016-6105 Rev 2 (`nasa-se`); PDF pages. Machine-readable:
`catalog/nasa-se-lifecycle.json` (`python -m agentlib nasa-se lifecycle --kind phase|kdp|review|trl`).

## Phases (spaceflight projects, NPR 7120.5)

| Phase | Stage | Purpose (paraphrase, Table 2.2-1 PDF pp. 22-23) | Reviews (blue boxes) | PDF |
|---|---|---|---|---|
| Pre-Phase A: Concept Studies | Pre-Formulation | Broad spectrum of mission ideas; feasibility, draft system-level requirements, technology needs | MCR, informal proposal review | 39 |
| Phase A: Concept and Technology Development | Formulation | Feasibility and desirability; final mission concept, system-level requirements, technology developments, technical management plans; baseline the SEMP | SRR, MDR/SDR | 41 |
| Phase B: Preliminary Design and Technology Completion | Formulation | Initial baseline capable of meeting needs; end-product requirements and preliminary design | PDR, safety review | 43 |
| Phase C: Final Design and Fabrication | Implementation | Complete detailed design, fabricate hardware, code software | CDR, PRR, SIR, safety review | 45 |
| Phase D: System Assembly, Integration and Test, Launch | Implementation | Assemble, integrate, verify, validate and launch; transition to use | TRRs, SAR (or pre-ship review), ORR, FRR, functional/physical configuration audits, safety review | 47 |
| Phase E: Operations and Sustainment | Implementation | Conduct the mission and sustain it | PLAR, CERR, PFAR (human flight), DR, system upgrade review, safety review | 49 |
| Phase F: Closeout | Implementation | Decommission/dispose; analyse returned data and samples | DRR | 50 |

- KDPs are the events at which the decision authority determines readiness to progress to the next phase;
  decisions may carry liens, and a project failing a KDP may retry or be terminated (PDF p. 32).
  KDP A-F sit between the phases in Figure 3.0-1 (PDF p. 34).
- Projects with life-cycle cost above $250 million commit to the Agency Baseline Commitment at the end of
  Phase B (PDF p. 42). Phase B is where top-level and flowed-down requirements are finalised and placed under
  configuration control (PDF p. 42).
- Figure 3.0-1 footnotes (PDF p. 34): flexibility is allowed in timing, number and content of reviews if the
  equivalent information is provided at each KDP; PRR only when there are multiple copies of systems; for
  robotic missions SRR and MDR may be combined; SAR generally applies to human space flight.
- Other life cycles (IT NPR 7120.7, R&T NPR 7120.8, software NPR 7150.2) differ (PDF p. 32).

## Reviews (Table 6.7-1, PDF pp. 200-204; TRR PDF p. 122)

| Review | Name | Phase | Entrance/success criteria | Required products (Table 3.0-1, "**") | PDF |
|---|---|---|---|---|---|
| MCR | Mission Concept Review | Pre-Phase A | NPR 7123.1 Table G-3 | Stakeholder identification (Baseline); Concept definition (Baseline); MOE definition (Approve) | 200 |
| SRR | System Requirements Review | Phase A | NPR 7123.1 Table G-4 (program: G-1) | SEMP (Baseline); Requirements (Baseline) | 200 |
| MDR/SDR | Mission / System Definition Review | Phase A | NPR 7123.1 Table G-5 (program: G-2) | SEMP (Baseline, uncoupled/loosely coupled programs); TPM definition (Approve); Architecture definition (Baseline); Allocation of requirements to next lower level (Baseline); Required leading indicator trends (Initial) | 201 |
| PDR | Preliminary Design Review | Phase B | NPR 7123.1 Table G-6 | Design solution definition (Preliminary) | 201 |
| CDR | Critical Design Review | Phase C | NPR 7123.1 Table G-7 | Design solution definition (Baseline) | 201 |
| PRR | Production Readiness Review | Phase C | NPR 7123.1 Table G-8 | (not in Table 3.0-1) | 202 |
| SIR | System Integration Review | Phase C | NPR 7123.1 Table G-9 | Integration plans (Update); V&V results (Initial) | 202 |
| TRR | Test Readiness Review | Phase D | tailored by the project | (not in Table 3.0-1) | 122 |
| SAR | System Acceptance Review | Phase D | NPR 7123.1 Table G-11 | (not in Table 3.0-1) | 202 |
| ORR | Operational Readiness Review | Phase D | NPR 7123.1 Table G-12 | V&V results (Preliminary); Operations plans (Update); Operational procedures (Update); Decommissioning and Disposal plans (Baseline) | 203 |
| FRR | Flight Readiness Review | Phase D | NPR 7123.1 Table G-13 | V&V results (Baseline); Certification flight/use (Final) | 203 |
| PLAR | Post-Launch Assessment Review | Phase E | NPR 7123.1 Table G-14 | - | 203 |
| CERR | Critical Event Readiness Review | Phase E | NPR 7123.1 Table G-15 | - | 203 |
| PFAR | Post-Flight Assessment Review | Phase E | NPR 7123.1 Table G-16 | - | 204 |
| DR | Decommissioning Review | Phase E | NPR 7123.1 Table G-17 | Decommissioning plans (Update) | 204 |
| DRR | Disposal Readiness Review | Phase F | NPR 7123.1 Table G-18 | Disposal plans (Update) | 204 |

Key results of a successful review (paraphrased from Table 6.7-1):

- **SRR** freezes program/project requirements (PDF p. 200).
- **MDR/SDR**: the mission/system and its operation are understood well enough to warrant design and
  acquisition of end items (PDF p. 201).
- **PDR** approves the **design-to baseline** and authorises proceeding into Implementation toward final
  design; it is the last review of Formulation (PDF p. 201).
- **CDR** approves the **build-to baseline**, production and verification plans, and authorises coding of
  deliverable software and system qualification testing and integration (PDF p. 201).
- **SIR** approves the final as-built baseline and verification plans for integration (PDF p. 202).
- **SAR**: the buyer accepts the system and shipment is authorised (PDF p. 202).
- **ORR**: ready to assume normal operations; **FRR**: maturity exists for launch and flight authorisation
  (PDF p. 203).

TRRs: held informally early and more formally later; several TRRs with tailored entrance/success criteria
assess test ranges, facilities, trained testers, instrumentation, integration labs and support equipment
(PDF p. 122). Glossary: a TRR ensures the test article, facility, support personnel and procedures are
ready (PDF p. 246).

## Product maturity (Table 3.0-1, PDF p. 35)

`nasa-se review-checklist <review>` prints every product and maturity for the review. Highlights:
SEMP preliminary at MCR, baselined at SRR (projects, tightly coupled and single-project programs) or MDR/SDR
(uncoupled/loosely coupled programs); requirements baselined at SRR; architecture and allocation baselined
at MDR/SDR; design solution preliminary at PDR and baselined at CDR; interface definitions and V&V plans
baselined at PDR; V&V results initial at SIR, preliminary at ORR, baselined at FRR; decommissioning and
disposal plans baselined at ORR.

## Running a review well (6.7, PDF pp. 196-205)

1. Plan: purpose, objectives, entry and success criteria, review team make-up (PDF p. 199).
2. Assess against the six technical assessment criteria (PDF p. 196) and the trends of technical measures
   (MOEs, MOPs, KPPs, TPMs) - key reviews are where trends are scrutinised for early warning (PDF p. 199).
3. Capture results, recommendations and actions in review reports/minutes; resolve action items
   (PDF pp. 199, 205).
4. Formality is customisable (tabletop review for a small project vs formal RID/RFA process with boards
   for a large one) without an SE NPR waiver; dropping a required review needs a waiver/deviation (PDF p. 56).
