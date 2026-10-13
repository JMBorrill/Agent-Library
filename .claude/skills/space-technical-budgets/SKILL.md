---
name: space-technical-budgets
description: Build and check spacecraft/robot engineering budgets (mass, power, energy per mode, data volume, link margin, pointing/timing) with explicit allocations, current best estimates, maturity-based contingency and system margin against a programme-supplied margin policy, plus TPM trend tracking and radio link budgets (FSPL, EIRP, G/T, Eb/N0). Use when preparing or reviewing a mass/power/data/link budget, setting or auditing contingency and margin, tracking technical performance measures across design iterations, or checking a link closes before a design review.
metadata:
  pack: space-engineering
  version: "1.0.0"
  sources: "nasa-se ecss-se"
---

# Space technical budgets (mass, power, energy, data, link) with margin policy

## Purpose
Give every critical resource an allocation, a current best estimate (CBE) with a stated maturity, a
contingency that shrinks as maturity grows, and a system margin checked against the **programme's own**
margin policy — then track those numbers over time as technical performance measures (TPMs) so a
breach is seen before it happens. Results are **analysis aids with stated assumptions**; any numerical
design margin produced or proposed here is a **proposal until approved by the programme** (named
budget owner / system engineer).

## When to use
- Building or updating a mass, power, energy-per-mode, data-volume, link or pointing/timing budget.
- Reviewing a supplier's or subsystem's budget before a design review (SRR/PDR/CDR-style).
- Choosing contingency per maturity class or auditing whether margins meet policy.
- Tracking TPMs across dated snapshots and warning when the trend projects a breach.
- Checking a radio link closes (proximity, relay or direct-to-Earth) with explicit losses.

**Do not use when:** no allocation or margin policy exists yet and nobody owns setting one (stop —
ask the programme; do not invent policy values); the problem is a full RF/propagation analysis with
fading statistics, coding curves or interference (hand to an RF/communications specialist); pointing
error needs a statistical error-budget method beyond simple RSS; or a contract makes a specific
standard's margin table mandatory and you have not read that standard.

## Inputs
Required
- Budget CSV: `assets/templates/budget.csv` — `item_id, parent, budget, unit, cbe, maturity,
  quantity, mode, notes`. Rows referenced as a `parent` are group headers (their `cbe` is ignored).
  `mode` blank/`all` means the item draws in every mode of that budget.
- Margin policy JSON (programme-supplied): `assets/templates/margin-policy.json`, schema
  `assets/schemas/margin-policy.schema.json` — contingency % per maturity (optionally overridden per
  budget), required system margin %, allocation (or `allocation_by_mode`), `margin_basis`
  (`allocation` default, or `predicted`), `combine` (`sum` default, `rss` for independent error terms).
Optional
- Dated snapshots of the same budget for TPM trends; a milestone date to project to.
- Link JSON: `assets/templates/link.json`, schema `assets/schemas/link-input.schema.json` — every
  quantity is `{"value", "unit"}`; units are validated.

The files `assets/examples/margin-policy-example.json` and `margin-policy-tight-example.json` carry
**example values — not from ECSS or NASA; replace with your programme's policy**. The script warns
`example-policy-in-use` whenever such a file is used.

## Procedure
1. **Get the policy first.** Obtain the margin policy from the programme (document ID and issue in
   `label`). If none exists, draft one as a *proposal* in the template and route it for sign-off; do
   not run conclusions against invented numbers.
2. **Define budgets and allocations.** One budget per resource; power and energy per operating mode
   (e.g. drive, hop-prep, safe). Allocations flow down from system requirements (`se-requirements`).
3. **Build the item tree.** One leaf per hardware/software item with `quantity`, `unit`, `cbe` and
   `maturity` (`estimated` < `calculated` < `heritage`/`measured`, or the programme's classes). Record
   the evidence for each CBE in `notes` (drawing, datasheet, weighing record).
4. **Energy and data:** compute energy items upstream as power × duty × duration for each mode and
   enter them as `energy` rows (Wh); data as volume per pass/period against downlink capacity.
5. **Roll up and check:**
   `python3 scripts/budget_calc.py budget.csv --policy policy.json`
   Fix every `error` (unit mismatch, missing maturity, unknown mode, budget not in policy, negative
   margin, margin below policy). Resolve or justify each `warning` (missing quantity is assumed 1).
6. **Track TPMs** at each design iteration (keep each dated CSV under configuration control):
   `python3 scripts/budget_calc.py --policy policy.json --snapshot 2026-01-01=a.csv --snapshot 2026-04-01=b.csv --project-to <milestone>`
   A `trend-projects-breach` or `trend-projects-margin-shortfall` warning triggers a corrective-action
   discussion (mass reduction, power-mode rescheduling, re-allocation), not an automatic redesign.
7. **Close the links:** `python3 scripts/link_budget.py evaluate link.json` (or `fspl` for path loss
   only). List every loss explicitly; record where each gain/loss value came from.
8. **Report** totals, margins, trend and open items; route the report and any proposed margin or
   allocation change to the budget owner for sign-off (`se-change-control` after baseline).

## Decision criteria
| Situation | Rule |
|---|---|
| Margin < 0 (predicted > allocation) | Blocking. Escalate to system engineer; options: reduce, re-allocate, descope — owner decides. |
| 0 ≤ margin < policy | Blocking for the review; record as a TPM concern with an owner and closure plan. |
| Trend projects breach before milestone | Warning: open a risk (`se-risk-analysis`) and plan corrective action. |
| CBE without evidence | Treat maturity as `estimated` whatever the column says. |
| Item draws in all modes | Use `mode` = `all`; never duplicate it per mode (double counting). |
| Independent error terms (pointing, timing jitter) | `combine: rss` only if the terms are independent and zero-mean; otherwise `sum` (conservative). |
| Link margin below programme minimum | Blocking; re-check losses and assumptions before changing hardware. |
| Policy marked `is_example` | Results are illustrative only; never present them as programme margins. |

## Outputs
- Budget report (`budget_calc.py --json`, schema `assets/schemas/budget-report.schema.json`): totals per
  budget/mode, roll-up per header node, margins, status, TPM trend, findings.
- Link report (`link_budget.py evaluate --json`, schema `assets/schemas/link-report.schema.json`).
- `budget-review.md` (free text): open items, evidence gaps, proposed allocation/margin changes
  awaiting programme sign-off.

## Validation
- `python3 scripts/budget_calc.py assets/examples/budget-pass.csv --policy assets/examples/margin-policy-example.json --json` → exit 0.
- `python3 -m unittest tests.test_space_technical_budgets -v` (known answers: FSPL 2.4 GHz/1 km ≈
  100.05 dB; hand-computed contingency roll-up 19.6 kg CBE + 1.925 kg = 21.525 kg).
- PASS means the arithmetic is consistent and the supplied numbers meet the supplied policy. It does
  **not** mean the CBEs are right, the item list is complete, the policy is adequate, or the design is
  acceptable; those need the accountable engineer and an independent reviewer.

## Examples
- `assets/examples/budget-pass.csv` + `margin-policy-example.json` → exit 0; mass 21.525 kg vs 30 kg
  (28.25 % margin); warning `example-policy-in-use`; info `unit-converted` (harness in grams).
- `assets/examples/budget-fail.csv` + `margin-policy-tight-example.json` → exit 1 with
  `duplicate-id`, `unit-mismatch`, `missing-maturity`, `budget-not-in-policy`, `unknown-mode`,
  `margin-below-policy` (mass), `negative-margin` (power/drive); warning `missing-quantity`.
- `assets/examples/tpm/mass-snapshot-*.csv` (three dates) → exit 0 with
  `trend-projects-margin-shortfall` at the default 180-day horizon.
- `assets/examples/link-pass.json` → exit 0 (Eb/N0 margin ≈ 18.0 dB); `link-fail.json` → exit 1
  `negative-link-margin`.

## Escalation and stop conditions
- **Stop** if no margin policy or allocation can be sourced — ask the programme; do not fill in values.
- **Stop** if the contract invokes a specific standard's margin philosophy you cannot read; flag
  "requires licensed-standard check".
- Hand to `systems-engineer` (budget owner/TPM tracking), `systems-architect` (re-allocation trades),
  `vv-engineer` (how each CBE will be verified: weighing, power measurement, link test) and
  `safety-risk-reviewer` when a margin shortfall affects a safety function (e.g. survival heater power).
- Any physical test (weighing flight hardware, RF radiation tests) needs authorisation by a qualified
  human under the programme's test and safety procedures.

## References
- `nasa-se` — technical assessment and TPM tracking concept (handbook section on Technical Assessment,
  §6.7 per secondary table-of-contents snippets) *(unverified; primary INACCESSIBLE — see
  `sources/audits/nasa-se.md`)*. No NASA margin values are used.
- `ecss-se` — the space-sector system-engineering standard; its budget/margin provisions were **not
  read** and no clause numbers or values are cited. Check applicability and content under its own
  licence (`sources/audits/ecss-se.md`).
- Method notes: [references/budget-method.md](references/budget-method.md);
  link equations: [references/link-budget-notes.md](references/link-budget-notes.md).
