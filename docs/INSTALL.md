# Installation and project integration

The library is modular: use the whole repository, install selected packs into a project, or copy single
skills into any tool that supports the open Agent Skills format. Requirements: Python ≥ 3.10, no
third-party packages (optional `requirements-dev.txt` only adds schema/YAML cross-checks for tests).

## Option A — open the library itself in Claude Code
```
git clone <your fork of this repository> agent-library && cd agent-library
python3 scripts/run_all_checks.py          # structure, catalogue sync, tests, demo reproduction
claude                                     # skills in .claude/skills and agents in .claude/agents are discovered
```
Ask, for example: *"Use the select-frameworks skill on this project description: … then propose the
install plan."*

## Option B — install selected capabilities into an existing project (recommended)
1. **Describe the project** in a profile (template:
   `.claude/skills/select-frameworks/assets/templates/project-profile.json`).
2. **Get a justified selection**:
   ```
   python3 .claude/skills/select-frameworks/scripts/select_frameworks.py my-profile.json --markdown > framework-selection.md
   ```
   Review selected *and* excluded packs with the project owner; adjust flags if wrong.
3. **Dry-run the install** (nothing is written):
   ```
   python3 scripts/install_packs.py --target /path/to/project --skills a,b,c --agents x,y
   # or by pack:  --packs systems-engineering,space-engineering
   ```
   Each item shows `CREATE`, `SKIP` (identical already present) or `CONFLICT` (a different file exists).
4. **Apply**: add `--apply`. If any conflict exists the installer refuses and writes nothing. To replace
   conflicting items deliberately, add `--overwrite`; originals are copied to
   `<project>/.agent-library-backup/<UTC timestamp>/` first.
5. The installer records what it installed (with SHA-256 hashes and library `VERSION`) in
   `<project>/.claude/agent-library.lock.json`. It never edits `settings.json`, `CLAUDE.md` or
   `AGENTS.md`, never installs to `~/.claude`, and makes no network calls.
6. Optionally append the operating rules from this repository's `CLAUDE.md` to your project's
   `CLAUDE.md` by hand.

Agents automatically pull in the skills they reference (reported as notes). Scripts inside installed
skills run from the project with `python3 .claude/skills/<skill>/scripts/<script>.py ...`.

## Option C — other Agent Skills-compatible tools
Skills use only spec frontmatter (`name`, `description`, `metadata`, optional `license`), so they are
portable. Install skills without Claude-specific agents into any directory:
```
python3 scripts/install_packs.py --target /path/to/project --packs ai-governance --no-agents --skills-dir .agents/skills --apply
```
Agent definitions in `.claude/agents/` are Claude Code subagent files; for other tools, use their body
text as role instructions and keep the tool restrictions (reviewers read-only).

Uploading to claude.ai or the Skills API: zip a single skill directory; no non-spec keys are present.

## Updating
Re-run the same install command: identical items are skipped, changed library items show as
`CONFLICT` if you modified them locally (your edits are protected unless you choose `--overwrite`).

## Recommended development and review workflow (all projects)
1. **Frame and tailor** — `select-frameworks`; engineering projects add `se-technical-planning`.
2. **Define** — needs/discovery, then requirements or PRD; lint them.
3. **Design and analyse** — trades/decisions, threat model, oversight design, budgets.
4. **Build and verify** — V&V matrix, code review, security checks, AI evals.
5. **Independent review and gates** — `independent-review` + domain reviewer agents; `se-review-gates`.
6. **Release/transition/operate** — readiness, SLOs, incident response, transition package.
Human authorities named in the selection output make every gate, risk-acceptance, regulatory and
deployment decision.

## Maintaining the library
```
python3 scripts/validate_library.py        # structure
python3 scripts/build_catalog.py           # after changing skills/agents/packs (updates router + capability guide)
python3 scripts/coverage_report.py --run-tests --write
python3 scripts/source_freshness.py        # which sources need re-checking
python3 examples/run_demos.py              # regenerate demo outputs after intentional changes
```
New skills follow `docs/CONVENTIONS.md` and `docs/PACK_BUILDER_BRIEF.md`.
