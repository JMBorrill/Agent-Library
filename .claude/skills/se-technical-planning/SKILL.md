---
name: se-technical-planning
description: Tailor a proportionate systems-engineering approach to a project's risk, safety, regulatory and novelty profile — rigour per process, artifacts, milestone reviews and named decision authorities — and draft the engineering plan (milestones, work breakdown, responsibility matrix, baselines, reserves). Use at project start or phase change, when deciding how much process a project needs, or when nobody knows who approves baselines, risk acceptance or physical tests.
metadata:
  pack: systems-engineering
  version: "1.1.0"
  sources: "nasa-se-manage nasa-se"
---

# Technical planning and process tailoring

## Purpose
Right-size the engineering process: enough rigour where failure is costly or dangerous, little
bureaucracy elsewhere — and make decision rights explicit before they are needed. Corresponds to the
NASA process *Technical Planning* (see References).

## When to use
- Project kick-off, phase transitions, or when scope/risk changes materially.
- A team asks "do we really need a CDR / an ICD / a risk register?".
- Before the first baseline: who approves what must be written down.

**Do not use when:** you need a delivery schedule for a software backlog only (use the team's agile
tooling; `product-shaping` for bounded bets), or a financial business case (`finance-options`).

## Inputs
Required: project profile JSON — `risk_class` (low/moderate/high), `safety_critical`, `regulated`,
`novel_technology`, `hardware`, `software`, `team_size`, `decision_owner`, and `safety_authority` when
safety-critical (examples in `assets/examples/`).
Optional: milestones, budget, staffing, external obligations. Plan template:
`assets/templates/engineering-plan.md`.

## Procedure
1. **Classify risk** with the decision owner: consequence of failure (people, money, mission,
   reputation), novelty, complexity, regulatory exposure. Record the rationale.
2. **Tailor**: `python3 scripts/tailor_process.py profile.json --markdown`
   Review each process's proposed rigour; adjust with written rationale (the heuristic is a starting point).
3. **Name authorities**: decision owner, safety authority, compliance/legal where applicable, change
   authority for baselines. No authority ⇒ no gate can be passed.
4. **Plan milestones and reviews** from the tailored review list; define entry evidence per review
   (`se-review-gates`).
5. **Work breakdown**: products → work packages → owners; link each work package to the artifacts it
   produces.
6. **Responsibility matrix**: for each artifact, who authors, who independently reviews, who approves.
   Authors never approve their own artifacts.
7. **Configuration and data**: when each register comes under control (`se-configuration-management`)
   and where data lives (`se-technical-data-management`).
8. **Reserves**: schedule/cost/technical margins and who may release them.
9. **Approve and revisit**: decision owner approves the plan; revisit at each milestone or trigger.

## Decision criteria
| Profile | Effect |
|---|---|
| risk_class low/moderate/high | base rigour light/standard/rigorous |
| safety_critical | V&V, interfaces, risk, configuration, assessment → rigorous; TRR mandatory for hazardous tests; safety authority required |
| regulated | requirements, requirements management, configuration, data → rigorous; compliance authority |
| novel_technology | design solution, risk, assessment, decision analysis → rigorous |
| software-only | implementation/integration one level lighter (CI pipeline provides integration evidence) |
| safety-critical but "low" risk | warning — confirm classification with safety authority |

## Outputs
Tailoring table (`--markdown`/`--json`), `engineering-plan.md`, responsibility matrix, review schedule.

## Validation
Exit 0 ⇒ profile complete and consistent enough to tailor. The rigour mapping is this library's
heuristic (`assets/data/tailoring.json`, provenance stated), **not NASA policy**; the owner approves.

## Examples
- `assets/examples/profile-aster.json` → moderate base, safety + novelty raise 7 processes to rigorous;
  reviews SRR, PDR, CDR, TRR, SAR; safety authority listed.
- `assets/examples/profile-saas.json` → light rigour, walk-through SRR, TRR only for hazardous tests.
- `assets/examples/profile-fail.json` → exit 1: `risk-class`, `no-decision-owner`, `team-size`.

## Escalation and stop conditions
- Stop if no decision owner is named. Safety-critical work without a safety authority is an error.
- Regulated domains: compliance/legal authority confirms obligations (`finance-fca-scope-check` for UK
  financial services triage).

## References
- `nasa-se-manage` — Technical Planning §6.1 *(secondary corroboration only; see
  `sources/audits/nasa-se-manage.md`)*. Tailoring levels are original to this library.
