# Mortgage Criteria Platform (synthetic): a worked demonstration

An AI-powered lender criteria search and decision-support web app for UK mortgage brokers, run through
the library end to end on a **simulated second-charge case**. Every lender, broker, borrower, document and
number here is synthetic: lenders are fictitious (Northbridge Mutual (synthetic), Harrowgate Home Loans
(synthetic), Ospreyfield Building Society (synthetic)), and the borrower (Alex Sample, synthetic) does
not exist. No real personal data, no real lender criteria, no real credit decision.

The product is **decision support**. Its outputs are `eligible_indicative`, `ineligible_indicative` or
`refer`, with reasons and sources. The broker decides what to recommend; authorised lender credit staff
make every lending decision. Nothing in this folder is an approval, an offer, legal advice or a compliance
conclusion, and nothing has been signed by a human.

All 27 deterministic steps are reproduced by `python3 examples/run_demos.py --demo mortgage-criteria`
(see [outputs/RUN-SUMMARY.md](outputs/RUN-SUMMARY.md)). As-of date for every dated check: 2026-10-13.

## 1. Framework selection

Step 01 ran `select-frameworks` on [inputs/profile.json](inputs/profile.json) (adapted from the library's
`profile-mortgage.json`: same flags, description extended to the second-charge simulation).
Output: [outputs/01-framework-selection.md](outputs/01-framework-selection.md).

**Oversight level: high** (regulated, high risk class, AI informing decisions about individuals).

| Pack | Selected? | Why (routing output; to be confirmed by the product owner) |
|---|---|---|
| finance-credit | yes | lending, mortgage and lender keywords; UK + regulated adds `finance-fca-scope-check` |
| ai-governance | yes | AI component informing decisions about individuals; adds `ai-human-oversight` |
| reliability-security | yes | multi-tenant online service holding consumer personal data |
| product | yes | external users (broker firms) |
| ux | yes | broker-facing UI (accessibility target in the PRD; `ux-accessibility-review` not run here, no prototype HTML exists yet) |
| software | yes | software is being built (code review and traceability apply once code exists; not run here) |
| systems-engineering | yes, core skills only | see below |
| orchestration | yes | `independent-review` applies to every project |
| **space-engineering** | **rejected** | no space or low-gravity context; nothing in the platform has a physical or orbital element |

**Why systems-engineering core skills were still selected for a web app.** The router selects the pack
on `risk:high`, not on hardware. A wrong indicative result can push a consumer towards an unsuitable
secured loan, so the platform needs what the SE core gives: traceable `shall` requirements with owners
(`se-requirements`), a V&V matrix that separates verification from validation (`se-verification-validation`)
and an evidence-based gate (`se-review-gates`). The hardware-oriented parts of the pack (interfaces as
ICDs, technical budgets, physical test planning) were not used; `se-risk-analysis`, `se-change-control`
and `se-configuration-management` are selected for later phases (baselining after owner approval) and
are not exercised in this demo.

## 2. Agents per phase

| Phase | Authors | Reviewers (independent of the authors) |
|---|---|---|
| Frame: selection, discovery, regulatory triage | `product-lead` | `credit-regulatory-reviewer` (triage), `independent-reviewer` |
| Define: PRD, flow-down, requirements | `product-lead` (PRD), `requirements-engineer` (register) | `independent-reviewer` |
| Criteria and affordability, credit governance | `financial-analyst` | `credit-regulatory-reviewer` |
| Design: threat model, ASVS map | `requirements-engineer` drafted security requirements; threat model drafted for review | `security-reviewer` |
| AI: risk register, system card, evals, injection, oversight | `ai-evaluation-engineer` | `ai-governance-reviewer` |
| V&V plan and pilot gate | `requirements-engineer`, `ai-evaluation-engineer` | `independent-reviewer` |
| Final challenge | none (review only) | `independent-reviewer` (claim screen step 26; full review left in [review/](review/README.md)) |

One independent review is on file: the `credit-regulatory-reviewer` report in
[review/independent-review.md](review/independent-review.md), answered in
[review/lead-response.md](review/lead-response.md) (see "Independent review" below). The other assigned
reviews (`security-reviewer`, `ai-governance-reviewer`, `independent-reviewer`) are pending, and no
reviewer acceptance is recorded anywhere in this demo. The gate authority is the product owner, and only after the
compliance officer has reviewed the triage.

## 3. Skill execution (27 steps, 16 skills, 6 packs)

| Step | Skill / script | Expected | Actual | What it shows |
|---|---|---|---|---|
| 01 | select-frameworks / select_frameworks.py | 0 | 0 | packs, agents, oversight high |
| 02 | finance-fca-scope-check / reg_triage.py | 1 | 1 | `refer`: perimeter answers left unknown (review F-01); 14 partial candidate areas |
| 02b | finance-fca-scope-check / reg_triage.py (perimeter-worst-case copy) | 0 | 0 | hypothetical: arranging and promotions both true; 17 candidate areas |
| 03 | product-discovery / evidence_audit.py | 0 | 0 | 6 counted observations, 3 hypotheses not counted; PROCEED_WITH_CONDITIONS to alpha |
| 04 | product-requirements-brief / prd_check.py (draft) | 1 | 1 | 4 `job-story-format` errors |
| 05 | product-requirements-brief / prd_check.py --flow-down | 0 | 0 | 14 candidate rows in `outputs/candidate-reqs.csv` |
| 06 | se-requirements / req_lint.py (candidates) | 0 | 0 | candidates well-formed |
| 07 | se-requirements / req_lint.py (edited draft) | 1 | 1 | 3 errors, 5 warnings |
| 08 | se-requirements / req_lint.py (fixed) | 0 | 0 | 20 rows, 0 errors, 0 warnings, all `proposed` |
| 09 | credit-criteria-modelling / criteria_engine.py (draft) | 1 | 1 | overlapping versions + stale rule |
| 10 | credit-criteria-modelling / criteria_engine.py (fixed) | 0 | 0 | 14 rules, 0 findings |
| 11 | credit-criteria-modelling / criteria_engine.py --case | 0 | 0 | 1 eligible_indicative, 1 refer, 1 ineligible_indicative |
| 12 | credit-criteria-modelling / affordability_calc.py | 0 | 0 | CLTV 72.86%, stressed payment with lender-policy label |
| 13 | credit-risk-governance / governance_check.py | 1 | 1 | real open gap `model-not-validated` (MCP-CTL-031) |
| 14 | security-threat-model / threat_model_check.py | 0 | 0 | 19 threats, 4 tenant-isolation; 9 high risks with planned-only mitigations (warnings) |
| 15 | security-asvs-controls / asvs_coverage.py | 0 | 0 | L2 subset V8 + V14: 16 rows mapped, 0 verified |
| 16 | ai-eval-harness / run_eval.py (prior v0.3 responses) | 1 | 1 | 8 of 8 gates fail, pass rate 8/16 |
| 17 | ai-eval-harness / run_eval.py (current responses) | 1 | 1 | draft PT-01 decision-wording terms on every item: 2 of 8 gates fail (`not_contains`, `pass_rate` 14/16) |
| 18 | ai-prompt-injection-review / injection_scan.py (malicious) | 1 | 1 | `flag`, score 17, 6 signals |
| 19 | ai-prompt-injection-review / injection_scan.py (benign) | 0 | 0 | `clean` (not proof of safety) |
| 20 | ai-prompt-injection-review / tool_policy_check.py --expect | 0 | 0 | 11 calls: 5 allow, 1 require_approval, 5 deny; 11/11 match |
| 21 | ai-human-oversight / oversight_check.py | 0 | 0 | 7 decisions; AI never above `recommend` for decisions about borrowers; proposed rollback triggers on every row (design completeness only) |
| 22 | ai-risk-assessment / ai_risk_register_check.py | 0 | 0 | 7 risks, residuals all medium (judgement) |
| 23 | ai-risk-assessment / system_card_check.py | 0 | 0 | card recommends NO_GO; sign-off pending |
| 24 | se-verification-validation / vmatrix_check.py | 0 | 0 | 13 requirements planned, 2 pass (offline evals), 7 needs with validation |
| 25 | se-review-gates / review_readiness.py | 1 | 1 | pilot readiness **NO_GO**; 37 open actions (30 major) |
| 26 | independent-review / claim_check.py | 0 | 0 | no overclaiming language in README and inputs |

An expected exit of 1 means the checker found the defect or gap it should find. Steps 02 and 17 changed
from an expected 0 to an expected 1 after the independent review: step 02 now refers because the perimeter
is genuinely unanswered, and step 17 now fails because two recorded answers contain draft PT-01 terms.

### Draft to fix pairs

1. **PRD (04 to 05).** The first draft ([inputs/prd-draft.md](inputs/prd-draft.md),
   [inputs/stories-draft.csv](inputs/stories-draft.csv)) wrote two stories as "I want an answer..." and
   "I want CLTV ... shown", which hide the motivation; this was a genuine authoring slip found when the
   linter was first run. Rewritten as "I want to get..." and "I want to see...", the brief passes and
   flows down.
2. **Requirements register (07 to 08).** The requirements engineer's first edit of the flowed-down
   candidates ([inputs/requirements-draft.csv](inputs/requirements-draft.csv)) set MCP-SYS-005 to
   status `approved` while its threshold was still TBR, used a non-method "pen test", pointed MCP-SYS-012 at a
   need that does not exist (MCP-STK-003), wrote "quickly", and merged two obligations into MCP-SYS-009.
   The corrected register ([inputs/requirements.csv](inputs/requirements.csv)) keeps every row `proposed`
   until a named owner approves it.
3. **Lender criteria (09 to 10).** The draft ([inputs/criteria-draft.json](inputs/criteria-draft.json))
   added Northbridge's v8 CLTV rule (80%) without closing v7 (75%), so two versions were in effect, and
   carried a Harrowgate rule last verified 194 days before the as-of date. The fix closes v7 on
   2026-08-31 and records a (synthetic) re-confirmation by the lender criteria contact on 2026-10-05.
4. **AI evaluation (16 to 17).** Prior recorded responses (system v0.3) cited a document that was never
   retrieved, invented a lender ("Brightmoor"), leaked an NI number and an email, stated that a lender
   would lend, over-refused a legitimate question and returned invalid JSON. The current recorded
   responses fixed those defects, but after the review added draft PT-01 decision-wording terms to every
   item (F-03) they fail 2 of 8 gates: mcp-q09 says "I can't confirm that a lender will lend" [evidence: inputs/responses-current.jsonl mcp-q09] (a refusal
   that still contains "will lend") and mcp-q10 says "self-employed accepted", quoting the lender's own
   guide. The substring scorer cannot tell negated or quoted wording from a decision statement; whether
   such wording is allowed is for the compliance officer, who owns PT-01 (action MCP-RID-013). The recorded
   responses were not edited. Both runs are **offline fixture evaluations of recorded responses**; no
   live model was called.

## 4. UK regulated-risk triage summary

Source: [outputs/02-fca-triage.json](outputs/02-fca-triage.json) from
[inputs/fca-questionnaire.json](inputs/fca-questionnaire.json) (service model
`information_criteria_search`, no advising or lending claimed, AI in decisions, vulnerable customers
expected). After review finding F-01, `arranges` and `communicates_promotions` are `null`: legal counsel
answers the first and the compliance officer the second. The triage therefore returns `refer`, and the 14
areas below are a partial list. A hypothetical perimeter-worst-case copy
([inputs/fca-questionnaire-perimeter-worst-case.json](inputs/fca-questionnaire-perimeter-worst-case.json),
step 02b, both answers `true`) adds TRI-AUTH-001 (permissions / appointed representative), TRI-SYSC-001
(systems and controls) and TRI-MCOB-005 (financial promotions), 17 areas in all; that run is on file and is
not an answer to the perimeter question. The FCA Handbook was INACCESSIBLE in this environment (`sources/audits/fca.md`).
**Every Handbook and statute reference below is (unverified)**, must be checked against the point-in-time
Handbook, and **requires compliance sign-off** (compliance officer, or legal counsel / DPO where named)
before anyone relies on it. This is triage, not legal advice.

| Candidate | Area (unverified) | Confidence | Sign-off role |
|---|---|---|---|
| TRI-PERG-001 | PERG perimeter guidance (unverified) | high | Legal counsel |
| TRI-PERG-002 | PERG: criteria-search versus arranging/advising boundary (unverified) | high | Legal counsel |
| TRI-MCOB-001 | MCOB applies to regulated mortgage activity (unverified; second charge since 2016 per secondary source) | high | Compliance officer |
| TRI-MCOB-002 | MCOB 11.6 responsible lending and affordability (unverified; secondary snippets only) | high | Compliance officer |
| TRI-MCOB-003 | MCOB advice and selling standards (unverified) | medium | Compliance officer |
| TRI-MCOB-004 | MCOB second-charge specifics and transitional provisions (unverified) | medium | Compliance officer |
| TRI-PRIN-001 | PRIN 2A Consumer Duty (unverified; in-force dates from secondary source) | high | Compliance officer |
| TRI-PRIN-002 | PRIN 2A and FCA vulnerability guidance (unverified) | medium | Compliance officer |
| TRI-SYSC-002 | SYSC and PRIN 2A applied to AI in decisions (unverified) | medium | Compliance officer |
| TRI-DISP-001 | DISP complaints and Financial Ombudsman Service (unverified) | medium | Compliance officer |
| TRI-BUS-001 | PERG business customers (unverified) | low | Legal counsel |
| TRI-GDPR-001 | UK GDPR / DPA 2018, outside the FCA registry (unverified) | high | Legal counsel and DPO |
| TRI-GDPR-002 | UK GDPR automated decision-making, outside the registry (unverified) | medium | Legal counsel and DPO |
| TRI-EQA-001 | Equality Act 2010, outside the registry (unverified) | medium | Legal counsel |

The highest-priority open question is the perimeter (TRI-PERG-002): whether showing indicative lender
matches to brokers stays an information service or becomes arranging or advising depends on
presentation and introductions, and needs a reasoned legal view before build decisions that depend on it.

## 5. Specification (inputs/)

| Artifact | Content |
|---|---|
| [prd.md](inputs/prd.md), [stories.csv](inputs/stories.csv) | Outcomes with guardrails (wrong-lender submissions at most 2%, zero decision wording), 5 job stories with Given/When/Then, non-goals, accessibility (WCAG 2.2 AA target), privacy and security, release slices |
| [requirements.csv](inputs/requirements.csv) | 7 stakeholder needs (MCP-STK, MCP-STY) and 13 system requirements MCP-SYS-001 to MCP-SYS-013, all `proposed`, each with verification method and measurable acceptance |
| [criteria.json](inputs/criteria.json), [case-second-charge.json](inputs/case-second-charge.json), [affordability-case.json](inputs/affordability-case.json) | 14 versioned synthetic rules for 3 fictitious lenders with source and verification dates; synthetic case MCP-CASE-0007 |
| [controls-register.csv](inputs/controls-register.csv), [governance-topics.json](inputs/governance-topics.json) | 12 platform-operator controls (all `designed`), topics tailored for an operator that grants no credit |
| [threat-model.json](inputs/threat-model.json), [asvs-control-map.csv](inputs/asvs-control-map.csv) | STRIDE data-flow model (tenant = broker firm); ASVS L2 subset V8 Authorization and V14 Data Protection (index audit: sources/audits/owasp-asvs.md) |
| [oversight-matrix.csv](inputs/oversight-matrix.csv) | Who decides what: lending decision is `inform` only with lender credit staff deciding; broker recommendation; explanation and challenge routes; proposed rollback/pause triggers on every row; approver role named, or "none" with a justification, on every row |
| [ai-risk-register.csv](inputs/ai-risk-register.csv), [system-card.json](inputs/system-card.json) | 7 AI risks with NIST AI RMF function references; card recommends NO_GO with conditions, sign-off `pending` |
| [tool-policy.json](inputs/tool-policy.json), [tool-calls.json](inputs/tool-calls.json), [uploaded-statement-malicious.html](inputs/uploaded-statement-malicious.html) | Proposed tool policy, 11 proposed calls, and a synthetic attacker document (hidden comment, white text, image exfiltration) |

**Synthetic case result (step 11), indicative only.** MCP-CASE-0007: employed, GBP 45,000 second charge,
property GBP 350,000, first charge GBP 210,000, so CLTV = (210,000 + 45,000) / 350,000 = 72.86%.
Northbridge Mutual (synthetic): `eligible_indicative` (all 6 rules in effect met; v8 cap 80%). The
result note states that this excludes affordability assessment, credit search, valuation and underwriting.
Harrowgate Home Loans (synthetic): `refer` (the case does not state secured arrears in the last 12
months; missing data is never assumed to pass). Ospreyfield Building Society (synthetic):
`ineligible_indicative` (CLTV above its 65% cap). Lender underwriting decides in every case.

**Affordability arithmetic (step 12).** Product payment GBP 435.26/month at 8.2% over 15 years;
stressed payment GBP 489.09 at 10.2%, where the 2.0-point margin is labelled as Northbridge Mutual
(synthetic) lending policy v8, a lender-policy input and not a regulatory rate; DTI 41.29% (stressed
basis: uses the GBP 489.09 stressed payment; 40.04% at the product rate); payment-to-net-income 14.82%
(stressed basis; 13.19% at the product rate); net disposable income GBP 260.91/month (stressed basis). These are arithmetic, not an affordability assessment; the thin
disposable income is exactly the kind of figure a broker and the lender must judge.

## 6. Verification procedures

[inputs/vmatrix.csv](inputs/vmatrix.csv) plans one verification activity per system requirement
(MCP-VER-001 to 013) and one validation activity per need (MCP-VAL-001 to 007), including the
**human-review workflow**: override logging (MCP-VER-009), broker challenge to the lender criteria
contact (MCP-VER-013), override and challenge walkthrough (MCP-VAL-005) and decision-boundary validation
with brokers and lender credit staff (MCP-VAL-006).

Only two results are `pass`, and both say what they are: MCP-VER-005 (grounding) and MCP-VER-006
(decision-prediction refusal) record the step 17 **offline fixture evaluation of recorded responses**
executed in this demo, with configuration and dataset hash, and no reviewer yet (the checker warns).
Every other activity is `not_tested`: no pilot build exists, so nothing else has been tested.

Eval design ([inputs/evalset.jsonl](inputs/evalset.jsonl), [inputs/eval-config.json](inputs/eval-config.json)):
16 items covering criteria lookup, hallucination bait, a superseded-version trap, decision-prediction
refusals, an over-refusal control, PII in a case note, structured output and income-type and
adverse-credit slices. Since the review, [eval-config.json](inputs/eval-config.json) also applies six
draft PT-01 decision-wording terms (`global_must_not_contain`) to every item; the list is proposed and the
compliance officer owns it. With n = 16 the 95% Wilson lower bound for 16/16 is 0.81, so the gates are set on
point estimates (`gate_on_interval: false`) and the result is weak evidence.

## 7. Readiness recommendation

Step 25 ([outputs/25-pilot-gate.txt](outputs/25-pilot-gate.txt)) applies programme pilot criteria
written for this demo ([inputs/pilot-gate-criteria.json](inputs/pilot-gate-criteria.json)) and returns
**NO_GO** for a limited broker pilot. Blocking: triage refers and no compliance or legal review of any
candidate (PIL-01, action MCP-RID-001), no independent validation of the AI component (PIL-06, governance
gap from step 13), tenant-isolation mitigations planned but not implemented (PIL-08), DPIA not started
(PIL-09), the step 17 eval now failing on PT-01 terms, and 30 open major actions (including the 23
obligations to verify, O-01 to O-23, raised by the review). Conditions: eval re-run against a pinned live
model (PIL-05), the oversight matrix not yet validated (PIL-07 `partial`: MCP-VAL-005/006 not tested), real
lender confirmation of criteria (PIL-10) and 7 open minor actions. The independent review record is cited
as `independent_review_ref`.
The recommendation is advisory; only the product owner can record a gate decision, and only after the
compliance officer has reviewed the triage. A realistic next target is GO_WITH_CONDITIONS for a pilot on
synthetic cases once PIL-01, PIL-06, PIL-08 and PIL-09 close.

## Limitations and unknowns

- All evidence is synthetic. The discovery "observations" are labelled synthetic session records; they
  show how the log is audited, not what real brokers do.
- Eval results come from recorded responses only (offline fixture adapter). They say nothing about a
  live model, production traffic or attacks outside the 16 items; fairness slices have 3 and 2 items.
- PT-01 terms are matched as substrings, so negated or quoted wording counts as a hit (2 of the current
  recorded answers); the draft list itself is unapproved.
- PII and refusal detection in the harness are heuristics; the injection scanner has known false
  negatives (paraphrase, other languages). The tool policy, not the scanner, carries the control, and
  provenance labels in the tool-call file are trusted as given.
- Lender rules, stress margins, the 90-day re-verification limit and every threshold are proposed values,
  not sourced from any real lender or regulator.
- The perimeter question (information service versus arranging or advising) is open and could change the
  product design, the permissions needed and most of the triage.
- The governance register contains only `designed` controls; the checker does not flag untested designed
  controls, so structural coverage there says nothing about operation.
- ASVS IDs and AI RMF categories were chosen from bundled indexes by title; requirement text must be
  read before relying on them. NIST AI RMF and Basel primary texts were INACCESSIBLE (see sources/audits/).

## Evidence actually checked

- Every output in [outputs/](outputs/RUN-SUMMARY.md) was produced by the library scripts in this run and
  read by the authoring agent; exit codes match `demo.json`.
- The DTI and payment-to-net-income bases were recomputed for the labels in section 5 (stressed and
  product-rate figures match the independent review's recomputation).
- CLTV and the product-rate payment were cross-checked by hand (72.857% rounds to 72.86%; annuity on
  GBP 45,000 at 8.2% over 180 months is about GBP 435.25/month, matching 435.26 within rounding).
- The eval dataset hash in [inputs/system-card.json](inputs/system-card.json) matches the
  `dataset_sha256` in outputs/17-eval-current.json.
- Not checked: any real lender document, any FCA Handbook text, any live model, any pilot build, any
  human decision.

## Human sign-offs required (none recorded)

| Who | What they must decide |
|---|---|
| Compliance officer | Each triage candidate (14 partial, up to 17 in the worst case) against the current Handbook; the `communicates_promotions` answer; prohibited-terms list PT-01; pilot readiness input |
| Legal counsel | Perimeter (TRI-PERG-001/002) and the `arranges` answer, business-customer scope, UK GDPR automated decision-making, Equality Act review of criteria |
| Lender credit staff (per lender) | The encoded criteria for their products; every lending decision on any real case |
| Data Protection Officer | DPIA, lawful basis, retention period, provider data processing agreement (role name used throughout; whether a DPO must be formally designated is itself for legal counsel to confirm) |
| Product owner | The PRD, requirement approvals (status `proposed` to `approved`), and the gate decision after compliance review |
| Head of Model Validation | Independent validation of the AI component (MCP-CTL-031) |

No sign-off has been given. The system card's `sign_off.status` is `pending`.

## Reproduction

```
python3 examples/run_demos.py --demo mortgage-criteria          # regenerate outputs/
python3 examples/run_demos.py --demo mortgage-criteria --check  # re-run, fail on exit or output drift
python3 .claude/skills/independent-review/scripts/claim_check.py examples/mortgage-criteria/README.md examples/mortgage-criteria/inputs examples/mortgage-criteria/review/lead-response.md examples/mortgage-criteria/review/README.md examples/mortgage-criteria/outputs/RUN-SUMMARY.md
```

Run over the whole `review/` folder, the claim screen exits 1 on one line of the reviewer's own file
(`independent-review.md:27`, the quoted F-03 probe sentence). The author does not edit that file; see
[review/lead-response.md](review/lead-response.md).

Run from the library root with Python 3 (standard library only). Outputs are written only by
`run_demos.py`; step 05 also writes `outputs/candidate-reqs.csv`.

## Independent review

A separate `credit-regulatory-reviewer` agent reviewed this demo on 2026-10-13
([review/independent-review.md](review/independent-review.md), filed verbatim). Its advisory
recommendation: **GO_WITH_CONDITIONS for designing a closed pilot on synthetic cases and fictitious lenders
only**, and pilot launch **NO_GO** (it judged the step 25 NO_GO justified). Its main findings were the
pre-answered perimeter question (F-01), an eval that could not detect decision wording (F-03) and PIL-07
recorded as met from a completeness-only check (F-04).

The lead response ([review/lead-response.md](review/lead-response.md)) closes within the demo F-01 (answers
set to unknown plus the worst-case run), F-03's eval change (with the two resulting failures recorded, not
hidden), F-04's matrix changes (PIL-07 now `partial`), F-11, F-12 and F-13; everything else (F-02, F-05 to
F-10, F-15, O-01 to O-23, plus the PT-01 failures and the oversight-matrix approval) is an open action in
[inputs/pilot-review.json](inputs/pilot-review.json) with an owner, due date and required closure
evidence. No human decision on any finding, the pilot design or the gate is recorded.

## Library observations (reported, not fixed)

- `ai-risk-assessment/scripts/system_card_check.py`: the non-human owner pattern matches the words
  "model" and "AI" anywhere, so human role titles such as Head of Model Risk or AI Governance Lead
  raise `owner-non-human` errors. This demo used a different role title instead.
- `ai-eval-harness/scripts/run_eval.py`: the `exact` scorer compares the whole output, including inline
  `[doc:ID]` citations, so an item with both `expected` and `expected_citations` can never pass. The
  item mcp-q12 was redesigned without required citations.
- `ai_risk_register_check.py` checks only the format of `eval_ids`, not that the evaluation exists.
- `claim_check.py` screens only .md/.txt/.rst files; the CSV and JSON specification files are not
  screened for overclaiming language.
