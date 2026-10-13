# Source audit: `dora`

| Field | Value |
|---|---|
| Source ID | `dora` |
| Title (as verified) | "DORA’s software delivery performance metrics" (guide); "A history of DORA’s software delivery metrics" (insight); DORA capability catalog; DORA Guides |
| Publisher / author | DORA (Google LLC; `CC-BY-4.0` file states "Copyright 2026 Google LLC"); metrics guide and history authored by Nathen Harvey |
| Edition / version / effective date | Metrics guide front matter: date 2024-03-29, `updated: 2026-01-05`. History page: 2026-01-02. Most recent report referenced: "State of AI-assisted Software Development 2025" (research/2025 dated 2025-07-14) |
| Canonical URL (registry) | https://dora.dev/guides/ |
| URL(s) actually read | `https://raw.githubusercontent.com/dora-team/dora.dev/main/<path>` for paths in the access ledger (site page equivalent: https://dora.dev/guides/dora-metrics/) |
| Access status | VERIFIED for the metrics guide, metrics history, licence and FAQ; PARTIALLY_VERIFIED for the capability catalog (list discovered by probing, may be incomplete) |
| Access method | Official site-source GitHub repository raw files via curl. dora.dev itself not fetched (proxy blocks) |
| Date checked | 2026-10-13 |
| Licence / reuse terms (as verified) | Documentation, media and design assets: CC BY 4.0; source code: Apache License 2.0 (`README.md` § "Licensing"; `CC-BY-4.0` file; `LICENSE` = Apache 2.0). Note: annual PDF reports were not checked and may carry different terms |
| Normative status | Advisory (research-based practitioner guidance) |

## Access ledger
Base: `https://raw.githubusercontent.com/dora-team/dora.dev/main/`

Succeeded (200, read): `README.md`, `LICENSE`, `CC-BY-4.0`, `firebase.json` (redirects), `hugo/config.toml`, `docs/publishing-content.md`, `docs/README.md` (not used), `hugo/content/_index.md`, `hugo/content/guides/_index.md`, **`hugo/content/guides/dora-metrics/_index.md`**, **`hugo/content/insights/dora-metrics-history/index.md`**, `hugo/content/capabilities/_index.md`, `hugo/content/research/_index.md`, `hugo/content/research/2024/_index.md` (not used), `hugo/content/research/2025/_index.md`, `hugo/content/faq/_index.md`, `hugo/content/guides/how-to-transform/index.md` (not used), `hugo/content/quickcheck/_index.md` (not used), and 31 capability files `hugo/content/capabilities/<slug>/index.md` (front matter read: title, core, category).

Failed (404): root-level `content/...` paths, `hugo/hugo.toml`, `hugo/content/guides/dora-metrics/index.md`, `hugo/content/guides/dora-metrics-four-keys/index.md`, `hugo/content/guides/dora-metrics.md`, `hugo/content/metrics/*`, `hugo/content/core/_index.md`, `hugo/content/research/2026/_index.md`, several guessed data files (`hugo/data/capabilities.json` etc.), `CONTRIBUTING.md`. GitHub API (directory listing) blocked, so the capability list could not be enumerated authoritatively.

## Verified content
**Metrics guide** — `hugo/content/guides/dora-metrics/_index.md` (title "DORA’s software delivery performance metrics"):
- Five metrics; the callout says the model shifted from the original four keys to five (MTTR → Failed deployment recovery time).
- Metrics described as leading indicators for organisational performance and well-being, and lagging indicators for delivery practices.
- § "Throughput and instability" → "### Throughput": **Change lead time** (commit to version control → deployed in production), **Deployment frequency** (deployments per period or time between deployments), **Failed deployment recovery time** (time to recover from a deployment that fails and needs immediate intervention). "### Instability": **Change fail rate** (ratio of deployments needing immediate intervention, e.g. rollback or hotfix), **Deployment rework rate** (ratio of deployments that are unplanned and caused by a production incident).
- Observation: the current guide places Failed deployment recovery time under **Throughput**, not instability; the history page groups it the same way ("Software Delivery Throughput"). Recorded as written.
- § "Key insights": speed and stability are not trade-offs; best measured per application/service; context matters, blending across teams/organisations is problematic.
- § "Common pitfalls" (7): Setting metrics as a goal; Having one metric to rule them all; Using industry as a shield against improving; Making disparate comparisons; Having siloed ownership; Competing; Focusing on measurement at the expense of improvement.
- § "Next steps": reduce batch size; team loop — Set a baseline (Quick Check), Have a conversation, Have the whole team commit…, Turn that commitment into a plan, Do the work, Check your progress, Repeat.

**History** — `hugo/content/insights/dora-metrics-history/index.md`: 2014 four variables (deployment frequency, lead time for changes, MTTR, change fail rate; CFR excluded from that year's construct); 2015 throughput vs stability; 2018 availability added ("SDO performance"); 2021 reliability; 2023 MTTR/time to restore renamed and redefined as failed deployment recovery time (to exclude non-change failures); 2024 deployment rework rate added; two factors "Software Delivery Throughput" and "Software Delivery Instability". Note the history page gives slightly different short definitions (e.g. change fail rate as a percentage of deployments causing production failures; rework rate as unplanned deployments to fix bugs) — the guide's wording is used in the extract.

**Capabilities** — `hugo/content/capabilities/_index.md` (title "Catalog"); `docs/publishing-content.md` lists categories `fast flow`, `fast feedback`, `climate for learning` and a `core` front-matter flag. 31 capability pages confirmed by probing (slug / category / core flag):
- fast flow: continuous-delivery (core), database-change-management (core), deployment-automation (core), flexible-infrastructure (core), loosely-coupled-teams (core), streamlining-change-approval (core), version-control (core), working-in-small-batches (core), trunk-based-development (core: false), visual-management (no flag), wip-limits "Work in process limits" (no flag).
- fast feedback: continuous-integration (core), monitoring-and-observability (core), pervasive-security (core), test-automation (core), test-data-management (core), customer-feedback (no flag), proactive-failure-notification (no flag).
- climate for learning: code-maintainability (core), documentation-quality (core), generative-organizational-culture (core), job-satisfaction (core), well-being (core), learning-culture (no flag), team-experimentation (no flag), transformational-leadership (no flag).
- AI (core: false): ai-accessible-internal-data, clear-and-communicated-ai-stance, healthy-data-ecosystems, platform-engineering, user-centric-focus.

**Report year** — `hugo/content/faq/_index.md` sections cover "State of AI-assisted Software Development 2025", "ROI of AI-assisted Software Development", "DORA AI Capabilities Model", and Accelerate State of DevOps 2024/2023/2022; `hugo/content/research/2025/_index.md` "DORA Research: 2025 Overview" dated 2025-07-14. No 2026 research index found (404).

**Licence** — `README.md` § "Licensing", `CC-BY-4.0`, `LICENSE`.

Machine-readable extract: `sources/extracts/dora-metrics.json`.

## Secondary corroboration (not primary verification)
None used. `firebase.json` confirms `/guides/dora-metrics-four-keys` redirects to `/guides/dora-metrics/` (a repo file, but only routing evidence).

## Elements useful as AI skills
- Metric glossary with categories (5 metrics) — metrics guide § "Throughput and instability".
- Anti-pattern checklist for metric programmes (7 pitfalls) — § "Common pitfalls".
- Unit-of-analysis rule: per application/service; no cross-team league tables — § "Key insights", pitfalls "Making disparate comparisons", "Competing".
- Improvement loop (baseline → conversation → commit → plan → do → check → repeat) — § "Next steps".
- Terminology migration map (MTTR → failed deployment recovery time; four keys → five metrics) — history page.
- Capability catalog with Core flags as an improvement-option menu — capability front matter.

## Proposed skills, agents and tools
- Planned `software-delivery-metrics` and `software-improvement-experiment` (per `sources/framework-build-plan.json`); agents: Software quality reviewer, Reliability engineer.
- Tools: metric-definition schema (name, category, numerator/denominator, unit, per-service granularity) with a validator that rejects org-wide blended or cross-team comparison outputs and legacy names (MTTR) unless flagged as historical; pitfalls checklist; evaluation fixture checking definitions and data granularity.

## Limitations, applicability and copyright
- DORA does not prescribe precise computation formulas (e.g. what counts as a "failed" deployment); implementations must document their own operational definitions.
- Benchmarks/performance clusters from annual reports were not read; do not cite cluster thresholds from this audit.
- Capability list is probe-based and may omit pages; core flag missing on some pages (treat as unknown).
- Classification of failed deployment recovery time under throughput is as found in the 2026-01 guide; re-check, since older material treated recovery time as stability.
- CC BY 4.0 for site content: attribute DORA/Google LLC. Annual report PDFs' terms not verified.
- Living site on `main`; commit SHA not captured.

## Re-check by
2027-01-13 — check for a 2026 DORA report and any metric renaming/re-categorisation in `hugo/content/guides/dora-metrics/_index.md`; obtain a full capability listing (e.g. via clone) to confirm the catalog.
