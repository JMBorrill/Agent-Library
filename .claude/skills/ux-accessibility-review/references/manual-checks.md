# Manual accessibility checks (reference checklist)

Every item here is **MANUAL**: `html_a11y_check.py` cannot test it. Static checks catch markup
defects; they do not show whether a disabled person can complete the journey. Use this list with
the review template (`assets/templates/a11y-review.md`). WCAG success-criterion numbers below are
given from general knowledge and are marked *(unverified)* unless the gov-design extract cites them.

Source context: `gov-design` (GOV.UK Design System, VERIFIED files listed in
`sources/audits/gov-design.md`). The extract records that the Design System targets WCAG 2.2 AA and
that using its components does not by itself make a service accessible
(`src/accessibility/index.md`).

## Keyboard (MANUAL)
- [ ] Complete the whole journey with Tab, Shift+Tab, Enter, Space and arrow keys only.
- [ ] Focus is always visible and never trapped; order follows the visual order.
- [ ] After a failed submit, focus moves to the error summary (GDS-ERR-05; not statically testable).
- [ ] Error-summary links move focus to the field in error.
- [ ] No action depends on hover or drag; sliders have a non-drag alternative (GDS-QP-08, WCAG 2.2 SC 2.5.1).
- [ ] Date entry works without a JavaScript calendar (GDS-DATE-02).

## Screen readers (MANUAL)
Test at least one desktop and one mobile pairing actually used by your users (for example NVDA or
JAWS with a Windows browser, VoiceOver on iOS/macOS, TalkBack on Android). Record versions.
- [ ] Page title is announced and, on error, starts with "Error:" (GDS-ERR-07).
- [ ] Each field announces its label, hint and error message; the hidden "Error:" prefix is read (GDS-ERR-09).
- [ ] Radio/checkbox groups announce the legend (GDS-OPT-01).
- [ ] Conditionally revealed questions are announced sensibly (GDS-OPT-03 notes known issues; WCAG 2.2 SC 4.1.2).
- [ ] Dynamic updates (saved, sent, booked) are announced without moving focus unexpectedly.

## Zoom, reflow and text spacing (MANUAL)
- [ ] 200% browser zoom: no loss of content or function.
- [ ] 400% zoom on a 1280px-wide window (≈320 CSS px): content reflows to one column without
      horizontal scrolling *(WCAG 2.2 SC 1.4.10, unverified)*.
- [ ] Increased line, letter, word and paragraph spacing does not clip text *(SC 1.4.12, unverified)*.
- [ ] Mobile: works in portrait and landscape.

## Colour and contrast (MANUAL, tool-assisted)
- [ ] Body text ≥ 4.5:1, large text ≥ 3:1 *(SC 1.4.3 — cited by the gov-design extract for placeholder text)*.
- [ ] Focus indicators, input borders and icons ≥ 3:1 against adjacent colours *(SC 1.4.11, unverified)*.
- [ ] Status (booked / cancelled / needs attention) is not shown by colour alone; warning buttons do not rely on red alone (GDS-BTN-04).

## Content and cognition (MANUAL)
- [ ] One question per page where practical (GDS-QP-01); headings are unique per page (GDS-QP-06).
- [ ] Error messages are specific and use the component templates (GDS-ERR-12, -14, -15, -16).
- [ ] Error messages reuse label wording (GDS-ERR-10).
- [ ] Eligibility or capacity problems lead to an explanation page, not a field error (GDS-ERR-13).
- [ ] Time limits can be extended or are absent; session expiry warns first.
- [ ] Back button returns to the previous page with answers kept (GDS-QP-07, GDS-ERR-08).

## Validation behaviour (MANUAL, runtime)
- [ ] Errors appear on submit, not on blur (GDS-VAL-03).
- [ ] Server-side validation exists even with client-side checks (GDS-VAL-02).
- [ ] Spaces, hyphens and brackets in phone numbers and postcodes are accepted (GDS-VAL-04, GDS-ADDR-01).

## Research with disabled users (MANUAL)
- [ ] Usability sessions include people who use assistive technology and people with cognitive or
      motor impairments, recruited and paid appropriately.
- [ ] Findings are logged in the discovery evidence log (`product-discovery`) with session IDs.
