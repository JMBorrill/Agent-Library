---
name: independent-review
description: Perform a sceptical, independent challenge review of any artifact (requirements, designs, plans, business cases, AI evaluations, product briefs, demo reports) — audit claims against evidence, expose hidden assumptions, request specific missing evidence, screen language for overclaimed assurance, and recommend GO / GO_WITH_CONDITIONS / NO_GO without deciding. Use before gates, decisions, publication or hand-over, and whenever an artifact asserts approval, compliance, safety or research findings.
metadata:
  pack: orchestration
  version: "1.0.0"
  sources: "nasa-se-manage google-review nist-ai"
---

# Independent challenge review

## Purpose
Provide the separation of duties every high-stakes artifact needs: someone who did not write it checks
that each conclusion follows from evidence that actually exists, that limitations are visible, and that
no agent has granted itself authority. Applies across packs; domain checks come from the domain skills.

## When to use
- Before any review gate, investment or design decision, external publication or transition.
- When an artifact says "approved", "compliant", "safe", "validated", "users said", or cites precise
  clauses of a standard.
- After an agent produced a large artifact quickly — check it before anyone relies on it.

**Do not use when:** you authored the artifact (find another reviewer), or for line-level code review
(`software-code-review`, which applies the same independence principle).

## Inputs
Required: the artifact(s) and their claimed evidence; the domain skill's checks that apply.
Optional: source audits (`sources/audits/`), prior review findings, the decision being supported.
Template: `assets/templates/review-findings.csv`.

## Procedure
1. **Confirm independence**: you did not author it; note any conflicts.
2. **Identify the decision** the artifact supports and who owns it.
3. **List the claims** (performance, compliance, safety, user evidence, cost, citations).
4. **Trace each claim to evidence**: open the file/record/test output. Classify: supported,
   partially supported, unsupported, contradicted. Never accept "see attached" without opening it.
5. **Re-run deterministic checks** from the relevant skills (e.g. `req_lint.py`, `vmatrix_check.py`,
   `cashflow.py`, `run_eval.py`, `static_checks.py`) and compare with what the artifact reports.
6. **Screen the language**: `python3 scripts/claim_check.py <files or dirs>`; every error must be
   rephrased as a recommendation or backed by `[signoff: name, YYYY-MM-DD]`; research claims need
   `[evidence: ...]`; precise clause citations need a verification marker.
7. **Challenge assumptions**: what would have to be true? What is the cheapest evidence that would
   change the conclusion? Check source access status — INACCESSIBLE sources cannot support
   "verified" claims.
8. **Write findings** (`review-findings.csv`): severity, location, claim, evidence requested, owner.
9. **Recommend** GO / GO_WITH_CONDITIONS / NO_GO with reasons; state explicitly that the named human
   authority decides.

## Decision criteria
| Finding | Severity |
|---|---|
| Unsupported safety, compliance or approval claim | critical (blocks) |
| Deterministic check fails or differs from what the artifact reports | major |
| Research quote/finding without evidence reference | major |
| Precise source citation from an inaccessible source not marked unverified | minor |
| Missing owner, date or assumption list | minor |
| Style or clarity | observation |

## Outputs
`review-findings.csv`, review summary (recommendation, blocking findings, conditions, evidence
requests), `claim_check.py --json` report.

## Validation
`claim_check.py` exit 0 ⇒ no overclaiming language detected. It is a language screen with false
negatives; it does not establish truth. Unit tests: `tests/test_independent_review.py`.

## Examples
- `assets/examples/report-pass.md` → exit 0 (negated claims, evidence tags, a cited sign-off record).
- `assets/examples/report-fail.md` → exit 1: `assurance-claim` ×3, `absolute-claim`,
  `unsupported-research` ×2; warning `unverified-citation`.

## Escalation and stop conditions
- Critical findings go to the human decision owner directly, not only to the author.
- If evidence is withheld or cannot be opened, record NO_GO-recommended for affected claims.
- Domain expertise gaps → hand to `safety-risk-reviewer`, `security-reviewer`,
  `credit-regulatory-reviewer` or `ai-governance-reviewer`.

## References
- Separation of author and reviewer and evidence-based reviews: `nasa-se-manage` (Technical Assessment,
  unverified in-session), `google-review` (code review standard — verified, CC BY 3.0), `nist-ai`
  (independent review in AI governance, unverified). Notes: [references/review-heuristics.md](references/review-heuristics.md).
