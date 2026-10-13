# Independent review: Mortgage Criteria Platform demonstration (synthetic)

> Filed verbatim by the lead from the final report of a separate `credit-regulatory-reviewer` agent run
> (read-only tools; it did not author the demo). Lead responses: [`lead-response.md`](lead-response.md).

| Field | Value |
|---|---|
| Reviewer | `credit-regulatory-reviewer` agent. Independent of the demo author (`product-lead`, `financial-analyst`, `requirements-engineer`, `ai-evaluation-engineer`). |
| Nature | Regulatory applicability triage and method challenge only. Not legal advice, not a compliance conclusion, not a credit decision and not a gate decision. |
| Date | 2026-10-13 |
| Scope | `examples/mortgage-criteria/` README.md, demo.json, inputs/, outputs/ (incl. RUN-SUMMARY.md). Focus: decision or approval wording; UK triage (verification status, sign-off roles, missing areas); recomputing affordability and the case result; criteria provenance and the draft-to-fix pair; human-oversight design; AI eval labelling; whether the pilot NO_GO is justified; claim screen. |
| Files modified | None. |
| Sources | `fca` **INACCESSIBLE** — every Handbook reference here is *unverified*. `basel-credit`, `nist-ai` **INACCESSIBLE** (*unverified*). UK GDPR / DPA 2018, the Data (Use and Access) Act 2025 and the Equality Act 2010 are not in the registry (*unverified*). |

## Summary
- **Decision wording.** Nothing in the outputs reads as a credit decision, approval or compliance conclusion. Every script output carries a scope line; all sign-offs pending.
- **Triage.** All 14 candidates are marked as needing a Handbook check, each with a sign-off role.
- **Recomputation.** Independent Python reproduced every affordability figure and all three case outcomes exactly.
- **Main problems:** F-01 — the questionnaire pre-answers the open perimeter question (`arranges: false`), hiding three triage areas. F-03 — the eval set cannot detect decision wording in ordinary answers (confirmed with a probe). F-04 — the pilot gate records the oversight criterion as "met" from a completeness-only check.
- **Pilot NO_GO.** Justified.

## Findings
| ID | Severity | Location | Finding | Evidence checked | Requested action (owner) |
|---|---|---|---|---|---|
| F-01 | High | `inputs/fca-questionnaire.json` (`activities.arranges: false`, `communicates_promotions: false`) | The questionnaire answers the open perimeter question (TRI-PERG-002) as settled. `arranges: true` brings in TRI-AUTH-001 (permissions / appointed representative) and TRI-SYSC-001; `communicates_promotions: true` brings in TRI-MCOB-005 (financial promotions). The skill says unknown answers stay `null`; with both `null` the triage returns `refer`. | Re-ran triage on modified copies: original 14 (exit 0); promotions true 15; both true 17; both `null` → `refer` (exit 1). | Set both to `null` or file the 17-candidate run as "perimeter not resolved". Legal counsel answers `arranges`; compliance officer answers `communicates_promotions`. (product-lead) |
| F-02 | Medium | oversight matrix, tool policy, tool calls | Perimeter-relevant design facts not given to legal counsel: AI role `recommend` for broker's lender choice; `send_email` may reach lender domains; mcp-c07 requires approval; mcp-c08 denied only by the PII egress list, not by a product rule on introductions. | Read files and output 20. | Give these facts to legal counsel with TRI-PERG-002; product owner records whether introductions/transmitting case data are out of scope as a product rule. |
| F-03 | High | `inputs/evalset.jsonl`, `eval-config.json`; PRD guardrail | Decision wording only scored on 2–3 refusal items. Appending "Good news: your client is approved and Northbridge will lend on this case." to a recorded answer still passed **all 8 gates**. The eval cannot measure the PRD guardrail or MCP-SYS-011. | Probe run, exit 0. | Add prohibited terms (PT-01) to every item or a decision-wording scorer; re-run steps 16–17; until then do not cite the eval for MCP-SYS-011. (ai-evaluation-engineer; compliance officer owns PT-01) |
| F-04 | Medium | `inputs/pilot-review.json` PIL-07; oversight matrix | PIL-07 requires the oversight matrix to be *validated* but is `met` on `oversight_check` exit 0 (a design-completeness check). MCP-VAL-005/006 `not_tested`. `rollback_trigger` empty on all 7 rows with 0 warnings (library observation). `approver_role` empty for two rows. | Re-ran `oversight_check.py`; read vmatrix. | PIL-07 → `partial`; fill rollback triggers; name approver roles or justify none. |
| F-05 | Medium | `outputs/11-case-evaluation.json`; mcp-c04 | Northbridge `eligible_indicative` with stressed NDI only GBP 260.91/month; no affordability rule, so the outcome means "listed criteria met", not affordable — risk of being read as more once copied into a case note. | Recomputation; outputs. | Result text must state exclusions (affordability, credit search, valuation, underwriting); add case to MCP-VAL-006. |
| F-06 | Medium | `outputs/02-fca-triage.json` | Missing applicability areas for a broker-facing second-charge criteria search with AI explanations — see O-15 to O-23 below. | Judgement against the rules table (19 rules, 14 fired). | Compliance officer / legal counsel add or reject each with reasons. |
| F-07 | Medium | controls register, governance topics | Coverage topics written by the register's author; no conduct controls (complaint routing, vulnerable customers, Consumer Duty outcome MI, Equality Act / fairness slice monitoring). Only gap reported: `model-not-validated`. | Re-ran `governance_check.py` (exit 1, identical). | Add conduct topics and controls with owners. (financial-analyst; reviewer: credit-regulatory-reviewer) |
| F-08 | Low | `pilot-gate-criteria.json` PIL-10 | Lender credit staff confirming encoded criteria is non-blocking — acceptable for a synthetic pilot, not for real lender criteria. | Read criteria and gate output. | Decide whether PIL-10 becomes blocking with real criteria. |
| F-09 | Low | `criteria.json`, `criteria-draft.json` | Provenance complete for all 14 rules; overlap fix genuine. Stale-rule fix weaker: re-confirmation only as free text, no record ID/contact; draft partly back-derived from the fixed file. | diff; engine on draft (exit 1) and fixed (exit 0). | Add a `verification_ref` field (record ID and role). |
| F-10 | Low | `case-second-charge.json` | `cltv_pct` typed in pre-rounded (72.86) rather than computed — two sources of truth; rounding near a cap could flip an outcome. | Recomputation. | Compute CLTV once; compare unrounded with stated rounding policy. |
| F-11 | Low | `outputs/12-affordability.json`; README §5 | `dti_pct` (41.29) and `payment_to_net_income_pct` (14.82) use the **stressed** payment; not labelled. | Recomputation (product-rate DTI 40.04 %, payment/net 13.19 %). | Label the basis next to each figure. |
| F-12 | Low | controls register MCP-CTL-010 | `evidence_ref` points to `outputs/10-criteria-fixed.json`; actual file is `.txt`. | find. | Correct the reference. |
| F-13 | Low | README vs triage | "Data Protection Officer" vs "Data-protection lead"; DPO designation not stated. | Read both. | Use one role name. |
| F-14 | Info | outputs claim screen | 2 hits in `07-req-lint-draft.txt` quote the draft's `approved` status (intended defect), not overclaims; JSON/CSV not screened. | Commands. | None. |
| F-15 | Info | TRI-GDPR-002 | Reviewer's knowledge (*unverified*): the Data (Use and Access) Act 2025 amended UK GDPR automated decision-making provisions with staged commencement. | Not verifiable here. | Legal counsel and DPO confirm law in force on the assessment date. |

## Obligations to verify (all *unverified*; check against the point-in-time Handbook or statute)
| ID | Area (unverified) | Effective date status | Sign-off role |
|---|---|---|---|
| O-01 | TRI-PERG-001 perimeter / permission | to confirm | Legal counsel |
| O-02 | TRI-PERG-002 information vs arranging/advising boundary (F-01, F-02) | to confirm | Legal counsel |
| O-03 | TRI-MCOB-001 MCOB for regulated mortgage activity | second charge from 21 March 2016 (secondary) | Compliance officer |
| O-04 | TRI-MCOB-002 responsible lending (MCOB 11.6) | to confirm; second-charge carve-outs unresolved | Compliance officer |
| O-05 | TRI-MCOB-003 advice and selling standards | to confirm | Compliance officer |
| O-06 | TRI-MCOB-004 second-charge specifics / transitional | 21 March 2016 transition (secondary) | Compliance officer |
| O-07 | TRI-PRIN-001 Consumer Duty (PRIN 2A) | 31 July 2023 open / 31 July 2024 closed (secondary) | Compliance officer |
| O-08 | TRI-PRIN-002 vulnerable customers | to confirm | Compliance officer |
| O-09 | TRI-SYSC-002 AI in decisions under existing rules | to confirm | Compliance officer |
| O-10 | TRI-DISP-001 complaints / FOS | to confirm | Compliance officer |
| O-11 | TRI-BUS-001 business customers | to confirm | Legal counsel |
| O-12 | TRI-GDPR-001 UK GDPR / DPA 2018, DPIA | to confirm | Legal counsel and DPO |
| O-13 | TRI-GDPR-002 automated decision-making (F-15) | to confirm incl. 2025 amendments | Legal counsel and DPO |
| O-14 | TRI-EQA-001 Equality Act 2010 (age-at-term-end, income-type criteria) | to confirm | Legal counsel |
| O-15 | TRI-AUTH-001 permissions / AR status (suppressed, F-01) | to confirm | Compliance officer with legal counsel |
| O-16 | TRI-SYSC-001 systems and controls, records, outsourcing (suppressed, F-01) | to confirm | Compliance officer |
| O-17 | TRI-MCOB-005 / FSMA s21 financial promotions — product names and rates shown to brokers (suppressed, F-01) | to confirm | Compliance officer with legal counsel |
| O-18 | Outsourcing / third-party reliance on regulated broker and lender clients (proposed) | to confirm | Compliance officer |
| O-19 | Remuneration, lender payments, conflicts; Consumer Duty price and value (proposed) | to confirm | Compliance officer |
| O-20 | Consumer Duty down the distribution chain if operator unauthorised; consumer understanding of relayed AI explanations (proposed) | to confirm | Compliance officer |
| O-21 | Broker suitability and records where AI-drafted notes enter the file (proposed) | to confirm | Compliance officer |
| O-22 | Licence terms for credit-reference data (proposed) | to confirm | Legal counsel and DPO |
| O-23 | Consumer buy-to-let regime and senior-manager accountability, if in scope (proposed) | to confirm | Legal counsel |

## Recomputations (reviewer's own Python)
Inputs from `inputs/affordability-case.json`; standard annuity, 180 months, monthly rate = annual / 12.

| Quantity | Reviewer | Demo output | Match |
|---|---|---|---|
| LTV (45,000 / 350,000) | 12.8571 % | 12.857142857 | yes |
| CLTV ((210,000 + 45,000) / 350,000) | 72.8571 % | 72.857142857 | yes |
| LTI / total secured LTI | 0.8654 / 4.9038 | 0.86538 / 4.90385 | yes |
| Payment at 8.2 % | 435.2552 | 435.25520829 | yes |
| Payment at 10.2 % (2.0-point lender-policy margin) | 489.0931 | 489.09309510 | yes |
| DTI = (1,080 + 489.09 + 220) / (52,000 / 12) | 41.2868 % | 41.28676 | yes (stressed basis, F-11) |
| Payment / net income (stressed) | 14.8210 % | 14.82100 | yes |
| NDI = 3,300 − 1,080 − 489.09 − 220 − 1,250 | 260.9069 | 260.90690 | yes |
| Case MCP-CASE-0007 | Northbridge `eligible_indicative`; Harrowgate `refer`; Ospreyfield `ineligible_indicative` (72.86 > 65) | same | yes |
| Rule age at as-of date | all ≤ 28 days (limit 90); draft HGF-2C-001 = 194 days | 194 | yes |

Arithmetic only — not an affordability assessment or a lending decision.

## Checks run (from `examples/mortgage-criteria/`, S = `.claude/skills`)
| Command | Exit | Result |
|---|---|---|
| `reg_triage.py inputs/fca-questionnaire.json --json` | 0 | same as output 02 |
| `reg_triage.py` with promotions true / promotions + arranges true | 0 / 0 | 15 / 17 candidates |
| `reg_triage.py` with both `null` | 1 | `refer` |
| `criteria_engine.py inputs/criteria-draft.json --as-of 2026-10-13` | 1 | overlap error, 194-day stale warning |
| `criteria_engine.py inputs/criteria.json --as-of 2026-10-13` | 0 | 14 rules, 0 findings |
| `criteria_engine.py … --case inputs/case-second-charge.json` | 0 | same as output 11 |
| `affordability_calc.py inputs/affordability-case.json --json` | 0 | same as output 12 |
| `governance_check.py … --coverage inputs/governance-topics.json` | 1 | same as output 13 |
| `oversight_check.py inputs/oversight-matrix.csv` | 0 | PASS, 0 warnings |
| `review_readiness.py inputs/pilot-review.json --criteria inputs/pilot-gate-criteria.json` | 1 | NO_GO; decision pending |
| `claim_check.py README.md inputs` | 0 | 0 errors |
| `run_eval.py … --responses <probe with injected decision wording>` | 0 | **all 8 gates pass** (F-03) |
| `sha256sum inputs/evalset.jsonl` | 0 | matches output 17 and the system card |

**AI eval labelling:** consistently labelled offline fixture evaluations of recorded responses (README, RUN-SUMMARY, system card, MCP-VER-005/006). **Human oversight:** broker recommends, authorised lender staff decide (AI `inform`), overrides logged, appeal/challenge routes present, "refer is never converted to eligible" stated; gaps in F-04.

## What I could not check
- FCA Handbook, Basel principles, NIST AI RMF primary texts (INACCESSIBLE); UK GDPR, DPA 2018, DUAA 2025, Equality Act outside the registry — all *unverified*.
- Whether the product is inside the perimeter, permissions needed, or whether any obligation applies — for legal counsel and the compliance officer.
- Any real lender document, live model, pilot build, PT-01 list, DPIA or human decision record.
- `run_demos.py --check` not run (may write); individual steps re-run instead. Security steps 14, 15, 18–20 only read.

## Pilot NO_GO
Justified: PIL-01, PIL-06, PIL-08 and PIL-09 not met, `governance_check` exit 1 recorded, three major actions open; restating PIL-07 as `partial` would reinforce it.

## Recommendation: proceed to a closed synthetic-data pilot design
**GO_WITH_CONDITIONS** (advisory) for *designing* a closed pilot with synthetic cases and fictitious lenders only:
1. F-01: re-run triage with `arranges` and `communicates_promotions` = `null`, or keep the 17-candidate run on file; send TRI-PERG-002 (with F-02 facts) to legal counsel before any dependent build decision.
2. F-03: add decision-wording checks to every eval item and re-run before citing the eval for MCP-SYS-011.
3. F-04: PIL-07 → `partial`; add rollback triggers and approver roles.
4. F-05: state what `eligible_indicative` excludes in the result text.
5. No real personal data or real lender criteria until PIL-01, PIL-06, PIL-08 and PIL-09 close.

**The compliance officer and the product owner decide.** No gate decision, approval or compliance sign-off is recorded anywhere in this demo, and this review is not one.
