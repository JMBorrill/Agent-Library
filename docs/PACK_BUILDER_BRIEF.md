# Brief for building a skill pack (used by humans and builder agents)

Read first: `docs/CONVENTIONS.md`, the exemplar skill `.claude/skills/se-requirements/` (SKILL.md,
`scripts/req_lint.py`, `assets/`, `references/`) and its test `tests/test_se_requirements.py`,
`tests/helpers.py`, `docs/crosswalks/README.md`, `packs/packs.json`, `sources/registry.json`, and the
audit for each of your sources in `sources/audits/<id>.md` plus any `sources/extracts/*` for them.

## What "done" means for each skill
1. `SKILL.md` with the ten required sections, spec-only frontmatter, `metadata.pack` = the pack named
   in `packs/packs.json`, `metadata.sources` = registry IDs, `metadata.version` semver. < 500 lines
   (aim 80–180). Practical, decision-oriented procedure; not an essay.
2. At least one deterministic stdlib-only script in `scripts/` whenever *any* part of the method can be
   computed or checked (calculations, register linting, coverage, policy evaluation). Pure functions +
   `main(argv)`; exit 0/1/2; `--json`; scope note line.
3. `assets/templates/` (blank inputs), `assets/schemas/` (JSON Schema for JSON inputs/outputs where
   used), `assets/examples/` with at least one `*pass*` and one `*fail*` fixture (synthetic data only).
4. `tests/test_<skill_name_with_underscores>.py` (unittest, using `tests.helpers`), covering: pass
   fixture → exit 0; fail fixture → exit 1 with specific expected rule IDs; known-answer numeric tests
   (hand-computed values, tolerances stated) for calculators; edge cases (zero/negative denominators,
   empty input, malformed rows → exit 2 or explicit error finding); JSON output validated against schema
   where one exists.
5. `references/*.md` for longer method notes (original wording; attribute sources; no long quotations).

## Source honesty (hard rules)
- Check `sources/audits/<id>.md` for the access status. If the primary source was INACCESSIBLE in this
  environment, you may still build the skill from well-established public knowledge of the method,
  but every section number, control ID, rate or date taken from memory must be marked
  *(unverified)* in SKILL.md/references, and crosswalk rows must use `"source_verification": "unverified"`.
- Never claim to have read a document you did not read. Never invent clause numbers or quotes.
- Regulatory/financial/safety outputs are decision *support*: no script may output "approved",
  "compliant" or a credit decision. Use `refer`, `recommend`, `requires human sign-off`.

## Crosswalk
Write `docs/crosswalks/<source-id>.json` for each source you own (format in `docs/crosswalks/README.md`),
mapping the source's main elements to your skills, the agents named in `packs/packs.json`, artifacts and
test files that exist.

## Do NOT edit
`packs/packs.json`, `sources/registry.json`, `sources/audits/*`, `scripts/*`, `tests/helpers.py`,
`.claude/agents/*`, or any skill/test you were not assigned. If you need a change there, say so in your
final report.

## Self-check before finishing
```
python3 scripts/validate_library.py --filter "skill <name>" [--filter ...] --filter crosswalks/<id>
python3 -m unittest tests.test_<name> -v
```
Errors about agents not existing yet in crosswalks are expected (the lead creates agents); everything
else must be clean. Report: skills built, scripts, test counts and results (paste the final unittest
line), known limitations, any requested changes to shared files.
