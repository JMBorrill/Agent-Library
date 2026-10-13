---
name: credit-criteria-modelling
description: Model lender eligibility criteria as versioned, machine-readable rules with provenance (lender, product, criterion, operator, value, unit, effective dates, source document, last verified), validate them (unknown operators, overlapping versions, stale or unsourced rules) and evaluate a synthetic case to eligible_indicative / ineligible_indicative / refer with per-rule reasons; plus affordability arithmetic (LTV, second-charge CLTV, LTI, annuity repayment at product and stressed rate, DTI, net disposable income). Use when building or reviewing a mortgage or loan criteria-search / decision-support product, onboarding lender criteria, or checking affordability calculations. Never outputs an approval.
metadata:
  pack: finance-credit
  version: "1.0.0"
  sources: "basel-credit fca"
---

# Lender criteria modelling and affordability arithmetic

## Purpose
Make lender criteria auditable data rather than prose: every rule traceable to a dated lender
document, versioned by effective period, re-verified on a schedule, and evaluated so that missing
information produces `refer`, never a silent pass. Pair the rules with transparent affordability
arithmetic so a decision-support product (e.g. an AI mortgage criteria-search platform) shows an
indicative match and the reasons, while the lender keeps the decision. Draws on sound
credit-granting practice (`basel-credit`) and UK mortgage conduct expectations (`fca`) - both
primary texts unverified here.

## When to use
- Building or reviewing a criteria-search / eligibility engine for first- or second-charge
  mortgages, secured or unsecured loans.
- Onboarding or updating a lender's criteria; auditing a criteria database for stale rules.
- Checking LTV/CLTV/LTI/stressed-payment/DTI/NDI arithmetic in a product or spreadsheet.

**Do not use when:** you need the regulatory perimeter view (use `finance-fca-scope-check` first);
you are reviewing a lender's governance framework (use `credit-risk-governance`); or a real
applicant needs a decision or advice - that is the lender's/adviser's regulated responsibility.

## Inputs
Required
- Criteria JSON (`assets/templates/criteria.json`; schema `assets/schemas/criteria.schema.json`).
- Synthetic case JSON (`assets/templates/case.json`; schema `assets/schemas/case.schema.json`) with
  `application_date`, `facts` keyed by criterion, optional `units`.
- Affordability JSON (`assets/templates/affordability.json`; schema
  `assets/schemas/affordability-input.schema.json`).
Optional
- `--as-of` date and `--max-age-days` re-verification limit (default 90).

## Procedure
1. **Define the fact dictionary**: each criterion key, unit and meaning (e.g. `cltv_pct` = (first
   charge balance + new loan) / value x 100). Same key and unit across all lenders.
2. **Encode each lender rule** with provenance: source document (title, version, page/section),
   effective_from/to, last_verified, unit. One rule per atomic criterion; supersede rather than edit
   (close the old rule with `effective_to`, add a new rule ID).
3. **Validate:** `python3 scripts/criteria_engine.py criteria.json --as-of 2026-10-01`. Fix every
   error (`unknown-operator`, `overlapping-effective-dates`, `missing-source`, `bad-value`,
   `bad-effective-period`, `duplicate-rule-id`); re-verify `stale-criterion` rules with the lender.
4. **Compute affordability inputs:** `python3 scripts/affordability_calc.py case-aff.json`. The
   stress margin is a lender-policy input - label it with the policy reference; never present it as
   a regulatory rate.
5. **Evaluate the case:** `python3 scripts/criteria_engine.py criteria.json --case case.json`.
   Read per-rule reasons; missing data and unit mismatches give `refer`.
6. **Present results** as indicative only, with reasons and sources; route `refer` to a human
   (adviser/broker or lender). Never display "approved" or imply an offer.
7. **Log** criteria version, case inputs and outputs for audit; hand to
   `credit-regulatory-reviewer` before launch and on material changes.

## Decision criteria
| Situation | Outcome / action |
|---|---|
| Any rule in effect fails | `ineligible_indicative` for that lender/product, with the failing rule(s). |
| A required fact is missing, null, wrong type or wrong unit | `refer` - never assume a pass. |
| A passing rule is stale (`last_verified` older than limit) | `refer` until re-verified. |
| No rules in effect on the application date | `refer` (criteria gap). |
| All rules in effect pass, none stale | `eligible_indicative` - still subject to lender underwriting. |
| LTV or CLTV > 100%, or zero income | Error finding; ratios reported as undefined, refer to a human. |
| Criteria validation has errors | Do not evaluate cases (engine exits 1). |

## Outputs
- Validation + evaluation JSON (`criteria_engine.py --json`; schema
  `assets/schemas/criteria-output.schema.json`).
- Affordability JSON (`affordability_calc.py --json`; schema
  `assets/schemas/affordability-output.schema.json`).
- Criteria change log (rule IDs superseded, source, verifier, date).

## Validation
- `python3 scripts/criteria_engine.py assets/examples/criteria-pass.json --case assets/examples/case-pass.json --json` -> exit 0.
- `python3 scripts/affordability_calc.py assets/examples/affordability-pass.json --json` -> exit 0.
- Exit 1 = criteria errors / affordability error findings; exit 2 = unreadable input, negative or
  non-numeric values, missing fields, invalid case date.
- PASS means rules are well-formed and arithmetic is defined. It does **not** mean the rules match
  the lender's current criteria, that the customer can afford the loan, or that the product meets
  FCA requirements.

## Examples
- `assets/examples/criteria-pass.json` + `assets/examples/case-pass.json` (synthetic second-charge,
  CLTV 72.5%): Northbridge Mutual (synthetic) `eligible_indicative`; Fernvale Home Finance
  (synthetic) `refer` (missing `self_employed_years_trading`); Kestrel Lending (synthetic)
  `ineligible_indicative` (CLTV > 65%).
- `assets/examples/criteria-fail.json` (`--as-of 2026-10-01`): exit 1 with `unknown-operator`,
  `missing-source`, `bad-value`, `bad-effective-period`, `overlapping-effective-dates`; warning
  `stale-criterion`.
- `assets/examples/affordability-pass.json`: CLTV 72.50%, product payment 463.51, stressed (9.5%)
  522.11, DTI 38.44%, NDI 527.89. Known answer: 200,000 over 25 years at 5% -> 1,169.18/month.
- `assets/examples/affordability-fail.json`: exit 1 with `cltv-exceeds-100`, `income-zero`,
  `net-income-zero`.

## Escalation and stop conditions
- Stop if a rule has no source document or the lender has not confirmed the criteria version.
- Any `refer`, or any use with real applicants, needs a qualified human (adviser, underwriter).
- Whether presenting results amounts to advice or arranging is a perimeter question: escalate via
  `finance-fca-scope-check` to compliance/legal. Fairness of criteria (proxy discrimination) goes
  to `credit-regulatory-reviewer` and legal.

## References
- `basel-credit` - sound credit-granting process (well-defined criteria, limits) *(area-level only;
  primary INACCESSIBLE, see `sources/audits/basel-credit.md`)*.
- `fca` - FCA Handbook MCOB responsible lending/affordability (MCOB 11.6 partially corroborated by
  secondary snippets); second-charge mortgages within MCOB from 21 March 2016 (secondary) - all
  *(unverified against the Handbook; see `sources/audits/fca.md`)*. No rule text is reproduced; stress
  margins here are lender-policy inputs, not regulatory figures.
- Design notes: [references/criteria-design.md](references/criteria-design.md).
