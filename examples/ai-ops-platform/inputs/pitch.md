# Pitch: MVP AI scheduling assistant - drafts replies and proposes slots, owner approves (synthetic)

## Problem
Sole-trader service owners (dog walkers, cleaners) answer booking texts by hand in the evening
(AIOPS-EV-001) and describe rescheduling as long back-and-forth threads (AIOPS-EV-002). The pilot
export shows a median 4.2 booking changes per business per week (AIOPS-EV-003). Whether owners will
trust AI drafts (AIOPS-AS-003) and pay for them (AIOPS-AS-004) is still a hypothesis to test in alpha.

## Appetite
6 weeks for two developers and one designer. If it cannot fit, we cut scope rather than extend.

## Solution
Breadboard (places, affordances, connections):
- **Inbox** (place) lists inbound customer SMS/email for one tenant → affordance "Draft reply" →
  connects to **Draft panel**.
- **Draft panel** (place) shows the AI-drafted message, the up to 3 proposed slots taken from the
  tenant's own calendar, and the source message; affordances "Approve and send", "Edit", "Discard".
- **Booking element**: approving a proposed slot creates a tentative booking in the tenant calendar
  and sends the confirmation message; nothing is sent or booked without the owner's tap.
- **Activity log** (place) records every draft, edit, approval and tool call with tenant ID.

Fat-marker sketch description: a two-column inbox with the draft panel on the right; no new navigation.

## Rabbit holes
- Inbound emails can carry hidden instructions to the assistant (indirect prompt injection) -> Decision: inbound content is treated as untrusted data; side-effecting tools are never callable from it and every send needs owner approval.
- Cross-tenant leakage through shared AI context or caches -> Decision: one prompt context per request scoped to one tenant; no cross-tenant retrieval index in the MVP.
- Calendar conflicts with external calendars -> Patch: MVP reads only the in-app calendar; external sync is a no-go.
- Auto-send pressure from early users -> Resolution: auto-send stays off for the MVP; revisit only after AIOPS-EXP evidence and an oversight review.

## No-gos
- No auto-send of AI-drafted messages.
- No payments or invoicing changes.
- No external calendar sync (Google/Outlook) in the MVP.
- No voice calls or call summaries.
