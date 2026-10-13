---
name: se-decision-analysis
description: Structure and document consequential technical or programme decisions with explicit alternatives, must-criteria screens, weighted criteria, evidence-tagged scores, weight sensitivity and switching weights, ending in a recommendation for a named human decision owner and a decision-log entry. Use for trade studies, make/buy/reuse choices, technology or supplier selection, or whenever a decision needs a defensible, reviewable rationale.
metadata:
  pack: systems-engineering
  version: "1.0.0"
  sources: "nasa-se-manage nasa-se"
---

# Decision analysis

## Purpose
Turn a contested choice into a transparent, reproducible analysis whose result is robust (or visibly
fragile) to the weights and evidence behind it — and keep the decision with an accountable human.
Corresponds to the NASA process *Decision Analysis* (see References).

## When to use
- Architecture/design trade studies (called from `se-architecture-trades`).
- Make/buy/reuse, supplier, technology, test-approach or tooling decisions with lasting consequences.
- Any time someone asks "why did we pick X?" and no written rationale exists.

**Do not use when:** the choice is cheap to reverse (just decide and record it), a mandatory constraint
already determines the answer (record the constraint instead), or the decision is financial appraisal
of investment options (use `finance-options` / `finance-npv-irr`, then optionally summarise here).

## Inputs
Required: decision question, named decision owner, ≥ 2 alternatives (include baseline/do-nothing where
meaningful), criteria with weights and direction, scores with evidence basis.
Template: `assets/templates/decision.json`; log entry: `assets/templates/decision-log.md`.

## Procedure
1. **Frame**: write the question, scope, decision owner, deadline and what happens if no decision is
   made. Confirm the decision is worth formal analysis.
2. **Generate alternatives** broadly before evaluating; include the baseline. Do not let the preferred
   option define the criteria.
3. **Define criteria**: separate *musts* (pass/fail thresholds → `must: {min|max}`) from *wants*
   (weighted). Criteria must be independent (no double counting) and measurable or clearly scaled.
4. **Set weights with the decision owner before scoring**, record who set them; weights sum to 1.
5. **Score** each alternative on each criterion with `basis` ∈ measured/test/analysis/heritage/
   estimate/vendor/judgement and a `source`. Prefer measured and analysis; label judgement honestly.
6. **Run**: `python3 scripts/decision_matrix.py decision.json`
   Review: screened-out alternatives, ranking and margin, `rank-sensitive` criteria and switching
   weights, `weak-evidence` share of the winner.
7. **Probe fragility**: if the winner flips within ±20 % of a weight or the margin is small, gather
   better evidence for the deciding criteria (research activity → `se-risk-analysis`) rather than
   tuning weights.
8. **Recommend and record**: write the decision-log entry with recommendation, uncertainties and
   revisit triggers. The decision owner records the decision and signs; departures from the
   recommendation are recorded with rationale.

## Decision criteria
| Signal | Interpretation / action |
|---|---|
| Margin < `close_margin` (default 0.05) | Treat as a tie; decide on risk, reversibility or more evidence |
| `rank-sensitive` within ±20 % weight | Result depends on value judgement — escalate weight-setting to the owner |
| Switching weight close to current weight | Same as above |
| > 50 % of winner's score from estimate/judgement/vendor | Seek independent evidence before committing |
| Fewer than 3 feasible alternatives with min-max | Use `normalisation: none` and a common scale (`scale_max`) |
| All alternatives fail a must | Revisit requirements or generate new alternatives — do not relax musts silently |

## Outputs
`decision.json` (inputs), analysis report (`--json`, schema `assets/schemas/decision-report.schema.json`),
`decision-log.md` entry signed by the owner.

## Validation
Exit 0 ⇒ inputs complete and analysis computed (weights valid, every score numeric, owner named).
Known-answer test: `tests/test_se_decision_analysis.py`. The tool cannot judge whether the criteria are
the right ones or the scores true; the independent reviewer checks that.

## Examples
- `assets/examples/decision-pass.json` (ASTER locomotion concept, synthetic scores) → HOP recommended,
  WHEEL screened out by a must-criterion, `minmax-few-alternatives` warning, switching weights shown.
- `assets/examples/decision-fail.json` → exit 1: `no-decision-owner`, `direction`, `missing-score`.

## Escalation and stop conditions
- No named decision owner → stop; analysis without an owner is advocacy.
- Safety, regulatory, contractual or > agreed cost thresholds → the decision belongs to the authority
  defined in the project plan (`se-technical-planning`); the agent only recommends.
- Reviewer (`independent-reviewer`) checks criteria independence, weight provenance and evidence.

## References
- `nasa-se-manage` — Decision Analysis §6.8 *(secondary corroboration only; see `sources/audits/nasa-se-manage.md`)*.
- Method notes and pitfalls: [references/decision-method.md](references/decision-method.md).
