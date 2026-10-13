# Source audit: `google-review`

| Field | Value |
|---|---|
| Source ID | `google-review` |
| Title (as verified) | Google Engineering Practices Documentation — "Google's Code Review Guidelines" (The Code Reviewer's Guide "How to do a code review"; "The CL author's guide to getting through code review") |
| Publisher / author | Google (repository `google/eng-practices`) |
| Edition / version / effective date | Living document; no version number. Read from branch `master` on 2026-10-13 (no commit SHA captured — GitHub API blocked) |
| Canonical URL (registry) | https://google.github.io/eng-practices/ |
| URL(s) actually read | `https://raw.githubusercontent.com/google/eng-practices/master/<path>` for the paths listed in the access ledger |
| Access status | VERIFIED (for the 15 files listed) |
| Access method | Official GitHub repository raw files via curl (raw.githubusercontent.com). The registry URL (google.github.io) was not fetched — proxy blocks it |
| Date checked | 2026-10-13 |
| Licence / reuse terms (as verified) | CC BY 3.0 (Creative Commons Attribution 3.0 Unported). `LICENSE` is the CC Attribution 3.0 Unported legal code; `README.md` § "License" says the documents are licensed under CC-By 3.0. Adaptations need attribution and indication of changes |
| Normative status | Advisory (Google's internal canonical policy per `review/index.md`, but advisory guidance for any other organisation) |

## Access ledger
Base: `https://raw.githubusercontent.com/google/eng-practices/master/`

| Path | Result |
|---|---|
| `README.md` | 200, read |
| `LICENSE` | 200, read (header and licence identity) |
| `review/index.md` | 200, read |
| `review/emergencies.md` | 200, read |
| `review/reviewer/index.md` | 200, read |
| `review/reviewer/standard.md` | 200, read |
| `review/reviewer/looking-for.md` | 200, read |
| `review/reviewer/navigate.md` | 200, read |
| `review/reviewer/speed.md` | 200, read |
| `review/reviewer/comments.md` | 200, read |
| `review/reviewer/pushback.md` | 200, read |
| `review/developer/index.md` | 200, read |
| `review/developer/small-cls.md` | 200, read |
| `review/developer/cl-descriptions.md` | 200, read (headings and guidance; example blocks skimmed) |
| `review/developer/handling-comments.md` | 200, read |
| `review/developer/review-tools.md` | 404 (guessed path; does not exist) |

Not attempted / failed: `google.github.io/eng-practices` (proxy blocks the domain); GitHub API for the commit SHA (blocked).

## Verified content
- **Terminology** — `README.md` § "Terminology": CL = changelist (one self-contained change); LGTM = "Looks Good to Me", the approval.
- **Overview checklist** — `review/index.md` § "What Do Code Reviewers Look For?": Design, Functionality, Complexity, Tests, Naming, Comments, Style, Documentation. Also § "Picking the Best Reviewers" and § "In-Person Reviews (and Pair Programming)" (pair-programmed code with a qualified peer counts as reviewed).
- **The standard** — `review/reviewer/standard.md` § "The Standard of Code Review": the senior principle is to favour approval once a CL definitely improves overall code health even if it isn't perfect; no perfect code, only better code; mark unimportant polish with "Nit:". Sub-sections "Mentoring", "Principles" (facts over opinions; style guide is the absolute authority on style; design is rarely pure preference; else be consistent with codebase), "Resolving Conflicts" (consensus, then meeting/video call with result recorded on the CL, then escalation; don't let a CL sit).
- **What to look for** — `review/reviewer/looking-for.md` headings: "Design", "Functionality", "Complexity" (incl. over-engineering), "Tests", "Naming", "Comments", "Style", "Consistency", "Documentation", "Every Line" (with "Exceptions"), "Context", "Good Things", "Summary".
- **Navigation** — `review/reviewer/navigate.md`: "Step One: Take a broad view of the change", "Step Two: Examine the main parts of the CL" (send major design comments immediately), "Step Three: Look through the rest of the CL in an appropriate sequence".
- **Speed** — `review/reviewer/speed.md`: "Why Should Code Reviews Be Fast?" (team velocity), "How Fast Should Code Reviews Be?" (one business day maximum to respond), "Speed vs. Interruption" (don't break focus), "Fast Responses" (individual response time matters most), "Cross-Time-Zone Reviews", "LGTM With Comments" (three qualifying conditions), "Large CLs" (ask to split; otherwise give design comments), "Code Review Improvements Over Time", "Emergencies".
- **Comments** — `review/reviewer/comments.md`: "Courtesy" (comment on code, not the developer), "Explain Why", "Giving Guidance" (fixing is the developer's job), "Label comment severity" with labels **Nit**, **Optional (or Consider)**, **FYI**, "Accepting Explanations" (explanations should usually become clearer code, not review-tool replies).
- **Pushback** — `review/reviewer/pushback.md`: "Who is right?", "Upsetting Developers", "Cleaning It Up Later" (insist on cleanup now unless emergency; file a bug otherwise), "General Complaints About Strictness", "Resolving Conflicts".
- **Emergencies** — `review/emergencies.md`: "What Is An Emergency?", "What Is NOT An Emergency?", "What Is a Hard Deadline?".
- **Small CLs** — `review/developer/small-cls.md`: "Why Write Small CLs?", "What is Small?" (one self-contained change; ~100 lines usually reasonable, ~1000 usually too large; file count matters; reviewers may reject for size alone), "When are Large CLs Okay?", "Writing Small CLs Efficiently", "Splitting CLs" (Stacking; by Files; Horizontally; Vertically; Horizontally & Vertically), "Separate Out Refactorings", "Keep related test code in the same CL", "Don't Break the Build", "Can't Make it Small Enough".
- **CL descriptions** — `review/developer/cl-descriptions.md`: "First Line" (short, standalone, imperative, blank line after), "Body is Informative", "Bad CL Descriptions", "Good CL Descriptions", "Using tags", "Generated CL descriptions", "Review the description before submitting the CL".
- **Handling comments** — `review/developer/handling-comments.md`: "Don't Take it Personally", "Fix the Code", "Think Collaboratively", "Resolving Conflicts".
- **Licence** — `LICENSE` (Attribution 3.0 Unported) and `README.md` § "License".

Machine-readable extract: `sources/extracts/google-review-guidance.json`.

## Secondary corroboration (not primary verification)
None used. The published site (google.github.io/eng-practices) is generated from this repo but was not fetched.

## Elements useful as AI skills
- Approval decision rule (code-health improvement, not perfection) — `review/reviewer/standard.md`.
- 12-aspect review checklist and summary bullets — `review/reviewer/looking-for.md`.
- Three-step review order with early design feedback — `review/reviewer/navigate.md`.
- Severity labelling of findings (Nit / Optional / FYI; unlabelled = required) — `review/reviewer/comments.md` § "Label comment severity".
- Comment-writing rubric (courtesy, explain why, guidance balance) — `review/reviewer/comments.md`.
- Size/split heuristics and split strategies — `review/developer/small-cls.md`.
- CL description check (first line + body; bad examples) — `review/developer/cl-descriptions.md`.
- Emergency classification test — `review/emergencies.md`.
- Escalation ladder for disagreements — `review/reviewer/standard.md` § "Resolving Conflicts".
- Response-time SLO (≤ 1 business day) and LGTM-with-comments conditions — `review/reviewer/speed.md`.

## Proposed skills, agents and tools
- `software-review` (existing, `.claude/skills/software-review`) and planned `software-code-review`, `software-maintainability` (per `sources/framework-build-plan.json`); agent: Software quality reviewer.
- Tools: a findings schema with `aspect` (enum from the 12 aspects) and `severity` (required / Nit / Optional / FYI); a CL-description linter (first line length/imperative/blank line; flags the "bad" pattern list); a diff-size heuristic flag (lines and files) citing `small-cls.md`; evaluation fixture: intentionally flawed PR.

## Limitations, applicability and copyright
- Google-specific context (g3doc, OWNERS files, Google style guides, Google-internal tooling) — treat these as examples; adapt for other organisations.
- Thresholds (100/1000 lines, one business day) are explicitly heuristics, not hard rules.
- Unversioned living document on `master`; commit SHA not captured. Re-pin when possible.
- CC BY 3.0: attribution required; indicate changes. Paraphrases only in this library; headings quoted.

## Re-check by
2027-04-13 — re-read `review/reviewer/*.md` and `review/developer/*.md` on `master` for changes (especially comment labels and small-CL thresholds); capture commit SHA; confirm LICENSE unchanged.
