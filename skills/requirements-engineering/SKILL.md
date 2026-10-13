---
name: requirements-engineering
description: >-
  Writes, reviews, validates, traces and plans verification of technical requirements using the NASA
  Systems Engineering Handbook (NASA/SP-2016-6105 Rev 2): single-"shall" statements with rationale, the
  Appendix C "How to Write a Good Requirement" checklist (unverifiable and ambiguous terms, TBD/TBR,
  positive and active statements, one thought per statement), requirement metadata (Table 4.2-2),
  the six requirements-validation questions, bidirectional traceability and self-derived requirements
  (Section 6.2), verification methods (test, analysis, inspection, demonstration) and the Appendix D
  requirements verification matrix. Deterministic tools lint requirement sets (CSV/YAML/JSON/Markdown)
  and check traceability and verification coverage. Use when drafting or rewriting requirements or
  specifications, reviewing a requirements document before SRR/PDR, building a traceability matrix or
  VCRM, or auditing orphans, TBDs and unverifiable requirements in any engineering project.
license: Skill text MIT; NASA/SP-2016-6105 Rev 2 is a US Government work
metadata:
  version: 1.0.0
  category: systems-engineering
  maturity: beta
  sources: [nasa-se]
  catalogs: [nasa-requirements-checklist, nasa-se-processes]
  tools:
    - "python -m agentlib nasa-se lint-requirements"
    - "python -m agentlib nasa-se trace"
    - "python -m agentlib nasa-se req-checklist"
---

# Requirements engineering (NASA SE Handbook Rev 2)

Requirements are defined in the Technical Requirements Definition process (4.2) and managed in the
Requirements Management process (6.2) of the NASA SE engine. This skill turns the handbook's guidance
(Appendix C checklist, Table 4.2-2 metadata, verification methods, Appendix D matrix) into a repeatable
procedure backed by two deterministic tools. Rules and term lists come from
`catalog/nasa-requirements-checklist.json` - run the tools instead of judging wording from memory.

## When to use

- Drafting a requirements specification (system, subsystem, interface, software) or rewriting weak ones.
- Reviewing a requirements set before SRR, MDR/SDR or PDR, or as a peer review.
- Building or auditing a traceability matrix (parent/child, orphans, gold plating) and a verification
  cross-reference matrix (VCRM).
- Workflow stage `requirements-audit` of `workflows/technical-review-gate.yaml`.

Pair with `skills/nasa-systems-engineering/` for stakeholder expectations, ConOps and reviews, and
with `skills/evidence-and-citation/` before delivering a report.

## Key rules (verified in the PDF)

- **Terms** (C.1, PDF p. 249): *shall* = requirement; *will* = facts or declaration of purpose;
  *should* = goal.
- **Form**: complete sentences with a **single "shall"** per statement, with rationale captured
  (4.2.1.2.3, PDF p. 81); active voice - "The product shall ..." or "responsible party shall ..."
  (C.2, PDF p. 249); state WHAT is needed, not HOW; no descriptions of operations ("The operator shall..."
  is almost always operational) (C.2, PDF p. 249); stated positively, not "shall not" (C.3, PDF p. 250).
- **Clarity**: one thought per statement, one subject and one predicate; no indefinite pronouns (this,
  these) or ambiguous terms ("as appropriate", "etc.", "and/or", "but not limited to") (C.4, PDF p. 250).
- **Verifiability**: free of unverifiable terms - flexible, easy, sufficient, safe, ad hoc, adequate,
  accommodate, user-friendly, usable, when required, if required, appropriate, fast, portable,
  light-weight, small, large, maximize, minimize, robust, quickly, easily, clearly, other "-ly" and "-ize"
  words (C.4, PDF p. 252); include tolerances (C.2, PDF p. 249).
- **TBD/TBR**: minimise TBDs; prefer a best estimate marked TBR with rationale, the action to resolve it,
  who is responsible and by when (C.3, PDF p. 250).
- **Metadata** (Table 4.2-2, PDF p. 83): Requirement ID, Rationale, Traced from, Owner, Verification
  method, Verification lead, Verification level.
- **Verification methods** (PDF p. 121): Analysis (incl. modeling, simulation, similarity), Demonstration,
  Inspection, Test - nothing else.
- **Traceability** (6.2, PDF pp. 163-165): bidirectional (parent and children). A requirement with no
  parent that is not an acceptable self-derived requirement indicates a flawed trace or gold plating.

## Workflow

1. **Gather context**: stakeholder expectations (NGOs, MOEs), ConOps, parent requirements, constraints.
   Requirements must trace to these (C.4 Traceability, PDF p. 251).
2. **Draft** each requirement with [templates/requirements-spec.md](templates/requirements-spec.md):
   `ID | Requirement | Rationale | Parent | Verification method | Verification level | Owner`.
   Follow [references/writing-requirements.md](references/writing-requirements.md). Quantify every
   performance value with a tolerance or bound.
3. **Lint** (deterministic, Appendix C):
   ```sh
   python -m agentlib nasa-se lint-requirements reqs.csv            # table; exit 1 on errors
   python -m agentlib nasa-se lint-requirements reqs.csv --format markdown -o lint-report.md
   ```
   Fix every error (missing/duplicate ID, no or multiple "shall", ambiguous or unverifiable term,
   invalid verification method). Resolve or justify warnings (TBD, passive voice, negative statement,
   operational statement, compound statement, missing rationale/method). `--fail-on warning` for a strict gate.
4. **Validate** the set with the six questions (4.2.1.2.4, PDF pp. 83-84) and the full C.4 checklist
   (`python -m agentlib nasa-se req-checklist`): written correctly, technically correct, satisfies
   stakeholders, feasible, verifiable, not redundant/over-specified; check completeness of requirement
   areas (functional, performance, interface, environment, facility, transportation, training, personnel,
   operability, safety, security, physical, design - PDF p. 250). See
   [references/validation-checklist.md](references/validation-checklist.md).
5. **Trace**:
   ```sh
   python -m agentlib nasa-se trace reqs.csv --external NGO- --matrix --format markdown -o trace.md
   ```
   Errors: orphans, dangling parents/children, cycles, duplicate IDs, missing/invalid verification
   method. Warnings: one-way links, unallocated top-level requirements. Mark genuinely self-derived
   requirements `self-derived` in the parent column and seek concurrence from the next level up.
   Use `--top-level <level>` when top-level requirements trace to documents outside the file, or
   `--external <prefix>` for baselined parent documents. Detail:
   [references/traceability-and-verification.md](references/traceability-and-verification.md).
6. **Plan verification**: build the VCRM with [templates/verification-matrix.md](templates/verification-matrix.md)
   (Appendix D Table D-1 columns): only "shall" requirements; one method set per requirement; success
   criteria; level; phase; facility; responsible organisation. Record the matrix in
   [templates/traceability-matrix.md](templates/traceability-matrix.md) for bidirectional status.
7. **Baseline and manage change**: baseline after validation (typically SRR); afterwards changes go
   through the CCB with impact assessment (PDF p. 166); watch for requirements creep (PDF p. 167).

## Decision rules

- A statement without "shall" is not a requirement; "will" and "should" text belongs in context or goals.
- Two "shall"s, or "and" joining two actions, means split into two requirements with separate IDs.
- An unverifiable term is an error even with a verification method assigned: replace it with a
  measurable criterion (value, tolerance, conditions).
- "Simulation", "modeling" or "similarity" are recorded as **Analysis**; "review" or "audit" of documents
  is **Inspection** (inspection includes drawings, documents and records, PDF p. 121).
- Orphans are resolved by tracing, by explicit self-derived status with concurrence, or by deletion as gold
  plating - never by leaving them silent.
- TBDs are acceptable only when tracked in a TBD/TBR list with owner and closure date.

## Outputs

- Requirements specification table (ID, statement, rationale, parent, method, level, owner).
- Lint report (Markdown/JSON) with each finding mapped to its Appendix C/Table 4.2-2 source and page.
- Traceability report and matrix; verification matrix (VCRM) per Appendix D.
- Rewritten requirements with before/after and rationale for each change.

## Quality checklist

- [ ] `lint-requirements` shows 0 errors; every warning fixed or dispositioned in writing.
- [ ] `trace` shows 0 errors; self-derived requirements listed for concurrence.
- [ ] Every requirement has rationale, verification method (T/A/I/D) and verification level.
- [ ] All TBD/TBR items listed with owner and closure date.
- [ ] VCRM contains only "shall" requirements, with success criteria.
- [ ] Citations use PDF pages, e.g. `[nasa-se C.4, p. 252]`; `evidence check` passes.

## Sources

`nasa-se` - NASA Systems Engineering Handbook, NASA/SP-2016-6105 Rev 2 (2016), pinned PDF
`sources/pdfs/nasa-systems-engineering-handbook-rev2.pdf` (356 pages; printed page = PDF page - 13).
Pages relied on (PDF): verification vs validation 2.4 pp. 24-25; Technical Requirements Definition 4.2
pp. 76-85 (example requirements p. 79, single-shall rule p. 81, Table 4.2-1 p. 82, Table 4.2-2 and
Rationale box p. 83, validation steps pp. 83-84); Methods of Verification box p. 121; Table 5.3-1 p. 122;
Requirements Management 6.2 pp. 163-168; Appendix C checklist pp. 249-252; Appendix D verification matrix
pp. 253-255; Appendix E validation matrix p. 256.

## Limitations

- Output supports, but does not replace, qualified engineering judgement, stakeholder agreement and formal
  baselining/approval by the project's configuration control authority.
- The linter is lexical: it cannot judge technical correctness, feasibility, completeness of the set, the
  right level, or whether a requirement states implementation; those checklist items need human review.
  Heuristic rules (passive voice, compound statements, "-ly"/"-ize" words, missing tolerance) can produce
  false positives - disposition them, do not blindly rewrite.
- The handbook's Expanded Guidance (requirement types, databases, standards) is not in the source pack.
