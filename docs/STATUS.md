# Implementation status and resume guide

Last updated: 2026-10-13. Branch: `claude/agent-library-implementation-31pde7`.

## How to resume

```sh
pip install -r requirements-dev.txt
python -m agentlib registry --write && python -m agentlib validate   # lists what is broken/missing
python -m pytest -q
python -m agentlib eval
```

Validation errors point directly at missing or inconsistent components. Contract: `docs/AUTHORING.md`.
Builder brief used for the framework work (reproduce it for any unfinished framework): every framework
delivers a catalog + `scripts/extract/<module>.py`, `agentlib/frameworks/<module>.py` with a CLI
sub-command, `tests/test_<module>.py`, skill(s) with references/templates, subagent(s), an eval suite
(>= 4 cases with golden + negative) and `docs/frameworks/<module>.md`.

## Completed (committed, tested)

| Component | Status |
|---|---|
| Core `agentlib` (validate, registry, list, eval offline/live/grade, install) | done, tests in `tests/test_core_*.py` |
| JSON schemas, plugin + marketplace manifests (`claude plugin validate .` passes) | done |
| CI: `.github/workflows/validate.yml`, manual `live-evals.yml` | done |
| `evidence-and-citation` skill + `agentlib evidence` checker + eval suite | done |
| `framework-selector` skill + `agentlib route` + eval suite | done |
| Agents `review-board-chair`, `evidence-auditor`; 5 workflows; 7 commands; root templates | done |
| Docs: AUTHORING, ARCHITECTURE, EVALUATION, USING_IN_OTHER_REPOS, CLAUDE.md, Agent SDK example | done |

## Framework builds

| Framework | Module / CLI | Skills | Agents | State |
|---|---|---|---|---|
| NASA SE Handbook | `nasa_se` / `nasa-se` | nasa-systems-engineering, requirements-engineering | systems-engineer, requirements-engineer | done: 17 processes, 16 reviews, 55 checklist items, 90 tests, 10 eval cases |
| NPR 7150.2D + NASA-STD-8739.8B | `nasa_swe` / `nasa-swe` | nasa-software-engineering, nasa-software-assurance | software-engineering-lead, software-assurance-engineer | in progress |
| NIST AI RMF + Playbook | `ai_rmf` / `ai-rmf` | nist-ai-rmf | ai-risk-assessor, ai-governance-advisor | done: 72 subcategories, 460 playbook actions, 48 tests, 5 eval cases |
| NIST SSDF | `ssdf` / `ssdf` | nist-ssdf | secure-development-reviewer | done: 19 practices, 42 tasks, 42 tests, 5 eval cases |
| OWASP ASVS 5.0.0 | `asvs` / `asvs` | owasp-asvs | application-security-verifier | done: 345 reqs, 45 tests, 6 eval cases |
| Green Book 2026 | `greenbook` / `greenbook` | green-book-appraisal | economic-appraisal-analyst | done: 121 items, 69 tests, 6 eval cases |

Workflows reference these exact names; they validate once all agents/skills exist.

## Known gaps / next work

- Update `README.md` with final inventory and plugin install line.
- (done) Example citation pages verified against the PDF text.
- Optional: native `claude plugin eval` cases in `plugin-evals/` (configured in plugin.json).
- Run live evals (`live-evals.yml`) once an API key secret exists; record results here.
