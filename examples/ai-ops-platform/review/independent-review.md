# Independent review: AI Operations Platform demonstration (synthetic)

> Filed verbatim by the lead from the final report of a separate `security-reviewer` agent run (read-only
> tools; it did not author the demo). Lead responses: [`lead-response.md`](lead-response.md).

| Field | Value |
|---|---|
| Reviewer role | `security-reviewer` agent. I did not author this demo. I bring method, not professional authority. |
| Date | 2026-10-13 |
| Scope | `examples/ai-ops-platform/` README.md, `inputs/`, `outputs/` (including RUN-SUMMARY.md): multi-tenant isolation, AI tool misuse and indirect prompt injection, PII handling, ASVS citations, the readiness recommendation, labelling of economics and research claims. |
| Mode | Read-only; no demo file modified (`git status --porcelain examples/ai-ops-platform` empty after the run). |
| Sources | `owasp-asvs` VERIFIED (bundled 5.0.0 index: IDs, levels and section titles only). `nist-ai` INACCESSIBLE (*unverified*). `nist-ssdf` PARTIALLY_VERIFIED (not exercised). `google-sre` INACCESSIBLE (burn-rate values *unverified*, not reviewed). STRIDE from general knowledge *(unverified)*. |
| Decision rights | Only the product owner and security owner can accept risk or decide to proceed. No such decision is recorded. |

## Summary
The package is candid: every mitigation `planned`, every ASVS row `not_verified`, NO_GO reported, estimates and hypotheses labelled; re-running the checks reproduced the README's results. The main weakness is the injection defence: it rests on provenance labels that the tool policy takes as given, and no part of the design says who assigns them. A paraphrased injection written by the reviewer passed the scanner as CLEAN, and tool calls it could cause were never denied — owner approval was the only remaining control. Tenant-isolation modelling also omits background jobs, inbound message routing and how row-level security works in practice.

## Findings
Severities are the reviewer's *proposed* ratings; risk acceptance belongs to the security owner.

| ID | Severity | Location | Finding | Evidence checked | Requested action |
|---|---|---|---|---|---|
| SR-01 | High | `tool-policy.json`; AIOPS-TM-T06; AIOPS-SYS-013 | Injection defence depends on a correct `provenance` label that the policy check trusts as given; nothing assigns provenance. An owner clicking "draft reply" on a malicious thread would produce calls labelled `user`/`system` → `require_approval` instead of `deny`. A paraphrased SMS injection scored CLEAN. | RV-01 (`send_sms`, provenance `user`, other customers' numbers) → REQUIRE_APPROVAL; RV-02 (`system`, `internal`) → REQUIRE_APPROVAL; crafted SMS scan exit 0, CLEAN. | Orchestrator assigns provenance as taint: any call proposed in a turn whose context contains `retrieved_content` carries that label. Add "provenance mislabelled" threat; add RV-01/RV-02 cases (expected `deny`). |
| SR-02 | High | T17; `tool-policy.json`; `code-fixed/tool_executor.py` | T17 claims recipients restricted to the thread's own customer, but no policy rule or executor check enforces it; `send_sms` accepts any `to_number`; `thread_customer()` unused. | RV-01 to a number outside the thread with other customers' PII not denied; draft and fixed executors differ only in the docstring. | Enforce server-side recipient = thread customer; add policy rule and corpus case; until then do not describe T17's mitigation as designed. |
| SR-03 | High | `code-fixed/tool_executor.py`; AIOPS-STY-002 | Approval check not bound to tenant, tool, arguments, single use or expiry (replay / argument swap); STY-002 puts two side effects behind one approval. | Code read; static screen cannot see this. | Server-verified, single-use, short-lived approval tokens bound to a hash of (tenant, user, tool, canonical args); show every side effect's arguments at approval. |
| SR-04 | Medium | PRD outcomes; AIOPS-AS-003; oversight matrix | Owner approval is the last line of defence while metrics push for fast approval (< 2 min, ≥ 60 % approved with minor edits); approval fatigue not modelled. | PRD, assumptions, oversight matrix. | Add approval-fatigue threat; treat edit/inspection rates as safety signals; flag drafts whose recipient or content departs from the thread. |
| SR-05 | High | threat model (components, DF6) | Background-job tenant isolation not modelled: automatic reminder SMS (`act`) implies a worker with no component or threat; DF6 queue `crosses_boundary: false`. | Threat model, oversight matrix; structural check exit 0. | Add worker/scheduler component, flows and tenant-isolation threats; tenant ID carried and re-asserted in jobs; include reminder job in AIOPS-VER-101. |
| SR-06 | Medium | DF4/C5 | Inbound SMS/email → tenant routing not modelled (misrouting, shared sender IDs). | DF4, T15, T16. | Tenant-routing threat; per-tenant numbers/addresses, mapping under change control, quarantine unmatched. |
| SR-07 | Medium | C3 RLS; T02 | RLS cited without design detail: owner/privileged/worker bypass, pooled-connection context leaks, exports and reports out of scope; "no cache in MVP" not a requirement. | Threat model, requirements, tool calls. | Threats/requirements: forced RLS, non-owner app role, per-transaction tenant context, export/report filtering, "no shared cache" with a test. |
| SR-08 | Medium | `code-fixed/booking_repository.py` `create_booking` | `customer_id` inserted without checking it belongs to `tenant_id`. | Static checks (draft exit 1 SC003; fixed exit 0); code read. | Composite FK (tenant_id, customer_id) or explicit ownership check; add case to VER-101. |
| SR-09 | Medium | `tool-policy.json` | PII/egress rules inconsistent: legitimate owner email reply **denied**; exfiltration to an unlisted domain needs only approval when caller self-declares `internal`; forbidden domains are a denylist. | RV-03 → DENY; RV-04 (`drop@attacker.invalid`, `internal`) → REQUIRE_APPROVAL. | Route email via gateway with recipient binding; derive classification from tool and data; default-deny unlisted destinations for side-effecting tools; add RV-03/RV-04. |
| SR-10 | Medium | AIOPS-VER-102; T09; PRD retention | Personal data in prompt/activity logs not modelled; append-only log vs 24-month deletion/erasure unreconciled; provider retention TBC; no DPIA. | README §5, threat model, PRD. | Log-disclosure threat; redaction, access control, retention; erasure approach (e.g. crypto-shredding); keep eval logs synthetic. |
| SR-11 | Medium | `evalset-drafting.jsonl` | All 12 items single-tenant (T1); no cross-tenant canaries; one injection item using a pattern the scanner already catches; responses are hand-written fixtures (disclosed). | Doc-ID/tag tally; step 19 summary. | Add T2 canaries and paraphrased injections (crafted SMS); run against the real candidate model with a sealed hold-out. |
| SR-12 | Medium | DF2/DF3/DF5 | DF5 carries the gateway API key but categories left at default TID; `--categories STRIDE` gives 3 errors; missing flows C6→C3, C4→C6; LLM provider key not an asset. | `threat_model_check.py --categories STRIDE` exit 1. | STIDE on credential flows; add flows and LLM key asset; treat completions as untrusted input. |
| SR-13 | Medium | ASVS citations | All 44 cited IDs exist with correct levels, but several look mismatched against recollection of 5.0.0 text *(unverified)* — e.g. `v5.0.0-4.1.1` for webhook signatures, `v5.0.0-14.2.1` for provider DPA/retention, `v5.0.0-2.2.1` for markup stripping; MFA should check 6.3.3. | One-liner over the index: 44 found, 0 missing. | Read 5.0.0 requirement text and re-map before security-owner review. |
| SR-14 | Medium | `asvs-control-map.csv` | Map covers V8/V14/V16 (32 rows, honest `not_verified`); 12 further cited IDs in V1–V4, V6, V12, V13, V15 have no verification row (deferral acknowledged). | `asvs_coverage.py --require-complete` exit 0; set difference. | Add those chapters before slice-1 code review. |
| SR-15 | Medium | readiness checklist; `sre-production-readiness` | NO_GO **justified** (rollback, restore, on-call). But the readiness script never treats security as blocking: with those three done it returns GO_WITH_CONDITIONS with no isolation test, tool-enforcement test or DPIA. | `readiness_check.py` exit 1; what-if copy exit 0. | Security owner records isolation, tool-enforcement and DPIA evidence as launch blockers. Library observation. |
| SR-16 | Low | README §10; `static-checks-config.json` | SC003 inactive without `--config` (README reproduce block omits it); tenant-table list must stay current; screen cannot tell whether `tenant_id` comes from the session. | Static checks with/without config. | Document config in README and CI; generate tenant-table list from schema. |
| SR-17 | Low | T11 | Accepted with `mitigations: []` but relies on an unrecorded 5 s statement timeout; acceptance correctly pending sign-off. | Threat model. | Record the timeout as a planned mitigation; security owner signs or rejects. |
| SR-18 | Low | oversight matrix vs T16 | T16 says drafts only when the owner opens a thread, but inbound triage (`act`) runs the model on every inbound message unattended. | Oversight matrix. | Reconcile; rate-limit triage per tenant. |
| SR-19 | Low | `claim_check.py` scope | Screens only .md/.txt; CSV/JSON claims not screened. | `claim_check.py` exit 0, 5 files. | Note the scope limit in RUN-SUMMARY. |
| SR-20 | Info (positive) | README §3.1, §3.6; unit economics; assumptions | Inputs tagged estimate/benchmark (synthetic); outputs called arithmetic not a forecast; downside LTV:CAC 0.66 escalated; hypotheses labelled; composite quote withdrawn; phone numbers in the Ofcom drama range; only key `sk-FAKE-0000`. | Files, step 03/11 summaries, grep. | None — keep these labels when real data arrives. |

## Checks run (from the repository root; "demo" = `examples/ai-ops-platform/inputs`)
| # | Command | Exit | Result |
|---|---|---|---|
| 1 | `threat_model_check.py <demo>/threat-model.json` | 0 | 19 threats, 0 errors, 9 warnings |
| 2 | same, `--categories STRIDE` | 1 | DF2, DF3, DF5 `missing-stride-coverage` |
| 3 | same, `--strict` | 1 | warnings become blocking |
| 4 | `asvs_coverage.py <demo>/asvs-control-map.csv --level 2 --chapters V8,V14,V16` | 0 | 100 % mapped; 0 pass / 32 not_verified |
| 5 | same, `--require-complete` | 0 | same |
| 6 | one-liner: cited ASVS IDs vs index | 0 | 44 IDs, all found, levels match |
| 7 | `static_checks.py <demo>/code-draft` (no config) | 0 | SC003 inactive (info) |
| 8 | `static_checks.py <demo>/code-draft --config …` | 1 | SC003 at `booking_repository.py:13` |
| 9 | `static_checks.py <demo>/code-fixed --config …` | 0 | PASS |
| 10 | `injection_scan.py <demo>/inbound-email-injection.txt` | 1 | FLAG, score 14 |
| 11 | `injection_scan.py <crafted paraphrased SMS>` | **0** | **CLEAN, score 0 — false negative** |
| 12 | `tool_policy_check.py <demo>/tool-calls.json --policy … --expect` | 0 | 8/8 as expected |
| 13 | `tool_policy_check.py <crafted calls RV-01..04>` | 1 | REQUIRE_APPROVAL, REQUIRE_APPROVAL, DENY, REQUIRE_APPROVAL |
| 14 | `dependency_pin_check.py examples/ai-ops-platform` | 0 | `no-manifests` warning |
| 15 | `claim_check.py README.md inputs` | 0 | 0 errors |
| 16 | `claim_check.py outputs/RUN-SUMMARY.md` | 0 | 0 errors |
| 17 | `readiness_check.py <demo>/readiness-checklist.json` | 1 | NO_GO (rollback, on-call, restore) |
| 18 | `readiness_check.py <what-if copy>` | 0 | GO_WITH_CONDITIONS with no security evidence |
| 19 | `run_demos.py --demo ai-ops-platform --check` | 0 | PASS, no drift |

## What I could not check
- ASVS requirement text (index has IDs/levels/titles only) — SR-13 judgements are *unverified* recollection.
- The system itself (no code base, database/RLS, LLM provider, gateways or orchestrator exist); live or penetration tests (none authorised, no target); real-model behaviour (fixtures only); legal and data-protection matters (no DPIA); SLO/burn-rate values (`google-sre` INACCESSIBLE).
- A clean heuristic result is not security assurance.

## Recommendation on "proceed to building the MVP on synthetic data"
**GO_WITH_CONDITIONS** (reviewer's proposal; the product owner and the security owner decide). The NO_GO launch-readiness result stands and is justified.
1. Before slice 2 (tools and approve-to-book): close SR-01, SR-02, SR-03 (taint-based provenance, recipient binding, argument-bound approvals) and add RV-01 to RV-04 plus the crafted SMS to the corpora.
2. Before any real tenant or customer data: finish SR-05, SR-06, SR-07, SR-10, SR-12; re-map ASVS citations (SR-13) and extend the map (SR-14); complete DPIA and provider terms; run AIOPS-VER-101 against the built system.
3. Before the launch review: security owner records isolation, tool-enforcement and DPIA evidence as launch blockers (SR-15) and decides on T11 (SR-17).

Slice 1 (inbox and AI draft panel, manual send, no tools) can start under condition 2 alone. No approval, acceptance or sign-off is recorded anywhere in the package, and this review does not provide one.
