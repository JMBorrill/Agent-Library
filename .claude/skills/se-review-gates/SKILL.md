---
name: se-review-gates
description: Prepare and run evidence-based milestone reviews (concept, requirements, system definition, preliminary/critical design, test readiness, acceptance, operational readiness) by checking criteria against recorded evidence, automated check results and open actions, then producing a GO / GO_WITH_CONDITIONS / NO_GO recommendation for a named human gate authority. Use when assembling a review package, chairing or simulating an independent review, or deciding whether a project is ready to pass a gate.
metadata:
  pack: systems-engineering
  version: "1.1.0"
  sources: "nasa-se-manage nasa-se"
---

# Milestone review gates

## Purpose
Make gate decisions on evidence rather than slides: each readiness criterion is met with a reference,
partially met with a condition, or blocks. The reviewer recommends; the gate authority decides.
Supports the NASA process *Technical Assessment* and the life-cycle reviews it serves (see References);
reviews are milestones, not additional processes.

## When to use
- Assembling a review package (requirements review, design reviews, test readiness, acceptance, ops).
- Acting as independent reviewer: challenge evidence, raise review item discrepancies (RIDs/actions).
- Deciding whether a physical test may proceed (TRR) — as a recommendation to the authorising human.

**Do not use when:** you only need the status of a few parameters (`se-technical-assessment`), or for
software release readiness (`sre-production-readiness`) unless the software is part of a system gate.
Do not run every review on every project — choose per `se-technical-planning` tailoring.

## Inputs
Required: review JSON (`assets/examples/review-pass.json` shows the shape): review type, authors,
independent reviewers, gate authority, evidence per criterion, automated check results, actions.
Criteria: default `assets/data/review-criteria.json` (**library-defined generic criteria — not NPR 7123.1
text**); supply programme criteria with `--criteria`.
Package template: `assets/templates/review-package.md`.

## Procedure
1. **Select the review and criteria** appropriate to the phase and tailoring; load programme criteria if
   they exist.
2. **Run the automated checks** on current artifacts and record exit codes and report paths — e.g.
   `req_lint.py` (se-requirements), `vmatrix_check.py` (se-verification-validation), `icd_check.py`,
   `risk_check.py`, `tpm_track.py`, `baseline_diff.py`.
3. **Map evidence to each criterion**: `met` only with an evidence reference a reviewer can open;
   `partial` with a justification; `na` with a justification.
4. **Independent review**: a reviewer who did not author the artifacts reads the evidence, challenges
   assumptions, and records actions (`severity` major/minor, owner, due date, closure evidence).
5. **Compute**: `python3 scripts/review_readiness.py review.json [--criteria programme.json]`
6. **Write the review report**: recommendation, blocking items, conditions with owners/dates, dissenting
   views, and the explicit statement that the gate authority decides.
7. **Record the decision** only as given by the named gate authority (name, date, conditions).
8. **Track actions to closure**; closed actions need closure evidence.

## Decision criteria
| Situation | Effect |
|---|---|
| Blocking criterion not met / missing / met-without-evidence | NO_GO |
| Any automated check failed | NO_GO (fix or justify and re-run) |
| Open major action | NO_GO |
| Partial criteria, non-blocking gaps, open minor actions | GO_WITH_CONDITIONS |
| All met with evidence, no open actions | GO (still a recommendation) |
| No reviewer independent of the authors | NO_GO |

## Outputs
`review-package.md`, `review_readiness.py --json` report, action/RID log, gate decision record
(completed by the human authority).

## Validation
Exit 0 ⇒ recommendation is GO or GO_WITH_CONDITIONS on the evidence supplied. The tool checks evidence
*presence and status*, not technical quality; the independent reviewer must open the evidence.

## Examples
- `assets/examples/review-pass.json` (SRR) → GO_WITH_CONDITIONS (partial SRR-04, open minor action).
- `assets/examples/review-fail.json` (TRR) → NO_GO: `claimed-without-evidence`, `na-without-justification`,
  `check-failed`, `action-incomplete`, `no-independent-review`; TRR-03 (test hazards) not met.

## Escalation and stop conditions
- Never state that a gate has been passed, a test authorised or a design approved; only the gate
  authority can. Physical tests with hazards require qualified human authorisation after TRR.
- If criteria are disputed, escalate to the gate authority before the review, not after.
- Reviewer agents (`independent-reviewer`, `safety-risk-reviewer`) cannot review their own work.

## References
- `nasa-se-manage` — Technical Assessment §6.7; life-cycle reviews per NPR 7123.1 *(secondary
  corroboration only — review acronyms corroborated, phase mapping and criteria NOT verified; see
  `sources/audits/nasa-se.md`)*.
- Review roles and pitfalls: [references/review-practice.md](references/review-practice.md).
