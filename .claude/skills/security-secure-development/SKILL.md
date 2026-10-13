---
name: security-secure-development
description: Map an organisation's secure software development evidence to NIST SSDF (SP 800-218 v1.1) practices and tasks, check practice/task IDs, evidence presence and freshness, coverage per group (PO, PS, PW, RV), and check dependency manifests (requirements.txt, package.json, pyproject.toml) for unpinned or range-specified versions and missing lockfiles. Use when preparing for a customer or supplier secure-development questionnaire, building an SSDF evidence register, auditing evidence age, or tightening dependency pinning as a supply-chain control.
metadata:
  pack: reliability-security
  version: "1.0.0"
  sources: "nist-ssdf"
---

# Secure development practices (NIST SSDF) and dependency pinning

## Purpose
Maintain an honest, current register showing which SSDF practices the organisation performs, with
an owner and dated evidence for each, and keep one concrete supply-chain control — reproducible,
pinned dependencies — mechanically checked.

## When to use
- Building or refreshing an SSDF practice → evidence register.
- Answering a customer/supplier security questionnaire that references SSDF.
- Quarterly evidence-freshness review.
- Hardening dependency management in an application repository.

**Do not use when:** you need application-level security requirements (use
`security-asvs-controls`); you need code-level findings (`security-code-checks`); you need
vulnerability scanning of dependencies (use a software composition analysis tool — this skill only
checks pinning); or you need a formal attestation (requires legal/compliance sign-off).

## Inputs
Required
- Evidence register CSV (template `assets/templates/ssdf-evidence.csv`): `practice_id`, `task_id`
  (optional), `evidence_ref`, `evidence_date`, `owner`, `status`
  (planned | implemented | verified | not_applicable), `justification`.
- Repository paths containing dependency manifests (for the pinning check).
Optional
- Reference date (`--as-of`) and maximum evidence age (`--max-age-days`, default 365 — library default).

## Procedure
1. **Use the v1.1 identifiers** from `assets/data/nist-ssdf-practices.json` (19 practices, 42
   tasks; there is **no PW.3** in v1.1). Write IDs as `SSDF-v1.1-PO.1` / `SSDF-v1.1-PO.1.1` in
   shared reports.
2. **Collect evidence per practice** (ideally per task): policy documents, CI configuration,
   review records, pen-test reports, signing runbooks. Name an owner for each row. Record a date for
   each implemented/verified item. Mark `not_applicable` only with a written justification.
3. **Check the register**:
   `python3 scripts/ssdf_evidence_check.py ssdf-evidence.csv --as-of 2026-10-13`
4. **Fix errors** (unknown IDs, missing evidence/date, unjustified N/A, future dates); refresh
   `stale-evidence`; plan work for `practice-not-covered`. Use `--require-all` before an external
   submission.
5. **Check dependency pinning** (supports PW.4 reuse of well-secured components and PS
   protections — mapping is this library's judgement):
   `python3 scripts/dependency_pin_check.py path/to/repo --mode app`
   Use `--mode library` for packages published for others to consume.
6. **Record** the check outputs as evidence rows themselves (dated), and hand the register to the
   security owner for review.

## Decision criteria
| Situation | Rule |
|---|---|
| Practice only `planned` | Not covered; appears as `practice-not-covered`. |
| Evidence older than max age | Warning; refresh before external use. |
| ID like PW.3 or v1.2-only practice | Error; re-map to v1.1 IDs (v1.2 was a draft at last check). |
| Application with range specifiers and a lockfile | Warning (npm) / info (pyproject) — the lockfile pins; exact pins make upgrades explicit. |
| Application with ranges and no lockfile | Error — builds are not reproducible. |
| VCS dependency without full commit hash | Error in app mode — the branch can move under you. |
| Library package | Ranges are normal; a lockfile is recommended for CI only. |
| External attestation requested | Requires human legal/compliance sign-off; the scripts never attest. |

## Outputs
- `ssdf-evidence.csv` register; check report (`--json`), schema
  `assets/schemas/ssdf-evidence.output.schema.json`.
- Dependency pinning report (`dependency_pin_check.py --json`), schema
  `assets/schemas/findings-report.schema.json`.

## Validation
- `ssdf_evidence_check.py ... --json` → exit 0 = every row uses a valid v1.1 practice/task, done rows
  have evidence and a valid date not after `--as-of`, N/A rows are justified. Uncovered practices
  are warnings unless `--require-all`.
- `dependency_pin_check.py ... --json` → exit 0 = no unpinned application dependencies without a
  lockfile and no unpinned VCS references.
- PASS does **not** mean the practices are effective, that evidence is adequate, or that
  dependencies are free of vulnerabilities or malicious code.

## Examples
- `assets/examples/evidence-pass.csv` (`--as-of 2026-10-13`) → exit 0, 19/19 practices covered.
- `assets/examples/evidence-fail.csv` (same) → exit 1: `unknown-practice` (PW.3),
  `version-mismatch`, `task-practice-mismatch`, `no-evidence`, `future-evidence-date`,
  `na-without-justification`, `bad-evidence-date`, `status-value`; warnings `stale-evidence`,
  `practice-not-covered`, `no-owner`.
- `assets/examples/deps-pass/` → exit 0; `assets/examples/deps-fail/` → exit 1 with
  `unpinned-dependency`, `unpinned-vcs`, `missing-lockfile`.

## Escalation and stop conditions
- **Stop** before any statement of SSDF conformance or attestation leaves the organisation — that
  needs the accountable executive and legal/compliance review.
- Escalate uncovered RV (vulnerability response) practices and unpinned production dependencies to
  the `security-reviewer` agent.
- If SSDF v1.2 has been finalised, stop and re-baseline IDs before using this register externally.

## References
- `nist-ssdf` — NIST SP 800-218 v1.1 via the official OSCAL catalog
  (`usnistgov/oscal-content`, `nist.gov/SP800-218/ver1/json/NIST_SP800-218_ver1_catalog.json`):
  4 groups, 19 practices, 42 tasks; no PW.3; PO.1.3 formerly PW.3.1. Status **PARTIALLY_VERIFIED**:
  the OSCAL rendering was read, the PDF narrative was not (`sources/audits/nist-ssdf.md`). Practice
  titles are NIST's (US Government work). Source ID: `nist-ssdf`.
- SSDF v1.2 (SP 800-218 Rev.1 draft, Dec 2025) is known only from secondary sources *(unverified)*
  and is not reflected here.
- Dependency pinning rules and the mapping of pinning to SSDF practices are this library's own.
- Method notes: [references/ssdf-evidence.md](references/ssdf-evidence.md).
