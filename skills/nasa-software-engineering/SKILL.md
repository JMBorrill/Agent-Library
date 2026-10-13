---
name: nasa-software-engineering
description: >-
  Applies NPR 7150.2D NASA Software Engineering Requirements to a project: proposes a software
  classification (Classes A-F, Appendix D) with cited rationale, generates and checks the Appendix C
  Requirements Mapping Matrix (compliance matrix with status, tailoring and evidence), and plans the
  life-cycle work the SWE requirements demand (planning, cost and schedule, requirements, architecture,
  design, implementation, testing, configuration management, risk, peer reviews, measurement,
  non-conformances, safety-critical software, cybersecurity). Use when a NASA or NASA-contracted
  software project needs a classification, a compliance/requirements mapping matrix, a tailoring request,
  a software development/management plan, a test plan, a requirements specification outline, or an
  answer about which SWE requirements apply and where they are in the NPR.
metadata:
  version: 1.0.0
  category: software-engineering
  maturity: beta
  sources: [nasa-software-requirements, nasa-software-assurance, nasa-software]
  catalogs: [npr-7150-2d, nasa-std-8739-8b]
  tools:
    - "python -m agentlib nasa-swe classify"
    - "python -m agentlib nasa-swe matrix"
    - "python -m agentlib nasa-swe check-matrix"
    - "python -m agentlib nasa-swe show"
    - "python -m agentlib nasa-swe sa-tasks"
    - "python -m agentlib nasa-swe sc-assess"
---

# NASA software engineering (NPR 7150.2D)

NPR 7150.2D states 130 numbered requirements (`[SWE-nnn]`): 30 institutional requirements in Chapter 2
and 100 project requirements in Chapters 3-5 whose applicability by software class is fixed by the
Appendix C Requirements Mapping Matrix. This skill turns a project description into a candidate
classification, the applicable requirement set, a mapping matrix and the plans that satisfy it, with
every claim traced to a page of the pinned PDF.

## When to use

- Classifying software (or each subsystem) against Appendix D Classes A-F.
- Producing or reviewing a Requirements Mapping Matrix / compliance matrix, including tailoring
  ("relief") requests and the approvals they need.
- Writing or reviewing a Software Development/Management Plan, Software Test Plan or Software
  Requirements Specification for NASA work.
- Answering "which SWEs apply to Class X?", "what does SWE-nnn require?", "what changes if the software
  is safety-critical?".
- Not for: software assurance planning, safety-criticality assessment details, IV&V or SA audits - use
  [`skills/nasa-software-assurance/`](../nasa-software-assurance/SKILL.md); system-level life-cycle
  reviews - use the systems engineering skills.

## Workflow

1. **Scope the software.** List each system/subsystem containing software, its use, who depends on it,
   whether it flies or operates a vehicle/facility, and its mission role. Classification is per system
   or subsystem (SWE-020) [nasa-software-requirements SWE-020, p. 24].
2. **Propose a class with the tool, never from memory.**
   `python -m agentlib nasa-swe classify --list-questions` shows the Appendix D scopes, criteria and
   exclusions with ids (e.g. `B-scope`, `B-1a`, `C-1f`, `D-x4`). Answer them in a YAML file
   (`id: yes|no`, plus `safety_critical: yes|no`) and run
   `python -m agentlib nasa-swe classify --answers answers.yaml` (or `--yes ID` repeatedly).
   Decision rules the tool applies (and you must explain):
   - the higher class wins when several appear to apply [nasa-software-requirements Appendix D D.2, p. 79];
   - an exclusion removes a class (e.g. Class B excludes NASA Class D payloads, which Class C covers)
     [nasa-software-requirements Appendix D Class B, p. 82];
   - safety-critical software cannot be Class E - it is Class D or higher
     [nasa-software-requirements Appendix D Class E, p. 85];
   - Class F is business/IT infrastructure; engineering systems (A-E) are classified separately.
   Report `Candidate class: Class X` and state that the project manager classifies, software engineering
   and software assurance Technical Authorities must agree, and the NASA Chief Engineer resolves disputes
   [nasa-software-requirements Appendix D D.2, p. 79]. Details: [references/software-classification.md](references/software-classification.md).
3. **Determine safety-criticality** with the SMA organization (SWE-205)
   [nasa-software-requirements SWE-205, p. 26]: `python -m agentlib nasa-swe sc-assess --criteria a,b`
   applies NASA-STD-8739.8B 4.2 criteria a-e. If yes, SWE-023, SWE-134, SWE-219 (100 % MC/DC) and
   SWE-220 (cyclomatic complexity <= 15) are triggered. See [references/safety-critical-software.md](references/safety-critical-software.md).
4. **Generate the Requirements Mapping Matrix.**
   `python -m agentlib nasa-swe matrix --class B --safety-critical [--ivv] --format md|csv|json -o rmm.csv`.
   It lists every requirement marked `X` for the class with its Appendix C Authority, conditional notes,
   and empty Status / Tailoring rationale / Approval / Evidence columns. Use only the allowed statuses:
   Compliant, Partially Compliant, Non-Compliant, Planned, Tailored, Not Applicable.
5. **Fill the matrix.** For each row record how the project meets it (plan section, procedure) and the
   evidence (document id, repository link, review record). Requirements that do not apply (e.g. IV&V
   when not required) are tailored out *with justification* - every `X` requirement must appear
   [nasa-software-requirements Appendix C, p. 55]. Tailoring needs rationale, risk evaluation and the
   approval of the Authority named in Appendix C; HQ-authority requirements (SWE-032, SWE-141) need NASA
   HQ approval; cybersecurity (3.11) relief needs SAISO/CISO agreement
   [nasa-software-requirements SWE-150, p. 19]. Guidance: [references/compliance-matrix-and-tailoring.md](references/compliance-matrix-and-tailoring.md).
6. **Check the matrix** before it goes to the Technical Authorities:
   `python -m agentlib nasa-swe check-matrix rmm.csv --class B`. Fix every ERROR (unknown ids,
   duplicates, missing applicable rows, invalid or missing status, compliant rows without evidence,
   tailored/N-A rows without rationale) and resolve WARNINGS (missing approvals, Chapter 2 ids in the
   matrix). Quote the summary statistics in your answer.
7. **Plan the life cycle** using the templates and [references/lifecycle-requirements.md](references/lifecycle-requirements.md):
   planning, cost, schedule, training (3.1-3.4), CMMI rating for Class A/B (SWE-032), reuse, cybersecurity,
   traceability (Table 1 of SWE-052), requirements, architecture, design, implementation, testing,
   operations/maintenance/retirement (Chapter 4), and CM, risk, peer reviews, measurement and
   non-conformances (Chapter 5). Use `python -m agentlib nasa-swe show SWE-nnn` for exact wording.
8. **Coordinate software assurance.** For each SWE, `python -m agentlib nasa-swe sa-tasks --swe SWE-nnn`
   shows the NASA-STD-8739.8B tasks SA will perform, so plans give SA the access and artefacts it needs.

## Decision rules

- Never invent SWE numbers, classes, thresholds or pages; if a value is not in the catalog or the PDF,
  say it was not verified. The NASA Software Engineering Handbook (NASA-HDBK-2203, `nasa-software`) is a
  living wiki and is not bundled - recommend it for rationale/guidance, do not quote it.
- Quantitative rules that *are* in NPR 7150.2D: two cost models for Class A/B projects >= $2 million,
  one model otherwise (SWE-015, p. 23); CMMI-DEV ML3 for Class A, ML2 for Class B (SWE-032, p. 28);
  100 % MC/DC on safety-critical components (SWE-219, pp. 26-27); cyclomatic complexity <= 15 for
  safety-critical components unless waived with rationale (SWE-220, p. 27).
- Chapter 2 requirements (Center Director, OCE, Chief SMA, TAs) are not rows of the project matrix.
- A requirement whose wording is conditional (IV&V, safety-critical, project category) still appears in
  the matrix; mark it Not Applicable with rationale when the condition is false.
- If the class changes, plans and supplier contracts must be updated (SWE-021) [nasa-software-requirements SWE-021, p. 19].

## Outputs

Return Markdown with these headings (omit those not requested):

1. `Classification` - `Candidate class: Class X - <title>`, matched Appendix D criteria with citations,
   exclusions considered, safety-critical status, authority statement.
2. `Applicable requirements` - count for the class and notable conditional requirements.
3. `Requirements Mapping Matrix` - table with columns SWE | Section | Requirement | Authority | Status |
   Tailoring / waiver rationale | Approval | Evidence (tool-generated, then filled).
4. `Matrix check` - summary statistics and findings from `check-matrix`.
5. `Plan / artefact` - the filled template(s).
6. `Sources` - citations in the form `[nasa-software-requirements SWE-nnn, p. N]`.

Templates: [software development/management plan](templates/software-development-plan.md),
[compliance matrix](templates/compliance-matrix.md), [software test plan](templates/software-test-plan.md),
[software requirements specification](templates/software-requirements-spec.md).

## Quality checklist

- [ ] Class proposed via `nasa-swe classify`, with criteria ids and Appendix D page citations.
- [ ] Safety-critical determination recorded (or flagged as pending with SMA).
- [ ] Matrix generated by the tool; every `X` requirement for the class present; `check-matrix` has 0 errors.
- [ ] Every Compliant row has evidence; every Tailored / Not Applicable row has rationale and approver.
- [ ] Every SWE id cited exists (`nasa-swe show`); page citations match the catalog.
- [ ] Statement that the classification and tailoring are decided by the accountable authorities.

## Sources

- `nasa-software-requirements` - NPR 7150.2D, NASA Software Engineering Requirements (effective
  2022-03-08, expires 2027-03-08). Relied on: Ch. 1 structure (PDF pp. 8-10), Ch. 2 roles and tailoring
  principles (pp. 11-19), Ch. 3 software management requirements (pp. 20-31, incl. Table 1 traceability
  p. 31), Ch. 4 life-cycle requirements (pp. 32-38), Ch. 5 supporting requirements (pp. 39-43), Ch. 6
  recommended records (pp. 44-45), Appendix C Requirements Mapping Matrix (pp. 55-78), Appendix D software
  classifications (pp. 79-86). Printed page numbers equal PDF page numbers.
- `nasa-software-assurance` - NASA-STD-8739.8B (2022), used for the safety-critical criteria (4.2,
  pp. 15-16) and the SA/SS tasks mapped to each SWE (Table 1, pp. 17-47).
- `nasa-software` - NASA Software Engineering and Assurance Handbook (NASA-HDBK-2203, swehb.nasa.gov),
  a living wiki that is **not bundled**; recommended further reading for rationale, tailoring guidance and
  document content. Nothing in this skill is quoted from it.
- Catalogs `catalog/npr-7150-2d.json` and `catalog/nasa-std-8739-8b.json`, extracted by
  `scripts/extract/nasa_swe.py`; indexes in [references/requirements-index.md](references/requirements-index.md).

## Limitations

- Output supports, but does not replace, qualified professional judgement or formal assurance/approval:
  classification, safety-criticality and tailoring are decided by the project manager with the
  Engineering, SMA, CIO (and where relevant Health and Medical) Technical Authorities.
- The classifier is a deterministic walk of Appendix D definitions; it cannot judge facts the user did
  not supply, and examples in Appendix D are illustrative, not exhaustive.
- Center-specific processes, contract clauses, NPR 7120.x/8705.x requirements and the SWEHB wiki are
  outside the bundled sources and must be checked separately.
- NPR 7150.2D expires 2027-03-08; confirm the current revision in NODIS before use.
