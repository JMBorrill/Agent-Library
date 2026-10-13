---
name: se-stakeholder-conops
description: Define stakeholder expectations and a concept of operations (mission need, stakeholders and decision rights, nominal and off-nominal scenarios, modes, environment, constraints, measures of effectiveness, assumptions) with evidence-tagged needs. Use at the start of an engineering project or new phase, before writing requirements, when the problem or users are unclear, or when reviewing a ConOps for solution bias, missing failure scenarios or invented stakeholder claims.
metadata:
  pack: systems-engineering
  version: "1.1.0"
  sources: "nasa-se-design nasa-se"
---

# Stakeholder expectations and concept of operations

## Purpose
Establish what the system must achieve, for whom and under what conditions — before anyone designs
it — and record which needs are evidenced and which are still hypotheses. Corresponds to the NASA
process *Stakeholder Expectations Definition* (see References).

## When to use
- New project, new phase, or major scope change.
- Requirements exist but nobody can say which stakeholder need each serves.
- Before an SRR-style review (ConOps is an entry item).

**Do not use when:** the task is consumer product discovery with user research methods (use
`product-discovery`, then summarise validated needs here), or detailed requirement writing (`se-requirements`).

## Inputs
Required: problem statement or brief; list of known stakeholders and the decision owner.
Optional: meeting notes, research records, contracts, regulations, prior concepts.
Templates: `assets/templates/conops.md`, `stakeholders.csv`, `needs.csv`.

## Procedure
1. **Identify stakeholders**: decision owner (who approves), users/operators, maintainers, safety/
   regulatory authorities, funders, people affected but not consulted. Record influence, interests and
   decision rights.
2. **State the mission need** as a problem, without solution words. Keep a separate "candidate
   concepts" list if solutions are already proposed.
3. **Capture needs** in `needs.csv`: one need per row, attributed to a stakeholder, with an `evidence_ref`
   (minutes, research record, contract clause). No evidence ⇒ label it a hypothesis in the text.
4. **Write scenarios**: nominal flows *and* off-nominal/contingency (faults, aborts, recovery,
   maintenance, disposal). Each scenario names actors, trigger, sequence, end state.
5. **Describe modes, environment and constraints** (physical, regulatory, budget, schedule, facility).
6. **Define measures of effectiveness (MOEs)** per need — how the stakeholder will judge success,
   quantified where possible. MOEs later drive validation (`se-verification-validation`).
7. **List assumptions and open questions** with owners.
8. **Check**: `python3 scripts/conops_check.py conops.md --stakeholders stakeholders.csv --needs needs.csv`
9. **Validate with stakeholders** — walk the decision owner through scenarios and MOEs; record approval.
   Then hand the needs to `se-requirements`.

## Decision criteria
| Situation | Rule |
|---|---|
| Quote or "users told us" without evidence tag | Error — never invent interviews; mark as hypothesis or remove |
| Need with no MOE | Error — define how success will be judged |
| Mission need names a design | Warning — move design to candidate concepts |
| No off-nominal scenario | Error — failure scenarios generate safety and recovery requirements |
| No decision owner | Error — escalate to sponsor |
| Conflicting stakeholder needs | Record both; decision owner resolves; do not average |

## Outputs
`conops.md`, `stakeholders.csv`, `needs.csv`, `mission-brief.md` (one-page summary), check report.

## Validation
Exit 0 ⇒ sections, scenarios, needs/MOE links and evidence tags present. It cannot confirm the needs are
right — only stakeholder validation can.

## Examples
- `assets/examples/conops-pass.md` + `stakeholders-pass.csv` + `needs-pass.csv` → exit 0, no findings.
- `assets/examples/conops-fail.md` + `*-fail.csv` → exit 1: `missing-section`, `no-off-nominal`,
  `unsupported-stakeholder-claim`, `need-without-moe`, `no-decision-owner`, `no-role`, `unknown-need`;
  warning `solution-in-need`.

## Escalation and stop conditions
- Stop if no decision owner can be identified; do not proceed to requirements.
- Safety-affected parties (operators, public) need a safety authority among stakeholders.
- Author: `systems-engineer`; challenge: `independent-reviewer`.

## References
- `nasa-se-design` — Stakeholder Expectations Definition §4.1 *(secondary corroboration only; see
  `sources/audits/nasa-se-design.md`)*.
