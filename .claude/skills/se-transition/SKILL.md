---
name: se-transition
description: Prepare and check a product transition package — deliverables with versions, configuration IDs and acceptance records, documentation, known limitations, waivers for any open verification, training, support, handling and storage — so the receiving organisation can accept the product knowingly. Use when handing a prototype, system, data set or software release to a user, operator, customer or the next project phase.
metadata:
  pack: systems-engineering
  version: "1.0.0"
  sources: "nasa-se-realize nasa-se"
---

# Product transition

## Purpose
Hand over a product so that the receiver knows exactly what they are getting, what it has and has not
been shown to do, and how to operate, maintain and store it. Corresponds to the NASA process *Product
Transition* (see References).

## When to use
- Delivering to a customer/operator, moving a prototype to another team, releasing a data set,
  transferring to the next life-cycle phase or to storage/disposal.
- Before an acceptance review (`se-review-gates`, SAR-style).

**Do not use when:** deploying software to production — use `sre-production-readiness` (link its
result here if the software is a deliverable of a system).

## Inputs
Required: transition package JSON (`assets/templates/transition.json`): receiver, deliverables
(version, configuration ID, acceptance reference, documentation, known issues), open verification items
with waivers, limitations flag, training, support plan, handling/storage.
Also needed: V&V matrix status (`se-verification-validation`), configuration baseline
(`se-configuration-management`).

## Procedure
1. **List deliverables** (hardware, software, data, documents) with exact version and configuration ID
   matching the audited baseline.
2. **Collect acceptance evidence** per deliverable (acceptance test, review minutes, receiver checks).
3. **Disclose open items**: every verification result that is fail, blocked or not tested appears with a
   waiver approved by the authority — or the transition waits.
4. **Document limitations and known issues** in plain language for the receiver.
5. **Prepare enabling items**: operator/maintenance documentation, training, spares, tools, support
   contacts, handling, storage, transport and disposal conditions (especially stored energy, batteries,
   hazardous materials).
6. **Check**: `python3 scripts/transition_check.py transition.json`
7. **Receiver sign-off**: the receiving organisation's named representative accepts (records name and
   date). The agent never signs.

## Decision criteria
| Situation | Rule |
|---|---|
| Open fail/blocked/not-tested without approved waiver | NOT_READY |
| Limitations not documented | NOT_READY |
| Deliverable without version/configuration/acceptance reference | NOT_READY |
| Training/support/handling missing | Warning — receiver decides whether acceptable |
| Package complete, no receiver sign-off yet | READY_FOR_ACCEPTANCE (info: awaiting receiver) |

## Outputs
Transition package JSON + human-readable transition note, check report, receiver acceptance record.

## Validation
Exit 0 ⇒ READY_FOR_ACCEPTANCE: package complete and honest about open items. Acceptance itself is the
receiver's decision.

## Examples
- `assets/examples/transition-pass.json` → READY_FOR_ACCEPTANCE with `awaiting-receiver` info (one
  not-tested item under an approved waiver).
- `assets/examples/transition-fail.json` → NOT_READY: `no-receiver`, `missing-version`,
  `open-verification-unwaived`, `limitations-undocumented`, …

## Escalation and stop conditions
- Hazardous deliverables (stored energy, batteries, pressure) need handling instructions reviewed by
  `safety-risk-reviewer`.
- Never transfer with undisclosed failures; escalate to the decision owner for waiver decisions.

## References
- `nasa-se-realize` — Product Transition §5.5 *(secondary corroboration only; see
  `sources/audits/nasa-se-realize.md`)*.
