---
name: product-requirements-brief
description: Write and lint a software product requirements brief (PRD) - measurable outcomes and guardrails, users, job stories ("When..., I want to..., so I can..."), Given/When/Then acceptance criteria, non-goals, assumptions linked to discovery evidence, risks, accessibility, privacy and security, release slices - and flow verifiable candidate requirements into the se-requirements register. Use when turning a shaped pitch or discovery findings into build-ready scope, reviewing a PRD or backlog of stories, or handing product scope to engineering for traceable requirements.
metadata:
  pack: product
  version: "1.0.0"
  sources: "gov-service shape-up"
---

# Product requirements brief

## Purpose
Give designers and engineers a short, testable statement of what outcome a release must achieve,
for whom, within which boundaries — with every important claim traceable to discovery evidence and
every must-have behaviour expressed as an executable acceptance scenario. Where formal requirements
are needed, the brief flows down into proposed "shall" requirements that `se-requirements` can lint
and a requirements owner can approve.

## When to use
- After a bet on a shaped pitch (`product-shaping`) or a discovery gate (`product-discovery`).
- Reviewing an existing PRD, epic or story backlog before sprint/cycle planning.
- Engineering, assurance or a client needs traceable requirements derived from product scope.

**Do not use when:** the problem is not yet validated (discovery first); the solution is not yet
bounded (shape first); you are writing system/subsystem engineering requirements from a ConOps (use
`se-requirements` directly); or you need test procedures (use `se-verification-validation`).

## Inputs
- PRD Markdown — template `assets/templates/prd.md` with `##` sections: Outcomes and metrics,
  Users, Job stories, Non-goals, Assumptions, Risks, Accessibility, Privacy and security,
  Release slices.
- Stories CSV — template `assets/templates/stories.csv`
  (`id, job_story, acceptance_criteria, priority, evidence_ids, requirement_ids`); `priority` ∈
  must | should | could | wont; several scenarios separated by `;` each starting with `Given`.
- Optional: discovery evidence log CSV (product-discovery format) to resolve evidence IDs.
- Optional: requirement ID prefix (e.g. `DWS-SW`) and requirements owner.

## Procedure
1. **Outcomes first.** Write 1–3 outcomes as metric: baseline → target by date, plus at least one
   guardrail. Outputs ("ship feature X") are not outcomes.
2. **Users and context.** Name the primary users, their context and access needs; include secondary
   users who receive outputs (e.g. owners receiving SMS).
3. **Job stories.** For each need: "When <situation>, I want to <motivation>, so I can <outcome>".
   Keep UI words (button, screen, click) out of the motivation — they belong in design.
4. **Acceptance criteria.** For each must story write ≥1 scenario: `Given <context> When <event>
   Then <observable result with a threshold>`. Prefer numbers (time, count) over adjectives.
5. **Boundaries.** Non-goals as bullets (copy the pitch's no-gos and add any new ones); risks with
   mitigations; assumptions with evidence IDs or planned tests.
6. **Non-negotiables.** Accessibility (conformance target such as WCAG 2.2 AA, plus specific needs;
   run `ux-accessibility-review` on prototypes) and privacy/security (data collected, purpose,
   retention, abuse cases). These are not traded against appetite.
7. **Release slices.** Order the smallest independently valuable slices.
8. **Lint:**
   `python3 scripts/prd_check.py prd.md --stories stories.csv --evidence evidence.csv`
   Fix all errors; resolve or justify warnings in the PRD.
9. **Flow down (when traceable requirements are needed):**
   `python3 scripts/prd_check.py prd.md --stories stories.csv --flow-down candidate-reqs.csv --prefix DWS-SW`
   then `python3 ../se-requirements/scripts/req_lint.py candidate-reqs.csv --tree` (paths relative
   to this skill directory). Each must/should story becomes a stakeholder-level need; each scenario a
   software-level `shall` with `status=proposed`, `verification_method=test`.
10. **Review and approve.** The requirements owner rewrites candidates as needed and approves via
    `se-requirements`; the product owner signs off the brief.

## Decision criteria
| Situation | Rule |
|---|---|
| Must story without Given/When/Then | Error — not ready for build |
| Must story with no evidence ID | Warning — confirm it is a real need or downgrade to should/could |
| Evidence ID cited is a hypothesis | Warning — it is not evidence |
| Outcome has no number | Error; "TBD" target is a warning to close before release |
| Accessibility/privacy section missing or placeholder | Error — never deferred to "later" |
| Motivation names UI controls | Warning — rewrite as the underlying need |
| Story fails format but is useful | Rewrite it; the format forces the situation and outcome to be explicit |
| Flowed-down requirement reads awkwardly | Expected — candidates are mechanical; the requirements owner rewrites before approval |
| Requirement ID already used by another story | Error — one ID, one requirement |

## Outputs
- `prd.md`, `stories.csv` (templates in `assets/templates/`).
- Lint report (`prd_check.py --json`, schema `assets/schemas/prd-check.output.schema.json`).
- `candidate-reqs.csv` in the se-requirements column order
  (`id,parent,level,statement,rationale,source,owner,status,verification_method,acceptance_criteria,verification_id`).

## Validation
- `python3 scripts/prd_check.py <prd.md> --stories <stories.csv> --json` → exit 0 no errors, 1 errors
  (`--strict` also fails on warnings), 2 unreadable input or bad options.
- Flowed-down output from the pass example lints with 0 errors and 0 warnings in `req_lint.py`
  (tested).
- PASS does **not** mean the brief is right: it cannot tell whether outcomes are the most valuable,
  whether stories reflect real users, or whether acceptance thresholds are adequate. It confirms the
  brief is complete, testable in form and traceable.

## Examples
- `assets/examples/prd-pass.md` + `assets/examples/stories-pass.csv` +
  `assets/examples/evidence-log.csv` (synthetic dog-walking "walker day off") → exit 0 with one
  warning (`story-without-gwt` on a could story); `--flow-down` produces 7 rows (3 needs, 4 shall
  requirements).
- `assets/examples/prd-fail.md` + `assets/examples/stories-fail.csv` → exit 1 with
  `placeholder-section`, `missing-section`, `outcome-unmeasurable`, `non-goals-empty`,
  `job-story-format`, `unknown-evidence-id`, `duplicate-id`, `must-without-gwt`, `id-format`,
  `requirement-id-format`, `priority`; warnings `accessibility-unspecific`, `solution-in-story`,
  `non-evidence-cited`, `ambiguous-acceptance`, `must-without-evidence`.

## Escalation and stop conditions
- **Stop** if a must story depends on an untested high-risk assumption — return to
  `product-discovery` or carry it as an explicit release condition signed by the product owner.
- **Escalate** privacy, security or accessibility trade-offs to the accountable owner; never mark
  them out of scope to fit a deadline.
- Hand the brief to `product-lead`; candidate requirements to `requirements-engineer`
  (`se-requirements`); ask `independent-reviewer` to challenge briefs for large or regulated releases.

## References
- `gov-service` — GOV.UK Service Manual ideas on understanding users, measuring success and making
  services accessible *(INACCESSIBLE in this environment; secondary only, no section relied on —
  see `sources/audits/gov-service.md`)*.
- `shape-up` — pitch no-gos and appetite carried into non-goals and release slices *(INACCESSIBLE;
  secondary only — see `sources/audits/shape-up.md`)*.
- Job-story and Given/When/Then forms are widely used community conventions, restated in original
  wording; notes in [references/prd-writing.md](references/prd-writing.md).
