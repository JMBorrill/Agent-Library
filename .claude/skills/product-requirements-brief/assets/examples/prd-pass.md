# Product brief: Walker day off and re-offered walks (synthetic)

Owner: product lead (synthetic) · Status: draft for review · Pitch: walker-day-off (2-week appetite)

## Outcomes and metrics
- Share of walks cancelled because of a walker day off that are rebooked within 48 hours rises from
  30% (pilot baseline) to at least 45% within 8 weeks of release.
- Median time a walker spends handling a day off falls from about 40 minutes (interviews,
  self-reported) to under 10 minutes, measured in a follow-up usability session with 5 walkers.
- Guardrail: client complaint rate does not rise by more than 1 percentage point.

## Users
- Sole-trader dog walkers with 10–40 regular clients who manage bookings on their phone.
- Dog owners (clients) who receive SMS and do not have an account.

## Job stories
- DWS-STY-001: When I am ill on a working day, I want to tell all affected owners at once, so I can rest without spending an hour on messages.
- DWS-STY-002: When a walk is cancelled, I want to be offered a replacement time, so I can keep my dog's routine.
- DWS-STY-003: When I review my week, I want to see which cancelled walks still need a decision, so I can follow up before the weekend.

## Non-goals
- No route optimisation or travel-time estimates.
- No changes to pricing, cancellation fees or payments.
- No multi-walker (team) accounts in this release.

## Assumptions
- Owners accept SMS sent on the walker's behalf — supported only by desk research so far
  (DWS-EV-005); the ethics experiment DWS-AS-005 runs during beta.
- Walkers can complete the flow without training (DWS-EV-003).

## Risks
- SMS delivery failures leave owners uninformed -> show delivery status and a "needs attention" strip.
- Offered slot clashes with an existing walk -> only offer slots free in the walker's own calendar.

## Accessibility
Target WCAG 2.2 AA. The day-off flow must work with a screen reader and keyboard only, support 200%
text resize on mobile, and not rely on colour to show walk status. SMS content is plain text with the
time written in full.

## Privacy and security
SMS contain the dog's name and the walk time only — no address. Owner phone numbers are already held
under the existing privacy notice; no new data is collected. Reply links expire after 72 hours and are
single-use.

## Release slices
- Slice 1: mark day off and list affected walks (walker only, no SMS).
- Slice 2: SMS with offered slot and accept/decline reply link.
- Slice 3: needs-attention strip in the week view.
