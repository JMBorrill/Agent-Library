---
name: se-change-control
description: Assess a proposed change to a baselined requirement, interface or design item by tracing its impact through derived requirements, verification evidence, interfaces and risks, then preparing a change request for an owner or change-board decision. Use when someone wants to modify an approved requirement, an agreed interface or a tested configuration, when evidence may have been invalidated by a change, or when preparing a change request.
metadata:
  pack: systems-engineering
  version: "1.1.0"
  sources: "nasa-se-manage nasa-se"
---

# Change impact assessment and control

## Purpose
Prevent silent baseline drift: every change to a controlled item is proposed, its consequences traced
and costed, prior evidence invalidated where appropriate, and a human authority disposes of it before
the baseline is updated. Supports the NASA processes *Requirements Management* and *Configuration
Management* (see References); `se-configuration-management` owns baselines and status accounting.

## When to use
- A requirement value, interface parameter, component, software version or procedure in a baseline
  is proposed to change.
- A test failed and someone proposes relaxing the requirement instead of fixing the design.
- After an unplanned change is discovered (configuration audit) — assess retrospectively.

**Do not use when:** the item is still `proposed`/`draft` and not baselined (edit it, keeping history);
or for code review of a software change (use `software-code-review`; for baselined software
requirements still use this skill).

## Inputs
Required: change request (`assets/templates/change-request.md`, or JSON with `cr_id`, `changed_ids`,
`reason`), and the current registers: requirements, V&V matrix, ICD, risk register (any subset).
Optional: extra trace links CSV (`from_id,to_id`), cost/schedule data, supplier contracts.

## Procedure
1. **State the change precisely**: item IDs, current value → proposed value, reason, evidence.
2. **Trace impact**:
   `python3 scripts/change_impact.py --cr cr.json --requirements R.csv --vmatrix V.csv --icd I.csv --risks K.csv`
3. **Review each impacted item** — the tool follows recorded links only. Ask the owners of impacted
   requirements/interfaces whether unrecorded dependencies exist (analysis models, software
   parameters, procedures, training, spares).
4. **Plan re-verification** for every `re-verify` action: prior pass/fail results obtained on the old
   configuration no longer count as evidence for the new one.
5. **Estimate consequences**: cost, schedule, mass/power/data budgets (`space-technical-budgets`),
   risk changes (`se-risk-analysis`), safety implications.
6. **Present options**: accept, accept with conditions, revise, defer, reject — with the impact of each.
7. **Obtain disposition** from the authority named in the technical plan (owner or change board).
   Baselined interfaces need both owners. Record decision, approver and date in the change request.
8. **Implement only after approval**: update registers (new version), mark superseded evidence,
   increment the baseline (`se-configuration-management baseline_diff.py` confirms every modification
   is covered by an approved CR).

## Decision criteria
| Situation | Rule |
|---|---|
| Change to approved requirement / baselined interface | Owner or board approval required before editing |
| Change invalidates passing evidence | Re-verification planned before the item is re-claimed as verified |
| Proposal relaxes a requirement after a test failure | Treat as a waiver/deviation: requires parent-need check and stakeholder agreement |
| Impact touches safety-related item or hazard control | Escalate to `safety-risk-reviewer` and safety authority |
| Changed ID unknown to all registers | Stop — the item is not under configuration control (exit 1) |

## Outputs
Completed change request, impact report (`--json`), updated registers after approval, re-verification
entries in the V&V matrix.

## Validation
`change_impact.py` exit 0 ⇒ every changed ID exists in at least one register and the recorded trace
was followed. The impact set is a **lower bound**; completeness depends on recorded links.

## Examples
`assets/examples/change-request.json` (raise sampling 200 → 500 Hz) with the example registers →
impacted: DEMO-SUB-001 (derived), DEMO-IF-003 (baselined interface), DEMO-RSK-002, DEMO-VER-001 and
DEMO-VER-005 (passing evidence invalidated); parent DEMO-STK-001 to check. Unknown ID → exit 1.

## Escalation and stop conditions
- No approval authority defined → stop and ask the project owner to name one (`se-technical-planning`).
- The agent never approves its own change request; `independent-reviewer` or a human checks impact
  completeness.

## References
- `nasa-se-manage` — Requirements Management §6.2, Configuration Management §6.5 *(secondary
  corroboration only; see `sources/audits/nasa-se-manage.md`)*.
