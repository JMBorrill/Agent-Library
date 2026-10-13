# Changelog

All notable changes. Versions follow semantic versioning of the library (`VERSION`); each skill also
carries its own `metadata.version`.

## [0.1.0] — 2026-10-13 — first working library

Built from the `standards-agent-factory-kit` starter (imported unmodified as commit `cc1c5c7`).

### Audit of the starter (see `docs/audits/initial-repo-audit.md`)
- Baseline validators passed but gave false assurance: 6 of 16 skills referenced by the NASA map did
  not exist; agents had no `tools` allowlist (inherited every tool); skills were 5-line templates with
  no scripts, fixtures or tests.

### Added
- **Authoring contract** `docs/CONVENTIONS.md`; Agent Skills spec verified from the official
  `agentskills/agentskills` repository; Claude Code skill/subagent docs verified.
- **Validator** `scripts/validate_library.py` with strict frontmatter parser (PyYAML parity tested),
  spec-only keys, required sections, reference existence, stdlib-only imports, agent tool allowlists,
  read-only reviewers, pack/registry/NASA-map/crosswalk integrity; mutation tests re-create the
  starter's defects.
- **45 skills in 9 packs**, each with procedure, decision criteria, escalation, scripts, templates,
  schemas and pass/fail fixtures:
  - systems-engineering (16): every NASA common technical process mapped to a tested skill.
  - space-engineering (2), software (3), reliability-security (7), product (4), ux (1),
    finance-credit (6), ai-governance (4), orchestration (2).
- **14 agents** with explicit least-privilege tools; 6 read-only reviewers; human-approval sections.
- **Source research**: 19 source audits with honest access statuses (4 VERIFIED, 1 PARTIALLY_VERIFIED,
  14 INACCESSIBLE under the session's network policy), extracts (ASVS 5.0.0 index of 345 requirements,
  SSDF practices, DORA metrics, GOV.UK rules, Google review guidance), 19 crosswalks.
- **Project integration**: `select-frameworks` router (reasons, exclusions, oversight, sign-offs,
  workflow), `scripts/install_packs.py` (dry-run default, conflict refusal, backups, dependency
  resolution, lock manifest), generated `docs/CAPABILITY_GUIDE.md`.
- **Quality tooling**: `scripts/coverage_report.py` (measured coverage), `scripts/source_freshness.py`,
  `scripts/run_all_checks.py`, GitHub Actions workflow (Python 3.10 and 3.13).
- **Demonstrations**: Project ASTER, Mortgage Criteria Platform, AI Operations Platform, reproducible
  via `examples/run_demos.py --check`, each independently reviewed by a separate agent.

### Changed
- Starter skills rewritten in place (names kept): `ai-risk-assessment`, `finance-options`,
  `product-discovery`, all `se-*`; `software-review` renamed `software-code-review`.
- `scripts/check_repo.py` and `scripts/check_framework_manifest.py` now delegate to the validator.
- Registry enriched (access status, licence, normative status, check/review dates, audit pointer);
  Green Book URL variant discrepancy recorded.

### Review cycle (same release)
- Independent library review (GO_WITH_CONDITIONS; 0 critical, 2 major, 8 minor): all actioned findings
  fixed with regression tests proven to fail on pre-fix code.
- Three demo reviews by separate read-only reviewer agents; findings either fixed in the library,
  closed in the demo, or recorded as owned open actions (see `examples/*/review/lead-response.md`).
- Library changes from reviews: rotating-frame escape check, affordability refer signal, unit-economics
  lifetime consistency and warnings, cashflow CSV periods, SLO threshold tolerance, decision-matrix input
  checks, review-record evidence, TPM projection sanity, ICD requirement links, system-card human titles,
  eval citation/exact scoring, global prohibited terms, oversight pause triggers, triage null answers,
  claim-check quote pairing, tool-policy tainting/recipient binding/default-deny, readiness blocking items.

### Known limitations
See `docs/progress.md` → "Open items". Notably: 14 sources need primary re-verification; no human
expert has reviewed any capability; heuristic scanners (security, injection, claims) have false
negatives by design.
