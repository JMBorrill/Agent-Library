---
name: software-code-review
description: Review a code change (pull request / CL / diff) for overall code health using Google's engineering-practices standard - design, functionality, complexity, tests, naming, comments, style, consistency, documentation, every line, context and good things - with labelled findings (Required/Nit/Optional/FYI), file:line references and an explicit decision. Use when reviewing a PR or diff, triaging an oversized change, writing review comments, or checking that a review record is complete; includes a diff risk scanner (size, missing tests, secrets, swallowed exceptions, debug output, TODOs, commented-out code, long functions).
metadata:
  pack: software
  version: "2.0.0"
  sources: "google-review"
---

# Code review for code health

## Purpose
Give a decision on a code change that is fast, explained and consistent: approve once the change
clearly improves the overall health of the codebase, even if it is not perfect, and record every
finding with a severity label, a `file:line` location and the reason, so the author knows exactly
what must change before merge and what is optional.

## When to use
- Reviewing a pull request, changelist (CL) or patch you have been asked to review.
- Deciding whether to ask for an oversized change to be split.
- Pre-screening a diff for mechanical risk signals before spending human attention.
- Auditing a review record (for an independent reviewer or a release gate).

**Do not use when:** you need a security assessment (use `security-code-checks` for a screen, then
`security-threat-model` / the `security-reviewer` agent); you need requirement-to-test evidence (use
`software-requirements-traceability`); or you are the author reviewing your own change — a review
needs a second person.

## Inputs
Required
- The diff (unified format, e.g. `git diff --unified`) and access to the surrounding files.
- The change description (first line + body) and any linked issue/requirement IDs.
Optional
- Team style guide, previous review threads, CI/test results, design doc.
- Review report in `assets/templates/review-report.json` or `assets/templates/review-report.md`.

## Procedure
1. **Pre-screen the diff** (mechanical signals only):
   `python3 scripts/diff_risk_scan.py change.diff`
   Treat every `error` (secret pattern, swallowed exception, > 1000 changed lines) as a question
   the review must answer. If it reports `cl-too-large`, ask the author to split before a line review
   (stacked, by files, horizontally by layer, or vertically by feature; refactorings separately).
2. **Take a broad view.** Read the description: does the change make sense, is it one
   self-contained thing, is now the right time? If the direction is wrong, say so immediately and
   courteously, with an alternative — do not line-review a change that should not exist.
3. **Review the main part first.** Find the file(s) with the core logic and look at design before
   detail. Send major design comments straight away so the author is not polishing doomed code.
4. **Go through the rest in a sensible order** (reading tests first often helps). Read every
   human-written line assigned to you, with enough surrounding context to understand it. If you
   are not qualified for a part (security, privacy, concurrency, accessibility, i18n), say so and
   name who should review it.
5. **Apply the aspects** to what you read: design, functionality (edge cases, concurrency, user
   impact), complexity (incl. speculative over-engineering), tests (present, would fail when broken,
   maintainable), naming, comments (explain why), style (guide is authoritative; preferences are
   Nits), consistency, documentation, every line, context (whole file/system), good things.
   See [references/review-method.md](references/review-method.md) for the question list.
6. **Write findings** — one per issue, each with: label, aspect, `file:line`, what and *why*.
   Labels: unlabelled/`Required` = must change before merge; `Nit` = minor polish, author may
   skip; `Optional` (or `Consider`) = suggestion; `FYI` = for the future. Comment on the code,
   never the person; give guidance, but fixing is the author's job.
7. **Decide** using the decision criteria below and record it as `Decision: <value>`.
8. **Check the record** before sending: `python3 scripts/review_report_check.py review.md`
   (or `.json`). Fix every error.
9. **Respond quickly**: aim to respond within one business day of the request (source heuristic);
   individual response time matters more than total cycle time.

## Decision criteria
| Situation | Decision |
|---|---|
| Change improves overall code health; only Nit/Optional/FYI remain | `lgtm` |
| Remaining required points are small, you trust the author to make them and no re-review is needed | `lgtm-with-comments` |
| Any open Required finding that needs re-review, or tests missing for changed behaviour | `request-changes` |
| Design disagreement not resolved by facts/style guide after discussion | `escalate` (tech lead / maintainer), record outcome on the change |
| Change degrades code health | `request-changes` — never accept it except in a genuine emergency |
| Size > ~1000 changed lines or many unrelated files | ask to split (source heuristic: ~100 lines usually fine) |
| "Will clean up later" | insist on cleanup now unless emergency; otherwise require a tracked issue |
| Emergency fix (prod incident, major security hole) | review for safety now, full re-review afterwards |

Thresholds above are heuristics from the source, not hard limits; `--small-lines`, `--large-lines`,
`--max-files` and `--max-function-lines` make them configurable (the last two are library defaults).

## Outputs
- `code-review.md` or `.json` — template `assets/templates/review-report.md` / `.json`; JSON schema
  `assets/schemas/review-report.schema.json`.
- Diff scan report — `diff_risk_scan.py --json`, schema `assets/schemas/findings-report.schema.json`.
- Optional `regression-test-plan.md` listing tests the author should add (from Required test findings).

## Validation
- `python3 scripts/diff_risk_scan.py change.diff --json` → exit 0 = no blocking mechanical signals;
  `--strict` also blocks on warnings. Exit 2 = unreadable/malformed diff.
- `python3 scripts/review_report_check.py review.md --json` → exit 0 = the record has a decision,
  labelled findings with `file:line`, and no decision/finding contradiction.
- PASS does **not** mean the code is correct, secure or well designed, nor that the review was
  thorough. The scanner sees only added lines and simple patterns; it misses most real defects and can
  flag false positives (e.g. a print in a CLI). The secret patterns never prove a credential is real
  or absent.

## Examples
- `assets/examples/pr-pass.diff` — small tenant-scoping fix with a test → exit 0.
- `assets/examples/pr-fail.diff` — booking service with fake keys (`AKIAFAKEFAKEFAKEFAKE`,
  `sk-FAKE-...`), bare `except: pass`, empty `catch {}`, `print`/`console.log`, TODO without issue,
  commented-out code, a 76-line function and no tests → exit 1 (`hardcoded-secret`,
  `swallowed-exception`, `no-test-changes`, `debug-output`, `todo-without-issue`,
  `commented-out-code`, `long-function`).
- `assets/examples/review-pass.json`, `assets/examples/review-pass.md` → exit 0.
- `assets/examples/review-fail.md` → exit 1 (`missing-decision`, `bad-location`,
  `missing-severity-label`; warnings `comment-targets-person`, `unknown-aspect`).

## Escalation and stop conditions
- **Stop and escalate** when a secret pattern looks real (rotate it; treat the repo history as
  exposed) or when the change touches authentication, authorisation, tenant isolation, payments or
  personal data — hand to the `security-reviewer` agent.
- Unresolved disagreement after discussion → meeting/call, record the outcome on the change, then
  tech lead or maintainer. Do not let a change stall silently.
- Use the `software-quality-reviewer` agent for routine reviews; `independent-reviewer` for
  challenge reviews of high-risk changes. Reviewers report findings; they do not rewrite the change.

## References
- `google-review` — Google Engineering Practices Documentation (google/eng-practices, branch
  `master`, read 2026-10-13): `review/reviewer/standard.md` (The Standard of Code Review),
  `looking-for.md` (12 aspects), `navigate.md`, `comments.md` (Label comment severity), `speed.md`,
  `pushback.md`, `review/developer/small-cls.md`, `cl-descriptions.md`, `review/emergencies.md`.
  Verified: see `sources/audits/google-review.md`. Source ID: `google-review`.
- Attribution: adapted (paraphrased and restructured, with added scripts and thresholds marked as
  library defaults) from *Google Engineering Practices Documentation*, © Google, licensed
  CC BY 3.0 (https://creativecommons.org/licenses/by/3.0/). Changes were made.
- The `security` aspect value and the scanner rules are library additions, not from the source.
- Method notes: [references/review-method.md](references/review-method.md).
