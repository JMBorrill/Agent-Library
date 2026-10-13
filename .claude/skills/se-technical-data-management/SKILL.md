---
name: se-technical-data-management
description: Plan and audit how technical data (requirements, models, drawings, test data, reviews, records) is identified, owned, classified, stored, access-controlled, retained and kept as a single source of truth, including personal-data and export-control flags and credential hygiene. Use when setting up project data storage, onboarding a team, preparing for an audit or transition, or checking a data register for missing owners, conflicting copies, embedded credentials or unbounded retention.
metadata:
  pack: systems-engineering
  version: "1.0.0"
  sources: "nasa-se-manage nasa-se"
---

# Technical data management

## Purpose
Ensure the right people can find the authoritative version of every technical record — and nobody
else can — for as long as it is needed and no longer. Corresponds to the NASA process *Technical Data
Management* (see References).

## When to use
- Project start (decide repositories, naming, classification, retention).
- Before audits, reviews or transition (evidence must be retrievable).
- When duplicates or "which version is right?" questions appear.
- When personal data, export-controlled or confidential data enters the project.

**Do not use when:** designing a production application's data model or privacy controls (use
`security-threat-model`, `security-asvs-controls`); this skill manages *project* records.

## Inputs
Required: data register CSV (`assets/templates/data-register.csv`).
Optional: organisational classification scheme, retention policy, access-control roles.

## Procedure
1. **Inventory** data items: registers, models, CAD, test data, review records, decisions, code releases.
2. **Assign** owner, classification (public/internal/confidential/restricted/export_controlled), location
   (system of record), retention, access roles, and whether the entry is the source of truth.
3. **One source of truth** per item; copies are marked as copies and point to the source.
4. **Personal data**: record lawful basis and minimise; involve the data-protection lead.
5. **Never store credentials** in locations, registers or repositories; use a secrets manager.
6. **Check**: `python3 scripts/data_register_check.py register.csv --as-of YYYY-MM-DD`
7. **Review periodically** and at transition; archive or dispose per retention.

## Decision criteria
| Finding | Action |
|---|---|
| `credential-in-location` | Remove immediately, rotate the credential, notify the owner (the script redacts values) |
| `multiple-sources-of-truth` | Choose one; mark others as copies or delete |
| `personal-data-no-basis` | Stop processing until the data-protection lead records a basis |
| `export-control-review` | Qualified export-control officer confirms handling before sharing |
| `unbounded-retention` | Bound retention or record justification |

## Outputs
`data-register.csv`, data management notes (repositories, naming, classification), check report.

## Validation
Exit 0 ⇒ register entries complete and consistent with the rules above. It cannot verify that access
controls are actually enforced or that classification is legally correct.

## Examples
- `assets/examples/data-register-pass.csv --as-of 2026-10-13` → exit 0.
- `assets/examples/data-register-fail.csv` → exit 1: `duplicate-id`, `missing-owner`, `classification`,
  `credential-in-location`, `no-access-control`, `personal-data-no-basis`, `multiple-sources-of-truth`.

## Escalation and stop conditions
- Credentials or personal data found in the wrong place → notify the owner and security/data-protection
  lead; do not copy the value anywhere (including reports).
- Export-controlled technical data → qualified human review before any sharing.

## References
- `nasa-se-manage` — Technical Data Management §6.6 *(secondary corroboration only; see
  `sources/audits/nasa-se-manage.md`)*.
