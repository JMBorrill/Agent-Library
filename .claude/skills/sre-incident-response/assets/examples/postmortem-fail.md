# Postmortem: criteria search outage (synthetic, deliberately defective)

Incident ID: MCW-INC-0007

## Summary
Mortgage-criteria search was down for a while.

## Impact
Lots of brokers were affected.

## Timeline
| Time | Event |
|---|---|
| 2026-08-02 14:30 | Search errors start |
| 2026-08-02 14:10 | Dave deployed the new index mapping |
| 2026-08-02 15:05 | Rolled back |

## Root cause
Human error: Dave forgot to run the reindex job. He should have known the mapping change needed it.

## What went well
Rollback worked.

## Action items
| Action | Owner | Priority | Due | Tracking |
|---|---|---|---|---|
| Be more careful with deploys | TBD | urgent | next sprint | none |
| Add reindex step to deploy pipeline | search-team | P2 | 2026-08-30 | MCW-311 |
