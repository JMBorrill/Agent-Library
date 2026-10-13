---
name: ai-risk-assessment
description: Assess an AI system's risks proportionately with the NIST AI RMF (GOVERN, MAP, MEASURE, MANAGE) - context and intended use, affected parties, harms, trustworthiness characteristics, a scored risk register linked to evaluations, a model/system card and a go/no-go recommendation for human sign-off. Use when scoping or reviewing an LLM app, RAG assistant, agent or model deployment, linting an AI risk register, or checking a system card before a release decision.
metadata:
  pack: ai-governance
  version: "2.0.0"
  sources: "nist-ai"
---

# AI risk assessment (NIST AI RMF, proportionate)

## Purpose
Give a named decision-maker an evidence-backed picture of what an AI system is for, who it can
harm and how, which risks remain after controls, and what evidence supports that — packaged as a
linted risk register, a validated system card and a GO / GO_WITH_CONDITIONS / NO_GO
*recommendation*. The assessment informs a human decision; it never makes one.

## When to use
- Before building or buying an LLM application, RAG assistant, agent or ML model for a real use.
- Before a release, a model/vendor version change, a new user group or a new data source.
- Reviewing someone else's AI risk register or model/system card.
- Periodic review of a deployed system (pair with monitoring evidence).

**Do not use when:** you need to run the evaluations themselves (`ai-eval-harness`); you are
screening content or agent tool calls for injection (`ai-prompt-injection-review`); you are
designing approval/override workflow (`ai-human-oversight`); or a legal conformity assessment
under a specific law is required — that needs qualified counsel, and this skill is not one.

## Inputs
Required
- System description: purpose, users, decision context, model/provider, data sources, tools.
- Risk register CSV: `assets/templates/ai-risk-register.csv`.
- System card JSON: `assets/templates/system-card.json` (schema `assets/schemas/system-card.schema.json`).
Optional
- Evaluation reports (`ai-eval-harness` JSON), oversight matrix (`ai-human-oversight`), injection
  review results, incident history, DPIA reference.

## Procedure
1. **Size the effort (proportionality).** Classify the use: *low* (internal drafting, no decisions
   about people), *elevated* (customer-facing, personal data, tool use), *high* (decisions or
   recommendations about individuals' access to credit, housing, jobs, health or services; or
   autonomous side effects). Low: steps 2–4 and a short card. Elevated/high: all steps.
2. **GOVERN — set accountability.** Name the accountable executive, system owner, risk acceptor
   and reviewer (author ≠ reviewer). Record policies that apply and third-party components
   (models, APIs, datasets) with versions.
3. **MAP — context.** Write intended use, users, decision context and explicit out-of-scope uses.
   List affected parties (direct users, subjects of decisions, bystanders, the organisation) and
   how each could be harmed. Use harm categories *people / organisation / ecosystem*.
4. **MAP — risk identification.** For each harm pathway write a risk row: cause → event →
   consequence. Tag the trustworthiness characteristic(s) at stake (keys in the template) and
   AI RMF references `AIRMF-1.0-<FUNCTION>-<cat>[.<sub>]`. Cover at least: confabulation,
   privacy leakage, prompt injection/tool misuse, unfair performance across groups,
   over-reliance, third-party change, misuse outside scope.
5. **Score inherent risk** (likelihood × impact, 1–5 each) before controls, then list controls.
6. **MEASURE — link evidence.** Every live risk needs at least one `eval_ids` entry pointing at a
   real evaluation (run with `ai-eval-harness`) or a recorded review. Residual scores without
   evidence are judgement and must be flagged as such.
7. **Score residual risk** and set status (`open | mitigating | accepted | transferred | closed`).
   Residual ≥ 15 (default) needs a named *human* `accepted_by`, or more mitigation.
8. **Lint the register:**
   `python3 scripts/ai_risk_register_check.py register.csv --as-of YYYY-MM-DD --json`
   Fix all errors; justify warnings in `notes`.
9. **MANAGE — plan response.** Monitoring metrics, alert owner, rollback triggers and procedure,
   review dates. Hand oversight design to `ai-human-oversight`.
10. **Write the system card** and validate:
    `python3 scripts/system_card_check.py card.json --as-of YYYY-MM-DD --json`
11. **Recommend** using the decision criteria below and the report template
    `assets/templates/risk-assessment-report.md`. Leave `sign_off.status` as `pending`; only the
    named human changes it.

## Decision criteria
| Situation | Recommendation / rule |
|---|---|
| Any live risk with residual ≥ high threshold and no human acceptor | NO_GO until mitigated or accepted by a named human |
| A gating eval failed (card `result: fail`) | NO_GO, or GO_WITH_CONDITIONS only with explicit conditions and owner |
| High inherent risk with no linked eval | Not assessable — run evals first |
| Evals older than 180 days, or dataset version differs from production | Re-run before recommending |
| Decisions about individuals (credit, eligibility) | Require oversight matrix passing `oversight_check.py`; AI may only inform/recommend/draft |
| Low-proportionality use, all risks low residual | GO, with monitoring and review date |
| Register/card lint fails | No recommendation is issued |

## Outputs
- `ai-risk-register.csv` + lint report (`--json`, schema `assets/schemas/findings-report.schema.json`).
- `system-card.json` + check report (same findings schema).
- `risk-assessment-report.md` from `assets/templates/risk-assessment-report.md`, ending in a
  recommendation that states "requires human sign-off".

## Validation
- `python3 scripts/ai_risk_register_check.py assets/examples/ai-risk-register-pass.csv --as-of 2026-10-13` → exit 0.
- `python3 scripts/system_card_check.py assets/examples/system-card-pass.json --as-of 2026-10-13` → exit 0.
- PASS means the register is well-formed, arithmetic is right, references match the bundled
  AI RMF function/category structure, evidence links and acceptors exist, and the card is
  complete and internally consistent. It does **not** mean the risk list is complete, the scores
  are right, the evals are valid or the system is safe to deploy.
- Subcategory references (e.g. `AIRMF-1.0-MEASURE-2.11`) are checked for pattern only and
  reported as `rmf-subcategory-unverified` — the subcategory list was not obtained.

## Examples
- `assets/examples/ai-risk-register-pass.csv` — exit 0 (one info: unverified subcategory).
- `assets/examples/ai-risk-register-fail.csv` (with `--as-of 2026-10-13`) — exit 1: `duplicate-id`,
  `rmf-ref-unknown` (MAP 7), `rmf-ref-format`, `inherent-score-mismatch`, `score-range`,
  `no-owner`, `no-eval-evidence`, `high-residual-not-accepted`, `accepted-by-non-human`,
  `review-overdue`, `risk-id-format`, `status`.
- `assets/examples/system-card-pass.json` — exit 0; `system-card-fail.json` — exit 1 with
  `eval-result-inconsistent`, `go-with-failing-eval`, `duplicate-eval-id`, `sign-off-non-human`,
  `no-human-contact`, schema errors.

## Escalation and stop conditions
- Stop if intended use or decision context is unclear, or if no human will own risk acceptance.
- Escalate to qualified legal/compliance, data protection and domain experts for regulated
  decisions (credit, employment, health), special-category data, or children's data.
- Hand evaluation design to `ai-evaluation-engineer`; challenge review to
  `ai-governance-reviewer` and `independent-reviewer`. The author never signs off.

## References
- `nist-ai` — NIST AI RMF 1.0 (AI 100-1) and Playbook. Primary text **INACCESSIBLE** in this
  environment; see `sources/audits/nist-ai.md`. Function names and category counts (GOVERN 1–6,
  MAP 1–5, MEASURE 1–4, MANAGE 1–4) and the seven trustworthiness characteristics are secondary
  corroboration only *(unverified against the primary)*. Category topic hints in
  `assets/data/airmf-1.0-structure.json` are paraphrases *(unverified)*.
- Method notes, scoring scale and harm taxonomy: [references/ai-rmf-method.md](references/ai-rmf-method.md).
