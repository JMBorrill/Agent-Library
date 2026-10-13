---
name: ai-human-oversight
description: Design and check human oversight for AI decision support - automation level per decision (inform, recommend, draft, act), who approves what, override logging, explanations and appeal routes, automation-bias mitigations, escalation, kill switch and rollback triggers - with a validator for the oversight matrix. Use when an AI system informs or makes decisions about people (credit, eligibility, claims, hiring), when an agent gains autonomy, or when reviewing whether oversight is real rather than rubber-stamping.
metadata:
  pack: ai-governance
  version: "1.0.0"
  sources: "nist-ai"
---

# Human oversight for AI decision support

## Purpose
Decide, for every decision an AI system touches, how much the AI may do, which named human role
is accountable, how humans can override and individuals can appeal, how over-reliance is
countered, and how the system is stopped and rolled back — recorded in an oversight matrix that
a script can check for gaps.

## When to use
- Introducing AI into decisions about individuals (lending, eligibility, pricing, claims, hiring,
  fraud flags) or raising an AI's autonomy (draft → act).
- Designing agent approval flows for side-effecting tools (pair with `ai-prompt-injection-review`).
- Reviewing whether existing oversight works (override rates near zero are a warning sign).

**Do not use when:** the AI has no influence on decisions or external actions (e.g. private
brainstorming); or the question is a legal determination of what a specific law requires —
take this design to qualified counsel.

## Inputs
Required
- List of decisions the system informs or takes, with impact on individuals and the organisation.
- Oversight matrix CSV: `assets/templates/oversight-matrix.csv`.
Optional
- Risk register (`ai-risk-assessment`), eval results (`ai-eval-harness`), staffing/capacity data,
  complaint and appeal process descriptions.

## Procedure
1. **List decisions** at the granularity a person would challenge (e.g. "decline application",
   not "underwriting"). Mark `about_individuals`.
2. **Rate impact** low / medium / high / critical (critical = lasting financial, legal or safety
   effect on a person, or hard to reverse).
3. **Choose the AI role** using the decision criteria table: `inform` (shows facts), `recommend`
   (proposes an outcome), `draft` (prepares an artefact a human edits/sends), `act` (takes effect
   without per-case human action).
4. **Assign humans**: operator (`human_role`) and, where needed, an `approver_role` who approves
   *before* the effect. Named roles, never "the system".
5. **Override and appeal**: every non-inform row logs overrides with reasons; decisions about
   individuals' access to credit or services give an explanation and an appeal/human-review route.
6. **Counter automation bias**: show rationale and sources; for high-impact decisions have the
   operator record a view before seeing the AI output, sample blind reviews, and monitor override
   and agreement rates (very high agreement can mean rubber-stamping).
7. **Monitoring, escalation, kill switch**: a metric per row; rollback trigger thresholds for
   every `act` row; a named kill-switch owner; a manual fallback with capacity.
8. **Validate:** `python3 scripts/oversight_check.py matrix.csv --json`. Fix errors; justify
   warnings in `notes`.
9. **Document** with `assets/templates/oversight-design.md` and hand to the system owner for
   sign-off.

## Decision criteria
| Situation | AI role allowed | Required controls |
|---|---|---|
| Critical decision about an individual | inform or recommend (draft for communications) | named approver; explanation; appeal; logged overrides |
| High impact about individuals | up to draft; `act` only with prior human approval per case | as above |
| Credit / eligibility / pricing-type decision | any role above | explanation_provided=yes **and** an appeal route (validator errors otherwise) |
| Medium impact, not about individuals | recommend/draft; act with rollback trigger | monitoring metric, override log |
| Low impact, reversible, high volume | act | rollback trigger, sample checks, kill-switch owner |
| Override rate ≈ 0% or agreement ≈ 100% over a period | — | investigate rubber-stamping; blind review sample |
| Monitoring metric breaches rollback trigger | — | revert to manual / previous version; escalate |

## Outputs
- `oversight-matrix.csv` + check report (`--json`, schema `assets/schemas/findings-report.schema.json`).
- `oversight-design.md` from `assets/templates/oversight-design.md`.

## Validation
- `python3 scripts/oversight_check.py assets/examples/oversight-matrix-pass.csv` → exit 0.
- `python3 scripts/oversight_check.py assets/examples/oversight-matrix-fail.csv` → exit 1.
- PASS means the matrix has no structural gaps under these rules. It does **not** show that
  reviewers have time, training or authority, that explanations are meaningful, or that the
  design satisfies any particular law. Credit-like decisions are detected by keywords in
  `decision_type` unless `about_individuals` is set — check rows the heuristic may miss.

## Examples
- `assets/examples/oversight-matrix-pass.csv` — synthetic mortgage decision support: AI files
  documents and triages email (`act`, with rollback triggers), recommends affordability, informs
  the accept/decline decision, drafts adverse-decision letters; all with appeal routes → exit 0.
- `assets/examples/oversight-matrix-fail.csv` → exit 1 with `ov-act-without-approval`,
  `ov-act-no-rollback`, `ov-explanation-required`, `ov-appeal-required`,
  `ov-approver-not-human`, `ov-no-human-role`, `ov-no-monitoring`, `ov-override-not-logged`,
  `ov-enum`; warnings `ov-automation-bias`, `ov-duplicate-decision`, `ov-no-kill-switch`.

## Escalation and stop conditions
- Stop if no one will own approval or appeals, or if staffing cannot handle the approval volume
  (approval queues that are always cleared in seconds are not oversight).
- Escalate decisions about individuals in regulated domains to compliance/legal and the
  accountable executive before any `act` role is enabled.
- `ai-governance-reviewer` reviews the matrix; `independent-reviewer` challenges the impact
  ratings; `ai-evaluation-engineer` supplies monitoring metrics.

## References
- `nist-ai` — AI RMF: *accountable and transparent* and *explainable and interpretable*
  trustworthiness characteristics (secondary corroboration); GOVERN accountability structures and
  MANAGE response/deactivation themes are paraphrased topic hints *(unverified)*; AI 600-1
  *human-AI configuration* risk name corroborated by secondary results *(unverified against the
  primary)*. Primary **INACCESSIBLE** — see `sources/audits/nist-ai.md`.
- Automation levels, automation-bias mitigations and kill-switch design notes:
  [references/oversight-method.md](references/oversight-method.md).
