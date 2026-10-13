---
name: sre-incident-response
description: Run and learn from production incidents - classify severity, assign incident roles (incident commander, operations lead, communications lead, scribe), keep a communication cadence, stabilise first, then write and check a blameless postmortem (summary, quantified impact, ordered UTC timeline, root causes and contributing factors, detection, response, what went well/badly, owned and tracked action items). Use when an incident is declared or suspected, when drafting or reviewing a postmortem, or when checking that postmortem action items have owners, priorities, due dates and tracking IDs.
metadata:
  pack: reliability-security
  version: "1.0.0"
  sources: "google-sre"
---

# Incident response and blameless postmortems

## Purpose
Restore service quickly with clear roles and predictable communication, then turn the incident into
learning: a blameless, evidence-based postmortem with quantified impact, a reliable timeline and
owned, tracked actions that reduce the chance or impact of recurrence.

## When to use
- An alert, customer report or SLO burn suggests users are affected now.
- After any SEV1/SEV2, any incident that consumed a large share of error budget, any data
  exposure, or a near miss worth learning from.
- Reviewing a draft postmortem before the review meeting; auditing open action items.

**Do not use when:** the issue is a known, low-impact bug with no user impact (use the normal
backlog); you are designing SLOs or alerts (use `sre-service-level-objectives`); or a security
breach needs legal/regulatory handling — follow the security incident process and involve the
`security-reviewer` and legal immediately (this skill still helps with roles and timeline).

## Inputs
Required
- What is broken, since when, who is affected (as best known), current mitigation options.
- For the postmortem: chat/log/alert history with timestamps, deploy and config change records.
Optional
- SLO budget data, customer reports, support tickets. Template `assets/templates/postmortem.md`
  (JSON form: schema `assets/schemas/postmortem.schema.json`).

## Procedure
**During the incident**
1. **Declare early** and classify severity (table below); open an incident channel and a running log
   with UTC timestamps.
2. **Assign roles** (one person may hold several in small teams, but the incident commander does not
   also debug): incident commander (coordinates, decides), operations lead (hands on systems),
   communications lead (status updates internal/external), scribe (timeline).
3. **Stabilise first**: prefer reversible mitigations (roll back, disable a feature flag, shed load,
   fail over) over root-cause debugging while users are affected.
4. **Communicate on cadence** (library defaults: SEV1 every 30 min, SEV2 every 60 min, SEV3 at
   start/resolution) with: impact, what is being done, next update time.
5. **Resolve and hand over**: confirm recovery against the SLI, record end time, assign postmortem
   owner and due date (default: draft within 5 working days for SEV1/SEV2).

**After the incident**
6. **Draft the postmortem** from the template: quantify impact; build the timeline from logs, not
   memory; describe causes as system conditions and decisions; list contributing factors; record
   detection time and how; what went well, badly, and where you got lucky.
7. **Check it**: `python3 scripts/postmortem_check.py postmortem.md --as-of 2026-10-13`
   Fix errors; rewrite any `blame-language` sentences to describe conditions, signals and decisions.
8. **Review** in a blameless meeting; agree action items with named owners, priorities, due dates
   and tracking IDs; prefer actions that change the system (automation, guardrails, alerts) over
   "be more careful".
9. **Track** actions to closure; re-run the check with `--as-of` to surface overdue items.

## Decision criteria
Severity (library defaults — adapt to your organisation):

| Severity | Criteria (any) | Response |
|---|---|---|
| SEV1 | Most users/tenants cannot use a critical journey; data loss or exposure; regulatory/financial harm | Page immediately, IC + comms lead, 30-min updates, exec notified |
| SEV2 | Critical journey degraded for many users, or broken for a subset (e.g. several tenants); SLO fast-burn alert | Page, IC assigned, 60-min updates |
| SEV3 | Minor degradation, workaround exists, or non-critical feature down | Business hours, updates at start/resolution |
| SEV4 | No user impact; near miss | Ticket; optional lightweight review |

| Situation | Rule |
|---|---|
| Unsure between two severities | Choose the higher; downgrade later. |
| Mitigation available but cause unknown | Mitigate first. |
| Data exposure suspected | Treat as SEV1 and involve security/legal immediately. |
| Postmortem names a person as cause | Rewrite: what made the action reasonable at the time, what guardrail was missing. |
| Action item "be more careful" / no owner | Not acceptable; convert to a system change with an owner. |

## Outputs
- Incident log/timeline; status updates.
- `postmortem.md` (template `assets/templates/postmortem.md`) or JSON (schema
  `assets/schemas/postmortem.schema.json`); check report (`--json`, schema
  `assets/schemas/findings-report.schema.json`).

## Validation
- `python3 scripts/postmortem_check.py pm.md --json` → exit 0 = all required sections, numeric impact,
  ≥ 2 timestamps in order, action items with owner/priority/due/tracking ID. `--strict` also blocks on
  warnings (blame language, missing time zone, missing severity, overdue actions).
- PASS does **not** mean the causes are right, the analysis is deep enough or the actions will work.
  The blame check is a word-pattern heuristic: it misses subtle blame and can flag innocent phrasing.

## Examples
- `assets/examples/postmortem-pass.md` (calendar sync backlog, SEV2) → exit 0 (with `--as-of
  2026-10-13`, one `action-overdue` warning).
- `assets/examples/postmortem-pass.json` (latency regression, SEV3) → exit 0.
- `assets/examples/postmortem-fail.md` (mortgage-criteria search outage) → exit 1 with
  `missing-section`, `impact-not-quantified`, `timeline-out-of-order`, `action-no-owner`,
  `action-bad-priority`, `action-bad-due-date`, `action-no-tracking-id`; warnings `blame-language`,
  `no-severity`, `timeline-timezone`, `no-contributing-factors`.

## Escalation and stop conditions
- Suspected security breach or personal-data exposure → stop normal flow; security incident process,
  `security-reviewer`, legal/DPO.
- Incident commander cannot get needed access or decisions → escalate to the engineering manager on
  call; record the delay in the timeline.
- Hand reliability follow-ups to the `reliability-engineer` agent; `independent-reviewer` for SEV1
  postmortems.

## References
- `google-sre` — *Site Reliability Engineering* (2016) Ch. 13 Emergency Response, Ch. 14 Managing
  Incidents, Ch. 15 Postmortem Culture: Learning from Failure; *Workbook* Ch. 9 Incident
  Response and Ch. 10 Postmortem Culture *(chapter titles from search snippets — unverified)*.
  Source **INACCESSIBLE** here (`sources/audits/google-sre.md`); claimed licence CC BY-NC-ND 4.0, so
  no book text is adapted — roles, severity table, cadence and checks are written independently from
  general industry practice. Source ID: `google-sre`.
- Method notes: [references/incident-practice.md](references/incident-practice.md).
