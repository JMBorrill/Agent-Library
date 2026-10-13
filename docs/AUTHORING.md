# Authoring guide (component contract)

Every component in this library is validated by `python -m agentlib validate`
and tested by `pytest`. This page is the contract those validators enforce.

## Repository layout

```
.claude-plugin/          plugin.json + marketplace.json (install as a Claude Code plugin)
skills/<name>/           Agent Skills (SKILL.md + references/ + templates/ + scripts/)
agents/<name>.md         Claude Code subagents (system prompts)
commands/<name>.md       Slash commands that launch workflows
workflows/<id>.yaml      Structured multi-stage workflows (schemas/workflow.schema.json)
templates/               Cross-cutting artefact templates used by workflows
catalog/<id>.json        Machine-readable framework catalogs extracted from sources/pdfs
agentlib/                Python package: validators, registry, evals, framework tools
agentlib/frameworks/     One module per framework; deterministic tools + CLI sub-commands
evals/<skill>/           Evaluation suite per skill (cases.yaml, golden/, fixtures/)
tests/                   pytest suite
schemas/                 JSON Schemas for front matter, workflows and catalogs
sources/                 Pinned official PDFs + provenance manifest
```

## Skills (`skills/<name>/SKILL.md`)

Follows the Anthropic Agent Skills format: YAML front matter then Markdown.

```yaml
---
name: green-book-appraisal            # kebab-case, equals directory name, <= 64 chars
description: >-                       # 60-1024 chars; WHAT it does and "Use when ..."
  Structures and quality-checks UK public-sector economic appraisals ... Use when ...
metadata:
  version: 1.0.0                      # semver
  category: economic-appraisal        # see schemas/skill-frontmatter.schema.json
  maturity: beta                      # draft | beta | stable
  sources: [treasury-green]           # ids from sources/pdf-manifest.json
  catalogs: [green-book]              # optional; files in catalog/
  tools: ["python -m agentlib greenbook npv"]   # optional; deterministic helpers
---
```

Only the portable keys `name`, `description`, `license`, `compatibility`, `metadata` and
`allowed-tools` are allowed, so skills also upload to claude.ai and the Skills API (other keys such as
`argument-hint` or `model` are hard errors there). Library metadata goes under `metadata`.

Required `##` sections in the body (prefix match, any order):
`When to use`, `Workflow`, `Outputs`, `Sources`, `Limitations`.

Rules:

* Keep `SKILL.md` under 500 lines. Put depth in `references/*.md` and link to
  them with relative links (links are checked).
* Every source id in `metadata.sources` must be cited in `## Sources` with
  edition and the sections/pages relied on (PDF page numbers, plus printed
  page where it differs).
* Paraphrase. Quote standards text only where exact wording matters (e.g. a
  requirement statement) and keep quotes short. Never invent clause numbers,
  requirement IDs, thresholds or page numbers — if something was not verified
  in the source, say so.
* Tell the model to run deterministic tools (`python -m agentlib ...`) for
  calculations and checklist generation rather than computing in its head.
* `## Limitations` must state that output supports, but does not replace,
  qualified professional judgement or formal assurance/approval.

## Catalogs (`catalog/<id>.json`)

Machine-readable extracts that make tools deterministic. Schema:
`schemas/catalog.schema.json`. Each item carries a `citation.pdf_page` that the
validator range-checks against the pinned PDF. Record `extraction.method`,
`fidelity` (`verbatim`, `verbatim-normalised-whitespace`, `paraphrased`,
`structural`) and the pages reviewed. Extraction scripts live in
`scripts/extract/` so catalogs are reproducible from the pinned PDFs.

## Framework tools (`agentlib/frameworks/<module>.py`)

* Pure, deterministic Python (stdlib + PyYAML + jsonschema only). No network.
* Load data via `agentlib.paths.load_catalog("<id>")`.
* Optionally expose `register(subparsers)` to add a CLI sub-command; it is
  discovered automatically (no edits to `cli.py`).
* Optionally expose grader functions `grade_xxx(output: str, check: dict) -> (bool, str)`
  for use as `python` checks in evaluation suites.
* Covered by `tests/test_<module>.py`.

## Agents (`agents/<name>.md`)

Claude Code subagent format: front matter `name` (= file stem),
`description` (60-1024 chars, say when to delegate), optional `tools`
(comma-separated), `model` (`inherit|sonnet|opus|haiku`). Body is the system
prompt (≥ 200 chars). Reference skills by path, e.g. `skills/asvs-verification/`;
referenced skills must exist.

## Workflows (`workflows/<id>.yaml`)

Stages name an `agent`, the `skills` it uses, the artefacts it `consumes` and
`produces`, and a `gate` (criteria + decision: `human`, `automated`,
`agent-review`). The validator checks that agents/skills exist, `depends_on`
points backwards, every consumed artefact was produced earlier (or is a
workflow input) and every workflow output is produced.

## Evaluation suites (`evals/<skill>/cases.yaml`)

See `agentlib/evals/spec.py` and `agentlib/evals/graders.py`. Each case needs a
prompt, deterministic checks and a `golden` output that passes. Add a
`negative` output (a plausible but flawed answer) wherever possible: offline CI
requires goldens to pass and negatives to fail, proving the checks
discriminate. Live mode runs the same checks against Claude's actual output.

## Before committing

```sh
python -m agentlib registry --write
python -m agentlib validate
python -m agentlib eval
python -m pytest
```
