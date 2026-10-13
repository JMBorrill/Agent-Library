---
name: se-configuration-management
description: Identify configuration items, establish versioned baselines, account for their status and audit that every difference between baselines is backed by an approved change request (no deletions instead of retirement, no reused retired IDs, no changes under rejected CRs). Use when setting up configuration control for a project, cutting a new baseline, preparing a configuration audit, or checking that requirements/ICD/risk registers changed only through approved changes.
metadata:
  pack: systems-engineering
  version: "1.0.0"
  sources: "nasa-se-manage nasa-se"
---

# Configuration management

## Purpose
Always know what the current approved configuration is, how it got there and which evidence applies
to which version. Corresponds to the NASA process *Configuration Management* (see References); the
change-assessment step itself is `se-change-control`.

## When to use
- Project start: decide what is under control (requirements, ICDs, drawings, software, test procedures,
  analysis models) and from which milestone.
- Cutting a baseline (e.g. after SRR, PDR, CDR) or a release.
- Before verification/acceptance: confirm tested configurations match the released configuration.
- Periodic configuration audits.

**Do not use when:** the artifact is exploratory and not yet relied on by others — premature control
slows learning; or for source-code branching strategy (use the repository's own process; register the
released version here as a configuration item).

## Inputs
Required: two versions of a controlled register (CSV with a key column), the change log
(`assets/templates/change-log.csv`).
Optional: configuration item list (`assets/templates/configuration-items.csv`), release notes.

## Procedure
1. **Identify configuration items (CIs)**: give each an ID, owner, type, version, storage location.
   Control interfaces and safety-related items first.
2. **Define baselines** and the milestone at which each register comes under control; record the
   approval authority (from `se-technical-planning`).
3. **Store baselines immutably** (tagged commits, versioned files) — never overwrite a released baseline.
4. **Control changes** through `se-change-control`; record each CR outcome in the change log.
5. **Audit each new baseline**:
   `python3 scripts/baseline_diff.py baseline-vN.csv baseline-vN+1.csv --changes change-log.csv`
   Every modification of a controlled item must cite an approved CR; retire rather than delete;
   never reuse retired IDs.
6. **Status accounting**: publish the baseline summary (added/removed/modified, open CRs, evidence
   invalidated) with the version identifier.
7. **Configuration audit before acceptance**: compare as-built/as-tested configuration identifiers in
   the V&V matrix with the released baseline; mismatches block acceptance claims.

## Decision criteria
| Finding | Disposition |
|---|---|
| `uncontrolled-change` / `rejected-cr-applied` | Revert or raise and approve a CR before releasing the baseline |
| `deleted-not-retired` | Restore the row with `status=retired` and a rationale |
| `retired-id-reused` | Restore retired content; allocate a new ID for the new item |
| `approval-without-cr` (warning) | Acceptable only if a baseline approval record exists — link it |
| `cr-not-implemented` (warning) | Implement, or update the CR status (deferred/withdrawn) |

## Outputs
Versioned baselines, `change-log.csv`, configuration item list, baseline audit report (`--json`),
status accounting summary.

## Validation
`baseline_diff.py` exit 0 ⇒ every change between the two files is accounted for by the change log under
the rules above. It cannot tell whether a change is wise or whether files outside the comparison
changed — audit each controlled register.

## Examples
- `baseline-v1.csv` → `baseline-v2-pass.csv` with `change-log.csv` → exit 0; warning
  `cr-not-implemented` for DEMO-CR-003.
- `baseline-v1.csv` → `baseline-v2-fail.csv` → exit 1: `deleted-not-retired`, `rejected-cr-applied`,
  `uncontrolled-change`, `retired-id-reused`; warning `approval-without-cr`.

## Escalation and stop conditions
- Uncontrolled change to a safety-related or contractual item → report to the configuration/change
  authority immediately; do not "fix" by editing the change log.
- The agent never marks a CR approved; approval comes from the named human authority.

## References
- `nasa-se-manage` — Configuration Management §6.5 *(secondary corroboration only; see
  `sources/audits/nasa-se-manage.md`)*.
