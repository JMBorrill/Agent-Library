# Source audit: `gov-design`

| Field | Value |
|---|---|
| Source ID | `gov-design` |
| Title (as verified) | GOV.UK Design System (README heading: "GOV.UK Design System") |
| Publisher / author | Government Digital Service (GDS), Crown Copyright (per repo `LICENSE`); site footer credits the "GOV.UK Design System team" |
| Edition / version / effective date | Repository `alphagov/govuk-design-system`, branch `main`, fetched 2026-10-13. Commit SHA not recorded (api.github.com blocked). `package.json` depends on `govuk-frontend` `^6.5.1`. Accessibility statement: prepared 23 October 2019, last reviewed and updated 18 December 2024 (per `src/accessibility-statement.md`). |
| Canonical URL (registry) | https://design-system.service.gov.uk/ |
| URL(s) actually read | `https://raw.githubusercontent.com/alphagov/govuk-design-system/main/<path>` for every path listed under "Verified content"; plus `https://raw.githubusercontent.com/alphagov/govuk-frontend/main/LICENSE.txt` and `.../govuk-frontend/main/packages/govuk-frontend/src/govuk/components/footer/template.njk` |
| Access status | VERIFIED (for the files listed below); the rendered website itself was not reached |
| Access method | Official GitHub repository raw files via curl (HTTP 200) |
| Date checked | 2026-10-13 |
| Licence / reuse terms (as verified) | Code: MIT License, "Copyright (c) 2017 Crown Copyright (Government Digital Service)" (`LICENSE`; `package.json` `"license": "MIT"`). Content: the repo has no separate content-licence file; the site footer (`views/partials/_footer.njk`) calls `govukFooter` with no `contentLicence` override, and the govuk-frontend footer template's default text states all content is available under the Open Government Licence v3.0 except where otherwise stated. So OGL v3.0 for prose is verified only indirectly via the template default, not via a statement in this repo. |
| Normative status | Advisory design guidance for UK government services; contextually expected for GOV.UK services (Service Standard point on using common components is referenced via Service Manual, not verified here). Accessibility conformance target: WCAG 2.2 AA (legal driver: Public Sector Bodies (Websites and Mobile Applications) (No. 2) Accessibility Regulations 2018). |

## Access ledger
- `curl https://design-system.service.gov.uk/...` — not attempted per brief (proxy returns CONNECT 403 for this host).
- `raw.githubusercontent.com/alphagov/govuk-design-system/main/README.md` — 200. Confirms repo holds the website; reusable code lives in `alphagov/govuk-frontend`. README says `npm run build` builds `./src` to `./build`, which led to the `src/` probes.
- `LICENSE` — 200 (MIT). `LICENCE`, `LICENSE.md`, `LICENCE.md` — 404.
- `package.json` — 200.
- `src/components/{error-message,error-summary,text-input,radios,checkboxes,date-input,button,fieldset}/index.md` — all 200.
- `src/patterns/{validation,question-pages,names,addresses,email-addresses,dates,check-answers,confirmation-pages,start-using-a-service,phone-numbers}/index.md` — all 200. Note: the validation page lives at `src/patterns/validation/` with front-matter title "Recover from validation errors"; `src/patterns/recover-from-validation-errors/index.md` — 404.
- `src/patterns/telephone-numbers/index.md` — 404; the pattern is `src/patterns/phone-numbers/index.md` (front matter lists a redirect from `/patterns/telephone-numbers`).
- `src/accessibility/index.md` — 200; `src/accessibility/accessibility-strategy/index.md` — 200; `src/accessibility-statement.md` — 200. (`src/accessibility-statement/index.md`, `src/accessibility-strategy/index.md` — 404.)
- `views/partials/_footer.njk`, `views/layouts/layout.njk`, `views/layouts/_generic.njk`, `docs/deployment.md` — 200 (footer read for licence). `CHANGELOG.md` — 404.
- `alphagov/govuk-frontend` `LICENSE.txt` and footer `template.njk` — 200.
- Files saved under `scratchpad/src/gov-design/`. Live example HTML (the `{{ example(...) }}` macros reference files under `src/<group>/<item>/<example>/index.njk`) was NOT downloaded, so exact markup in examples is not verified.

## Verified content
All paths relative to `alphagov/govuk-design-system@main`. Paraphrased.

- `src/components/error-summary/index.md`
  - "When to use this component": show an error summary whenever there is a validation error, even a single one, alongside inline error messages.
  - "How it works": must move keyboard focus to the summary (govuk-frontend JS does it), use heading 'There is a problem', link to each answer in error, keep wording identical to inline messages; also add 'Error: ' to the page title.
  - "Linking from the error summary to each answer": link targets for single field, multi-field (first erroneous field, or first field if unknown) and radios/checkboxes (first option).
  - "Where to put the error summary": top of `main`, below breadcrumbs/back link, above the `<h1>`.
- `src/components/error-message/index.md`
  - "When not to use this component": not for eligibility/permission/capacity problems.
  - "How it works": message after question and hint text, red border, keep all entered values, hidden 'Error:' prefix for screen readers (translatable).
  - "Match up error messages to labels", "Be clear and concise" (banned word list: jargon, 'forbidden', 'illegal', 'you forgot', 'prohibited', 'please', 'sorry', 'valid'/'invalid', 'oops'), "Be consistent", "Be specific", "Use instructions and descriptions", "Use error message templates", "Track errors".
- `src/patterns/validation/index.md` (title "Recover from validation errors")
  - "How it works": refuse impossible, ambiguous or missing-required data; ignore unwanted characters.
  - "How to tell the user about validation errors": re-show page with values, 'Error: ' title prefix, error summary with focus, inline messages.
  - "When to tell the user about validation errors": not on blur; on continue/submit.
  - "Client side and server side validation": server side always required.
  - "Turn off HTML5 validation": `novalidate` on forms; do not add `required`.
- `src/patterns/question-pages/index.md`: optional marking with '(optional)', never asterisks; back link, page heading, continue button required; "Start by asking one question per page"; label/legend as heading; "Hint text" (one short sentence, no full stops, no links); "Continue button" ('Continue' not 'Next', left aligned); "Using progress indicators"; "Using range sliders" (cites WCAG 2.2 SC 2.5.1).
- `src/components/text-input/index.md`: labels required, above input, sentence case, no colon; "Avoid placeholder text" (cites WCAG 2.2 SC 1.4.3); `inputmode` numeric/decimal; avoid `type="number"`; "Prefixes and suffixes"; "Use the autocomplete attribute" (WCAG 2.2 SC 1.3.5 AA in production); "Do not disable copy and paste"; "Avoid restricting the length of a user's input" (`maxlength`); spellcheck; "Error messages" templates.
- `src/components/radios/index.md`: options left of labels; no pre-selection; alphabetical ordering default; fieldset+legend; inline radios only for two short options; conditional reveal limits and "Known issues" (fails WCAG 2.2 SC 4.1.2); error templates.
- `src/components/checkboxes/index.md`: parallels radios; "Add an option for ‘none’" (last, 'or' divider, `exclusive` behaviour, error if both selected without JS); error templates.
- `src/components/date-input/index.md`: three fields in fieldset; accept month names; never auto-tab; "Use the autocomplete attribute for a date of birth" (`bday-day`/`bday-month`/`bday-year`); error priority order and templates.
- `src/components/fieldset/index.md`: legend must be first element in a fieldset; legend-as-heading for single-question pages.
- `src/components/button/index.md`: action-describing sentence-case text with listed standard labels; left-aligned primary; avoid multiple default buttons; start buttons use link tags; warning buttons sparingly, not colour alone; inverse buttons need 4.5:1 contrast; "Disabled buttons" (avoid unless research supports); `data-prevent-double-click`.
- `src/patterns/names/index.md`: field labels; middle names optional without '(optional)'; autocomplete `name` / `given-name` / `family-name`; spellcheck false; avoid title; allow name changes.
- `src/patterns/addresses/index.md`: address lookup (UK only, manual fallback, UPRN); postcode format tolerance; multiple inputs (county optional) with per-field autocomplete; textarea with `street-address`.
- `src/patterns/email-addresses/index.md`: explain why; 254 chars; `type="email"`, `spellcheck="false"`, `autocomplete="email"`; ~30 visible chars; error templates.
- `src/patterns/phone-numbers/index.md`: only collect if needed; tolerate formats; `autocomplete="tel"`; Ofcom drama numbers for examples; avoid input masking and reformatting; `tel:` link caveats.
- `src/patterns/dates/index.md`: date types; calendar control never JS-only; example dates use day ≥13 and month ≤9.
- `src/patterns/check-answers/index.md`: change links with hidden text; return to check answers after change; 'Not provided' for skipped optional answers; descriptive submit button.
- `src/patterns/confirmation-pages/index.md`: required contents list; interactive elements in green panel need 3:1 contrast changes; bookmarking.
- `src/patterns/start-using-a-service/index.md`: GOV.UK services must start on a GOV.UK content page; contents of a start point; avoid complex eligibility there.
- `src/accessibility-statement.md`: "Compliance status" — site, Frontend docs site and govuk-frontend codebase stated fully compliant with WCAG 2.2 AA; dates as above.
- `src/accessibility/accessibility-strategy/index.md`: "Baseline WCAG accessibility compliance" — target level AA of the latest WCAG version published for at least a year; AAA not required.
- `src/accessibility/index.md`: using the Design System does not by itself make a service accessible.

Structured extract: `sources/extracts/gov-design-rules.json` — 58 local rules (IDs `GDS-*`, local only), each with source file and an exact heading checked programmatically against the downloaded file.

## Secondary corroboration (not primary verification)
None used. All content above comes from the official repository.

## Elements useful as AI skills
- Static-HTML form audit checklist: error summary placement/heading/links (`error-summary/index.md`), 'Error: ' title prefix and `novalidate`/no `required` (`validation/index.md`), labels/placeholder/maxlength/inputmode/spellcheck (`text-input/index.md`), autocomplete tokens for personal data (`names`, `email-addresses`, `phone-numbers`, `addresses`, `date-input`), fieldset/legend (`fieldset/index.md`), no pre-selection (`radios`, `checkboxes`), disabled buttons (`button/index.md`). 44 of 58 rules flagged `testable_in_static_html: true`.
- Error-message copy linter: banned words and per-component templates (`error-message/index.md` "Be clear and concise"; error sections in text-input, radios, checkboxes, date-input, email-addresses, phone-numbers).
- Form journey review procedure: one thing per page, back link/heading/continue, check answers, confirmation page contents (`question-pages`, `check-answers`, `confirmation-pages`, `start-using-a-service`).

## Proposed skills, agents and tools
- Skill: "form accessibility and UX review (GOV.UK style)" driven by `gov-design-rules.json`.
- Tool: a static HTML checker script that evaluates the `testable_in_static_html` rules (title prefix, summary position/heading/links to existing ids, `novalidate`, absence of `required`/`maxlength`/`placeholder`-as-label/`disabled` buttons, autocomplete tokens on recognised fields, fieldset first-child legend).
- Tool: error-message wording linter with the banned list and template regexes.
- Agent: journey reviewer combining this source with `gov-service` (Service Standard) for public-sector services.

## Limitations, applicability and copyright
- Pinned only to `main` on 2026-10-13 (no SHA); file sha256 prefixes recorded in session notes (e.g. `error-summary/index.md` 09407b66217e3be8, `validation/index.md` 80388ab3551e7cfb). Re-fetch and diff before relying on it.
- Guidance is UK-government-specific and advisory; some rules are "must" within the guidance text but are not law. WCAG 2.2 AA is the legal baseline in the UK public sector via the 2018 regulations.
- Example markup (Nunjucks/HTML example files) was not downloaded; markup-level claims (e.g. exact class names, `aria-describedby` wiring) are not verified here.
- Code is MIT; prose licensing relies on the govuk-frontend footer default (OGL v3.0) — a human should confirm on the live site footer. Rule paraphrases are original wording; do not paste the guidance verbatim at length without attribution.
- Focus-move and validation-timing rules need runtime/browser testing, not static checks.

## Re-check by
2027-04-13 — re-fetch the listed files and diff; check for a newer WCAG target in the accessibility strategy/statement, govuk-frontend major version change, and confirm the content licence on the live footer.
