---
name: nist-ssdf
description: >-
  Secure software development lifecycle assessment and implementation planning with the NIST Secure
  Software Development Framework (SSDF) v1.1, NIST SP 800-218: scoping, task-by-task gap assessment
  across the 4 practice groups (PO, PS, PW, RV), 19 practices and 42 tasks, evidence collection,
  scoring and prioritised remediation roadmaps, attestation-style evidence matrices, and mapping a
  CI/CD pipeline's controls (SAST, SCA/SBOM, secret scanning, code review, signing, pinning) to the
  tasks they support. Also drafts secure development policies, vulnerability response/disclosure
  procedures, release integrity checklists and SBOM/provenance records. Use when asked to assess or
  improve a secure SDLC against SSDF / SP 800-218, prepare for a secure software development
  attestation or supplier questionnaire, explain an SSDF practice or task, or check which SSDF tasks a
  build pipeline covers.
license: Skill text MIT; SSDF content is NIST public information (attribution retained, no endorsement)
metadata:
  version: 1.0.0
  category: software-assurance
  maturity: beta
  sources: [nist-ssdf]
  catalogs: [nist-ssdf]
  tools:
    - "python -m agentlib ssdf list"
    - "python -m agentlib ssdf show"
    - "python -m agentlib ssdf assessment-template"
    - "python -m agentlib ssdf check-assessment"
    - "python -m agentlib ssdf evidence-matrix"
    - "python -m agentlib ssdf map-pipeline"
    - "python -m agentlib ssdf pipeline-controls"
---

# NIST SSDF v1.1 (SP 800-218) - secure SDLC assessment and planning

SSDF v1.1 defines outcome-based secure development practices in four groups: Prepare the Organization
(PO), Protect the Software (PS), Produce Well-Secured Software (PW) and Respond to Vulnerabilities (RV)
(Section 2, PDF p.13). Table 1 (PDF pp.14-28) lists **19 practices and 42 tasks**, each with notional
implementation examples and informative references. All task text, examples, references and pages come
from `catalog/nist-ssdf.json`; never quote a task, example or reference from memory - run the tools.

## When to use

- **Gap assessment / maturity baseline**: "How do we measure up against SSDF?", "score our secure SDLC",
  "what's missing before we sign a secure development attestation?"
- **Implementation planning**: turn gaps into an owned, dated roadmap; draft the policy, vulnerability
  response and release-integrity artefacts that many tasks need.
- **Pipeline review**: "which SSDF tasks does our GitHub Actions / GitLab pipeline cover?"
- **Explaining SSDF**: what a practice or task means, its examples, its references (e.g. SP 800-53 ids),
  and which EO 14028 Section 4e subsections Appendix A maps it to.
- **Supplier management**: express SSDF expectations to suppliers (PO.1.3) or review a supplier's answers.

Not for: application-level requirement verification (use an ASVS skill), legal advice on attestation
obligations, or certifying anyone - SSDF is not a certification scheme and "is not ... a checklist"
(PDF p.12, printed p.3).

## Key facts (verified in the PDF)

- Practices are outcomes, not prescribed tools or methods (Executive Summary PDF p.8; Introduction PDF pp.10-11).
- Practices, tasks and examples "are not prioritized"; adoption is risk-based, weighing risk, cost,
  feasibility and applicability; some practices do not apply (e.g. no compiler, no compiler practice)
  (PDF p.12). The order in Table 1 implies no sequence or importance (PDF p.13).
- Notional implementation examples are optional and not exhaustive; references do not all apply to every
  case (PDF p.13). Never treat an example as a requirement.
- Terms like "sensitive data", "qualified person", "well-secured" and environment names are deliberately
  undefined - the organisation must define them (PDF p.13).
- Responsibility may be shared with platform/service providers; tenants should agree who does each
  practice/task and how providers attest (PDF p.12).
- Retired ids (PW.3, PW.3.1, PW.3.2, PW.4.3, PW.4.5, PW.5.2) remain only as pointers; use the current id
  (Change Log, PDF p.36). PO.1.3 was formerly PW.3.1; PW.1.3 was formerly PW.4.3.
- Appendix A Table 2 (PDF p.33, printed p.24) maps EO 14028 Section 4e subsections to tasks; 4e(ix) maps to
  all practices and tasks "consistent with a risk-based approach".

Practice/task index with pages: [references/practices-and-tasks.md](references/practices-and-tasks.md).

## Workflow

1. **Scope.** Record the organisation, products/teams, SDLC model, delivery model (SaaS, on-prem, embedded),
   and any shared-responsibility split with platform providers. Define the SSDF-undefined terms you will use
   (environments, "qualified person", "sensitive data") - see [references/assessment-method.md](references/assessment-method.md).
2. **Generate the worksheet**: `python -m agentlib ssdf assessment-template --format yaml --out ssdf-assessment.yaml`
   (or `--format csv` / `md`). One row per active task (42); never add or drop rows by hand.
3. **Gather evidence task by task.** For each task run `python -m agentlib ssdf show <id>` to read the task,
   examples and references. Ask for artefacts, not assertions: policies, tickets, pipeline configs, logs,
   reports. Evidence ideas per group: [references/assessment-method.md](references/assessment-method.md).
   If a pipeline description exists, run step 4 first to pre-fill technical evidence leads.
4. **Map the pipeline (optional)**: describe the CI/CD steps in YAML (format in
   [references/pipeline-mapping-rules.md](references/pipeline-mapping-rules.md)) and run
   `python -m agentlib ssdf map-pipeline pipeline.yaml`. Use the result as *leads*: a supporting control is
   not proof the task is implemented.
5. **Set status per task** using the decision rules below; fill evidence, owner, target_date, justification.
6. **Validate and score**: `python -m agentlib ssdf check-assessment ssdf-assessment.yaml`. Fix every error
   (unknown/retired ids, missing tasks, invalid status, implemented without evidence, not-applicable without
   justification) and re-run until it reports `Validation: PASS`. Quote the tool's coverage figures exactly;
   do not recompute them.
7. **Prioritise and plan.** Start from the tool's "Prioritised gaps" list (a transparent heuristic - SSDF
   itself does not prioritise) and adjust with the organisation's risk context. Give every gap an owner, a
   target date and the artefact that will evidence it. Use the templates below for policy/procedure gaps.
8. **Produce outputs**: `python -m agentlib ssdf evidence-matrix ssdf-assessment.yaml --out ssdf-evidence-matrix.md`
   plus the summary report (see Outputs). Hand off attestation decisions to an accountable human.

### Status decision rules

| Status | Use when | Required fields |
|---|---|---|
| `implemented` | The task outcome is achieved for the whole scope and you have seen evidence | evidence (>= 1 artefact) |
| `partial` | Achieved for part of the scope, or some elements missing | evidence of what exists; gap in notes |
| `planned` | Not in place; funded/committed plan exists | owner, target_date (YYYY-MM-DD) |
| `not-implemented` | Not in place and no committed plan | notes; owner if known |
| `not-applicable` | Genuinely irrelevant to the scope (SSDF's own example: no compiler means no compiler-configuration practice, PDF p.12). Note PW.6 also covers interpreters and build tools, so "we don't compile" rarely makes all of PW.6 N/A | justification |

- Tool output alone is not evidence of `implemented`: a scanner that runs but whose findings are not triaged
  is at most `partial` for PW.7.2 (the task requires recording and triaging issues).
- Policy without practice (or practice without the defined policy/criteria) is `partial`.
- Unverified claims stay `partial` or are marked in notes "stated, not evidenced"; the checker scores
  `implemented` without evidence as 0 and lists it as a gap.
- Prefer `partial` to `not-applicable` when in doubt; `not-applicable` removes the task from the denominator.

## Outputs

1. **Filled worksheet** (`ssdf-assessment.yaml|csv|md`) that passes `check-assessment`.
2. **Assessment summary report** (Markdown) with headings: Scope and method; Overall result (coverage % and
   implemented % exactly as the tool reports, counts by status); Results by practice group (table);
   Validation issues; Prioritised gaps (table: rank, task id, status, why it matters, owner, target date);
   Roadmap (30/60/90 days or quarters); Assumptions and limitations. Cite tasks as `PW.7.2 (p.23)` using the
   PDF page from `ssdf show`.
3. **Evidence matrix** from `ssdf evidence-matrix` (attestation-style; not an attestation form).
4. **Pipeline mapping** from `ssdf map-pipeline` when a pipeline was reviewed, with a list of tasks lacking any
   supporting control and the proposed controls.
5. **Artefacts from templates** as needed:
   [SSDF gap assessment](templates/ssdf-gap-assessment.md),
   [secure development policy outline](templates/secure-development-policy-outline.md),
   [vulnerability response and disclosure procedure](templates/vulnerability-response-procedure.md),
   [software release integrity checklist](templates/release-integrity-checklist.md),
   [SBOM / provenance record](templates/sbom-provenance-record.md).

## Quality checklist

- [ ] Every task id cited exists in SSDF v1.1 (no PW.10.x, no retired ids presented as current).
- [ ] All 42 tasks assessed; `check-assessment` shows `Validation: PASS` (or remaining errors are listed).
- [ ] Figures quoted match the tool output; the prioritisation is labelled as a heuristic.
- [ ] Every `implemented` row names concrete evidence; every `not-applicable` row has a justification.
- [ ] No statement that the organisation or pipeline "is SSDF compliant/certified"; say "self-assessed
      coverage" and "supports" instead.
- [ ] Notional examples are presented as options, not requirements; page citations are PDF pages.
- [ ] Shared-responsibility items name the responsible party (PDF p.12).

## Sources

- `nist-ssdf` - NIST SP 800-218, *Secure Software Development Framework (SSDF) Version 1.1:
  Recommendations for Mitigating the Risk of Software Vulnerabilities*, February 2022
  (sources/pdfs/nist-ssdf-1-1.pdf). Relied on: Executive Summary (PDF p.8, printed p.vi); Section 1
  Introduction (PDF pp.10-12, printed pp.1-3); Section 2 and practice groups (PDF p.13, printed p.4);
  Table 1 practices, tasks, examples and references (PDF pp.14-28, printed pp.5-19); Appendix A Table 2
  EO 14028 mapping (PDF p.33, printed p.24); Change Log (PDF p.36, printed p.27). Printed page = PDF page - 9.
- Catalog: `catalog/nist-ssdf.json`, extracted by `scripts/extract/ssdf.py` (verbatim, whitespace normalised).

Further guidance: [assessment method](references/assessment-method.md),
[pipeline mapping rules](references/pipeline-mapping-rules.md),
[EO 14028 and attestation-style evidence](references/eo14028-and-attestation.md).

## Limitations

- Output supports, but does not replace, qualified professional judgement, independent assessment, or a
  formal attestation or approval by an accountable officer. A self-assessment score is not compliance.
- SSDF 1.1 only: later SSDF revisions or community profiles (e.g. for AI) are not in the catalog.
- The coverage formula, prioritisation tiers and pipeline mapping rules are this library's heuristics, not
  NIST guidance; NIST does not prioritise the practices.
- Informative references are reproduced as printed in 2022 (e.g. BSIMM12, OWASP ASVS 4.0.3); they may have
  been superseded.
- The skill does not reproduce any government attestation form; check the current official form and legal
  requirements separately.
