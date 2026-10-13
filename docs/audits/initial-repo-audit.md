# Initial repository audit (2026-10-13)

Auditor: Claude Code (Lead AI Systems Architect role). Baseline commit: `cc1c5c7` (starter kit imported unmodified).

## 1. Baseline inventory

| Area | Found | Observation |
|---|---|---|
| Skills (`.claude/skills/`) | 14 | All share one generic template: 5-line procedure, identical boilerplate quality gates, one source ID. No `references/`, `scripts/`, `assets/`, examples, decision criteria, input contracts or escalation rules. |
| Agents (`.claude/agents/`) | 10 | Frontmatter has only `name`/`description`. No `tools` allowlist, so each agent would **inherit every tool** (violates least privilege). No `skills` preloading, handoff contract, non-goals or sign-off boundaries. |
| Sources | 19 registry rows | URLs, versions as free text. No access status, licence verification, verified sections or check dates. Two URLs disagree with `docs/VERIFIED_REFERENCE_URLS.md` (`treasury-green`, `owasp-asvs`). |
| NASA crosswalk | 17 processes | Structurally complete, but **6 of 16 referenced skills do not exist** (`se-logical-decomposition`, `se-transition`, `se-configuration-management`, `se-technical-data-management`, `se-technical-assessment`, `se-decision-analysis`). |
| Scripts | 2 | `check_repo.py`, `check_framework_manifest.py`. |
| Templates | 5 | Requirements, verification matrix, ICD, risk register CSV headers; review checklist. |
| Examples | ASTER-01 | 2 proposed requirements, review notes. |
| Tests / CI | none | No unit tests, fixtures, negative cases or CI. |
| Installer / router | none | README instructs manual copying. |

## 2. Baseline validator runs (observed)

```
$ python3 scripts/check_repo.py
PASS: 14 skills; 10 agents; 2 example requirements; 19 sources.
$ python3 scripts/check_framework_manifest.py
PASS: 19 source URLs and framework plan entries; 17 preliminary NASA process mappings; metadata integrity only.
```

### Defects in the validators themselves
1. `check_framework_manifest.py` passes although six mapped skills do not exist (false assurance).
2. `check_repo.py` parses YAML by splitting on `:`; does not enforce Agent Skills rules (consecutive hyphens, `compatibility` length, `metadata` string map, unknown keys), body length, or that referenced files exist.
3. Agent check only confirms `name:`; does not check `description`, tools, or referenced skills.
4. Requirement check is hard-coded to one example file.

## 3. Authoring standards verified this session

| Standard | Access | Notes |
|---|---|---|
| Agent Skills specification | VERIFIED via official repo `agentskills/agentskills` `docs/specification.mdx` (agentskills.io itself blocked by network policy) | Fields: `name` (≤64, `[a-z0-9-]`, no leading/trailing/consecutive hyphens, = directory), `description` (≤1024), optional `license`, `compatibility` (≤500), `metadata` (string→string), `allowed-tools` (experimental). Body < 500 lines / < 5000 tokens recommended; references one level deep. |
| Claude Code skills docs | VERIFIED via WebFetch of code.claude.com/docs/en/skills | Claude-only keys (`disable-model-invocation`, `context`, ...) cause hard errors on claude.ai/Skills API upload → library uses only spec keys. Listing cap 1,536 chars for description. |
| Claude Code subagents docs | VERIFIED via WebFetch of code.claude.com/docs/en/sub-agents | `tools` omitted ⇒ inherits all tools; `skills` preloads full skill content (cost!); `disallowedTools`, `model`, `permissionMode`, `maxTurns`, `memory`, `color` available. |

## 4. Source access ledger (network-policy constrained)

The session's network policy blocks most publisher hosts (proxy `CONNECT 403`): nasa.gov, swehb.nasa.gov, ecss.nl, gov.uk, design-system.service.gov.uk, basecamp.com, google.github.io, sre.google, owasp.org, nist.gov, csrc.nist.gov, airc.nist.gov, pages.stern.nyu.edu, bis.org, handbook.fca.org.uk, dora.dev, agentskills.io. `raw.githubusercontent.com` is reachable, so sources whose **official** publisher repository is on GitHub can be read at primary level: Agent Skills spec, Google eng-practices, OWASP ASVS, GOV.UK Design System, dora.dev. Per-source results: `sources/audits/<id>.md`.

## 5. Gap and risk ranking

| Rank | Gap | Risk if unaddressed |
|---|---|---|
| 1 | Validators give false PASS | Users trust broken mappings |
| 2 | Agents inherit all tools | Over-privileged reviewers can edit what they review |
| 3 | Skills lack procedures, inputs, decision criteria, examples, tests | Superficial output; no reliability |
| 4 | No deterministic tools (trace, V&V coverage, finance maths, security checks) | Unreproducible results |
| 5 | Source provenance not recorded | Fabricated or stale citations |
| 6 | No installer/router | Manual copying overwrites user config |
| 7 | No worked end-to-end demos | Library unproven on realistic projects |

## 6. Dependency graph (build order)

```
authoring spec ─┬─> library validator ─> tests/CI
source audits ──┼─> crosswalks ─> coverage report
                └─> NASA SE slice (exemplar conventions)
                        ├─> space pack
                        ├─> software / security / SRE pack
                        ├─> product / UX pack
                        ├─> finance / credit pack
                        └─> AI governance pack
packs catalog ─> installer + framework router ─> 3 demonstrations ─> independent review
```
