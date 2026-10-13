---
name: nasa-software-assurance
description: >-
  Applies NASA-STD-8739.8B Software Assurance and Software Safety Standard: derives the software
  assurance (SA) and software safety tasks that apply to a project from its NPR 7150.2D class and
  Requirements Mapping Matrix (SASS-01, Table 1), plans SA work (SA plan, schedule, tailoring), performs
  the software safety-criticality assessment (4.2 criteria a-e), supports software hazard analysis with
  the Appendix A cause checklist, scopes IV&V (4.4 requirements and IPEP), and records SA audits and
  non-conformances. Use when writing or reviewing a software assurance plan, deciding whether software is
  safety-critical, preparing hazard-analysis inputs, checking IV&V applicability or IPEP content, auditing
  a software project against NPR 7150.2D / NASA-STD-8739.8B, or recording SA findings.
metadata:
  version: 1.0.0
  category: software-assurance
  maturity: beta
  sources: [nasa-software-assurance, nasa-software-requirements, nasa-software]
  catalogs: [nasa-std-8739-8b, npr-7150-2d]
  tools:
    - "python -m agentlib nasa-swe sa-tasks"
    - "python -m agentlib nasa-swe sc-assess"
    - "python -m agentlib nasa-swe hazard-causes"
    - "python -m agentlib nasa-swe matrix"
    - "python -m agentlib nasa-swe check-matrix"
    - "python -m agentlib nasa-swe show"
---

# NASA software assurance and software safety (NASA-STD-8739.8B)

NASA-STD-8739.8B makes one project-level requirement, SASS-01: the responsible project manager performs
the software assurance and software safety activities defined in Table 1 for the requirements marked
applicable in the project's NPR 7150.2 Requirements Mapping Matrix
[nasa-software-assurance SASS-01, p. 16]. Table 1 (pp. 17-47) lists, for each of the 100 Chapter 3-5 SWE
requirements, numbered SA/SS tasks (198 tasks in 103 rows; SWE-065 is split into 065a-065d). Section 4.4
adds 49 IV&V requirements (4.4.2.1-4.4.2.49), section 4.2 the safety-critical criteria, section 4.5 the
tailoring principles and Appendix A the guidance for software in hazard analyses.

## When to use

- Writing, reviewing or tailoring a Software Assurance Plan (including software safety).
- Determining whether software components are safety-critical and what that triggers.
- Preparing software inputs to hazard analyses / hazard reports and the software safety analysis.
- Deciding whether IV&V applies (SWE-141) and what the IV&V Provider and IPEP must cover.
- Planning or reporting SA audits, assessments, test witnessing and non-conformance tracking.
- Not for: choosing the software class or building the engineering compliance matrix - use
  [`skills/nasa-software-engineering/`](../nasa-software-engineering/SKILL.md) (SA concurs with the class).

## Workflow

1. **Establish the baseline.** Obtain the software class and the project's Requirements Mapping Matrix.
   If missing, run `python -m agentlib nasa-swe matrix --class <X>`; SA performs a classification or
   concurs with engineering's (SWE-020 task 1) [nasa-software-assurance Table 1 SWE-020, p. 25].
2. **Derive the applicable SA/SS tasks** with the tool:
   `python -m agentlib nasa-swe sa-tasks --class <X> --format md` (all tasks for requirements marked `X`)
   and `--swe SWE-nnn` for one requirement. Tasks tied to requirements the project tailored out drop
   only with SMA TA concurrence (step 6). Task verbs have defined meanings (Analyze, Assess, Confirm,
   Perform, Develop, Participate ...) [nasa-software-assurance 3.2, p. 10]; see
   [references/sa-planning-and-tasks.md](references/sa-planning-and-tasks.md).
3. **Assess safety-criticality** for each component with engineering:
   `python -m agentlib nasa-swe sc-assess --criteria <letters>` against 4.2 a-e
   [nasa-software-assurance 4.2, p. 15]. Report `Safety-critical determination: Yes|No` with the
   criteria letters and the hazard-report trace (Note to 4.2, p. 16). Use the
   [assessment template](templates/software-safety-criticality-assessment.md).
4. **Support hazard analysis.** Run `python -m agentlib nasa-swe hazard-causes [--area ...]` to get the
   Appendix A Table 2 checklist (12 cause areas, pp. 59-65); follow the phased process in A.1
   (pp. 58-59). Confirm hazard reports contain software contributions and trace to requirements
   (SWE-205 tasks) [nasa-software-assurance Table 1 SWE-205, p. 26]. Details:
   [references/safety-criticality-and-hazard-analysis.md](references/safety-criticality-and-hazard-analysis.md).
5. **Scope IV&V.** IV&V is required for projects reaching KDP A that are Category 1, Category 2 with
   Class A/B payload risk classification, or selected by the MDAA (SWE-141)
   [nasa-software-requirements SWE-141, p. 25]. If required: IPEP developed by the IV&V Provider and
   negotiated with the project (4.4.2.2), SMA TA concurrence (4.4.2.3) [nasa-software-assurance 4.4.2.3, p. 50];
   list requirements with `nasa-swe sa-tasks --ivv`. See [references/ivv.md](references/ivv.md).
6. **Write the SA plan** from [templates/sa-plan.md](templates/sa-plan.md): scope, class, safety-critical
   components, task list by life-cycle phase, audits (at least every two years on development processes,
   SWE-039 task 5 [nasa-software-assurance Table 1 SWE-039, p. 19]), schedule (SWE-016 task 2), cost
   estimate (SWE-015 task 1), metrics, reporting, IV&V interface, and the SA tailoring matrix (SWE-121
   task 2) with the three tailoring levels and SMA TA concurrence [nasa-software-assurance 4.5-1, p. 56].
7. **Execute and record.** Use [templates/sa-audit-report.md](templates/sa-audit-report.md) for audits and
   [templates/non-conformance-record.md](templates/non-conformance-record.md) for findings; follow the
   severity and closure rules in [references/sa-audits-and-nonconformances.md](references/sa-audits-and-nonconformances.md).
   Check the engineering matrix with `python -m agentlib nasa-swe check-matrix <file> --class <X>` and
   include its findings in the audit.

## Decision rules

- SA tasks apply because a SWE applies: no SWE `X` for the class (or approved tailoring) -> no Table 1
  task, unless the SA TA decides otherwise.
- Safety-critical if **any** of 4.2 a-e is met; record which. Class E software cannot be safety-critical
  (NPR 7150.2D p. 85) - a safety-critical "Class E" component is a classification error to raise.
- Thresholds quoted from the bundled sources only: 100 % MC/DC coverage for safety-critical components
  (SWE-219 task 1, 8739.8B p. 28), cyclomatic complexity <= 15 or a developer risk assessment (SWE-220
  task 1, p. 28), development process audits at least once every two years (SWE-039 task 5, p. 19).
- Never cite IV&V requirements beyond 4.4.2.49 or invent task numbers; verify with `nasa-swe show`.
- Disagreements between engineering/project and SA are identified, reported, tracked and elevated if
  unresolved (NPR 7150.2D 2.1.6.7, p. 16).

## Outputs

Markdown with the applicable headings:

1. `Scope and baseline` - class, matrix reference, safety-critical components, IV&V applicability.
2. `Safety-criticality assessment` - `Safety-critical determination: Yes|No`, criteria (4.2 a-e) met,
   hazard references, triggered SWEs.
3. `SA/SS task plan` - table: SWE | Task no. | Task (verbatim or close paraphrase) | Phase | Owner | Evidence.
4. `IV&V` - applicability rationale, IPEP status, 4.4.2.x requirements in scope.
5. `Audit / findings` - findings with severity, requirement reference, required action, due date.
6. `Sources` - citations `[nasa-software-assurance <locator>, p. N]` and `[nasa-software-requirements SWE-nnn, p. N]`.

## Quality checklist

- [ ] Task list generated with `nasa-swe sa-tasks` for the project's class; tailored items justified.
- [ ] Safety-critical determination per component with 4.2 criteria letters and hazard trace.
- [ ] IV&V applicability decided against SWE-141 criteria; IPEP and SMA TA concurrence tracked.
- [ ] SA plan covers audits, schedule, cost, metrics, reporting, tailoring matrix.
- [ ] Every SWE / 4.4.2.x / page citation verified against the catalogs.
- [ ] Statement that SA output informs, not replaces, SMA Technical Authority decisions.

## Sources

- `nasa-software-assurance` - NASA-STD-8739.8B, Software Assurance and Software Safety Standard
  (approved 2022-09-08). Relied on: 1.3-1.4 documentation and relief (PDF p. 6), 3.2 definitions of task
  verbs and safety-critical software (pp. 9-14), 4.1 SA description (p. 15), 4.2 safety-critical
  determination (pp. 15-16), 4.3 SASS-01 (p. 16), Table 1 SA/SS tasks (pp. 17-47), 4.4 IV&V (pp. 48-56),
  4.5 tailoring (pp. 56-57), Appendix A hazard guidelines and Table 2 (pp. 58-65). Printed page = PDF page.
- `nasa-software-requirements` - NPR 7150.2D (2022): SWE-020/205/141/131 and Appendix C/D used to decide
  which tasks apply (pp. 24-26, 55-86).
- `nasa-software` - NASA Software Engineering and Assurance Handbook (NASA-HDBK-2203, swehb.nasa.gov):
  living wiki, **not bundled**; recommended further reading (SA plan content, task guidance). Not quoted.
- Catalog index: [references/sa-task-index.md](references/sa-task-index.md) (generated from
  `catalog/nasa-std-8739-8b.json`).

## Limitations

- Output supports, but does not replace, qualified professional judgement or formal assurance/approval:
  safety-critical determinations, hazard acceptance, tailoring and IV&V scoping are decided by the project
  with the SMA Technical Authority (and NASA IV&V where applicable).
- The "safety-related task" flag in the catalog is a keyword heuristic, not a category of the standard.
- NPR 8715.3, NPR 8705.x, NASA-GB-8719.13, NASA-STD-1006 and the SWEHB are referenced by the standard but
  are not bundled; check them directly when relevant.
- Table 1 lists NPR section numbers as printed in the standard (e.g. SWE-032 as 3.9.3), which differ
  slightly from NPR 7150.2D (3.9.2); SWE ids are authoritative.
