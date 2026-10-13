# Accessibility review — <page / journey>

Date: <YYYY-MM-DD> · Reviewer: <name> · Build/commit: <ref> · Target: WCAG 2.2 AA (confirm)

## 1. Static checks (automated)
Command: `python3 scripts/html_a11y_check.py <page.html> --json`
Result: <PASS/FAIL, n errors, n warnings>

| Finding | Source rule | WCAG | Decision (fix / accepted with reason) | Owner |
|---|---|---|---|---|
| | | | | |

## 2. Manual checks (MANUAL — not covered by the script)
See `references/manual-checks.md`. Record each as pass / fail / not tested, with device, browser and AT version.

| Check | Result | Notes / evidence |
|---|---|---|
| Keyboard-only journey | | |
| Focus moves to error summary on submit | | |
| Screen reader (name, AT, browser) | | |
| Zoom 400% / reflow at 320 CSS px | | |
| Text spacing | | |
| Colour contrast (text, focus, non-text) | | |
| Plain language / error message wording | | |

## 3. Research with disabled users
Planned / completed sessions: <n, needs represented>

## 4. Summary for the product owner
Blocking issues · Accepted risks (with sign-off) · Retest date.
Static PASS is not a conformance claim.
