# Writing notes for product requirements briefs

Original wording. The job-story and Given/When/Then forms are community conventions (job stories
grew out of jobs-to-be-done practice; Given/When/Then from behaviour-driven development). They are not
taken from a registered source, so no attribution to a specific document is claimed.

## Job stories vs user stories
A user story ("As a <role>, I want <feature>, so that <benefit>") centres on a persona and often a
feature. A job story centres on the **situation** that triggers the need, which makes the context
testable:

- Weak: "As a walker I want a day-off button so that I can take days off."
- Strong: "When I am ill on a working day, I want to tell all affected owners at once, so I can rest
  without spending an hour on messages."

The linter accepts `so I can` or `so that I can`, and ignores a leading story ID (`DWS-STY-001:`).

## Acceptance scenarios
- One behaviour per scenario. Use capitalised keywords `Given`, `When`, `Then` (the parser is
  case-sensitive so that lower-case "when" inside a sentence is not mistaken for a keyword).
- Put thresholds in `Then`: "within 60 seconds", "one SMS per owner", "shown in the needs-attention
  strip". Avoid "fast", "easy", "appropriate".
- Cover the unhappy path for must stories (no reply, delivery failure, conflicting booking).

## Outcome metrics
Format: metric, baseline (with source), target, date, measurement method, guardrail. Self-reported
time savings are weak evidence — pair with observed sessions or analytics.

## Flow-down mapping (prd_check.py --flow-down)
| PRD element | se-requirements field |
|---|---|
| Story ID | `id` of a `stakeholder`-level need (no "shall"; req_lint reports `need-statement` info) |
| Story job text | `statement` of the need |
| Story outcome | need `acceptance_criteria` ("Target users achieve the outcome ... in a usability session"), method `demonstration`, ID `<P>-VAL-NNN` |
| Each Given/When/Then | `software`-level requirement, `parent` = story ID, statement "When <event>, the system shall ensure that <result> (precondition: <context>)", method `test`, ID from `requirement_ids` or generated `<prefix>-NNN`, verification `<P>-VER-NNN` |
| Evidence IDs | appended to `source` |
| Status | always `proposed` — approval belongs to the requirements owner |

Generated statements are deliberately mechanical. Rewrite them to remove UI detail and to make the
subject precise before approval.

## Accessibility and privacy sections
Name the conformance target (for UK public sector services WCAG 2.2 AA is the legal baseline per the
gov-design audit; commercial products often adopt the same). List concrete needs (keyboard only,
screen reader, zoom/reflow, colour independence, plain language). For privacy: data items, purpose,
lawful basis owner, retention, access, and abuse cases (e.g. reply links forwarded to others).
