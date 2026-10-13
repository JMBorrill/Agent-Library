# Credit governance areas and review prompts

The four areas below are the grouping reported by secondary sources for the BCBS credit risk
principles (2025 revision). Topic lists and prompts are this library's own generic practice
checklist - not the Basel text *(unverified mapping)*. See `sources/audits/basel-credit.md`.

## 1. Credit risk environment (`credit_risk_environment`)
Board-approved credit risk strategy and appetite; senior management implements policies and
procedures; new products and activities assessed before launch.
Prompts: when was appetite last approved and against what metrics? Who can change lending criteria?

## 2. Credit-granting process (`credit_granting`)
Well-defined granting criteria; overall and single-name/segment limits; clear approval authority;
exceptions and related-party lending handled at arm's length.
Prompts: can the person paid on volume approve the loan? Are criteria versioned with provenance
(see `credit-criteria-modelling`)?

## 3. Administration, measurement and monitoring (`administration_measurement_monitoring`)
Credit administration and documentation; monitoring of individual exposures and arrears; internal
risk rating; portfolio MI incl. concentrations; stress testing; problem-credit management.
Prompts: what early-warning indicators exist and who acts on them? How are models monitored?

## 4. Controls over credit risk (`controls`)
Independent ongoing credit review; timely escalation of limit breaches and exceptions; internal
audit coverage. Controls in this area must be independent of origination.

## Independence rule used by the script
A control with `control_type` in approval, credit-review, model-validation, limit-monitoring,
override-approval, collateral-valuation, independent-review - or any control in the `controls` area
- must have `independent_of_origination = yes`.

## What the script cannot judge
Design adequacy, whether the appetite is sensible, data lineage, conduct outcomes for customers in
financial difficulty, and whether jurisdiction-specific supervisory expectations are met.
