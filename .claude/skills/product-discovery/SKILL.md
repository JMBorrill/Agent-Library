---
name: product-discovery
description: Run evidence-led product discovery - separate observed evidence from hypotheses, register risky assumptions, audit the evidence log for fabricated quotes and untraceable claims, and recommend a discovery-to-alpha (or alpha-to-build) phase gate. Use when exploring a customer problem, validating a concept or MVP, preparing a discovery report, or challenging "users want X" claims before committing to build.
metadata:
  pack: product
  version: "2.0.0"
  sources: "gov-service"
---

# Evidence-led product discovery

## Purpose
Decide, on traceable evidence, whether a problem is worth solving and whether the team should move
from discovery into alpha (prototyping) or from alpha into building for real users. The method adapts
the phase model described in the GOV.UK Service Manual — discovery, alpha, beta, live *(unverified:
the primary source was inaccessible; see References)* — to commercial software products. The core
discipline: what we **observed** is kept apart from what we **believe**, and every risky belief is
either tested or explicitly carried as a condition.

## When to use
- Starting work on a new product, feature area or customer segment.
- Someone asserts "customers want X" and the team is about to commit design or engineering time.
- Preparing a discovery report or a phase-gate conversation (discovery → alpha, alpha → beta/build).
- Reviewing a research log for weak, duplicated or invented evidence.

**Do not use when:** the problem is already validated and you are sizing a statistical A/B test (use
`product-experiment-design`); you are bounding a solution for delivery (use `product-shaping`); you are
writing build requirements (use `product-requirements-brief`); or the decision is regulatory or
safety-critical (escalate — this skill does not assess compliance).

## Inputs
Required
- Evidence log CSV — `assets/templates/evidence-log.csv`
  (`id, claim, type, source_ref, method, date, participants, segment, confidence, linked_assumption`).
  `type` ∈ observation | hypothesis | assumption | desk_research; `method` ∈ interview |
  usability_test | analytics | survey | desk | none.
Optional (needed for a gate recommendation)
- Assumptions register CSV — `assets/templates/assumptions.csv`
  (`id, assumption, category, risk, evidence_ids, status`). `category` ∈ desirability | viability |
  feasibility | usability | ethics; `risk` ∈ high | medium | low; `status` ∈ untested |
  experiment_planned | testing | supported | refuted.
- Research plan, consent records and session notes (kept by the team; the log points to them).

## Procedure
1. **Frame the whole problem.** Write the problem without naming a solution; list who experiences
   it (including people with access needs or low digital confidence) and what is out of scope.
2. **Map assumptions before researching.** List what must be true for the idea to work across the
   five categories. Rate risk = impact if wrong × how little we know. Record in the assumptions CSV.
3. **Plan the cheapest ethical test for each high-risk assumption** (interviews, observation,
   prototype test, concierge test, analytics). Set status `experiment_planned`; put it in
   `assets/templates/experiment-backlog.md`. Statistical A/B tests go to `product-experiment-design`.
4. **Research and log as you go.** One row per finding. Observations need `source_ref` (session ID,
   recording or dataset), `method`, ISO `date` and `participants > 0`. Quotes must cite a session
   (e.g. `INT-03 transcript 12:40`). Write team beliefs as `hypothesis` rows — they are tracked,
   never counted.
5. **Link evidence to assumptions** (`evidence_ids`) and update status to `supported`/`refuted`
   only when linked evidence exists.
6. **Audit the log:**
   `python3 scripts/evidence_audit.py evidence.csv --assumptions assumptions.csv --target alpha --as-of YYYY-MM-DD`
   Fix every `error` (missing provenance, untraceable quotes, duplicate IDs, unknown links). Treat
   `warning`s as review prompts.
7. **Read the strength summary.** Strong = observation with ≥5 participants (configurable) or
   behavioural analytics; moderate = observation with 1–4 participants; weak = desk research.
   If most counted evidence is weak, plan more primary research before a gate.
8. **Write the discovery report** (`assets/templates/discovery-report.md`) with the audit output and
   the script's gate recommendation, then hand to the accountable owner for the decision.

## Decision criteria
| Situation | Recommendation rule (script) |
|---|---|
| Any integrity error (missing source/method/date/participants, untraceable quote, unknown link, duplicate ID) | DO_NOT_PROCEED until fixed |
| No valid evidence at all | DO_NOT_PROCEED |
| High-risk assumption with neither evidence nor planned experiment | DO_NOT_PROCEED |
| High-risk assumption refuted | DO_NOT_PROCEED — re-shape the concept |
| High-risk assumption untested but experiment planned, target `alpha` | PROCEED_WITH_CONDITIONS (test it in alpha) |
| Same, target `beta` (build for real users) | DO_NOT_PROCEED |
| Medium-risk assumption open | PROCEED_WITH_CONDITIONS |
| All high/medium assumptions supported by valid evidence | PROCEED |

Judgement rules: a quote heard once is a lead, not a pattern; prefer behaviour (what people did) over
stated intent ("would you pay?"); a refuted assumption is a success of discovery, not a failure.
Gate labels map to the library vocabulary GO / GO_WITH_CONDITIONS / NO_GO and are always
recommendations.

## Outputs
- `evidence-log.csv`, `assumptions.csv` (templates in `assets/templates/`).
- Audit report: `evidence_audit.py --json`, schema `assets/schemas/evidence-audit.output.schema.json`.
- `discovery-report.md`, `experiment-backlog.md` (templates in `assets/templates/`).

## Validation
- `python3 scripts/evidence_audit.py <log> --assumptions <register> --json` → exit 0 means no
  integrity errors (`--strict` also fails on warnings); exit 1 errors; exit 2 unreadable input.
- PASS does **not** mean the research was representative, well-conducted or correctly interpreted,
  nor that the gate is approved. It means every counted claim is traceable and no high-risk belief is
  silently treated as fact. The decision belongs to a named human.

## Examples
- `assets/examples/evidence-pass.csv` + `assets/examples/assumptions-pass.csv` (synthetic
  dog-walking scheduling SaaS): exit 0; 6 counted items (4 strong, 1 moderate, 1 weak); gate
  PROCEED_WITH_CONDITIONS because a medium-risk ethics assumption still has only a planned test.
- `assets/examples/evidence-fail.csv` + `assets/examples/assumptions-fail.csv` with `--target beta`:
  exit 1 with `observation-no-source`, `quote-without-session`, `duplicate-id`, `bad-date`,
  `observation-no-participants`, `observation-no-method`, `desk-no-source`, `unknown-assumption`,
  `status-without-evidence`, `high-risk-untested`, `unknown-evidence-id`, `invalid-risk`; gate
  DO_NOT_PROCEED.

## Escalation and stop conditions
- **Stop** if research involves children, vulnerable people, health or financial data without an
  agreed consent and data-protection approach — escalate to the data protection owner.
- **Stop** if asked to "fill in" quotes, participant counts or dates: never fabricate; log a
  hypothesis instead.
- Hand the report to `product-lead` for the decision; ask `independent-reviewer` to challenge the
  evidence before a beta/build commitment. Regulated services need their own assessment process.

## References
- `gov-service` — GOV.UK Service Manual: phases (discovery, alpha, beta, live, retirement), "how the
  discovery phase works", user research in discovery. **INACCESSIBLE in this environment**: all phase
  descriptions here are from secondary corroboration listed in `sources/audits/gov-service.md` and are
  *(unverified)*. No Service Standard point numbers are relied on.
- Method notes, evidence-strength rationale and assumption categories:
  [references/discovery-method.md](references/discovery-method.md).
