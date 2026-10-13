# Discovery method notes

Original wording. Source context: GOV.UK Service Manual (`gov-service`) — primary pages were
**inaccessible** in this environment; phase descriptions below follow the secondary corroboration in
`sources/audits/gov-service.md` and are *(unverified)*.

## Phases (adapted, unverified)
| Phase | Question it answers | Typical exit evidence |
|---|---|---|
| Discovery | Is there a problem worth solving, for whom, under which constraints? | Observed user behaviour and needs; constraints (technical, legal, policy); assumptions mapped; agreed out-of-scope list. Nothing is built for production. |
| Alpha | Which approach could work? | Prototypes tested with users; riskiest assumptions tested; feasibility spikes. |
| Beta | Does it work for real users at growing scale? | Working service used by real users (private then public); metrics. |
| Live | Keep improving and operating. | Ongoing research and performance data. |
| Retirement | Is it still needed / cost-effective? | — |

Secondary sources disagree on which transitions include a formal assessment; for commercial teams
treat each transition as a decision with a named owner.

## Evidence types
- **observation** — something seen or measured: an interview finding, a usability test result, an
  analytics measure, a survey result. Needs provenance (`source_ref`, `method`, `date`,
  `participants`).
- **desk_research** — someone else's published finding. Weak: different population, method unknown.
- **hypothesis** — what the team believes. Useful as a test target; never evidence.
- **assumption** — a belief recorded in the evidence log for completeness; the register is the
  better home.

## Why quotes need a session reference
Composite or "illustrative" quotes are a common way invented evidence enters product decisions,
especially when text is drafted with AI assistance. A quote is only usable if a reader can find the
session it came from. The audit flags any claim containing quoted words (three or more words
inside double quotes) whose `source_ref` lacks a session identifier (`INT-03`, `UT-2`, `session 4`,
`T12`, or a timestamp).

## Evidence strength (library heuristic, not from the source)
| Strength | Rule | Rationale |
|---|---|---|
| strong | observation with participants ≥ N (default 5) or method `analytics` | Repeated or behavioural signal |
| moderate | observation with 1–4 participants | A lead worth following |
| weak | desk research | Indirect |

Thresholds are deliberately simple; adjust `--strong-min-participants` for your context and say so.
Strength is about *quantity and directness*, not quality — a badly run 8-person study still counts
as "strong" here, which is why an independent review is required before build commitments.

## Assumption categories
desirability (do they want it), viability (does it work for the business), feasibility (can we
build/operate it), usability (can they use it), ethics (should we; harms, consent, data use).

## Cheap tests by category (examples)
| Category | Cheap test |
|---|---|
| Desirability | Problem interviews about past behaviour; observe current workaround |
| Viability | Concierge or "wizard of oz" service with real pricing conversation |
| Feasibility | Time-boxed technical spike; vendor API sandbox |
| Usability | Paper/clickable prototype test with 5–6 target users |
| Ethics | Review with people affected; data-protection screening |

## Recording gate decisions
The script outputs PROCEED / PROCEED_WITH_CONDITIONS / DO_NOT_PROCEED (= GO / GO_WITH_CONDITIONS /
NO_GO). Record the human decision separately with name, role, date, conditions and review date.
