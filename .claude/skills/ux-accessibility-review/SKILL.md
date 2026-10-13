---
name: ux-accessibility-review
description: Review web forms and pages for accessibility and GOV.UK Design System form patterns - static HTML checks for labels, fieldsets and legends, error summaries and inline errors, "Error:" page titles, autocomplete on personal-data fields, placeholders, disabled buttons, date inputs, html lang and img alt, each mapped to a GDS rule ID and WCAG reference - plus a manual checklist for keyboard, screen reader, 400% zoom and contrast. Use when reviewing a prototype, template or page before release, triaging accessibility defects, or planning accessibility testing.
metadata:
  pack: ux
  version: "1.0.0"
  sources: "gov-design"
---

# UX accessibility review (forms and error handling)

## Purpose
Find accessibility and form-usability defects early — in prototypes and templates — and make clear
which checks a machine can do and which need people. The static checker encodes rules from the
GOV.UK Design System (verified repository files; see References) that can be evaluated on HTML
markup; everything else is routed to a manual checklist and to research with disabled users.
**Static checks do not replace testing with assistive technology and with real users**, and a clean
result is never a conformance claim.

## When to use
- A form, sign-up, booking or settings page is ready as HTML (prototype, template output or
  saved page) and needs review before usability testing or release.
- Triaging an accessibility bug report or preparing an accessibility review for a release.
- Writing the Accessibility section of a PRD (`product-requirements-brief`).

**Do not use when:** you need a formal WCAG conformance audit or accessibility statement (commission
a qualified auditor; this skill supports but does not replace it); the UI is native mobile or canvas
rendered (markup checks do not apply); or the page is heavily client-rendered — save the rendered
DOM first, otherwise the checker sees an empty shell.

## Inputs
- HTML file of the page in the state to review (fresh and error states are different pages — check
  both; error-state checks only run when error messages or `aria-invalid="true"` are present).
- Target standard (default WCAG 2.2 AA, as targeted by the Design System per the extract).
- Optional: user research plan and AT/browser matrix for manual testing.

## Procedure
1. **Capture pages**: save the rendered HTML for each step, including a failed-submit (error) state.
2. **Run static checks** on each:
   `python3 scripts/html_a11y_check.py page.html --json`
   Each finding gives `rule`, `source_rule` (GDS-* or LOCAL-*), `wcag` (if the extract cites one)
   and an element locator.
3. **Fix errors** (missing labels, placeholder as label, radios outside fieldset, legend not first,
   unlinked or unreferenced error messages, missing error summary, summary links to missing ids,
   title without "Error: ", missing autocomplete on name/email/phone/address/date-of-birth fields,
   blocked paste, missing lang/alt, broken ARIA references, duplicate ids).
4. **Triage warnings** with the designer: fix, or record the research that justifies the deviation
   (e.g. a disabled button supported by testing).
5. **Run the manual checklist** in [references/manual-checks.md](references/manual-checks.md):
   keyboard, focus to error summary, screen readers, 400% zoom/reflow, text spacing, contrast,
   content and validation behaviour. Mark each item pass / fail / not tested.
6. **Plan research with disabled users** and log findings as evidence (`product-discovery`).
7. **Report** with `assets/templates/a11y-review.md`: static results, manual results, open issues,
   owners, retest date.

## Decision criteria
| Situation | Rule |
|---|---|
| Any static `error` | Fix before usability testing with external participants or release |
| `warning` with a research-backed reason | Accept, record reason and owner in the review |
| Errors present but no summary, or summary after the h1 | Error (GDS-ERR-01 / GDS-ERR-04) |
| Personal-data field without autocomplete | Error (GDS-AC-01, WCAG 2.2 SC 1.3.5) |
| Static PASS, manual checks not done | Report "not tested" — never "accessible" |
| Manual check fails on keyboard or screen reader | Blocking for release regardless of static result |
| Third-party widget (payment, map) fails | Escalate to the product owner; record in accessibility statement draft |

## Outputs
- Static report (`html_a11y_check.py --json`, schema `assets/schemas/a11y-check.output.schema.json`).
- Completed review (`assets/templates/a11y-review.md`) including manual results.
- Defect tickets referencing `source_rule` and WCAG pointers.

## Validation
- `python3 scripts/html_a11y_check.py page.html --json` → exit 0 no static errors, 1 errors
  (`--strict` also fails on warnings), 2 unreadable input.
- Tests confirm every GDS rule ID used by the script exists in `sources/extracts/gov-design-rules.json`
  with `testable_in_static_html: true`, and that each WCAG reference on a GDS rule is cited by the extract.
- PASS means only that the markup avoids the checked defects. It says nothing about focus
  management, keyboard operation, AT announcements, contrast, zoom, timing, content clarity or
  whether disabled users can complete the task.

## Examples
- `assets/examples/form-pass.html` — synthetic dog-walking "Request a walk" page in an error state
  (summary before h1, linked and referenced errors, autocomplete, fieldsets) → exit 0, no findings.
- `assets/examples/form-fail.html` — exit 1 with errors `input-unlabelled`, `placeholder-as-label`,
  `options-not-in-fieldset`, `fieldset-legend-not-first`, `error-not-associated`,
  `summary-link-broken`, `summary-link-missing`, `error-summary-position`, `title-error-prefix`,
  `autocomplete-missing`, `paste-blocked`, `html-lang-missing`, `img-alt-missing`,
  `aria-ref-broken`, `duplicate-id`; warnings include `button-disabled`, `date-native-input`,
  `date-incomplete`, `required-attribute`, `form-novalidate-missing`, `error-wording-banned`,
  `error-wording-generic`, `label-asterisk`, `maxlength-used`, `number-input-type`,
  `continue-button-next`, `autocomplete-unexpected`.

## Escalation and stop conditions
- **Stop** and escalate when asked to declare a service "accessible" or "compliant", or to write an
  accessibility statement from static results alone — that needs a qualified audit and human sign-off.
- Public-sector services in the UK have legal accessibility duties (per the gov-design audit); refer
  them to their accessibility lead.
- Hand findings to `product-lead` for prioritisation and to `software-quality-reviewer` for
  verification of fixes; `independent-reviewer` challenges release readiness claims.

## References
- `gov-design` — GOV.UK Design System, repository `alphagov/govuk-design-system@main` fetched
  2026-10-13. **VERIFIED** for the files listed in `sources/audits/gov-design.md`. Rules used are the
  `testable_in_static_html` entries of `sources/extracts/gov-design-rules.json` (local IDs GDS-*,
  paraphrased; e.g. error summary `src/components/error-summary/index.md`, validation
  `src/patterns/validation/index.md`, text input `src/components/text-input/index.md`, fieldset,
  radios, date input, button, names/email/phone/address patterns). Markup-level wiring (exact class
  names, `aria-describedby` usage) was **not** verified — the example markup files were not
  downloaded — so those checks are the library's interpretation.
- LOCAL-* rules (lang, title, img alt, ARIA references, duplicate ids) are library baseline checks,
  not from the extract; their WCAG pointers are *(unverified)*.
- Rule table and checker behaviour: [references/rule-map.md](references/rule-map.md); manual
  checklist: [references/manual-checks.md](references/manual-checks.md).
