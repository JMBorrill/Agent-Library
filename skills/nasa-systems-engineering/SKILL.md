---
name: nasa-systems-engineering
description: >-
  Applies the NASA Systems Engineering Handbook (NASA/SP-2016-6105 Rev 2): the SE engine of 17 common
  technical processes, the project life cycle (Pre-Phase A to F) with Key Decision Points, life-cycle
  technical reviews (MCR, SRR, MDR/SDR, PDR, CDR, PRR, SIR, TRR, SAR, ORR, FRR, PLAR, CERR, PFAR, DR,
  DRR), SE product maturity per review, the SEMP, tailoring/customisation, trade studies (decision
  analysis), technical risk records, ConOps and Technology Readiness Levels. Deterministic tools emit
  review readiness checklists, list processes/phases/reviews/TRLs and compute weighted decision
  matrices. Use when planning or assessing a system/mission/product development, preparing or judging a
  life-cycle review package, writing a SEMP or ConOps, tailoring SE practice for a small project,
  running a trade study, assessing technology maturity, or defining technical options for a business case.
license: Skill text MIT; NASA/SP-2016-6105 Rev 2 is a US Government work
metadata:
  version: 1.0.0
  category: systems-engineering
  maturity: beta
  sources: [nasa-se]
  catalogs: [nasa-se-processes, nasa-se-lifecycle, nasa-requirements-checklist]
  tools:
    - "python -m agentlib nasa-se processes"
    - "python -m agentlib nasa-se lifecycle"
    - "python -m agentlib nasa-se review-checklist"
    - "python -m agentlib nasa-se trade-study"
    - "python -m agentlib nasa-se lint-requirements"
    - "python -m agentlib nasa-se trace"
---

# NASA systems engineering (SE Handbook Rev 2)

The NASA SE Handbook describes **17 common technical processes** (the "SE engine", from NPR 7123.1)
applied iteratively and recursively at every product layer and in every life-cycle phase, a
spaceflight project life cycle of seven phases separated by **Key Decision Points**, and a set of
**life-cycle reviews** whose entrance/success criteria live in NPR 7123.1 Appendix G. The handbook is
guidance, "not intended in any way to be a directive" (PDF p. 10). All process, phase, review, product
maturity and TRL data in this skill come from the catalogs; run the tools rather than recalling them.

## When to use

- Planning the technical effort of a new system, mission, instrument, facility or product (any
  domain that benefits from disciplined SE), including the SEMP and life-cycle tailoring.
- Preparing, self-assessing or chairing a life-cycle review (e.g. "are we ready for PDR?").
- Writing a ConOps, defining stakeholder expectations / MOEs, or choosing an architecture by trade study.
- Assessing technology maturity (TRL) or heritage reuse; recording technical risks.
- Defining technical options (scope, key requirements, risks, maturity) for a business case
  (stage `technical-options` of `workflows/public-investment-business-case.yaml`).

For requirement writing, validation, traceability and verification matrices use
`skills/requirements-engineering/` (same source, Appendix C/D). Not for: NASA software engineering
requirements (NPR 7150.2) or software assurance - use the dedicated skills.

## Key facts (verified in the PDF)

- Processes 1-4 system design, 5-9 product realization (tasks executing the project), 10-17 technical
  management (crosscutting) - Figure 2.1-1, PDF pp. 18-19. List: `nasa-se processes`.
- Phases: Pre-Phase A (Pre-Formulation); A, B (Formulation); C, D, E, F (Implementation); KDP A-F
  separate them (PDF pp. 32-34). Phase purposes: Table 2.2-1 (PDF pp. 22-23).
- Review purposes/timing/results: Table 6.7-1 (PDF pp. 200-204); TRR: PDF p. 122. Each review's
  entrance and success criteria are **not reproduced in the handbook** - it cites NPR 7123.1 Tables
  G-1 to G-18. Say so; never invent criteria.
- Product maturity expected at each review (e.g. SEMP and Requirements baselined at SRR, design
  solution baselined at CDR): Table 3.0-1, PDF p. 35.
- Verification = "was the product realized right?" against "shall" statements; validation = "was the
  right product realized?" against stakeholder expectations/ConOps (PDF pp. 24-25, 116, 129).
- TRL 1-9 (Figure G.4-1, PDF p. 264); a system's TRL is its lowest element TRL (PDF p. 268); heritage in
  a changed architecture/environment drops to TRL 5 initially (PDF p. 265).

## Workflow

1. **Frame the effort.** Identify the product layer, current phase and next review:
   `python -m agentlib nasa-se lifecycle --kind phase` and `--kind review`. State the governing
   life cycle (NPR 7120.5 spaceflight; IT, R&T and software life cycles differ - PDF p. 32).
2. **Plan with the SE engine.** For each of the 17 processes decide how it is implemented, by whom, and
   what it produces this phase (`nasa-se processes --id <n>` shows inputs, outputs and activity
   headings with pages). Record this in the SEMP using [templates/semp-outline.md](templates/semp-outline.md)
   (Appendix J structure). Detail: [references/se-engine.md](references/se-engine.md).
3. **Tailor deliberately.** Classify the project (mission type, criticality, risk posture, complexity,
   lifetime, cost, launch constraints - PDF p. 53), then record each tailored or customised item
   in the Compliance Matrix attached to the SEMP. Tailoring needs a waiver/deviation; customisation does
   not but significant customisation is documented. See [references/tailoring-and-semp.md](references/tailoring-and-semp.md).
4. **Define stakeholder expectations and ConOps** (process 1): NGOs, MOEs, scenarios incl. off-nominal
   ones, using [templates/conops-outline.md](templates/conops-outline.md) (Appendix S).
5. **Requirements** (processes 2, 11): hand to `skills/requirements-engineering/`; run
   `nasa-se lint-requirements` and `nasa-se trace` before SRR/MDR/PDR.
6. **Decide by trade study** (processes 4, 17): define criteria (mandatory vs weighted), alternatives
   and evaluation methods, then compute:
   `python -m agentlib nasa-se trade-study trade.yaml` and write the decision report with
   [templates/trade-study-matrix.md](templates/trade-study-matrix.md) (Table 6.8-1 sections).
   Detail: [references/decision-analysis-and-risk.md](references/decision-analysis-and-risk.md).
7. **Manage technical risk** (process 13): one record per risk as scenario-likelihood-consequence
   triplets with uncertainty, trigger thresholds and mitigation/contingency plans -
   [templates/risk-record.md](templates/risk-record.md).
8. **Assess technology maturity** with the TRL scale and rules in
   [references/technology-readiness.md](references/technology-readiness.md).
9. **Prepare / assess the review**: generate the checklist, then assess each item against evidence:
   ```sh
   python -m agentlib nasa-se review-checklist PDR --project "<name>" -o pdr-checklist.md
   ```
   Assemble the package with [templates/review-readiness-package.md](templates/review-readiness-package.md).
   Mark every item Ready / Gap / Not applicable (with reason) and cite the artefact. Detail:
   [references/lifecycle-and-reviews.md](references/lifecycle-and-reviews.md).
10. **Cite and check**: cite as `[nasa-se <section>, p. <pdf page>]` and run
    `python -m agentlib evidence check <doc> --require-citations` (see `skills/evidence-and-citation/`).

## Decision rules

- Use the catalog's phase for each review: MCR Pre-Phase A; SRR and MDR/SDR Phase A; PDR Phase B (last
  Formulation review, approves the design-to baseline); CDR, PRR, SIR Phase C (CDR approves the
  build-to baseline); TRR, SAR, ORR, FRR Phase D; PLAR, CERR, PFAR, DR Phase E; DRR Phase F.
- A Table 3.0-1 product marked "**" is a required product for that review: missing = blocking gap.
- Combining SRR with SDR/MDR is acceptable customisation for a small project if both intents are met;
  skipping a required review needs a waiver/deviation (PDF p. 56).
- Trade studies precede, not follow, design decisions (PDF p. 40). An alternative failing a mandatory
  criterion is disregarded; if top alternatives are close or uncertainty could change the ranking,
  present all closely ranked alternatives (PDF pp. 210, 212).
- Never claim a review "passed" or a project is "approved": the decision authority decides at the KDP.

## Outputs

- SEMP draft or update (Appendix J structure) with Compliance Matrix entries for tailoring.
- Review readiness checklist and package with evidence log and gap list.
- ConOps outline; trade study / decision report with a recomputable decision matrix; risk records.
- TRL assessment table with rationale; technical option definitions (scope, key requirements, risks, maturity).

## Quality checklist

- [ ] Phase, next review and governing NPR life cycle stated.
- [ ] Every review item assessed against a named artefact or recorded as a gap; required (**) products checked.
- [ ] Entrance/success criteria referenced to NPR 7123.1 Appendix G table, not invented.
- [ ] Tailoring vs customisation distinguished; waivers/deviations identified.
- [ ] Decision matrix weights sum to 1 (or 100) and totals recompute; assumptions, uncertainty and dissent recorded.
- [ ] Risks written as scenario + likelihood + consequence with uncertainty.
- [ ] TRL claims state what was demonstrated, at what fidelity and in which environment.
- [ ] Citations use PDF pages, e.g. `[nasa-se 6.7, p. 201]`; evidence check passes.

## Sources

`nasa-se` - NASA Systems Engineering Handbook, NASA/SP-2016-6105 Rev 2 (2016), pinned PDF
`sources/pdfs/nasa-systems-engineering-handbook-rev2.pdf` (356 pages; printed page = PDF page - 13 from
PDF p. 14). Pages relied on (PDF): preface/scope p. 10; SE engine 2.1 and Figure 2.1-1 pp. 18-20;
Table 2.2-1 phases pp. 22-23; V&V distinction 2.4 pp. 24-25; life cycle 3.0-3.9 incl. Figure 3.0-1 and
Table 3.0-1 pp. 32-51; tailoring 3.11 pp. 52-62; process chapters 4-6 pp. 63-215 (risk 6.4 pp. 173-179;
technical assessment 6.7 and Table 6.7-1 pp. 196-205; decision analysis 6.8 pp. 206-214); TRR note
p. 122; glossary p. 246; technology assessment/TRLs Appendix G pp. 259-268; SEMP outline Appendix J
pp. 282-293; ConOps outline Appendix S pp. 314-317.

## Limitations

- Output supports, but does not replace, qualified professional judgement, the program/project decision
  authority, Standing Review Boards or formal NASA assurance/approval.
- Review entrance/success criteria are in NPR 7123.1 Appendix G (not bundled); the checklist points to
  the table but cannot apply its content. The NASA Expanded Guidance for SE referenced throughout the
  handbook is not part of the source pack.
- Catalog purposes and review descriptions are paraphrases; consult the cited page for exact wording.
- Life cycles other than NPR 7120.5 spaceflight (IT, R&T, software) are not modelled.
