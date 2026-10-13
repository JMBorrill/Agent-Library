# Product brief: MVP AI scheduling assistant (synthetic)

Owner: product lead (synthetic) · Status: draft for review · Pitch: inputs/pitch.md (6-week appetite)

## Outcomes and metrics
- Median time an owner spends answering a booking or reschedule request falls from about 6 minutes
  (pilot, self-reported, synthetic) to under 2 minutes within 8 weeks of MVP release, measured from
  inbox-open to send in the activity log for pilot tenants.
- Share of AI drafts approved with no more than minor edits reaches at least 60% within 8 weeks
  (proxy for usefulness; measured in the activity log).
- Guardrail: cross-tenant data exposure incidents stay at 0, and SMS opt-out rate does not rise by
  more than 0.5 percentage points against the pre-MVP pilot baseline.

## Users
- Sole-trader and micro service-business owners (dog walkers, cleaners) with 10 to 60 regular
  customers who run bookings from a phone, often in the evening.
- End customers of those businesses who receive SMS/email and have no account.

## Job stories
- AIOPS-STY-001: When a customer texts asking to move a booking, I want to answer with suitable free times in under 2 minutes, so I can keep my evening free.
- AIOPS-STY-002: When I approve a proposed time, I want to book the slot and confirm it to the customer in one step, so I can avoid double handling.
- AIOPS-STY-003: When the assistant suggests a message, I want to see where the suggestion came from, so I can trust what goes out in my name.
- AIOPS-STY-004: When I look back at my week, I want to see every message the assistant drafted, so I can spot mistakes.

## Non-goals
- No auto-send of AI-drafted messages in the MVP.
- No payments or invoicing changes.
- No external calendar sync.
- No voice calls or call summaries.

## Assumptions
- Owners will trust drafts enough to approve them quickly - hypothesis AIOPS-AS-003, to be tested in
  alpha; prototype sessions (AIOPS-EV-007) indicate owners edit drafts, not that they trust them.
- Owners will pay about GBP 29 per month - hypothesis AIOPS-AS-004 (AIOPS-EV-005 is a hypothesis row,
  not evidence); a pricing test is planned in alpha.
- Booking changes are frequent (AIOPS-EV-003).

## Risks
- Indirect prompt injection in inbound email triggers an unwanted send -> side-effecting tools require owner approval and are never callable from untrusted content.
- Cross-tenant leakage through AI context -> one tenant per prompt context, tenant filter on every query, isolation tests in CI.
- PII leaks into drafts (other customers' phone numbers or addresses) -> PII leakage eval gate at 0.

## Accessibility
Target WCAG 2.2 AA. The inbox and draft panel must work with keyboard only and a screen reader,
support 200% text resize on mobile, and must not rely on colour alone to show draft status. SMS
content is plain text with times written in full.

## Privacy and security
Data processed: customer names, phone numbers, email addresses, booking times and message text, per
tenant. Purpose: drafting replies and proposing bookings for that tenant only. Message text sent to
the LLM provider is limited to the current thread; retention of prompts at the provider is set to
the minimum the contract allows (to be confirmed by the data-protection lead). Messages and drafts
are retained 24 months then deleted. Abuse cases: injection via inbound email, cross-tenant access,
data egress via tool calls. A DPIA is required before beta.

## Release slices
- Slice 1: inbox with AI draft panel, owner edits and sends manually (no tools).
- Slice 2: proposed slots from the in-app calendar and approve-to-book.
- Slice 3: activity log with draft sources.
