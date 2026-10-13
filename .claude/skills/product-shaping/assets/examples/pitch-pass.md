# Pitch: Walker marks a day off and affected walks are re-offered (synthetic)

## Problem
Sole-trader walkers who fall ill or take a day off currently text every affected owner one by one
and then rebuild the week by hand (DWS-EV-001, DWS-EV-002). In the pilot export a median walker had
3.1 schedule changes per week (DWS-EV-004). Owners told us they only want to know two things: is my
dog's walk happening, and if not, when is the replacement.

## Appetite
2 weeks for one designer and one developer. If it cannot fit, we cut scope rather than extend.

## Solution
Breadboard (places, affordances, connections):
- **Calendar day view** (place) → affordance "Mark day off" → connects to **Affected walks list**.
- **Affected walks list** (place) shows each walk with two affordances: "Offer next free slot"
  (default) or "Cancel and notify".
- **Owner message** (element): one SMS per owner with the cancelled time and the offered slot,
  plus a reply link to accept or decline.
- **Week view** updates when an owner accepts; declined walks stay in a "needs attention" strip.

Fat-marker sketch description: a single full-width list under the calendar, no new navigation.

## Rabbit holes
- Offered slot clashes with another walker's booking in multi-walker businesses -> Decision: this pitch only covers sole traders; multi-walker accounts see "Cancel and notify" only.
- Owners who do not reply -> Resolution: walk stays cancelled after 24 hours and appears in the needs-attention strip; no automatic re-chasing.
- SMS costs for large client lists -> Patch: reuse the existing reminder SMS budget and cap at 40 messages per day off.

## No-gos
- No automatic route optimisation.
- No changes to pricing or cancellation fees.
- No owner-side app screens; SMS reply link only.
