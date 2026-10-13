---
name: security-threat-model
description: Build and check a STRIDE-style data-flow threat model - components, assets, trust boundaries, boundary-crossing data flows, threats rated by likelihood and impact, and mitigations mapped to version-qualified OWASP ASVS 5.0.0 requirement IDs - including tenant-isolation threats for multi-tenant SaaS. Use when designing or changing a system's architecture, adding an external integration (LLM provider, webhooks, payment), preparing a security design review, or checking that every trust-boundary crossing has analysed threats and that cited ASVS IDs exist.
license: CC BY-SA 4.0 applies to assets/data/asvs-5.0.0-index.json (OWASP ASVS 5.0.0); other files per repository licence
metadata:
  pack: reliability-security
  version: "1.0.0"
  sources: "owasp-asvs"
---

# Data-flow threat modelling (STRIDE, mapped to ASVS 5.0.0)

## Purpose
Produce a threat model that a security reviewer can challenge: an explicit data-flow picture with
trust boundaries, threats for every boundary crossing, a risk rating for each, and mitigations tied
to verifiable OWASP ASVS 5.0.0 requirements — so design decisions, verification work and accepted
risks are all traceable.

## When to use
- New system or major feature design; new external integration (AI/LLM provider, webhook,
  identity provider, payment processor); new tenant or data-classification boundary.
- Before a security design review or a production readiness review (`sre-production-readiness`).
- After an incident that revealed an unmodelled path.

**Do not use when:** you need code-level findings (use `security-code-checks`); you need a full
ASVS verification plan for the whole application (use `security-asvs-controls` — this skill only
cites ASVS for specific mitigations); or you need organisation-wide secure-development evidence
(use `security-secure-development`).

## Inputs
Required
- Architecture description: components (external entities, processes, data stores), data flows,
  where trust changes (internet edge, tenant boundary, third parties, data tier).
- Asset list with classification (public / internal / confidential / restricted).
Optional
- Target ASVS level (1–3), existing controls, previous incidents, penetration test results.
- Template: `assets/templates/threat-model.json`.

## Procedure
1. **Scope and draw.** List components with type; draw flows; mark every flow that crosses a trust
   boundary (`crosses_boundary: true` + `boundary` ID). Record the assets each flow carries.
2. **Enumerate threats per boundary-crossing flow** with STRIDE: by default at least Tampering,
   Information disclosure and Denial of service per flow (the STRIDE-per-element convention for
   flows); for internet-facing or privileged flows set `required_categories` to `STIDE` or `STRIDE`.
   Add Spoofing/Repudiation/Elevation threats on the processes at each end. If a category truly
   does not apply, record it under `not_applicable` with a reason.
3. **Multi-tenant systems** (`multi_tenant: true`): model tenant-isolation threats explicitly and
   flag them `tenant_isolation: true` — tenant ID taken from the request, queries missing the tenant
   filter, cross-tenant caches/queues/AI context, background jobs running in the wrong tenant.
4. **Rate** each threat: likelihood and impact (low/medium/high). Risk = product on a 1–3 scale:
   ≥ 6 high, 3–4 medium, ≤ 2 low.
5. **Mitigate**: for each threat write the control, its status (planned / implemented / verified)
   and the ASVS requirement(s) that verify it, cited as `v5.0.0-<chapter>.<section>.<req>`. Choose
   IDs by reading the requirement text in ASVS 5.0.0 — the bundled index holds IDs, levels and
   section titles only. Tenant-isolation threats should cite V8 (Authorization) requirements.
6. **Decide residual risk**: high risks need a mitigation or an explicit `accepted`/`transferred`
   status with `accepted_by` (a named risk owner) and `acceptance_rationale`.
7. **Check**: `python3 scripts/threat_model_check.py threat-model.json` — fix every error.
8. **Review**: hand to `security-reviewer` for challenge; feed cited ASVS IDs into the
   `security-asvs-controls` verification map; re-run when the architecture changes.

## Decision criteria
| Situation | Rule |
|---|---|
| Flow crosses a trust boundary | ≥ 1 threat for each required category (default T, I, D), else justified N/A. |
| Internet-facing flow or one carrying credentials/tokens | Require `STIDE` on the flow. |
| Sensitive asset crossing a boundary in clear text | Error — redesign (TLS) before anything else. |
| High risk, no mitigation, not accepted | Error — blocks the design review. |
| High risk with only planned mitigations | Warning — track to implementation before launch. |
| Risk accepted/transferred | Named risk owner + rationale; high risks need recorded sign-off by a human. |
| Multi-tenant system with no tenant-isolation threat | Error. |
| Unversioned (`1.2.5`) or v4 ASVS IDs | Error — v4 and v5 numbering differ; re-map against 5.0.0. |

## Outputs
- `threat-model.json` (schema `assets/schemas/threat-model.schema.json`).
- Check report (`--json`), schema `assets/schemas/findings-report.schema.json`, including STRIDE
  coverage per boundary-crossing flow and the list of cited ASVS IDs.
- `threat-model-review.md` — diagram, review notes, accepted risks with owners.

## Validation
- `python3 scripts/threat_model_check.py model.json --json` → exit 0 = structurally complete for the
  configured categories, no unmitigated/unowned high risks, all ASVS IDs exist in 5.0.0. `--strict`
  also blocks on warnings; `--categories STRIDE` raises the bar for every crossing flow.
- PASS does **not** mean the system is secure, that the threat list is complete, or that a cited
  ASVS requirement actually addresses the threat — those are human judgements.

## Examples
- `assets/examples/threat-model-pass.json` — AI Operations Platform (multi-tenant AI CRM and
  scheduling SaaS): browser, API, shared-schema tenant DB, LLM provider, calendar webhooks, worker;
  15 threats including cross-tenant read, tenant-ID tampering, prompt injection and wrong-tenant
  background jobs → exit 0.
- `assets/examples/threat-model-fail.json` → exit 1 with `no-tenant-isolation-threat`,
  `missing-stride-coverage`, `unmitigated-high`, `asvs-unversioned`, `asvs-version-mismatch`,
  `asvs-unknown-id`, `unknown-boundary`, `stride-category`, `acceptance-incomplete`,
  `mitigated-without-implementation`, `na-without-justification`.

## Escalation and stop conditions
- **Stop and escalate** to the `security-reviewer` agent and the system owner when a high risk has no
  credible mitigation, when tenant isolation depends on a single control, or when personal or
  regulated data goes to a third party without a recorded agreement.
- Risk acceptance is a human decision: the script never accepts risk; it only checks that an owner
  and rationale are recorded.
- Use `independent-reviewer` for a challenge review of models protecting high-impact assets.

## References
- `owasp-asvs` — OWASP ASVS 5.0.0 (tag `v5.0.0`): `0x03-What-is-the-ASVS.md` § "How to Reference ASVS
  Requirements" (version-qualified IDs) and level sections; chapter files for V1–V17. Index:
  `assets/data/asvs-5.0.0-index.json` (345 requirements: L1 70, L2 183, L3 92), copied from
  `sources/extracts/owasp-asvs-5.0.0-index.json`. Verified: `sources/audits/owasp-asvs.md`.
  Source ID: `owasp-asvs`.
- Licence: the bundled index is an adaptation of OWASP ASVS 5.0.0 © The OWASP Foundation,
  CC BY-SA 4.0; it remains under CC BY-SA 4.0 (see the `licence_notice` in the file).
- **STRIDE is Microsoft's threat-classification mnemonic**; it does not come from any source in this
  library's registry. The STRIDE-per-element default (T, I, D for data flows) is common practice
  stated from general knowledge *(unverified against a primary source here)*.
- Method notes: [references/stride-method.md](references/stride-method.md).
