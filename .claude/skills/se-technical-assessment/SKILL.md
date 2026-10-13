---
name: se-technical-assessment
description: Assess technical progress against plans using technical performance measures (TPMs) with limits, alert margins and trend projections, plus measures of effectiveness/performance and progress reviews. Use when tracking mass, power, latency, accuracy, cost-to-complete or similar key parameters over time, preparing a technical status or design review, or deciding whether a parameter trending toward its limit needs corrective action.
metadata:
  pack: systems-engineering
  version: "1.0.0"
  sources: "nasa-se-manage nasa-se"
---

# Technical assessment

## Purpose
Show, with numbers, whether the design is converging on its requirements before it is too late to
change cheaply — and trigger action when margins erode. Corresponds to the NASA process *Technical
Assessment* (see References); formal milestone reviews are run with `se-review-gates`.

## When to use
- From preliminary design onward, for the handful of parameters most likely to break the design
  (mass, power, data rate, latency, accuracy, unit cost, reliability).
- Monthly/sprint technical status reporting; before each design review.
- When an estimate is replaced by analysis or measurement (update the TPM history).

**Do not use when:** you need a full engineering budget roll-up across many items (use
`space-technical-budgets`, then track the totals here as TPMs) or delivery-process metrics for a
software team (use `software-delivery-metrics`).

## Inputs
Required: TPM history CSV (`assets/templates/tpm.csv`): one row per TPM per date with limit (from an
approved requirement), direction, alert margin, value and basis (estimate/analysis/measured/allocation).
Optional: next milestone date for projection; planned profile; MOE/MOP definitions from `se-stakeholder-conops`.

## Procedure
1. **Select TPMs** (typically 3–10): each tied to a requirement ID, with a limit, unit and direction.
   Prefer parameters that are measurable early and drive design.
2. **Set alert margins** with the owner (e.g. larger margins early in design when estimates are
   immature — values are project policy, not universal constants).
3. **Record values with basis and date**; never overwrite history.
4. **Assess**: `python3 scripts/tpm_track.py tpm.csv --milestone YYYY-MM-DD`
5. **Act on signals**: `breach` → corrective action plan or change request (`se-change-control`);
   `alert` or `projected-breach` → design review of contributors, margin recovery options, risk entry
   (`se-risk-analysis`); estimate-only alerts → prioritise measurement.
6. **Report** status, trend and actions in the technical status summary; feed review packages.

## Decision criteria
| Signal | Action |
|---|---|
| breach (margin < 0) | Error — corrective action or approved requirement change; no "ok" reporting |
| alert (margin < alert %) | Investigate contributors; add/update risk |
| projected-breach at milestone | Plan recovery now; trend uses last 3 points (linear) — check physical plausibility |
| limit changed over history | Confirm an approved CR exists |
| mixed units within a TPM | Convert before assessment (error) |

## Outputs
`tpm.csv` history, assessment report (`--json`), technical status summary with actions and owners.

## Validation
Exit 0 ⇒ data consistent and no TPM is in breach. Margins are arithmetic on supplied values; a linear
projection is a heuristic, not a forecast model.

## Examples
- `assets/examples/tpm-pass.csv --milestone 2027-01-15` → exit 0; warning `projected-breach` for
  TPM-LAT although its current margin is 28 %.
- `assets/examples/tpm-fail.csv` → exit 1: `breach`, `inconsistent-units`, `direction`; warnings `alert`,
  `projected-breach`.

## Escalation and stop conditions
- A breach on a safety-related parameter (e.g. e-stop latency) → `safety-risk-reviewer` and hold any
  dependent tests until dispositioned.
- Do not change limits to clear a breach; that is a requirement change needing approval.

## References
- `nasa-se-manage` — Technical Assessment §6.7 *(secondary corroboration only; see
  `sources/audits/nasa-se-manage.md`)*. TPM/MOE/MOP terminology is general SE usage.
