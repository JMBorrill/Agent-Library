---
name: software-delivery-metrics
description: Compute and interpret DORA's five software delivery performance metrics - Change lead time, Deployment frequency, Failed deployment recovery time, Change fail rate and Deployment rework rate - per service from a deployments CSV, with stated operational definitions, medians/percentiles, sample-size, mixed-service and timezone checks, and DORA's common-pitfall cautions. Use when baselining delivery performance, preparing an improvement retrospective, checking a metrics dashboard's definitions, or when someone proposes using delivery metrics as targets or team league tables.
metadata:
  pack: software
  version: "1.0.0"
  sources: "dora"
---

# Software delivery performance metrics (DORA)

## Purpose
Give one team a trustworthy, clearly defined baseline of its own delivery throughput and
instability for one application or service, so it can choose an improvement, act and re-measure —
without turning the numbers into targets or comparisons between teams.

## When to use
- Establishing a baseline before an improvement experiment (batch size, CI, deployment automation).
- Re-measuring after a change to see whether throughput/instability moved.
- Reviewing a delivery dashboard: are the definitions explicit and per service?
- Challenging a proposal to rank teams or set "deploy daily" mandates (use the cautions).

**Do not use when:** you need service reliability for users (use `sre-service-level-objectives`;
reliability is operational, not delivery, performance); you want individual developer productivity
(these metrics are not for individuals); or data comes from several unrelated services that you
intend to blend.

## Inputs
Required
- Deployments CSV (template `assets/templates/deployments.csv`): `deploy_id`, `service`,
  `deployed_at`, `status` (`success` | `failed` = needed immediate intervention such as rollback or
  hotfix).
- Optional columns: `commit_times` (`;`-separated) or `first_commit_at`; `is_rework` (`yes` =
  unplanned deployment caused by a production incident); `restored_at` for failed deployments.
- All timestamps ISO 8601 **with** offset (`Z` or `+01:00`); naive timestamps are rejected.
Optional
- Window (`--start`, `--end`, end exclusive), service filter (`--service`), minimum sample size.

## Procedure
1. **Write operational definitions** with the team before extracting data: what counts as a
   production deployment, a failed deployment (immediate intervention needed), a rework deployment,
   and "restored". DORA does not prescribe formulas; the script prints the definitions it applies.
2. **Extract one service** from the CD system and incident tracker into the CSV. Prefer commit
   timestamps for every commit in each deployment; otherwise first commit time.
3. **Compute**:
   `python3 scripts/dora_metrics.py deployments.csv --service scheduling-api --start 2026-09-01 --end 2026-10-01`
4. **Fix data errors** (`naive-timestamp`, `malformed-row`, `negative-duration`,
   `duplicate-deploy-id`) at source and re-run; excluded rows bias every metric.
5. **Read warnings**: `small-sample` (default < 10) → treat as indicative only; `mixed-services` →
   re-run per service; `unrecovered-failure` → recovery time is understated.
6. **Interpret all five together** (throughput: lead time, frequency, recovery time; instability:
   change fail rate, rework rate). Look at medians and p90, not means; note trends over several windows.
7. **Run the improvement loop**: baseline → team conversation → commit to one improvement → plan →
   do the work → check progress → repeat. Record the hypothesis and re-measure on the same definitions.

## Decision criteria
| Situation | Rule |
|---|---|
| Fewer than `--min-sample` deployments or lead-time samples | Report as indicative; widen the window rather than over-interpreting. |
| More than one service in the data | Do not publish a blended figure; compute per service. |
| Request to compare teams or set metric targets | Decline the comparison/target; cite the cautions; offer a per-team trend instead. |
| Throughput up and instability up | Investigate batch size and test/deploy automation before celebrating. |
| Recovery time large with few failures | Review the incidents individually; a median of 2 is not a trend. |
| Definitions changed between windows | Do not compare across the change; re-baseline. |
| Legacy names (MTTR, "four keys") in a dashboard | Rename to the current metric names and check definitions match. |

## Outputs
- Metrics report (`--json`), schema `assets/schemas/dora-metrics.output.schema.json` — metrics,
  definitions, categories, cautions and data findings.
- `delivery-metrics-baseline.md` — window, service, definitions, numbers, chosen improvement.

## Validation
- `python3 scripts/dora_metrics.py deployments.csv --json` → exit 0 = no data errors; exit 1 = rows
  excluded for data errors (metrics still shown for the remaining rows); exit 2 = unreadable file or
  bad window arguments.
- Percentiles use linear interpolation between closest ranks (rank = (n − 1) × p / 100).
- PASS does **not** mean performance is good or comparable to anyone else; benchmark clusters from
  DORA reports were not read for this library and are deliberately not provided.

## Examples
- `assets/examples/deployments-pass.csv` — 12 deployments of `scheduling-api` → exit 0; Deployment
  frequency 12 (0.75/day over 16 days), Change lead time median 7.5 h (n = 14), Change fail rate
  0.1667, Failed deployment recovery time median 1.125 h, Deployment rework rate 0.1667.
- `assets/examples/deployments-fail.csv` — exit 1 with `naive-timestamp`, `negative-duration`,
  `malformed-row`, `duplicate-deploy-id`; warnings `mixed-services`, `small-sample`,
  `unrecovered-failure`.

## Escalation and stop conditions
- **Stop** if asked to produce individual-level or cross-team ranking outputs; escalate to the
  engineering manager with the cautions.
- If deployment status or incident linkage cannot be reconstructed reliably, report only
  Deployment frequency and Change lead time and say why.
- Hand interpretation and improvement selection to the team; `software-quality-reviewer` may review
  definitions; `reliability-engineer` for recovery-time and incident data questions.

## References
- `dora` — DORA, "DORA's software delivery performance metrics" (`hugo/content/guides/dora-metrics/_index.md`,
  updated 2026-01-05): § "Throughput and instability" (five metric names and definitions), § "Key
  insights", § "Common pitfalls" (seven pitfalls), § "Next steps" (improvement loop); history page
  `hugo/content/insights/dora-metrics-history/index.md` (MTTR → Failed deployment recovery time,
  2023; rework rate added 2024). Verified: `sources/audits/dora.md`. Source ID: `dora`.
- Note: the current guide groups Failed deployment recovery time under throughput; this skill
  follows the guide as written.
- Attribution: definitions and cautions paraphrased from DORA (Google LLC), dora.dev, CC BY 4.0.
- Method notes: [references/metric-definitions.md](references/metric-definitions.md).
