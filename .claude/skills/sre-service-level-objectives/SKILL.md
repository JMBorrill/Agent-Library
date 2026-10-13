---
name: sre-service-level-objectives
description: Define, check and operate service level objectives - user-journey SLIs from good/valid events, targets, windows, error budgets (allowed bad minutes/events), budget consumed and remaining, burn rates and multi-window multi-burn-rate alert evaluation - plus an SLO specification validator (journey, SLI definition, target, window, owner, exclusion, alerting and error-budget policies). Use when setting or reviewing an SLO, computing an error budget (e.g. 99.9% over 30 days = 43.2 minutes), designing or testing burn-rate alerts, or deciding whether to slow releases because the budget is spent.
metadata:
  pack: reliability-security
  version: "1.0.0"
  sources: "google-sre"
---

# Service level objectives and error budgets

## Purpose
Express reliability as a promise users would recognise (an SLI over a user journey, a target and a
window), turn the gap below 100% into an explicit error budget, and alert on how fast that budget is
being spent — so the team knows when to stop shipping features and fix reliability, and when not to
worry.

## When to use
- Launching a service or a critical user journey (pairs with `sre-production-readiness`).
- Reviewing an existing SLO that pages too often, too late, or never.
- Computing budget status for a release decision or a monthly reliability review.
- Testing an alert policy against observed or synthetic error rates.

**Do not use when:** you need delivery/throughput metrics (use `software-delivery-metrics`); you are
in the middle of an incident (use `sre-incident-response`); or you need contractual SLA penalty
calculations (SLAs are legal commitments — involve the contract owner).

## Inputs
Required
- The user journey and how its success is observable (logs, load balancer, client telemetry).
- Good and valid event definitions; target; window (rolling or calendar).
Optional
- Event counts or bad minutes so far; observed error rates per alert window.
- SLO spec JSON (template `assets/templates/slo-spec.json`, schema `assets/schemas/slo-spec.schema.json`).

## Procedure
1. **Pick the journey** that matters to users (e.g. "receptionist books an appointment"), not a
   component metric.
2. **Define the SLI** as good events / valid events, saying exactly what counts as good (status,
   latency threshold, correctness), what is excluded from valid, and where it is measured.
3. **Choose target and window** from user expectations and current performance; never 100%.
   Compute the budget: `python3 scripts/slo_calc.py budget --target 99.9 --window-days 30`
   (→ 43.2 allowed bad minutes).
4. **Write the exclusion policy** (planned maintenance, client-caused errors) and the **error-budget
   policy** (what changes when the budget is exhausted, who can grant exceptions).
5. **Design alerts** as multi-window, multi-burn-rate rules: each rule has a long window, a short
   window (commonly about 1/12 of the long one) and a burn-rate threshold; it fires only when both
   windows exceed the threshold. Start from the example policy
   `assets/examples/alert-policy-example.json` (example values, see References) and tune.
6. **Validate the spec**: `python3 scripts/slo_calc.py validate slo-spec.json`.
7. **Test the alerts** against synthetic or replayed observations:
   `python3 scripts/slo_calc.py alerts --policy alert-policy.json --observations obs.json`
   Check that a fast burn pages within minutes and a slow leak raises a ticket, not a page.
8. **Operate**: report budget consumed/remaining each period
   (`budget ... --total-events N --bad-events B --elapsed-days E`); apply the error-budget policy;
   revisit the SLO quarterly or after major incidents.

## Decision criteria
| Situation | Rule |
|---|---|
| Target proposed at 100% | Reject: no budget for change; choose the highest target users would notice. |
| Budget consumed ≥ 100% in window | Apply the error-budget policy (e.g. pause risky releases); requires owner decision. |
| Average burn rate > 1 mid-window | Budget will run out before window end at this pace; prioritise reliability work. |
| Alert threshold × long window ÷ SLO window > 1 | Alert can only fire after exhaustion — lower threshold or shorten window. |
| No page-severity alert | Fast burns go unnoticed; add one. |
| SLI cannot distinguish good from bad for users | Redefine the SLI before setting targets. |
| Exclusions growing every month | Treat as a smell; review with the product owner. |

## Outputs
- `slo-spec.json` (schema `assets/schemas/slo-spec.schema.json`) and its validation report
  (`validate --json`, schema `assets/schemas/findings-report.schema.json`).
- Alert evaluation (`alerts --json`, schema `assets/schemas/alerts.output.schema.json`).
- Budget status for reviews (`budget --json`).

## Validation
- `validate` exit 0 = spec has all required elements, a target < 100%, a parseable window and
  consistent alert windows; exit 1 = errors; exit 2 = unreadable input.
- `alerts` exit 1 = at least one rule firing (usable in alert-policy tests); exit 2 = missing or
  invalid observations (zero/negative totals, short ≥ long window).
- Known answers: 99.9% over 30 days → 43.2 min; 99.9% over 28 days → 40.32 min; 99.95% over 30 days
  → 21.6 min; burn rate 14.4 over 1 h of a 30-day window spends 2% of the budget.
- PASS does **not** mean the SLO reflects user happiness or that alerts are well tuned.

## Examples
- `assets/examples/slo-spec-pass.json` (booking API, 99.9%, 30d rolling) → exit 0.
- `assets/examples/slo-spec-fail.json` (mortgage-criteria search) → exit 1 with `missing-field`,
  `sli-incomplete`, `target-range`, `window-format`, `alert-windows`; warnings `no-paging-alert`,
  `no-error-budget-policy`.
- `assets/examples/alert-policy-example.json` + `assets/examples/observations-example.json` →
  `fast-burn-page` firing (16.7× over 1 h, 21× over 5 m), exit 1.

## Escalation and stop conditions
- Exhausted budget with pressure to keep releasing → escalate to the product owner and SRE lead under
  the error-budget policy; do not silently relax the SLO.
- SLOs that appear in customer contracts → involve the contract/legal owner before changing.
- Hand reliability design questions to the `reliability-engineer` agent; use `independent-reviewer`
  to challenge SLOs for critical journeys.

## References
- `google-sre` — Google, *Site Reliability Engineering* (2016) Ch. 4 "Service Level Objectives" and
  *The Site Reliability Workbook* (2018) Ch. 2 "Implementing SLOs" and Ch. 5 "Alerting on SLOs"
  *(chapter numbers from search snippets — unverified)*. Source **INACCESSIBLE** in this environment
  (`sources/audits/google-sre.md`); claimed licence CC BY-NC-ND 4.0 — no text is adapted here;
  procedures are written independently. Source ID: `google-sre`.
- The SLI/error-budget/burn-rate arithmetic is generic. The alert thresholds in the example policy
  (14.4× 1 h/5 m, 6× 6 h/30 m, 1× 3 d/6 h) are commonly cited starting values reported by secondary
  blogs in the audit, **labelled as examples, not as taken from the source** *(unverified)*.
- Method notes: [references/slo-math.md](references/slo-math.md).
