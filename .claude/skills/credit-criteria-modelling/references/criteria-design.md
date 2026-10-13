# Criteria engine design notes

## Rule model
| Field | Purpose |
|---|---|
| rule_id | Stable, never reused; superseding creates a new ID |
| lender, product | Scope of the rule (synthetic names in examples) |
| criterion | Fact key from the shared dictionary (e.g. `cltv_pct`, `ccj_count_last_6y`) |
| operator | lt, lte, gt, gte, eq, neq, in, not_in, between, is_true, is_false |
| value, unit | Threshold and unit; unit must match the case unit when supplied |
| effective_from / effective_to | Version window (inclusive); null `effective_to` = open |
| source_document | Lender document title, version and page/section |
| last_verified | When a person last confirmed the rule against the lender source |

## Outcome logic (three-valued)
Per rule: pass / fail / refer. Product: any fail -> ineligible_indicative; else any refer (missing
data, unit or type mismatch, stale source) or no rules in effect -> refer; else eligible_indicative.
Treating unknown as refer avoids the most dangerous failure of criteria engines: false
"eligible" results caused by missing data.

## Affordability arithmetic
- Annuity: P i / (1 - (1+i)^-n); i = annual/12; n = 12 x years; zero rate -> P/n.
  Check: 200,000, 25 years, 5% -> i = 0.0041667, (1+i)^300 = 3.48129 -> 1,169.18.
- CLTV for second charge = (first-charge balance + new loan) / value.
- Stressed rate = max(product rate + lender stress margin, optional floor). The margin is a lender
  policy input. FCA rules on interest-rate stress testing exist in MCOB *(unverified - check the
  current Handbook text and any carve-outs for second charge)*.
- DTI uses gross monthly income; payment-to-income and NDI use net monthly income.

## Known limitations
- Rules are conjunctive per product; OR-logic between criteria must be modelled as separate products
  or `in` lists.
- No income multipliers by band, no credit scoring, no property valuation logic.
- Fairness: criteria such as age or employment type can have indirect discrimination effects -
  record justification and seek legal review (Equality Act 2010 - out of FCA registry, unverified).
