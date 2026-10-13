# Rule map: checker rule → source rule → WCAG

Generated from `scripts/html_a11y_check.py` (RULES table) and `sources/extracts/gov-design-rules.json`.
GDS-* IDs are local to this library (not official GOV.UK identifiers); source file and heading are
where the extract located the guidance in `alphagov/govuk-design-system@main` (verified 2026-10-13).
WCAG pointers on GDS rules appear only where the extract cites them; LOCAL rule pointers are *(unverified)*.

| Checker rule | Severity | Source rule | WCAG | Source file / heading |
|---|---|---|---|---|
| `input-unlabelled` | error | GDS-INP-01 | — | `src/components/text-input/index.md` — How it works |
| `label-trailing-colon` | warning | GDS-INP-01 | — | `src/components/text-input/index.md` — How it works |
| `label-asterisk` | warning | GDS-QP-03 | — | `src/patterns/question-pages/index.md` — When to use this pattern |
| `placeholder-as-label` | error | GDS-INP-02 | WCAG 2.2 SC 1.4.3 | `src/components/text-input/index.md` — Avoid placeholder text |
| `placeholder-present` | warning | GDS-INP-02 | WCAG 2.2 SC 1.4.3 | `src/components/text-input/index.md` — Avoid placeholder text |
| `options-not-in-fieldset` | error | GDS-OPT-01 | — | `src/components/fieldset/index.md` — How it works |
| `fieldset-legend-not-first` | error | GDS-OPT-01 | — | `src/components/fieldset/index.md` — How it works |
| `option-preselected` | warning | GDS-OPT-02 | — | `src/components/radios/index.md` — How it works |
| `error-not-associated` | error | GDS-ERR-09 | — | `src/components/error-message/index.md` — How it works |
| `error-prefix-missing` | warning | GDS-ERR-09 | — | `src/components/error-message/index.md` — How it works |
| `error-summary-missing` | error | GDS-ERR-01 | — | `src/components/error-summary/index.md` — When to use this component |
| `error-summary-heading` | warning | GDS-ERR-02 | — | `src/components/error-summary/index.md` — How it works |
| `error-summary-position` | error | GDS-ERR-04 | — | `src/components/error-summary/index.md` — Where to put the error summary |
| `summary-link-broken` | error | GDS-ERR-03 | — | `src/components/error-summary/index.md` — Linking from the error summary to each answer |
| `summary-link-missing` | error | GDS-ERR-03 | — | `src/components/error-summary/index.md` — Linking from the error summary to each answer |
| `summary-text-mismatch` | warning | GDS-ERR-06 | — | `src/components/error-summary/index.md` — How it works |
| `title-error-prefix` | error | GDS-ERR-07 | — | `src/patterns/validation/index.md` — How to tell the user about validation errors |
| `error-wording-banned` | warning | GDS-ERR-11 | — | `src/components/error-message/index.md` — Be clear and concise |
| `error-wording-generic` | warning | GDS-ERR-12 | — | `src/components/error-message/index.md` — Be specific |
| `autocomplete-missing` | error | GDS-AC-01 | WCAG 2.2 SC 1.3.5 | `src/components/text-input/index.md` — Use the autocomplete attribute |
| `autocomplete-unexpected` | warning | GDS-AC-01 | WCAG 2.2 SC 1.3.5 | `src/components/text-input/index.md` — Use the autocomplete attribute |
| `email-input-type` | warning | GDS-AC-03 | — | `src/patterns/email-addresses/index.md` — Help users to enter a valid email address |
| `spellcheck-not-disabled` | warning | GDS-INP-06 | — | `src/components/text-input/index.md` — How and when to spellcheck a user’s input |
| `button-disabled` | warning | GDS-BTN-02 | — | `src/components/button/index.md` — Disabled buttons |
| `continue-button-next` | warning | GDS-QP-05 | — | `src/patterns/question-pages/index.md` — Continue button |
| `date-not-in-fieldset` | error | GDS-DATE-01 | — | `src/components/date-input/index.md` — How it works |
| `date-native-input` | warning | GDS-DATE-01 | — | `src/components/date-input/index.md` — How it works |
| `date-incomplete` | warning | GDS-DATE-01 | — | `src/components/date-input/index.md` — How it works |
| `form-novalidate-missing` | warning | GDS-VAL-01 | — | `src/patterns/validation/index.md` — Turn off HTML5 validation |
| `required-attribute` | warning | GDS-VAL-01 | — | `src/patterns/validation/index.md` — Turn off HTML5 validation |
| `maxlength-used` | warning | GDS-INP-05 | — | `src/components/text-input/index.md` — Avoid restricting the length of a user's input |
| `number-input-type` | warning | GDS-INP-03 | — | `src/components/text-input/index.md` — Numbers |
| `paste-blocked` | error | GDS-INP-04 | — | `src/components/text-input/index.md` — Do not disable copy and paste |
| `range-slider` | warning | GDS-QP-08 | WCAG 2.2 SC 2.5.1 | `src/patterns/question-pages/index.md` — Using range sliders |
| `html-lang-missing` | error | LOCAL-LANG-01 | WCAG 2.2 SC 3.1.1 (unverified) | library baseline (not from the extract) |
| `title-missing` | error | LOCAL-TITLE-01 | WCAG 2.2 SC 2.4.2 (unverified) | library baseline (not from the extract) |
| `img-alt-missing` | error | LOCAL-IMG-01 | WCAG 2.2 SC 1.1.1 (unverified) | library baseline (not from the extract) |
| `aria-ref-broken` | error | LOCAL-ARIA-01 | — | library baseline (not from the extract) |
| `duplicate-id` | error | LOCAL-ID-01 | — | library baseline (not from the extract) |
| `empty-document` | error | LOCAL-DOC-01 | — | library baseline (not from the extract) |

Autocomplete findings also carry `related_rule` naming the specific pattern rule:
name → GDS-AC-02, email → GDS-AC-03, phone → GDS-AC-04, date of birth → GDS-AC-05, address → GDS-AC-06,
middle name → GDS-NAME-01.

## Field purpose detection (heuristic)
Purpose is inferred from `type`, then the `name`, then the `id` attribute, split into word tokens:
`email`; `tel`/`phone`/`mobile`; `dob`/`birth`/`bday` + day/month/year; `given`/`first`, `family`/`last`/`surname`,
`middle`, exactly `name`/`full name`; `address`/`postcode`/`town`/`city`/`county`/`street`. Names containing
`dog`, `pet`, `user`, `business`, `company`, `account` are not treated as personal names. Fields the
heuristic misses are not checked — review personal-data fields manually.

## Error-state detection
Error checks run when the page contains an element with class `govuk-error-message` or `error-message`,
or a control with `aria-invalid="true"`. The error summary is an element with class `govuk-error-summary`
or `role="alert"`. Inline errors must be referenced from the field (or its fieldset) via
`aria-describedby`; for fieldsets, a summary link to any control inside the fieldset satisfies GDS-ERR-03.
Pre-selected options are only flagged on non-error pages, because re-shown pages keep the user's answers
(GDS-ERR-08).

## Testable rules not (yet) automated
GDS-ERR-08 (answers kept), GDS-QP-01/02/04/06, GDS-OPT-03/04, GDS-DATE-02, GDS-BTN-01/03, GDS-NAME-01 (title select),
GDS-PHONE-01, GDS-CYA-01, GDS-CONF-01, GDS-INP-07, GDS-AC-03 (254 characters) — review manually.
