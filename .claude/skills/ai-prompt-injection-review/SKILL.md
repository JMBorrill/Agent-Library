---
name: ai-prompt-injection-review
description: Review an LLM application or agent for prompt-injection and tool-misuse risk - screen untrusted content (emails, documents, retrieved pages, tool output) with a heuristic injection scanner, and evaluate proposed agent tool calls against an allowlist/approval/egress/PII policy to get allow, deny or require_approval decisions. Use when designing or testing agent guardrails, reviewing indirect injection via RAG or CRM email, building an injection test corpus, or measuring detection rates.
metadata:
  pack: ai-governance
  version: "1.0.0"
  sources: "nist-ai"
---

# Prompt-injection and tool-misuse review

## Purpose
Show, with a reproducible corpus, how an AI system behaves when untrusted content tries to take
control — and make sure the *tool policy* (not the model's good behaviour) stops side effects
that untrusted content requests. Detection is a screen; the policy is the control.

## When to use
- Designing or reviewing an agent that reads email, documents, web pages or tool output and can
  call tools (send, update, fetch, pay, delete).
- Before connecting a new data source or a new side-effecting tool to an assistant.
- Building a regression corpus of injection attempts for `ai-eval-harness`.
- Investigating an incident where an assistant acted on embedded instructions.

**Do not use when:** you need a full application security test (use a security review skill and
a qualified tester); you want to certify a model as injection-proof (no heuristic can); or the
system has no untrusted input and no tools (a lighter review suffices).

## Inputs
Required
- Untrusted content samples or a labelled corpus JSONL (`{"id","text","label"}`), template
  `assets/templates/injection-corpus.jsonl`.
- Tool policy JSON (schema `assets/schemas/tool-policy.schema.json`, template
  `assets/templates/tool-policy.json`).
- Proposed tool calls JSON with provenance and data classification (schema
  `assets/schemas/tool-calls.schema.json`, template `assets/templates/tool-calls.json`).
Optional
- Agent architecture diagram, tool list with side effects, data classification scheme.

## Procedure
1. **Map trust boundaries.** List every input channel and label it `user`, `system`,
   `retrieved_content` or `tool_output`. Anything a third party can write is untrusted.
2. **Inventory tools.** Mark each as read-only or side-effecting. Fetching a URL is
   side-effecting (it can exfiltrate data in the query string).
3. **Write the policy**: allowlist, side-effecting tools, forbidden domains, egress allowlist,
   domains allowed to receive personal data. Core rule: *instructions originating from
   retrieved content or tool output can never trigger side-effecting tools.*
4. **Build the corpus**: benign samples from each channel plus attacks — direct override, role
   reassignment, hidden text (HTML comments, white text, zero-width, Unicode tags), markdown
   image exfiltration, tool-call coercion, base64 payloads, concealment requests — and include
   known misses (paraphrase, other languages) so the detection rate is honest.
5. **Screen content:**
   `python3 scripts/injection_scan.py corpus.jsonl --jsonl --json`
   Report detection rate, false negatives and false positives from the summary.
6. **Evaluate tool calls** produced by the agent on each attack (from logs or a dry run):
   `python3 scripts/tool_policy_check.py calls.json --policy policy.json --expect --json`
   Every expected decision must match; a deny that depends only on the scanner is a design gap.
7. **Fix by design, not by pattern**: remove the tool, require approval, narrow egress, separate
   untrusted content from instructions, strip hidden markup before the model sees it.
8. **Record results** as evidence for the AI risk register (`ai-risk-assessment`) and add the
   attacks to the eval set (`ai-eval-harness`).

## Decision criteria
| Situation | Decision |
|---|---|
| Side-effecting tool requested by retrieved content / tool output | deny (`TP-UNTRUSTED-SIDE-EFFECT`) |
| Personal data to a domain not allowed for personal data | deny (`TP-PII-EGRESS`) |
| Destination on forbidden list, or tool not allowlisted, or unknown provenance | deny |
| Side-effecting tool requested by user/system | require_approval (human sees full args) |
| Destination not on egress allowlist; args contain injection phrases; PII under a non-personal label; unknown classification | require_approval |
| Scanner verdict `flag` on content | quarantine or strip before the model reads it; human review |
| Scanner verdict `review` | process with no side-effecting tools available |
| Scanner `clean` | still apply the tool policy — clean is not safe |
| Detection rate below agreed target on the corpus | do not rely on screening; strengthen policy |

## Outputs
- Scan report (`injection_scan.py --json`, schema `assets/schemas/injection-scan.output.schema.json`)
  with per-document verdicts and, for labelled corpora, detection and false-positive rates.
- Decision report (`tool_policy_check.py --json`, schema `assets/schemas/tool-decisions.output.schema.json`).
- A short review note: trust boundaries, tool inventory, policy, corpus results, gaps, owners.

## Validation
- `python3 scripts/injection_scan.py assets/examples/mortgage-document-pass.txt` → exit 0;
  `assets/examples/crm-email-injection-fail.txt` → exit 1.
- `python3 scripts/tool_policy_check.py assets/examples/tool-calls-pass.json --policy assets/examples/tool-policy.json` → exit 0;
  `tool-calls-fail.json` → exit 1; `tool-calls-corpus.json --expect` → exit 0 (17/17 match).
- PASS for the scanner means no pattern matched; it does **not** mean the content is safe.
  PASS for the policy means each reported call met the policy given its labels; it cannot detect
  mislabelled provenance or calls the agent did not report.

## Examples
- `assets/examples/injection-corpus.jsonl` — 24 synthetic documents (10 benign, 14 malicious)
  including indirect injection in a CRM email for an AI operations platform (hidden HTML comment,
  image exfiltration) and in mortgage documents (white-text payslip instruction, valuation
  addendum with concealment). Current result: 12/14 malicious detected (85.7%); misses are the
  paraphrased social-engineering and French-language samples (labelled `known_false_negative`);
  1/10 benign flagged (security-training text quoting an attack); 1 benign sent to review.
- `assets/examples/tool-calls-corpus.json` + `tool-policy.json` — 17 calls: 4 allow,
  6 require_approval, 7 deny, all matching `expected_decision`.

## Escalation and stop conditions
- Stop and escalate if an agent can perform irreversible or financial actions on content from
  untrusted channels, or if provenance cannot be tracked through the pipeline.
- Escalate confirmed exploitation to the security incident process; preserve logs.
- `ai-evaluation-engineer` maintains the corpus; `ai-governance-reviewer` and
  `independent-reviewer` challenge policy coverage. Policy changes need the system owner.

## References
- `nist-ai` — AI RMF trustworthiness characteristic *secure and resilient* and MANAGE-function
  treatment of risks (secondary corroboration only; primary **INACCESSIBLE**, see
  `sources/audits/nist-ai.md`). AI 600-1 generative AI risks: *information security* is
  recalled from memory *(unverified)*; *data privacy* and *human-AI configuration* are
  corroborated names *(unverified against the primary)*.
- Attack taxonomy, rule rationale and corpus design: [references/injection-method.md](references/injection-method.md).
