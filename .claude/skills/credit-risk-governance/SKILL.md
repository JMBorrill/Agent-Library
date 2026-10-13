---
name: credit-risk-governance
description: Review a lender's or fintech's credit risk management framework and controls register against the four Basel credit-risk areas (credit risk environment, credit-granting process, administration/measurement/monitoring, controls) and produce a gap report - coverage, owners, testing age, evidence, independence of approval and review from origination, and validation of models/scorecards. Use when assessing a lending business's credit governance, preparing for an audit, investor or regulator conversation, onboarding a lending partner, or reviewing a credit controls register. Never outputs an approval.
metadata:
  pack: finance-credit
  version: "1.0.0"
  sources: "basel-credit"
---

# Credit risk governance review

## Purpose
Give a lender, fintech or lending partner an evidence-based gap report on its credit risk management
framework: is every area covered by an owned, tested, evidenced control; are approvals, credit review
and model validation independent of the people who originate loans; and are models validated. The
area structure follows the Basel Committee *Principles for the management of credit risk* as
reported by secondary sources (`basel-credit`; primary text not read - see References).

## When to use
- Reviewing a credit risk framework or controls register for a bank, building society, specialist
  or second-charge mortgage lender, BNPL or SME lending fintech.
- Due diligence on a lending partner whose criteria feed a decision-support platform.
- Preparing for internal audit, investor diligence or a supervisory conversation.

**Do not use when:** you need to evaluate an individual credit application (use
`credit-criteria-modelling`); you need a regulatory perimeter view (use `finance-fca-scope-check`);
or you need capital (Pillar 1/2) calculations - out of scope.

## Inputs
Required
- Controls register CSV (`assets/templates/controls-register.csv`): `control_id, area, description,
  owner, frequency, evidence_ref, last_tested, status, independent_of_origination`; optional `topic,
  control_type, model_risk, last_validated`.
- Review as-of date (`--as-of`), testing limit (`--max-test-age-days`, default 365).
Optional
- Credit policy, risk appetite statement, committee terms of reference, MI packs, audit reports.
- Custom topic coverage (`assets/templates/coverage-topics.json`, passed with `--coverage`).

## Procedure
1. **Confirm independence of the reviewer** from origination and from the register's author.
2. **Collect documents** and map each to an area; note anything requested but not provided.
3. **Normalise the register**: one row per control; `status` in `designed | operating |
   tested_effective | tested_deficient | not_implemented | retired`; `control_type` for approvals,
   credit review, limit monitoring, model validation; `model_risk=yes` for scorecards/models.
4. **Run the gap check:**
   `python3 scripts/governance_check.py register.csv --as-of 2026-10-01 --json > gap.json`.
5. **Triage findings**: errors are gaps needing an owner and date; warnings need judgement
   (deficient controls, missing topics, overdue model validation).
6. **Test beyond the register** (sampling): pick approvals and check the approver was independent,
   limits were applied, exceptions were logged, monitoring triggers fired; record evidence references.
7. **Judge what a script cannot**: appetite calibration, policy quality, concentration management,
   data quality, culture, fair treatment of customers in arrears (link to conduct review).
8. **Write the gap report** (`assets/templates/governance-review.md`) and send to
   `credit-regulatory-reviewer` / `independent-reviewer`. Management owns remediation.

## Decision criteria
| Finding | Treatment |
|---|---|
| `area-not-covered` | High priority gap; framework incomplete for that area. |
| `independence-lacking` on approval, credit review or model validation | High priority; segregation of duties failure. |
| `model-not-validated` | High priority before the model is relied on for decisions. |
| `missing-owner`, `never-tested`, `test-overdue`, `tested-without-evidence` | Gap; assign owner and date. |
| `control-deficient`, `topic-not-covered`, `model-validation-overdue` | Judgement; record rationale or action. |
| Register cannot be produced | Stop; report "unable to assess" rather than inferring controls. |

## Outputs
- Gap report JSON (`governance_check.py --json`; schema `assets/schemas/gap-report.schema.json`).
- `governance-review.md` from `assets/templates/governance-review.md` with sampled evidence.

## Validation
- `python3 scripts/governance_check.py assets/examples/controls-register-pass.csv --as-of 2026-10-01`
  -> exit 0 (no blocking gaps). Exit 1 = gaps; exit 2 = unreadable/malformed CSV or bad `--as-of`.
- "No blocking gaps" means the register is structurally complete. It does **not** mean the
  controls are well designed, operating effectively, adequate for the risk, or acceptable to a
  supervisor. No output of this skill is an approval.

## Examples
- `assets/examples/controls-register-pass.csv` (Northbridge Mutual (synthetic), second-charge
  lender, 18 controls): exit 0, all four areas covered.
- `assets/examples/controls-register-fail.csv` (Harbourline Finance (synthetic)): exit 1 with
  `independence-lacking`, `missing-owner`, `test-overdue`, `model-not-validated`, `never-tested`,
  `tested-without-evidence`, `duplicate-control-id`, `independence-unknown`, `area-not-covered`.

## Escalation and stop conditions
- Escalate immediately (to the CRO/board risk committee owner and `credit-regulatory-reviewer`)
  where approvals are not independent of origination or decision models are unvalidated.
- Stop and ask when the register is missing, or when evidence references cannot be opened.
- Regulatory interpretation (PRA/FCA/ECB implementation) needs qualified compliance or legal review.

## References
- `basel-credit` - BCBS *Principles for the management of credit risk* (revised 30 April 2025,
  d595, per secondary sources). Primary text INACCESSIBLE here. The four-area grouping is
  corroborated only by search snippets; the number of principles in the 2025 text and their
  wording are *(unverified)*. No principle text or numbering is reproduced. See
  `sources/audits/basel-credit.md`.
- Area and topic notes: [references/credit-governance-areas.md](references/credit-governance-areas.md).
