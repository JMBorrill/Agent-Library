# Progress and resume point

_Last updated: 2026-10-13 (session building v0.1.0). Branch: `claude/build-agent-library`._

## Resume in a new session
```
git checkout claude/build-agent-library
python3 scripts/run_all_checks.py           # expect all gates PASS
python3 scripts/source_freshness.py         # sources to re-verify
cat docs/progress.md                         # this file — start at "Open items"
```
Then: "Read docs/progress.md and docs/MASTER_CLAUDE_BUILD_PROMPT.md; resume from the first open item,
run tests, and update measured coverage."

## Stage status (master prompt phases)

| Phase | Status | Evidence |
|---|---|---|
| 0 Inventory / audit | done | `docs/audits/initial-repo-audit.md` |
| Authoring specs verified | done | Agent Skills spec (official repo), Claude Code skills + subagents docs |
| Source research | done within network limits | `sources/audits/` — 4 VERIFIED, 1 PARTIALLY_VERIFIED, 14 INACCESSIBLE |
| A NASA SE | done (mechanics tested; source fidelity unverified) | 16 skills; 17/17 processes → tested skills (`docs/coverage.md`) |
| B ECSS / space | partial | budgets + low-gravity physics built; ECSS clause mapping BLOCKED (no access/licence) |
| C Software / security / SRE | done | 10 skills; ASVS 5.0.0 index verified |
| D Product / UX | done | 5 skills; GOV.UK Design System verified; Service Manual & Shape Up unverified |
| E Finance / credit | done (unverified sources) | 6 skills; known-answer tests |
| F AI governance | done (unverified source) | 4 skills; injection corpus 12/14 detected (2 labelled misses) |
| Integration (router, installer) | done | `select-frameworks`, `scripts/install_packs.py` |
| QA (validator, tests, CI, coverage, freshness) | done | 594 tests; CI workflow; mutation tests |
| Demonstrations | done | 3 demos, reproducible (`examples/run_demos.py --check`) |
| Independent review | done — library (independent-reviewer) and each demo (safety-, credit-regulatory-, security-reviewer agents) | `docs/audits/independent-library-review.md`, `examples/*/review/` |

## Measured state (see `docs/coverage.md`, regenerate with `scripts/coverage_report.py --run-tests --write`)
- 45 skills, all "tested" by the measured definition (script/template + pass & fail fixtures + passing test module).
- 14 agents (8 authors, 6 read-only reviewers).
- 617 unit/fixture tests passing; validator 0 errors / 0 warnings; all gates in `scripts/run_all_checks.py` PASS.
- Human expert review: **pending for every capability**.

## Review findings and dispositions
Independent library review (GO_WITH_CONDITIONS, 0 critical / 2 major / 8 minor / 5 observations):
- Fixed with regression tests proven to fail on pre-fix code: F01 (rotating-frame escape speed),
  F02 (affordability refer signal, no PASS banner), F03/F04 (SLO threshold float, inputs), F05/F06
  (unit economics overrides, lifetime consistency), F07 (cashflow periods), F08 (decision matrix ids,
  scale), F09/F10 (strict-mode test).
- Demo-builder findings fixed: review record evidence, non-discriminating switching weights, negative
  TPM projections, ICD requirement links, demo side-file drift, system-card human titles, exact+citation
  eval scoring, eval-ID existence, SLO selection at MVP, cluster randomisation, `--out -`.

## Demonstration review outcomes (recommendations only — no human decision recorded)
| Demo | Reviewer | Recommendation | Gate status after responses | Open actions |
|---|---|---|---|---|
| ASTER-01 | safety-risk-reviewer | GO_WITH_CONDITIONS for paper design to PDR | SRR NO_GO (8 open major actions incl. F-01–F-07) | 12 RIDs |
| Mortgage criteria | credit-regulatory-reviewer | GO_WITH_CONDITIONS for closed synthetic pilot design | Pilot NO_GO; triage `refer` (perimeter unanswered); PT-01 eval fails 2 items | 37 |
| AI Ops platform | security-reviewer | GO_WITH_CONDITIONS to build on synthetic data | Launch NO_GO (6 blockers); v1 eval fails cross-tenant canary | 17 |

Library fixes triggered by demo reviews: global prohibited terms (eval), pause-trigger warning (oversight),
eligible_indicative exclusions (criteria), null-answer refer (triage), quote-pair bug (claim_check),
provenance tainting / recipient binding / default-deny egress (tool policy), project blocking items
(readiness), two social-engineering scanner rules (in-sample; a fresh paraphrase still scores CLEAN).

## Open items (next steps, in priority order)
1. **Primary-source verification for 14 INACCESSIBLE sources.** Either allow the domains in the
   environment network settings, or place lawfully obtained copies in `sources/originals/` and
   register them with `scripts/register_original.py`; then update each `sources/audits/<id>.md`,
   replace *(unverified)* markers that are confirmed, correct anything that differs, and set
   `access_status`. Priority: nasa-se (+ chapters), nist-ai (subcategory list), treasury-green, fca,
   basel-credit, google-sre, nasa-software, gov-service, shape-up, ecss-se, damodaran.
2. **Human expert review** of high-stakes skills: se-risk-analysis, se-review-gates, credit-*,
   finance-fca-scope-check, ai-human-oversight, security-*. Record reviewer, date and outcome in the
   skill's References section and bump `metadata.version`.
3. **Repository licence**: owner to choose (ASVS-derived data files must remain CC BY-SA 4.0).
4. ECSS supplements (`space-qualification-planning`, model philosophy) once ECSS is lawfully accessible.
5. NIST AI RMF subcategory-level validation once the Playbook export is available.
6. Optional: `install_packs.py --uninstall` using the lock manifest; human-readable batch output for
   `lowg_calc.py batch` (currently prints values as JSON in text mode — cosmetic).
7. Eval `must_not_contain` is substring-based and cannot tell negated/quoted phrases from statements (mortgage MCP-RID-013) — consider a decision-statement scorer.
8. Heuristic scanners (security code checks, injection scan, claim check) have known false negatives;
   extend corpora as real cases appear.

## Commands run this session (key results)
- Baseline: `check_repo.py` PASS, `check_framework_manifest.py` PASS (both since shown to give false assurance).
- `scripts/validate_library.py` → PASS 0 errors.
- `python3 -m unittest discover -s tests -t .` → 617 tests OK (coverage run).
- `examples/run_demos.py --check` → PASS, 3 demos.
- `scripts/run_all_checks.py` → all gates PASS.
