---
name: product-experiment-design
description: Design, size and evaluate product A/B experiments on conversion-type metrics - falsifiable hypothesis, one primary metric, baseline, minimum detectable effect, alpha/power sample size, duration, stopping rule, guardrails, ethics note and a decision rule fixed before launch; then evaluate results with a two-proportion z-test and confidence interval. Use when planning or reviewing an A/B test, asking "how many users do we need", checking whether a result is significant, or challenging peeking and moved goalposts.
metadata:
  pack: product
  version: "1.0.0"
  sources: "gov-service"
---

# Product experiment design

## Purpose
Turn a product hypothesis into an experiment whose outcome can change a decision: a falsifiable
prediction, a sample large enough to detect the smallest effect worth acting on, rules for stopping
and shipping written down before launch, and guardrails that catch harm. Then read the result
honestly — effect size with uncertainty, not just "p < 0.05".

## When to use
- A discovery assumption (see `product-discovery`) needs a quantitative test with real users.
- Someone asks for a sample size, duration, or "is this result significant?".
- Reviewing an experiment plan or readout before a ship decision.

**Do not use when:** you have fewer than a few hundred eligible users per arm in a reasonable window
(use qualitative research or a concierge test instead); the metric is continuous revenue or time
(this calculator covers proportions only — get a statistician or use a t-test-based method); the
change cannot ethically be withheld from a control group; or users have not been told experiments may
run and the change affects price, safety or access (escalate).

## Inputs
- Experiment plan JSON — template `assets/templates/experiment-plan.json`, schema
  `assets/schemas/experiment-plan.schema.json`. Key fields: `hypothesis.prediction`,
  `primary_metric.definition`, `baseline`, `mde` (absolute), `direction`, `alpha`, `power`,
  `sample_size_per_arm` and/or `expected_eligible_per_day`, `duration_days`, `stopping_rule`,
  `ethics.consent_note`, `decision_rule` (`set_before_launch`, `recorded_on`, `ship_if`,
  `do_not_ship_if`), `guardrails`.
- Results JSON (after the test) — counts per arm for the primary metric and each guardrail, see
  `assets/examples/results-pass.json`.
- Baseline rate from at least 2–4 weeks of historical data for the same population.

## Procedure
1. **Write the hypothesis**: "Because <evidence ID>, we believe <change> will <effect> for <users>",
   and a prediction with a direction and number ("rebooked-within-48h rises from 30% to ≥35%").
2. **Pick one primary metric** with an exact definition (numerator, denominator, window, unit of
   randomisation). Everything else is secondary or a guardrail.
3. **Choose the MDE** as the smallest effect that would change the decision (commercial value),
   not the effect you hope for.
4. **Size it**: `python3 scripts/experiment_calc.py sample-size --baseline 0.30 --mde 0.05`
   (defaults: alpha 0.05 two-sided, power 0.8, pooled formula). If traffic is fixed, check what is
   detectable: `experiment_calc.py mde --baseline 0.30 --n 1400`.
5. **Set duration** = required n ÷ eligible units per day per arm, rounded up to whole weeks
   (booking behaviour is weekly) and at least 7 days.
6. **Write stopping and decision rules before launch** and record the date. Peeking-based stopping
   ("stop when significant") is an error unless a sequential design is named.
7. **Add guardrails** (complaints, cancellations, opt-outs, latency) with a maximum tolerated
   absolute change, and an ethics/consent note.
8. **Check the plan**: `python3 scripts/experiment_calc.py plan plan.json` → fix all errors.
9. **After the run**, evaluate exactly as pre-registered:
   `python3 scripts/experiment_calc.py evaluate --plan plan.json --results results.json`.
   Report difference, CI and p-value; guardrail status; the script's recommendation; then the human
   decision.

## Decision criteria
| Situation | Rule |
|---|---|
| Any guardrail point estimate worse than its limit | RECOMMEND_DO_NOT_SHIP (overrides primary) |
| p < alpha and CI entirely on the predicted side of 0 | RECOMMEND_SHIP (subject to `ship_if` and human decision) |
| p < alpha and CI entirely on the harmful side | RECOMMEND_DO_NOT_SHIP |
| Otherwise | INCONCLUSIVE — do not "extend until significant"; decide per pre-registered rule |
| Guardrail CI crosses its limit but estimate within it | Warning: judgement, consider more data |
| Required n > achievable traffic | Raise MDE, lengthen within reason, or switch to qualitative evidence |
| Power < 0.8 or alpha > 0.1 | Warning; record why |

Formula choice: `pooled` (default) uses the pooled variance under H0 and unpooled under H1 (Fleiss
form without continuity correction); `unpooled` uses (z_α/2 + z_β)² × (p1q1 + p2q2) / d². Report which
one you used. See [references/statistics.md](references/statistics.md).

## Outputs
- Checked plan JSON and plan report (`plan --json`, schema `assets/schemas/report.output.schema.json`).
- Calculation records (`sample-size`/`mde`/`evaluate --json`, schema `assets/schemas/calc.output.schema.json`).
- Readout: primary effect with CI, guardrails, recommendation, and the named human decision.

## Validation
- `python3 scripts/experiment_calc.py plan <plan.json> --json` → exit 0 no blocking findings, 1
  blocking findings, 2 invalid/unreadable input (also for p = 0 or 1, MDE ≤ 0, power ≥ 1).
- Known answers (tests): baseline 10% → 12%, alpha 0.05 two-sided, power 0.8 → 3,841/arm pooled,
  3,839/arm unpooled; 100/1000 vs 130/1000 → z ≈ 2.103, p ≈ 0.0355, 95% CI ≈ [+0.0021, +0.0579].
- PASS does **not** mean the experiment is valid: randomisation bugs, sample-ratio mismatch, novelty
  effects, interference between walkers sharing clients and metric definition errors are not
  detected. Normal approximation is poor when expected counts per arm are below ~10.

## Examples
- `assets/examples/plan-pass.json` — `plan`: exit 0, required 1,377/arm (planned 1,400; 110/day × 28
  days ÷ 2 = 1,540 achievable).
- `assets/examples/plan-fail.json` — exit 1 with `prediction-not-falsifiable`,
  `multiple-primary-metrics`, `baseline-range`, `mde-range`, `power-range`, `optional-stopping`,
  `ethics-no-consent-note`, `decision-rule-not-preregistered`, `decision-rule-incomplete`,
  `decision-rule-after-launch`; warnings `duration-short`, `no-guardrails`.
- `evaluate --plan plan-pass.json --results results-pass.json` → exit 0, RECOMMEND_SHIP
  (diff +0.055, CI [+0.020, +0.090]); with `results-fail.json` → exit 1, `guardrail-breached`,
  RECOMMEND_DO_NOT_SHIP.

## Escalation and stop conditions
- **Stop** if the test changes prices, eligibility, safety information or treats protected groups
  differently — needs legal/ethics review before launch.
- **Stop** if the decision rule was edited after launch: report both versions to the decision owner.
- Unexpected sample-ratio mismatch or metric definition changes mid-test → halt the readout, ask an
  analyst. Hand plans and readouts to `product-lead`; ask `independent-reviewer` to check readouts
  that will drive major investment.

## References
- `gov-service` — GOV.UK Service Manual guidance on measuring success and iterating *(INACCESSIBLE in
  this environment; general context only, no section relied on; see `sources/audits/gov-service.md`)*.
- The statistical formulas are standard textbook results restated in original wording; derivation
  notes, known-answer calculations and pitfalls: [references/statistics.md](references/statistics.md).
