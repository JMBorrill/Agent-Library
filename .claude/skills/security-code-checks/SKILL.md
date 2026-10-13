---
name: security-code-checks
description: Run a lightweight, explainable heuristic security screen over Python, JavaScript, TypeScript and SQL files - hard-coded secrets, SQL built by string formatting, queries on tenant-scoped tables missing the tenant filter, debug mode, MD5/SHA-1 password hashing, unsafe deserialisation (pickle, yaml.load), disabled TLS verification, wildcard CORS with credentials and JWT 'none'/unverified tokens - each mapped to an OWASP ASVS 5.0.0 chapter or section. Use when pre-screening a change or repository before human security review, checking a multi-tenant codebase for missing tenant filters, or teaching common insecure patterns; not a SAST tool.
metadata:
  pack: reliability-security
  version: "1.0.0"
  sources: "owasp-asvs"
---

# Heuristic security code checks

## Purpose
Catch a short list of common, high-impact insecure patterns cheaply and explainably, so human
security review time goes to design and logic flaws. Every finding names the rule, the line, why it
matters, and the ASVS 5.0.0 area to read. It is a screen, not assurance.

## When to use
- Before requesting a security review of a pull request or a small repository.
- Checking a multi-tenant SaaS codebase for queries that forget the tenant filter.
- As a CI tripwire for the listed patterns (alongside, not instead of, a real SAST tool and
  secret scanner).
- Training: showing developers vulnerable vs fixed versions of the same code.

**Do not use when:** you need a security assessment, penetration test or SAST/DAST coverage; you
need dependency vulnerability scanning (use `security-secure-development` for pinning and an SCA
tool for CVEs); or you are reviewing architecture (use `security-threat-model`).

## Inputs
Required
- One or more files or directories (`.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.mjs`, `.cjs`, `.sql`).
Optional
- Tenant configuration: `--tenant-tables crm_contacts,appointments --tenant-column tenant_id`, or a
  JSON config (template `assets/templates/static-checks-config.json`). Without it SC003 is inactive.

## Procedure
1. **Configure tenant scope** (multi-tenant systems): list every table that holds tenant data and
   the tenant column. Keep the config in the repository.
2. **Run**: `python3 scripts/static_checks.py src/ --config static-checks-config.json`
3. **Triage each finding** — open the line, decide true or false positive:
   - True positive → fix (see [references/rules.md](references/rules.md) for the fix pattern) and,
     for secrets, rotate the credential and treat history as exposed.
   - False positive → add `static-checks: ignore[SC00N] <reason>` on that line; a suppression with no
     reason is ignored. Suppressions are reported as `info` for review.
4. **Re-run** until exit 0, then hand to human review with the report attached.
5. **Use the ASVS reference** on each finding to locate the relevant chapter/section, then read the
   requirements there (feeds `security-asvs-controls`).

## Decision criteria
| Situation | Rule |
|---|---|
| SC001 secret pattern on a real credential | Stop: rotate first, then remove from code and history; escalate. |
| SC003 tenant filter missing | Treat as a potential cross-tenant data leak until proven otherwise; block merge. |
| SC002 SQL built with formatting, input is "internal" | Still fix: parameterise; internal sources change. |
| SC005 MD5/SHA-1 not for passwords | The rule only fires near password words; checksum use is out of scope. |
| Finding is a false positive | Suppress with a reason on the line; reviewer confirms. |
| Clean result | Proceed to human review; do not describe the code as secure. |

## Outputs
- Screen report (`--json`), schema `assets/schemas/static-checks.output.schema.json`: findings with
  `rule`, `rule_id`, `asvs_ref`, `asvs_mapping` (section | chapter), file, line, masked snippet.
- Triage notes in the review record (true/false positive, fix or suppression reason).

## Validation
- `python3 scripts/static_checks.py PATH --json` → exit 0 = none of the nine patterns found (after
  reasoned suppressions); exit 1 = findings; exit 2 = path missing/unreadable.
- PASS does **not** mean the code is secure. The checks are line/regex-based with no data-flow or
  taint analysis: they miss vulnerabilities expressed differently (ORMs, query builders, aliases,
  multi-line concatenation) and can flag safe code. Secret values are masked in output.

## Examples
- `assets/examples/vulnerable-app-fail/` (AI ops booking API, mortgage-criteria API, report SQL) with
  `--config assets/examples/aiops-config.json` → exit 1, every rule SC001–SC009 triggered.
- `assets/examples/fixed-app-pass/` with the same config → exit 0.

## Escalation and stop conditions
- **Stop** and escalate to `security-reviewer` for any real secret, any confirmed tenant-filter gap,
  or JWT/TLS verification disabled in production paths.
- Do not mark findings as "accepted risk" here; risk acceptance is recorded by a human owner in the
  threat model (`security-threat-model`).

## References
- `owasp-asvs` — OWASP ASVS 5.0.0 chapter and section titles from the verified index
  (`sources/extracts/owasp-asvs-5.0.0-index.json`; audit `sources/audits/owasp-asvs.md`). Rules are
  mapped by **title match only**: section where a section title clearly matches (V1.2 Injection
  Prevention, V1.5 Safe Deserialization, V3.5 Browser Origin Separation, V9.1 Token source and
  integrity, V11.4 Hashing and Hash-based Functions, V13.3 Secret Management, V13.4 Unintended
  Information Leakage), otherwise chapter only (V8 Authorization, V12 Secure Communication).
  No requirement-level ASVS ID is claimed because requirement text was not part of the index.
  Source ID: `owasp-asvs`.
- The rule set and patterns are original to this library.
- Rule details and fixes: [references/rules.md](references/rules.md).
