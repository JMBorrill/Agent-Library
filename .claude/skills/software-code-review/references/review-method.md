# Code review method notes

Original wording for this library, paraphrasing *Google Engineering Practices Documentation*
(google/eng-practices, CC BY 3.0, © Google; changes made). Headings of the source are named so a
reader can find the original; no passages are reproduced. Verification: `sources/audits/google-review.md`.

## The standard (review/reviewer/standard.md)
- The goal is continuous improvement of code health, not perfection. Approve once the change
  definitely makes the codebase better overall, even if you would have written it differently.
- Technical facts and data beat opinions and personal preference. The style guide is the
  authority on style; anything not in it is a preference (mark it `Nit`) — or, absent other rules,
  follow the existing codebase.
- Design questions are rarely pure preference: weigh them on engineering principles.
- Conflicts: aim for consensus; then a conversation (record the outcome on the change); then
  escalate. A change should not sit blocked because reviewer and author disagree.

## Question list per aspect (review/reviewer/looking-for.md)
| Aspect | Questions to ask |
|---|---|
| Design | Do the parts interact sensibly? Does this belong in this codebase or a library? Is now the right time? |
| Functionality | Does it do what the author intends, and is that good for users and future developers? Edge cases, concurrency, races, UI behaviour? |
| Complexity | Can a reader understand each line/function/class quickly? Is anything easy to misuse? Is it solving a speculative future problem? |
| Tests | Are there unit/integration/end-to-end tests in the same change? Would they fail if the code broke? Are they simple and maintainable? |
| Naming | Does each name convey what the thing is/does without being unreadably long? |
| Comments | Do comments explain *why* rather than *what*? Could the code be made clearer instead? |
| Style | Does it follow the style guide? Is large reformatting separated into its own change? |
| Consistency | Where the guide is silent, is it consistent with the surrounding code? |
| Documentation | If build, test, use or release behaviour changes, are docs updated (or removed)? |
| Every line | Have you read every human-written line you were assigned? Do you understand it? Who covers parts you are not qualified for? |
| Context | Seen in the whole file/system, does the change improve or degrade health? |
| Good things | What did the author do well? Say so. |

## Navigation (review/reviewer/navigate.md)
1. Broad view: description and overall shape. Reject a wrong direction early, with an alternative.
2. Main part first; send major design comments immediately.
3. The rest in a sensible order (tests first can help).

## Comments (review/reviewer/comments.md)
- Courteous, about the code. Explain the reason. Balance pointing out problems with guidance;
  fixing is the author's responsibility.
- Labels: `Nit` (minor), `Optional`/`Consider` (suggestion), `FYI` (future). Unlabelled = required.
  This library writes `Required` explicitly so a script can count open required findings.
- An explanation given only in the review thread usually means the code should be clearer.

## Size and speed (review/developer/small-cls.md, review/reviewer/speed.md)
- One self-contained change, with its tests, leaving the system working. Around 100 lines is usually
  reasonable and around 1000 usually too large; spread across many files also counts. These are
  heuristics, and reviewers may decline a change for size alone.
- Respond within one business day at most; do not break your own focus to do so. LGTM-with-comments
  is for cases where the reviewer trusts the author to address the remaining points.

## What the scripts add (library-original)
`diff_risk_scan.py` rules (none are from the source except the size heuristics):

| Rule | Severity | Why |
|---|---|---|
| `cl-too-large` / `cl-size-medium` / `many-files` | error / info / warning | Size heuristics above |
| `no-test-changes` | warning | Tests aspect: behaviour changes should come with tests |
| `hardcoded-secret` | error | Credential in source control; rotate if real |
| `swallowed-exception` | error | Silently hides failures (functionality) |
| `debug-output` | warning | Leftover print/console/debugger in non-test code |
| `todo-without-issue` | warning | "Clean up later" must be tracked |
| `commented-out-code` | warning | Dead code; version control keeps history |
| `long-function` | warning | Complexity; default limit 60 non-blank lines (library default) |

Known limitations: only added lines are scanned; Python function length uses indentation, other
languages brace counting within a contiguous added block; secret patterns are illustrative, not a
substitute for a dedicated secret scanner.
