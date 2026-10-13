# Postmortem: calendar sync backlog delayed appointment reminders (synthetic)

Incident ID: AIOPS-INC-0142 · Severity: SEV2 · Date: 2026-09-14 · Status: action items in progress
Authors: reliability-engineer, scheduling-team · Review: blameless postmortem review 2026-09-17

## Summary
A configuration change reduced the calendar-sync worker pool from 12 to 2 workers. The sync queue
backed up, and appointment reminders for 38 tenants were sent between 2 and 5 hours late.

## Impact
- 38 of 412 tenants (9.2%) affected; 6,240 reminders delayed by 2-5 hours; 0 reminders lost.
- Booking API availability unaffected (99.97% over the incident window).
- Estimated 140 additional no-shows reported by pilot clinics (customer success survey).
- Reminder SLO budget: 61% of the 30-day budget consumed.

## Timeline
All times UTC.

| Time | Event |
|---|---|
| 2026-09-14 08:05 | Worker pool configuration change deployed with routine config bundle |
| 2026-09-14 08:40 | Sync queue depth passes 50,000 (no alert configured on queue age) |
| 2026-09-14 10:12 | Pilot clinic reports late reminders to support |
| 2026-09-14 10:25 | Support escalates; incident declared SEV2, incident commander assigned |
| 2026-09-14 10:48 | Worker pool restored to 12; backlog starts draining |
| 2026-09-14 13:30 | Backlog cleared; incident resolved |

## Root causes and contributing factors
Root cause: the worker pool size was part of a shared configuration bundle, and the bundle's
default for a test environment was applied to production.

Contributing factors:
- No validation that production worker counts stay within an expected range.
- Queue-age alerting existed for the booking queue but not for the calendar-sync queue.
- Config bundle changes were reviewed as low-risk because they usually only change feature flags.

## Detection
Detected by a customer report 2 h 7 min after the change; monitoring did not alert.

## Response
The incident commander coordinated; the operations lead identified the config diff and rolled the
pool size back; the communications lead posted status updates every 30 minutes.

## What went well
- Rollback of the configuration took 4 minutes once the change was identified.
- No reminders were lost because the queue is durable.

## What went badly
- Two hours passed before anyone knew.
- The status page update was delayed 20 minutes waiting for approval.

## Where we got lucky
- The incident started on a Monday morning when support staffing is highest.

## Action items
| Action | Owner | Priority | Due | Tracking | Status |
|---|---|---|---|---|---|
| Alert on calendar-sync queue age > 10 min | sre-oncall-lead | P1 | 2026-09-24 | AIOPS-2231 | done |
| Validate production worker counts in config CI | platform-lead | P1 | 2026-10-01 | AIOPS-2232 | open |
| Split environment defaults out of shared config bundle | platform-lead | P2 | 2026-10-31 | AIOPS-2233 | open |
| Pre-approve status page templates for SEV2 | comms-lead | P3 | 2026-10-15 | AIOPS-2234 | open |
