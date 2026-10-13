---
name: security-asvs-controls
description: Choose an OWASP ASVS 5.0.0 verification level (L1/L2/L3) and chapters for an application, build a control verification map (asvs_id, level, applicability with justification, implementation, verification method, evidence, status) and compute verification coverage with version-qualified ID validation. Use when planning application security verification, scoping a penetration test or security review against ASVS, tracking which ASVS requirements are verified with evidence, or checking a map for unknown IDs, unjustified N/A rows or passes without evidence.
license: CC BY-SA 4.0 applies to assets/data/asvs-5.0.0-index.json (OWASP ASVS 5.0.0); other files per repository licence
metadata:
  pack: reliability-security
  version: "1.0.0"
  sources: "owasp-asvs"
---

# OWASP ASVS 5.0.0 control verification map

## Purpose
Turn "we follow ASVS" into a verifiable plan and record: the level and chapters in scope, every
in-scope requirement marked applicable or justified as not applicable, how it is implemented, how
it was verified, the evidence, and the result — with coverage figures a reviewer can recompute.

## When to use
- Starting security verification for a web application or API (e.g. a mortgage-criteria web app or
  a multi-tenant SaaS).
- Scoping a penetration test or security code review against ASVS.
- Preparing evidence for a release gate or a customer security questionnaire.
- Re-baselining after ASVS changes version (IDs are not stable across major versions).

**Do not use when:** you have not yet identified threats and trust boundaries (start with
`security-threat-model`); you want a quick code screen (`security-code-checks`); or you need
organisation-level secure-development practices (`security-secure-development`).

## Inputs
Required
- Application description: users, data sensitivity, exposure (internet/internal), features in use
  (OAuth/OIDC, WebRTC, file upload, GraphQL, WebSocket).
- Target level and chapters (decided in step 1–2).
Optional
- Existing map CSV (template `assets/templates/control-map.csv`, or generate one with
  `--generate-template`), threat model, pen-test report, CI results.

## Procedure
1. **Choose the level** (your risk decision; see Decision criteria). Record the reason.
2. **Choose chapters**: drop chapters for features the application does not have (e.g. V17 WebRTC
   without WebRTC, V10 without OAuth/OIDC, V3 for machine-to-machine APIs with no browser client).
   Record each excluded chapter and why.
3. **Generate the skeleton**:
   `python3 scripts/asvs_coverage.py --generate-template --level 2 --chapters V1,V2,V4,V6,V7,V8,V11,V12,V13,V14,V15,V16 --out control-map.csv`
4. **Fill each row** after reading the requirement text in ASVS 5.0.0: `applicable` yes / no / na
   (no and na need a justification); `implementation_ref` (code, config, document);
   `verification_method` (automated-test, manual-test, code-review, config-review,
   documentation-review, pen-test, tool-scan, interview); `evidence_ref` (CI run, report ID);
   `status` not_verified / pass / fail. Documentation requirements (usually the first section of a
   chapter) are verified separately from their paired implementation requirements.
5. **Check and compute coverage**:
   `python3 scripts/asvs_coverage.py control-map.csv --level 2 --chapters V1,V2,V4,V6,V7,V8,V11,V12,V13,V14,V15,V16`
6. **Resolve errors**; for each `control-failed` either remediate and re-verify or raise a risk
   decision with the owner. Use `--require-complete` before a release gate.
7. **Report** scope, level, chapters excluded with reasons, coverage per chapter, failures and N/A
   items — never as "compliant" or "certified".

## Decision criteria
Level selection (library guidance in its own words; ASVS leaves the choice to the organisation's
risk analysis):

| Level | Choose when | Typical examples |
|---|---|---|
| L1 | Minimum first layer of defence; low-sensitivity data; or a starting point for a programme | Brochure sites, internal tools with no sensitive data, first pass on legacy apps |
| L2 | Default for most applications handling personal, financial or business-confidential data, or with authenticated multi-user/multi-tenant access | B2B SaaS, CRM/scheduling platforms, mortgage-criteria and broker portals |
| L3 | Compromise would cause severe harm (safety, large-scale financial loss, critical infrastructure, highly sensitive data) and the organisation can fund defence-in-depth | Payment/banking cores, health records, identity providers |

| Situation | Rule |
|---|---|
| Unsure between two levels | Pick the higher for chapters touching the most sensitive assets (e.g. V6, V8), record the split. |
| Row marked no/na | Justification ≥ 10 characters explaining why the requirement cannot apply; reviewer must agree. |
| Status pass | Needs `evidence_ref` (error) and a method (warning). Automated tool output alone is not sufficient evidence for most requirements. |
| Status fail | Error until remediated or a human risk owner records a decision outside the map. |
| ID from ASVS 4.x | Re-map; v4 and v5 numbering differ throughout. |
| Requirement above target level listed | Info only; allowed as extra assurance. |

## Outputs
- `control-map.csv` (template `assets/templates/control-map.csv`).
- Coverage report (`--json`), schema `assets/schemas/asvs-coverage.output.schema.json`.
- `asvs-verification-report.md` — scope, level rationale, chapter exclusions, coverage, failures,
  N/A list, open items, named reviewer.

## Validation
- `python3 scripts/asvs_coverage.py map.csv --level N [--chapters ...] --json` → exit 0 = every row
  is a valid ASVS 5.0.0 ID at the right level, N/A rows are justified, passes have evidence and no
  control failed. Missing in-scope requirements are warnings (errors with `--require-complete`).
- PASS does **not** mean the application meets ASVS: the script cannot judge evidence quality,
  and some requirements are stricter at higher levels within their text, which the level column
  does not capture.

## Examples
- `assets/examples/control-map-pass.csv` — mortgage-criteria web app, L1, chapters V7 and V8:
  `python3 scripts/asvs_coverage.py assets/examples/control-map-pass.csv --level 1 --chapters V7,V8`
  → exit 0, 100% mapped, 7 of 9 applicable passed.
- `assets/examples/control-map-fail.csv` (same command) → exit 1 with `asvs-unversioned`,
  `asvs-version-mismatch`, `asvs-unknown-id`, `level-mismatch`, `na-without-justification`,
  `pass-without-evidence`, `control-failed`, `duplicate-row`.

## Escalation and stop conditions
- **Stop** if the requested level is below what the data sensitivity indicates (e.g. L1 for a
  multi-tenant platform with financial data) — record the decision with the accountable owner.
- Failed V6/V7/V8 (authentication, session, authorization) controls on internet-facing apps go to
  the `security-reviewer` agent before release; tenant-isolation failures block release.
- Any external statement of conformance requires human sign-off; OWASP does not certify.

## References
- `owasp-asvs` — OWASP ASVS 5.0.0, tag `v5.0.0`: `0x03-What-is-the-ASVS.md` (levels, Which level to
  achieve, The structure of the ASVS, How to Reference ASVS Requirements, Documented security
  decisions); `0x04-Assessment_and_Certification.md` (no certification; tools alone insufficient;
  report scope, level, exceptions, N/A). Verified: `sources/audits/owasp-asvs.md`. Source ID: `owasp-asvs`.
- Index: `assets/data/asvs-5.0.0-index.json` — 345 requirements, L1 70 / L2 183 / L3 92; level is
  the lowest level at which a requirement applies. Adaptation of OWASP ASVS 5.0.0 © The OWASP
  Foundation, CC BY-SA 4.0; the file remains CC BY-SA 4.0.
- Method notes: [references/asvs-verification.md](references/asvs-verification.md).
