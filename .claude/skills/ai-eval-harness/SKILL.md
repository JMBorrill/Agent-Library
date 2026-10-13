---
name: ai-eval-harness
description: Run reproducible, provider-agnostic evaluations of an LLM/RAG/agent system against a JSONL eval set - exact/contains/regex, refusal, citation grounding, PII leakage, JSON validity - with per-tag Wilson 95% intervals and threshold gates that return pass/fail exit codes. Use when building an eval set, gating a model or prompt release, comparing a recorded good vs bad system, or producing MEASURE evidence for an AI risk register or system card.
metadata:
  pack: ai-governance
  version: "1.0.0"
  sources: "nist-ai"
---

# AI evaluation harness

## Purpose
Turn "the model seems fine" into a reproducible measurement: a versioned eval set, recorded or
live system responses, deterministic scorers, rates with confidence intervals per slice, and
explicit release gates. The report (dataset sha256, config, adapter) is the evidence that
`ai-risk-assessment` links from risk rows and system cards.

## When to use
- Defining release criteria for a prompt, model, retrieval index or vendor version change.
- Regression testing after any change (re-run with the same dataset hash).
- Comparing two recorded systems offline (fixture adapter) — e.g. good vs bad candidate.
- Producing evidence for grounding, refusal behaviour, PII leakage or structured-output validity.

**Do not use when:** the quality you need is subjective (tone, helpfulness) and needs human or
model-graded rubrics — this harness has no LLM judge by design; you need adversarial red-teaming
at scale (use it to *replay* found attacks); or you are screening untrusted content
(`ai-prompt-injection-review`).

## Inputs
Required
- Eval set JSONL: one item per line, schema `assets/schemas/evalset-item.schema.json`,
  template `assets/templates/evalset.jsonl`. Fields: `id`, `input`, optional `context`
  (`doc_id`, `text`), `expected`, `expected_contains`, `must_not_contain`, `expected_regex`,
  `expected_refusal`, `expected_citations`, `expect_json`, `allowed_pii`, `tags`.
- A system-under-test adapter:
  - `--adapter fixture --responses responses.jsonl` (default; offline, deterministic) —
    `{"id", "output"}` per line; citations written inline as `[doc:ID]` or as a `citations` list.
  - `--adapter command --command "python3 my_sut.py"` — runs a local program per item, item JSON
    on stdin, output on stdout. No shell; minimal environment (only `PATH`, `LANG` and any
    `--pass-env NAME`); `--timeout` per item. The harness itself makes no network calls but
    **cannot stop the command doing so** — run only trusted commands, prefer a sandbox, never
    pass real credentials in an eval run (use fakes like `sk-FAKE-0000`).
- Gates config JSON: schema `assets/schemas/eval-config.schema.json`, template `assets/templates/eval-config.json`.

## Procedure
1. **Define what must be true** for release, from the risk register (e.g. grounding ≥ 0.95,
   PII leakage = 0, refusal of out-of-scope requests = 1.0). Write each as a gate.
2. **Build the eval set.** Cover each risk with tagged items (`criteria`, `hallucination`,
   `refusal`, `over-refusal`, `pii`, `structured`, slices such as income type). Include
   negative items (questions with no answer in context, requests to disclose PII). Use synthetic
   or properly consented data only. Version the file; never edit a released version in place.
3. **Size it.** With n items all passing, the Wilson lower bound is roughly 1 − 3.84/n
   (n=14 → 0.785; n=100 → 0.963). Choose n so the bound can clear your gate if you gate on it.
4. **Record responses** (fixture) or wire the command adapter. Keep recorded responses with the
   report for audit.
5. **Run:**
   `python3 scripts/run_eval.py evalset.jsonl --responses responses.jsonl --config gates.json --json > report.json`
6. **Read failures, not just rates.** Each failed item lists its reasons (ungrounded citations,
   missing required citations, forbidden text, PII types, unexpected refusal).
7. **Record evidence**: put `dataset_sha256`, config, metric, interval and date into the system
   card's `evaluations` and the risk register's `eval_ids`.

## Decision criteria
| Situation | Rule |
|---|---|
| Any PII leakage on a gated set | Fail; fix redaction/prompting before re-run. One leak is enough. |
| Grounding below gate | Fail; check retrieval quality before prompt changes. |
| Small n (< 30 per gated slice) | Report interval; set `gate_on_interval: true` only if n supports it, otherwise state that the point estimate is weak evidence. |
| Gate metric has no applicable items | Gate fails ("not evaluable") — add items rather than delete the gate. |
| Exact match too brittle | Prefer `expected_contains` + `must_not_contain`; keep `expected` for constrained outputs. |
| Need judgement of quality | Add a human-graded rubric outside this harness; do not invent an automatic score. |
| Command adapter needs secrets/network | Stop: use recorded fixtures, or a sandbox approved by the system owner. |

## Outputs
- `report.json` — schema `assets/schemas/eval-report.schema.json`: metrics overall and per tag
  (k, n, rate, Wilson 95% interval), gate results, per-item checks, findings, and
  `reproducibility` (harness version, dataset sha256, config + sha256, adapter details).
- Exit code: 0 all gates pass, 1 any gate fails, 2 malformed input.

## Validation
- `python3 scripts/run_eval.py assets/examples/mortgage-criteria-evalset.jsonl --responses assets/examples/responses-good-pass.jsonl --config assets/examples/eval-config.json` → exit 0.
- Same with `responses-bad-fail.jsonl` → exit 1.
- PASS means the recorded outputs met these gates on this dataset. It does **not** establish
  accuracy in production, fairness across unseen groups, or robustness to attacks not in the set.
  The PII detectors are regex/Luhn heuristics (UK-centric phone and NI formats) with false
  positives and negatives; refusal detection is phrase-based.

## Examples
- `assets/examples/mortgage-criteria-evalset.jsonl` — 14 items over three fictional lenders
  (Northbank Homes, Fenmoor Mortgages, Larkspur Lending) and a synthetic case note.
- `assets/examples/responses-good-pass.jsonl` — all 7 gates pass, pass rate 14/14 (95% CI 0.785–1.0).
- `assets/examples/responses-bad-fail.jsonl` — hallucinated lender (Brightwater), citations to
  documents not supplied, missing citations, NI number/email/phone/card leakage, over-refusal,
  invalid JSON → every gate fails, exit 1.
- `assets/examples/eval-config.json` — the gates used above.

## Escalation and stop conditions
- Stop if the eval set contains real personal data without a documented basis, or if the command
  adapter would need production credentials.
- Escalate gate threshold choices to the system owner and `ai-governance-reviewer`; thresholds
  are risk-appetite decisions, not technical defaults.
- `ai-evaluation-engineer` authors evals; `independent-reviewer` checks that the eval set was
  not tuned to the candidate system (hold out a sealed split).

## References
- `nist-ai` — AI RMF MEASURE function (methods/metrics and evaluation against trustworthiness
  characteristics) *(category-level structure secondary-corroborated only; primary
  INACCESSIBLE — see `sources/audits/nist-ai.md`)*. Confabulation and data privacy as generative
  AI risks are corroborated names from AI 600-1 *(unverified against the primary)*.
- Scorer definitions, Wilson interval maths and adapter safety notes:
  [references/eval-method.md](references/eval-method.md).
