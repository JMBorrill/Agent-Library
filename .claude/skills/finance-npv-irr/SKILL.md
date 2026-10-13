---
name: finance-npv-irr
description: Evaluate a project or investment from its cash flows - NPV with an explicit period-0 convention, IRR with no-IRR and multiple-IRR detection, MIRR, simple and discounted payback, profitability index, CAPM and WACC hurdle rates, DCF enterprise value with a Gordon terminal value, one-way sensitivity tables and break-even switching values. Use when appraising a capital project, product build, acquisition or pricing change, checking someone else's NPV/IRR spreadsheet, or setting a hurdle rate.
metadata:
  pack: finance-credit
  version: "1.0.0"
  sources: "damodaran"
---

# NPV, IRR and discounted cash-flow appraisal

## Purpose
Turn a set of dated cash flows and a defensible discount rate into decision metrics that cannot be
misread: NPV under a stated timing convention, an IRR that is reported only when it is unique,
payback that says "never" when it never happens, and the switching values that show how far an
assumption must move before the answer flips. The method follows the standard corporate-finance
investment-decision logic (invest where returns exceed the hurdle rate, decide on value) associated
with the `damodaran` source; see References for verification status.

## When to use
- Appraising a capital project, product feature build, system replacement, acquisition or lease.
- Reviewing an NPV/IRR model produced by someone else (re-compute it independently).
- Estimating a cost of equity (CAPM) or WACC to use as a hurdle rate.
- Valuing a business unit or SaaS company with explicit FCFs plus a terminal value.

**Do not use when:** the question is per-customer economics (use `finance-unit-economics`); the
appraisal is a UK public-sector business case with a counterfactual and social values (use
`finance-options`); or you need a credit decision or affordability check (use
`credit-criteria-modelling`).

## Inputs
Required
- Cash flows per period (JSON `flows` or CSV `period,cash_flow`) - template
  `assets/templates/cashflow-case.json` or `assets/templates/flows.csv`.
- Discount rate per period (decimal), or `"rate": "wacc"` with a `wacc` block.
- Timing convention: `t0` (default; first flow at time 0, undiscounted) or `t1` (first flow at end of
  period 1 - the spreadsheet `NPV()` convention). The CSV `period`
  column is the actual period index: a CSV starting at period 0 is `t0`, at period 1 `t1`; a later
  start (e.g. 3) zero-fills the earlier periods (info `csv-leading-periods-zero-filled`) so each flow is
  discounted by its own period. Duplicate, negative or missing interior periods are rejected (exit 2);
  `--convention` cannot contradict the CSV periods.
Optional
- `finance_rate`, `reinvest_rate` (MIRR; default = discount rate); `capm`; `wacc`; `dcf`
  (`fcf` years 1..N, `rate`, `terminal_growth`); `sensitivity` and `breakeven` variables
  (`rate`, `inflow_scale`, `outflow_scale`). Input schema: `assets/schemas/cashflow-input.schema.json`.

## Procedure
1. **Frame the decision.** Write the question, the alternative (do nothing / next best option),
   horizon, currency and whether flows are nominal or real. The rate must match the flows' basis.
2. **Build incremental flows only:** cash (not accounting profit), after tax, including working
   capital and terminal/clean-up flows; exclude sunk costs; include opportunity costs. Tag each line
   in a short assumptions note with its evidence.
3. **Set the hurdle rate.** For a project with risk like the firm's, use WACC; for different risk,
   use a project-specific beta/CAPM. Record risk-free rate, beta, ERP and their dates.
4. **Run the calculator:** `python3 scripts/cashflow.py case.json` (or `flows.csv --rate 0.10`).
   Read the convention line first; re-run with `--convention t1` if comparing to a spreadsheet.
5. **Read IRR carefully.** `status=unique` is usable. `none-no-sign-change` (error `no-irr`) means
   no IRR exists. `multiple-possible` (warning `multiple-irr`) lists every root found on the grid;
   decide on NPV and MIRR, never on one root.
6. **Check payback** as a liquidity lens only; "never" is a valid answer; `payback-reversal` means
   later outflows push the position negative again.
7. **DCF valuation:** keep terminal growth below the discount rate (the script errors otherwise)
   and at or below long-run nominal growth; if `terminal-value-dominates` fires, extend the explicit
   period or justify the steady state.
8. **Stress the answer:** add `sensitivity` tables and `breakeven` variables; report each switching
   value as "% change from base needed for NPV = 0".
9. **Write up** the decision memo: metrics, assumptions, sensitivities, risks and what is not
   monetised; hand to `independent-reviewer` before anyone relies on it.

## Decision criteria
| Situation | Rule |
|---|---|
| NPV > 0 at the hurdle rate and switching values are comfortably far | Recommend proceeding to the next decision stage (a recommendation, not an approval). |
| NPV and IRR rankings disagree (mutually exclusive options) | Rank on NPV; IRR ignores scale and timing. |
| Multiple or no IRR | Report NPV/MIRR only; state why IRR is withheld. |
| A switching value is within plausible error of the input (e.g. < 10-15% change) | Flag as fragile; get better evidence for that input before deciding. |
| Terminal value > 75% of EV | Treat the valuation as an assumption about the steady state; show a range. |
| Nominal flows with a real rate (or vice versa) | Stop and fix; do not report a number. |
| Discount rate unsourced | Mark as assumption and show NPV at +/- 2 percentage points. |

## Outputs
- Calculator output (`cashflow.py --json`; schema `assets/schemas/cashflow-output.schema.json`).
- `decision-memo.md`: question, options, metrics table, sensitivity/switching values, risks,
  non-financial effects, assumption list with owners.

## Validation
- `python3 scripts/cashflow.py assets/examples/cashflow-pass.json --json` -> exit 0.
- Exit 1 means a blocking finding (`no-irr`, `irr-not-found`, `terminal-growth-ge-rate`); exit 2
  means malformed input (empty or non-numeric flows, rate <= -100%). `--strict` blocks on warnings.
- PASS means the arithmetic ran on consistent inputs. It does **not** mean the forecasts, rate or
  decision are right; that judgement belongs to the accountable owner.

## Examples
- `assets/examples/cashflow-pass.json` (synthetic scheduling/CRM SaaS module build): NPV
  -21.04 at 10% (t0), IRR 8.896% (unique), MIRR 9.22%, simple payback 2.6, discounted payback
  never, PI 0.979, WACC 7.5%, DCF EV 1,431.82; exit 0 with `terminal-value-dominates` warning.
- `assets/examples/cashflow-fail.json`: exit 1 with `no-irr` and `terminal-growth-ge-rate`.
- `assets/examples/cashflow-multiple-irr.json`: roots 10% and 20%, warning `multiple-irr`.
- `assets/examples/flows-pass.csv` with `--rate 0.10`: same NPV as the JSON pass case.

## Escalation and stop conditions
- Stop if flows mix nominal and real values, or if a material input has no evidence and no owner.
- Escalate to `financial-analyst` for model build and to `independent-reviewer` for challenge;
  the author does not review their own model.
- Anything presented to investors, lenders or a board needs a named human sign-off; outputs are
  not investment advice.

## References
- `damodaran` - corporate finance course material (investment decision, hurdle rate, cost of
  capital, valuation). Primary source INACCESSIBLE in this environment; only the high-level framing
  is secondary-corroborated. All formulas here are standard textbook methods written independently,
  not taken from the source *(unverified against the source; see `sources/audits/damodaran.md`)*.
- Method notes, formulas and pitfalls: [references/dcf-method.md](references/dcf-method.md).
