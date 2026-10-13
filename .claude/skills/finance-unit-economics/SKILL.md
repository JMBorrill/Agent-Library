---
name: finance-unit-economics
description: Compute and stress-test subscription/SaaS unit economics - blended and paid CAC, gross and contribution margin, churn-based lifetime, margin-adjusted (optionally discounted) LTV, LTV:CAC, CAC payback, cohort retention tables, base/downside/upside scenarios and sensitivity - with an assumption ledger tagging every input measured, estimate or benchmark. Use when sizing whether a SaaS or subscription product's growth is economic, preparing an investor or board metrics pack, checking a pricing or acquisition-channel change, or challenging LTV:CAC claims.
metadata:
  pack: finance-credit
  version: "1.0.0"
  sources: "damodaran"
---

# Unit economics (SaaS and subscription)

## Purpose
Show, per customer account, how much it costs to acquire, how much contribution it earns each
month, how long it is likely to stay, and how long until acquisition cost is recovered - with every
input labelled by where it came from, and every undefined ratio reported as undefined rather than
as a misleading number. The investment logic (value created only when lifetime contribution exceeds
the cost of acquiring it) is general corporate finance (`damodaran`); the specific SaaS metric
definitions are **common industry practice, not taken from that source**.

## When to use
- A SaaS/subscription business (e.g. a small-business scheduling/CRM product) needs a metrics pack.
- Deciding whether to scale an acquisition channel, change price, or cut churn.
- Challenging an LTV:CAC or payback claim in a pitch, plan or board paper.
- Turning raw cohort counts into a retention table and an implied churn rate.

**Do not use when:** you need project-level NPV/IRR (use `finance-npv-irr`); a public-sector
business case (use `finance-options`); or revenue recognition/accounting treatment questions
(needs an accountant).

## Inputs
Required (monthly basis; template `assets/templates/unit-economics-model.json`)
- `sales_marketing_spend`, `new_customers` (same period), `arpa_monthly`, `gross_margin_pct`
  (fraction), `monthly_churn` (fraction of accounts lost per month).
Each input is `{value, tag, source, owner, as_of}` with `tag` in `measured | estimate | benchmark`.
Optional
- `paid_spend`, `paid_new_customers`, `variable_cost_per_account_monthly`,
  `discount_rate_annual`, `horizon_months` (default 60), `scenarios` (overrides), `sensitivity`.
- Cohort CSV `cohort,month_index,active_customers` (template `assets/templates/cohorts.csv`).

## Procedure
1. **Fix definitions before numbers.** Decide what counts as a new customer, which costs sit in
   S&M (salaries, tools, agencies) and which variable costs sit below gross margin. Write them in
   the model `name`/notes; inconsistent definitions are the commonest error.
2. **Fill the ledger.** For each input record the tag, source (system, report, date) and owner.
   Benchmarks must name the dataset and date; prefer your own measured data once you have it.
3. **Build retention evidence** from billing data:
   `python3 scripts/unit_economics.py --cohorts cohorts.csv` and compare the implied monthly churn
   with the churn input. Young cohorts overstate retention; mixed-cohort averages hide trends.
4. **Run the model:** `python3 scripts/unit_economics.py model.json [--cohorts cohorts.csv]`.
   Fix every error (undefined CAC, inconsistent customers/spend, untagged benchmarks).
5. **Read the outputs:** CAC (blended and paid), contribution per account, lifetime, LTV, LTV:CAC,
   CAC payback months. **Lifetime definition:** expected active months *within the horizon* H under
   geometric survival, Σ_{t=1..H}(1−churn)^(t−1) = (1−(1−churn)^H)/churn (churn 0 → H and always
   `churn-zero-capped`); the untruncated 1/churn is reported as `lifetime_untruncated_months`.
   Simple and discounted LTV use the same survival curve and horizon, so they agree at a 0% rate.
6. **Stress it:** add `downside`/`upside` scenarios (churn, ARPA, CAC) and a churn sensitivity;
   report the downside LTV:CAC and payback, not just the base case. Override keys must be model
   input names; an unknown key (e.g. a typo `monthly_chrn`) is an error (`unknown-override-key`) and
   that scenario is not evaluated. A scenario whose name contains `downside` with LTV:CAC < 1 raises
   `downside-ltv-cac-below-1` (warning, escalate).
7. **Write the metrics note:** definitions, ledger, results table, scenarios, what would change the
   conclusion, open data issues; send to `financial-analyst` / `independent-reviewer`.

## Decision criteria
| Situation | Rule |
|---|---|
| Contribution per account <= 0 | Stop growth spend analysis; fix price or cost first (payback never). |
| CAC undefined (zero customers) | Report undefined; do not substitute a benchmark silently. |
| Churn = 0 or lifetime capped | Treat LTV as horizon-bound; show the cap explicitly in any claim. |
| LTV:CAC >= 3 and payback <= 12-18 months in the downside | Often cited heuristics (industry folklore, not a standard); supports scaling the channel *(recommendation only)*. |
| Paid CAC much higher than blended | Organic customers subsidise the ratio; decide channel spend on paid CAC. |
| Key input tagged `benchmark` | Flag (`benchmark-input` warning); replace with measured data before relying on the result. |
| Downside LTV:CAC < 1 | Growth destroys value under plausible assumptions; escalate (`downside-ltv-cac-below-1` warning). |
| Scenario/sensitivity key is not a model input | Error `unknown-override-key`; fix the name. |

## Outputs
- Metrics report (`unit_economics.py --json`; schema `assets/schemas/unit-economics-output.schema.json`)
  including the assumption ledger, base, scenarios, sensitivity and cohort retention.
- `unit-economics-note.md`: definitions, ledger, results, scenarios, open questions.

## Validation
- `python3 scripts/unit_economics.py assets/examples/unit-economics-pass.json --json` -> exit 0.
- Exit 1 = blocking findings (missing inputs, undefined CAC, inconsistent inputs, bad tags,
  benchmark/measured without source, unknown override keys); exit 2 = unreadable or non-numeric input. `--strict` also
  blocks on warnings.
- PASS means the ledger is complete and the arithmetic is defined. It does **not** validate the
  data, the attribution model or the forecast.

## Examples
- `assets/examples/unit-economics-pass.json` (synthetic SMB scheduling/CRM SaaS): CAC 1,000,
  contribution 70/month, lifetime 35.12 months within the 60-month horizon (untruncated 1/churn = 50),
  LTV 2,458.56 (discounted at 12%: 1,972.99), LTV:CAC 2.46, payback 14.29 months; downside LTV:CAC
  1.56; exit 0.
- `assets/examples/unit-economics-fail.json`: exit 1 with `cac-undefined`, `inconsistent-customers`,
  `inconsistent-spend`, `benchmark-without-source`, `assumption-bad-tag`; warnings
  `churn-zero-capped`, `non-positive-contribution`, `assumption-untagged`, `benchmark-input`.
- `assets/examples/cohorts-pass.csv` (average month-3 retention 90%) and
  `assets/examples/cohorts-fail.csv` (`cohort-no-month-0`, `duplicate-cohort-month`).

## Escalation and stop conditions
- Stop when spend and customer counts come from different periods or definitions.
- Escalate to `financial-analyst` for model ownership and `independent-reviewer` before any
  external use (investors, lenders, board). Outputs are not a valuation or investment advice.

## References
- `damodaran` - general corporate-finance framing (value creation, discounting). Primary source
  INACCESSIBLE in this environment *(unverified; see `sources/audits/damodaran.md`)*.
- SaaS metric definitions: common industry practice; no authoritative source is claimed.
- Formulas, pitfalls and cohort notes: [references/unit-economics-method.md](references/unit-economics-method.md).
