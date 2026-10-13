---
name: finance-options
description: Run a Green Book-style options appraisal - long list to short list against critical success factors, mandatory do-minimum/BAU counterfactual, five case business case outline, real prices on a common base year and period, user-supplied optimism bias, declining discount schedule, NPSV per option, switching values and non-monetised effects kept alongside. Use when preparing or reviewing a UK public-sector (or public-sector-style) business case, comparing investment options against a counterfactual, or checking an economic case for missing counterfactual, inconsistent price bases or silently dropped effects.
metadata:
  pack: finance-credit
  version: "2.0.0"
  sources: "treasury-green damodaran"
---

# Options appraisal (Green Book style)

## Purpose
Produce an economic case in which every short-listed option is compared with the same do-minimum or
business-as-usual counterfactual, on the same appraisal period, price base and discount schedule,
with optimism adjustments and non-monetised effects visible, and with switching values showing how
robust the ranking is. Structure follows HM Treasury Green Book practice (`treasury-green`) as
publicly described; the 2026 edition could not be read here, so specifics are *(unverified)*.

## When to use
- Drafting or reviewing the economic case of a business case (public sector, regulated utility,
  grant-funded programme, or a private body adopting the same discipline).
- Comparing build / buy / partner / do-minimum options for a system or service.
- Checking an appraisal for a missing counterfactual, mixed price bases or unequal periods.

**Do not use when:** a simple commercial NPV/IRR is enough (use `finance-npv-irr`); the question is
customer-level SaaS economics (use `finance-unit-economics`); or you need the official values for
carbon, QALYs or other appraisal parameters - obtain them from current HM Treasury/departmental
guidance, this skill does not supply them.

## Inputs
Required (template `assets/templates/options.json`; schema `assets/schemas/options-input.schema.json`)
- Appraisal settings: price base year, appraisal period (years 0..N), discount schedule
  (`"default"` or bands; default file `assets/templates/discount-schedule-default.json`).
- Critical success factors; long list with CSF assessment (`meets | partial | fails`) and
  short-list decision with reasons.
- Short list incl. exactly one `is_counterfactual` option; per option yearly `costs` and
  `benefits` (positive numbers), price basis, optimism bias % with source, non-monetised effects.
Optional
- `inflation_rate` for nominal series; five case outline text (`five_case`).

## Procedure
1. **Strategic framing.** Write SMART objectives and 3-6 critical success factors. Outline the five
   cases (strategic, economic, commercial, financial, management) *(case names corroborated only by
   secondary sources; unverified against Green Book 2026)* using
   `assets/templates/business-case-outline.md`.
2. **Long list.** Generate options across scope, solution, delivery, implementation and funding
   choices; assess each against every CSF; record why each discarded option was dropped.
3. **Short list.** Keep the do-minimum/BAU counterfactual (always), the likely preferred way forward,
   and realistic alternatives (aim for at least three including the counterfactual).
4. **Cost and benefit series.** Use real prices at one base year; convert nominal series with an
   explicit inflation (deflator) assumption; exclude sunk costs, transfers and financing costs from
   the economic case; values per year 0..N.
5. **Optimism bias.** Enter the uplift (costs) and reduction (benefits) % you justify, with source.
   Official rates are **not** hard-coded - obtain current supplementary guidance and record it.
6. **Non-monetised effects.** List every significant effect you could not value (direction,
   significance, evidence). `[]` means "considered, none found" - never omit the field.
7. **Run:** `python3 scripts/options_appraisal.py options.json` (or `--schedule my-schedule.json`).
   Fix all errors; review warnings.
8. **Interpret.** Compare NPSV relative to the counterfactual; read switching values (fraction of
   incremental benefits/costs that would have to change for incremental NPSV to reach zero; e.g.
   `-0.25` = benefits 25% lower). Weigh non-monetised effects, risk, affordability and
   deliverability. The highest NPSV is an input, not the decision.
9. **Hand over** to `financial-analyst` (model owner) and `independent-reviewer` (challenge); the
   senior responsible owner decides.

## Decision criteria
| Situation | Rule |
|---|---|
| No counterfactual, or more than one | Stop: appraisal invalid (`no-counterfactual`/`multiple-counterfactuals`). |
| Options differ in period or price base | Stop and rebase (`appraisal-period-mismatch`, `price-base-mismatch`). |
| Nominal series without deflator | Stop (`price-basis-unconvertible`). |
| Switching value magnitude < ~0.2 | Ranking fragile; seek better evidence on that driver before choosing. |
| Non-monetised effect rated high could reverse the ranking | Present it with equal prominence to NPSV; consider weighting/multi-criteria analysis. |
| Default discount schedule used | Confirm against Green Book 2026 and the 2026 discount rate review outcome before publication. |
| Health or other special discount schedules | Use only if verified current guidance requires them; supply via `--schedule`. |

## Outputs
- Appraisal results (`options_appraisal.py --json`; schema `assets/schemas/options-output.schema.json`):
  discount factors, PV costs/benefits, NPSV, incremental NPSV vs counterfactual, BCR, switching
  values, non-monetised effects per option, findings.
- `business-case.md` from `assets/templates/business-case-outline.md`; `assumptions.csv` with source,
  owner and date for each assumption.

## Validation
- `python3 scripts/options_appraisal.py assets/examples/options-pass.json --json` -> exit 0.
- Exit 1 on structural errors (listed above, plus `csf-missing`, `non-monetised-missing`,
  `series-length`, `negative-series-value`, `optimism-bias-range`); exit 2 on unreadable or
  non-numeric input or an invalid discount schedule. `--strict` blocks on warnings.
- PASS means the appraisal is internally consistent. It does **not** verify that values, rates or
  optimism bias reflect current HM Treasury guidance, nor that the preferred option is right.

## Examples
- `assets/examples/options-pass.json` (synthetic borough council appointment booking, GBP k,
  2026 prices, 10 years, default schedule): OPT-1 SaaS buy PVC 1,038.39, PVB 1,122.74, NPSV 84.35,
  +1,202.34 vs BAU; OPT-2 in-house build (nominal, deflated at 2%) NPSV -389.26; exit 0 with info
  `schedule-default-unverified`, `converted-nominal-to-real`.
- `assets/examples/options-fail.json`: exit 1 with `no-counterfactual`, `csf-missing`,
  `non-monetised-missing`, `appraisal-period-mismatch`, `price-base-mismatch`,
  `price-basis-unconvertible`.

## Escalation and stop conditions
- Stop if there is no credible counterfactual, or if costs/benefits lack sources and owners.
- Escalate to a qualified government economist / finance business partner before using results in
  a submission; to `independent-reviewer` for challenge. Never present output as approval.
- Re-check the discount schedule and optimism bias guidance on every use (audit re-check date in
  `sources/audits/treasury-green.md`).

## References
- `treasury-green` - HM Treasury Green Book (2026 edition, reported 5 Feb 2026). Primary text
  INACCESSIBLE here; long-list/short-list method, five case model, optimism bias, switching values
  and the STPR schedule are taken from general public knowledge and secondary snippets and are all
  *(unverified)*. Secondary snippets corroborate 3.5% (years 0-30), 3.0% (31-75), 2.5% thereafter;
  the 2.0/1.5/1.0% tail bands are *(unverified - confirm against Green Book 2026)*. See
  `sources/audits/treasury-green.md`.
- `damodaran` - general discounting logic *(unverified; `sources/audits/damodaran.md`)*.
- Method notes: [references/appraisal-method.md](references/appraisal-method.md).
