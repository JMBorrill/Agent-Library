# Library authoring conventions

These rules are enforced by `scripts/validate_library.py` and the test suite. They exist so that every
skill is portable (open Agent Skills spec), context-efficient, deterministic where possible and honest
about its evidence.

## 1. Skill directory layout

```
.claude/skills/<skill-name>/
├── SKILL.md              # required; < 500 lines; procedure, not an essay
├── references/           # optional; long-form notes loaded only on demand (one level deep)
├── scripts/              # optional; stdlib-only Python 3.10+ tools
└── assets/
    ├── templates/        # blank CSV/Markdown/JSON templates users fill in
    ├── schemas/          # JSON Schemas for structured inputs/outputs
    └── examples/         # worked examples; files named *pass* / *fail* double as test fixtures
```

Skills live in `.claude/skills/` so Claude Code discovers them when this repository is opened. Because
they only use spec fields they can be copied unchanged to any Agent Skills-compatible tool
(`scripts/install_packs.py --skills-dir`).

## 2. `SKILL.md` frontmatter (spec fields only)

```yaml
---
name: se-requirements                 # = directory name; [a-z0-9-], no leading/trailing/double hyphen, ≤64
description: Draft and lint traceable requirements... Use when ...   # one line; no YAML block scalars
metadata:
  pack: systems-engineering            # must exist in packs/packs.json
  version: "1.0.0"                     # semver of the skill
  sources: "nasa-se-design nasa-se-manage"   # space-separated source IDs from sources/registry.json
---
```

* `description` ≤ 1024 characters, single line, states **what** and **when** with trigger keywords; first
  clause carries the key use case (Claude Code truncates listings at 1,536 chars including `when_to_use`).
* Only `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools` are permitted.
  Claude-Code-only keys (`context`, `disable-model-invocation`, ...) break claude.ai / Skills API upload.
* `metadata` values are strings. `sources` must resolve in the registry. The *verification status* of a
  source is held once, in the registry, never re-asserted in the skill.

## 3. `SKILL.md` body — required sections (in this order)

| Heading | Content |
|---|---|
| `## Purpose` | One paragraph: the professional outcome. |
| `## When to use` | Activation triggers **and** a "Do not use when" list. |
| `## Inputs` | Required and optional inputs, with file formats. |
| `## Procedure` | Numbered, executable steps. Name the script to run at each deterministic step. |
| `## Decision criteria` | Explicit thresholds/rules for choices (e.g. when to escalate, how to pick a method). |
| `## Outputs` | Artifacts produced, their template/schema paths. |
| `## Validation` | Exact commands; what PASS does **and does not** mean. |
| `## Examples` | Pointers to `assets/examples/` (pass and fail) with expected results. |
| `## Escalation and stop conditions` | When to stop, ask a human, or hand off to which agent. |
| `## References` | Source IDs, the specific sections relied on, and their verification status pointer (`sources/audits/<id>.md`). |

Write procedures in original wording. Never paste long passages from sources. Mark any section number
that has not been verified against the primary source in this repository's audits as *(unverified)*.

## 4. Scripts

* Python ≥ 3.10, **standard library only**, self-contained (a skill must work when copied alone).
* `main(argv: list[str] | None = None) -> int`; importable pure functions for tests.
* Exit codes: `0` = no blocking findings, `1` = blocking findings, `2` = usage / unreadable input.
* `--json` flag emits machine-readable output (validated by `assets/schemas/*.output.schema.json` where
  defined). Human output ends with a one-line *scope note* (e.g. "Structural check only; not engineering
  approval").
* Findings use severities `error` (blocks), `warning` (needs judgement), `info`.
* Deterministic: no network, no randomness without a fixed seed, no wall-clock dependence unless a
  `--as-of` date is accepted.

## 5. Agents (`.claude/agents/<name>.md`)

Frontmatter: `name`, `description`, `tools` (explicit allowlist — never omitted), optional
`disallowedTools`, `model`, `skills` (preload only the 1–3 core skills; preloading copies full skill text
into context), `color`. Body sections required:

`## Responsibility`, `## Skills`, `## Boundaries` (non-goals), `## Collaboration and handoff`,
`## Evidence and reporting`, `## Human approval required`.

Reviewer agents (`*-reviewer`) must not have `Write` or `Edit`; they report, they do not fix.

## 6. Status vocabularies

Source access (`sources/registry.json` → `access_status`): `VERIFIED`, `PARTIALLY_VERIFIED`,
`INACCESSIBLE`, `UNVERIFIED`.

Capability coverage (computed by `scripts/coverage_report.py`, never hand-claimed):
`mapped` → `implemented` (skill + script/template present) → `tested` (unit tests + pass and fail fixture)
→ `human_review_pending` (always true until a named expert signs off) / `blocked`.

Artifact statuses: requirements `proposed | approved | retired`; results
`not_tested | pass | fail | blocked`; gate recommendations `GO | GO_WITH_CONDITIONS | NO_GO` —
a recommendation, never an approval.

## 7. Identifiers

* Requirements: `<PROJECT>-<LEVEL>-<NNN>` (e.g. `ASTER-SYS-001`, `MCP-SW-014`). Regex
  `^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-[0-9]{3,}$`. Never reuse a retired ID.
* Verification activities `<PROJECT>-VER-<NNN>`, validation `<PROJECT>-VAL-<NNN>`, interfaces
  `<PROJECT>-IF-<NNN>`, risks `<PROJECT>-RSK-<NNN>`, changes `<PROJECT>-CR-<NNN>`, decisions
  `<PROJECT>-DEC-<NNN>`.
* External control IDs are version-qualified: `ASVS-v5.0.0-1.2.5`, `SSDF-v1.1-PW.7`, `AIRMF-1.0-MAP-1.1`.

## 8. Honesty rules (tested)

`.claude/skills/independent-review/scripts/claim_check.py` flags assurance language ("compliant", "certified",
"approved", "qualified", "guaranteed", "passes NASA") that is not accompanied by a recorded human
sign-off. Demonstration outputs are run through it in CI.
