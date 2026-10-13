---
name: finance-fca-scope-check
description: Triage which UK regulatory areas a credit or mortgage product must examine - FCA perimeter (PERG), permissions, MCOB incl. responsible lending and second-charge specifics, CONC, PRIN incl. Consumer Duty, SYSC, DISP, plus out-of-registry UK GDPR/ICO and Equality Act flags - from a product questionnaire, each with reason, confidence, provenance, verify-effective-version flag and a named human sign-off role. Use when scoping a fintech, mortgage criteria-search platform, broker tool, BNPL or lending product before design, launch or a regulatory conversation. Triage only - not legal advice; non-UK or missing answers stop with escalate/refer.
metadata:
  pack: finance-credit
  version: "1.0.0"
  sources: "fca"
---

# FCA regulatory applicability triage

## Purpose
Give a product team an early, reasoned list of the FCA Handbook areas (and adjacent non-FCA law)
it must examine, so that compliance and legal review starts from the right questions - without
pretending to give legal advice or a compliance conclusion. Every candidate carries why it was
triggered, a confidence, where the rule came from, whether that was verified, a reminder to check
the point-in-time Handbook, and the role that must sign it off.

## When to use
- Scoping a new UK credit/mortgage product or feature (criteria search, affordability tool, broker
  CRM, BNPL, AI decision support) before build or launch.
- Preparing questions for compliance, legal counsel or a regulatory-permissions application.
- Re-triaging after a change in service model (e.g. information-only -> introductions/arranging).

**Do not use when:** the product is outside the UK (the script escalates); you need an actual
legal opinion, permission decision or compliance sign-off (qualified humans only); or you need the
content of a rule - read the current Handbook.

## Inputs
Required (template `assets/templates/questionnaire.json`; schema `assets/schemas/questionnaire.schema.json`)
- `jurisdiction`, `customer_types` (consumer/business), `products`, `service_model` (advice |
  execution_only | information_criteria_search | lending_direct), `activities.arranges/advises/lends`,
  `ai_in_decisions`, `vulnerable_customers`, `handles_complaints`.
Optional
- `performs_affordability_calculation`, `communicates_promotions`, `processes_personal_data`
  (assumed true if absent), `product_name`, `assessment_date`.
- Custom rules table (`--rules`), default `assets/rules/triage-rules.json`.

## Procedure
1. **Describe the product honestly**: who the customer is, what the firm does at each step (shows
   information, introduces, recommends, lends), and where AI influences outcomes.
2. **Answer every question** in the questionnaire; unknown answers stay `null` (they produce `refer`).
3. **Run triage:** `python3 scripts/reg_triage.py questionnaire.json` (add `--json` for records).
4. **Status handling:** `escalate` -> stop and send to legal counsel (non-UK or missing
   jurisdiction); `refer` -> complete missing answers with the product owner and re-run;
   `triage_complete_signoff_required` -> proceed to review.
5. **For each candidate area**, the named role reads the current point-in-time Handbook (or the
   relevant statute/ICO guidance for out-of-registry items), records the provisions that apply,
   and signs or rejects the candidate. Add areas the triage missed.
6. **Record** the triage output, reviewer decisions and Handbook version/date in the compliance
   file; re-run on any change of product, service model or rules table.
7. Hand to `credit-regulatory-reviewer` for independent challenge.

## Decision criteria
| Situation | Rule |
|---|---|
| Jurisdiction missing or not UK | `escalate`; produce no candidates. |
| Any required answer missing or unrecognised | `refer`; partial candidates shown as a starting point only. |
| Confidence `low` | Treat as an open question for legal counsel, not as "probably not applicable". |
| Out-of-registry item (UK GDPR, Equality Act) | Route to legal counsel / DPO; this library holds no verified source for it. |
| Verification `unverified` | Do not cite the sourcebook reference externally until a human confirms it. |
| Information/criteria-search service | Perimeter (arranging/advising boundary) is always high priority. |

## Outputs
- Triage JSON (`reg_triage.py --json`; schema `assets/schemas/triage-output.schema.json`): status,
  candidates (area, why, confidence, provenance, verification, `verify_effective_version: true`,
  `human_signoff_required.role`), findings.
- Reviewer log: candidate -> provisions confirmed -> decision -> signer -> Handbook date.

## Validation
- `python3 scripts/reg_triage.py assets/examples/questionnaire-pass.json --json` -> exit 0,
  status `triage_complete_signoff_required`.
- Exit 1 = `refer` or `escalate`; exit 2 = unreadable questionnaire or invalid rules table (every
  rule must carry provenance, verification, confidence and a sign-off role).
- Exit 0 means the triage ran on complete answers. It does **not** mean the product is within or
  outside the perimeter, permitted, or meets any rule. No output is a compliance conclusion.

## Examples
- `assets/examples/questionnaire-pass.json` (CriteriaLens (synthetic), AI second-charge criteria
  search, arranging, consumers): 16 candidates incl. PERG (perimeter and arranging/advising
  boundary), MCOB (incl. responsible lending, second-charge specifics, promotions), PRIN 2A, SYSC,
  DISP, plus UK GDPR (x2) and Equality Act out of registry.
- `assets/examples/questionnaire-fail-non-uk.json`: `escalate`, `non-uk-jurisdiction`, no candidates.
- `assets/examples/questionnaire-fail-missing.json` (BNPL add-on to a synthetic scheduling SaaS):
  `refer`, `missing-answer`, `unrecognised-answer`; partial candidates incl. CONC and BNPL status.

## Escalation and stop conditions
- Always: human sign-off by the named role (compliance officer, legal counsel, DPO) before any
  reliance; the triage never replaces them.
- Stop on non-UK jurisdiction, on contradictory answers, or when the product cannot be described
  clearly enough to answer the questionnaire.
- Escalate perimeter uncertainty to legal counsel before build decisions that depend on it.

## References
- `fca` - FCA Handbook (living rulebook). Primary text INACCESSIBLE in this environment. Secondary
  corroboration only: second-charge mortgages under FCA mortgage rules from 21 March 2016;
  Consumer Duty (PRIN 2A) in force 31 July 2023 (open products) / 31 July 2024 (closed); MCOB 11.6
  responsible lending partially corroborated. CONC and DISP scope not corroborated. All other
  sourcebook references are *(unverified)*. See `sources/audits/fca.md`.
- Non-FCA items (UK GDPR/DPA 2018, Equality Act 2010) are outside the source registry *(unverified)*.
- Rules table with provenance: [references/triage-rules-table.md](references/triage-rules-table.md)
  (generated from `assets/rules/triage-rules.json`).
