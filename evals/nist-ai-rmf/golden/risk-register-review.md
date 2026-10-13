# Review of the TalentRank AI risk register

Tool run: `python -m agentlib ai-rmf check-register hiring-risk-register.csv` -> **FAIL, 5 errors, 1 warning**.

## Defects found

| Risk | Defect | Why it matters | Fix |
|---|---|---|---|
| R-02 | Linked subcategory `MAP 6.1` does not exist (MAP has categories 1-5 only, Table 2, PDF pp. 31-33) | Invented ids break traceability | Replace with MAP 3.5 (human oversight) and MEASURE 2.8 |
| R-03 | Residual rating **high** with no escalation and no acceptance sign-off | High residual risk to applicants with disabilities cannot be silently tolerated; residual risks must be documented (MANAGE 1.4, PDF p. 37) and executive leadership owns AI risk decisions (GOVERN 2.3, PDF p. 28) | Escalate to the AI Risk Committee; add further controls; record decision |
| R-04 | Treatment **accept** with no `accepted_by` | Acceptance is a decision by a named authority (MANAGE 1.3 response options, PDF p. 37) | Record approver and date - or change treatment to mitigate via contract change-notification clause (GOVERN 6.1) |
| R-05 | Residual **high** exceeds inherent **medium** with no justification; also high residual without sign-off; residual L x I = 9 is medium on the matrix | Treatment that increases risk needs explanation | Correct residual to medium (L3 x I3) or justify; add escalation if it stays high |

Other observations (warnings / judgement):
- No risk recorded for the **safe** characteristic - acceptable if justified as low relevance; recorded in the context record.
- R-04 has no controls; vendor model updates should be monitored (MANAGE 3.2).

## Corrected register

| ID | Description | Affected stakeholders | Trustworthiness characteristics | Likelihood | Impact | Inherent rating | Treatment | Controls | Residual likelihood | Residual impact | Residual rating | Residual justification | Owner | Escalated to | Accepted by | Linked subcategories | Review date |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| R-01 | Ranking scores some postcodes lower due to historical hiring concentration, causing unfair rejection | applicants; hiring managers | fair-bias-managed | 4 | 4 | high | mitigate | remove postcode features; quarterly adverse-impact testing | 2 | 4 | medium | | Head of Talent Acquisition | | | MAP 5.1; MEASURE 2.11; MANAGE 1.3 | 2026-12-15 |
| R-02 | Recruiters over-rely on the ranking and skip lower-ranked CVs | applicants; recruiters | accountable-transparent; explainable-interpretable | 4 | 3 | high | mitigate | mandatory review of a random sample of lower-ranked CVs; ranking reasons shown | 3 | 3 | medium | | Recruitment Operations Lead | | | MAP 3.5; MEASURE 2.8; MANAGE 1.3 | 2026-12-15 |
| R-03 | Poor performance on CVs with employment gaps (incl. disability-related) and career changers | applicants with disabilities; career changers | fair-bias-managed; valid-reliable | 4 | 5 | critical | mitigate | supplementary manual screen for gap profiles; disaggregated testing before go-live | 3 | 4 | high | | Head of Talent Acquisition | AI Risk Committee (2026-10-20 meeting) | | MEASURE 2.11; MEASURE 2.5; MANAGE 1.3; MANAGE 1.4 | 2026-11-30 |
| R-04 | Vendor updates the underlying model without notice, changing ranking behaviour | applicants; HR | valid-reliable; secure-resilient | 3 | 3 | medium | accept | quarterly regression test on a fixed CV set | 3 | 3 | medium | | HR Systems Manager | | Chief People Officer, 2026-10-13 | MANAGE 3.1; MANAGE 3.2; GOVERN 6.1 | 2027-01-31 |
| R-05 | Candidate personal data retained in vendor logs beyond retention policy | applicants | privacy-enhanced | 2 | 3 | medium | transfer | contractual deletion clause; annual deletion attestation | 2 | 3 | medium | | Data Protection Officer | | | MAP 4.1; MEASURE 2.10; MANAGE 3.1 | 2026-12-31 |

Re-run of `check-register` on the corrected file: PASS (0 errors). R-03 remains **high** after
treatment and is escalated; the committee must decide whether to accept, add controls or not proceed.

Scales are the library 5x5 convention, not NIST's. This review supports, but does not replace, the
risk owners' and committee's judgement.
