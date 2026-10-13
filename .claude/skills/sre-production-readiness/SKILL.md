---
name: sre-production-readiness
description: Run a production or launch readiness review covering SLOs, monitoring, alerting, capacity, dependencies, rollback, runbooks, on-call, security sign-off, backup/restore testing and feature flags, with evidence references per item, and produce a GO / GO_WITH_CONDITIONS / NO_GO recommendation where no tested rollback, no staffed on-call, no SLO or an untested restore always block. Use before launching a new service or major feature, before moving a beta to general availability, or when auditing whether a service is still fit to run in production.
metadata:
  pack: reliability-security
  version: "1.1.0"
  sources: "google-sre"
---

# Production readiness review

## Purpose
Decide, with evidence, whether a service or feature is ready to take production traffic — and if
not, exactly what must happen first. The output is a recommendation with named blocking items and
owned conditions, for an accountable human to sign off.

## When to use
- New service, major feature or architectural change going to production.
- Beta → general availability; onboarding a large tenant; entering a new region.
- Periodic re-review of a service that has drifted (ownership change, repeated incidents).

**Do not use when:** you only need an SLO (use `sre-service-level-objectives`) or a security
assessment (use `security-threat-model` / `security-asvs-controls` and feed their result into the
security item); or for a routine deploy covered by normal CI/CD gates.

## Inputs
Required
- Readiness checklist JSON (template `assets/templates/readiness-checklist.json`, schema
  `assets/schemas/readiness-checklist.schema.json`) with one or more items per area, each with
  status (`done | partial | not_done | na`), evidence reference, owner and due date for open items.
- Named reviewers (service owner, SRE/reliability, security).
Optional
- `blocking_items` in the checklist (or `--blocking key,key` on the command line): project-defined
  launch blockers by item key or id, e.g. `security_isolation_tested`, `tool_enforcement_tested`,
  `dpia_complete` for a multi-tenant AI product.
- Launch date, traffic forecast, SLO spec, threat model, restore test record, rollback drill record.

## Procedure
1. **Schedule the review** early enough (library default: at least 2 weeks before launch) for
   NO_GO items to be fixed.
2. **Fill the checklist** — one item per question, evidence that someone else can open:
   - `slo` (key `slo_defined`): SLO spec validated (`sre-service-level-objectives`).
   - `monitoring`, `alerting`: SLI dashboards; burn-rate alerts tested; alerts link to runbooks.
   - `capacity`: load test against forecast peak with headroom; scaling limits and quotas known.
   - `dependencies`: each upstream/downstream with failure mode, timeout, retry/backoff, fallback.
   - `rollback` (key `rollback_tested`): rollback rehearsed and timed, including data/schema changes.
   - `runbooks`: for top alerts and known failure modes.
   - `oncall` (key `oncall_staffed`): rota staffed, trained, with escalation path.
   - `security`: threat model reviewed and security sign-off recorded. Split it into separate keyed
     items (tenant isolation tested, tool enforcement tested, DPIA complete) and list the ones that
     must block in `blocking_items` — by default security gaps only add conditions.
   - `backup_restore` (key `restore_tested`): restore actually performed and timed (RPO/RTO);
     `na` only with justification (stateless service).
   - `feature_flags`: launch behind a flag/kill switch, with the flag's owner and removal plan.
3. **Check**: `python3 scripts/readiness_check.py readiness-checklist.json`
   (add `--blocking security_isolation_tested,dpia_complete` to try extra blockers without editing the file).
4. **Review meeting**: walk blocking items first, then conditions. Every condition needs an owner and
   a date; agree which conditions must close before launch vs after.
5. **Record the human decision** (who decided, when, which conditions) next to the script's
   recommendation. Re-run after fixes.

## Decision criteria
| Situation | Recommendation |
|---|---|
| Any of: no SLO, rollback not tested, on-call not staffed, restore not tested (or blocking item done without evidence) | NO_GO |
| Any project blocking item (`blocking_items` / `--blocking`) missing, not done, N/A, or done without evidence | NO_GO |
| Checklist invalid (unknown area/status, duplicate IDs, `blocking_items` not a list of strings) | NO_GO until corrected |
| No security item done with evidence | warning `no-security-evidence` + condition (GO_WITH_CONDITIONS at best) |
| Non-blocking item partial/not done, done without evidence, unjustified N/A, area not reviewed | GO_WITH_CONDITIONS |
| Everything done with evidence (justified N/A allowed) | GO |
| Launch date pressure vs NO_GO | Escalate to the accountable executive; the script's recommendation does not change. |

The four library blocking items are fixed; projects add their own with `blocking_items` or
`--blocking` (a project blocker can never be satisfied by `na`). Unless a project lists them, an
open security item is a condition, not a blocker — decide this explicitly for products handling
personal data, multiple tenants or agent tools.

## Outputs
- Readiness report (`--json`), schema `assets/schemas/readiness.output.schema.json`: recommendation,
  blocking failures, project blocking items, conditions with owner/due, `requires_human_signoff: true`.
- `readiness-review.md` — decision record with reviewer names and agreed conditions.

## Validation
- `python3 scripts/readiness_check.py checklist.json --json` → exit 0 = GO or GO_WITH_CONDITIONS;
  exit 1 = NO_GO; exit 2 = unreadable/invalid JSON.
- PASS (GO) does **not** mean the service is reliable or secure; it means the checklist as written
  shows evidence for each item. Reviewers must open the evidence.

## Examples
- `assets/examples/readiness-pass.json` (AI ops scheduling engine) → GO, exit 0.
- `assets/examples/readiness-conditions-pass.json` (mortgage-criteria comparison view) →
  GO_WITH_CONDITIONS (`open-item`, `na-without-justification`), exit 0.
- `assets/examples/readiness-fail.json` (AI call summaries) → NO_GO, exit 1: `blocking-item-not-done`
  (slo_defined, rollback_tested), `blocking-no-evidence` (restore_tested), `blocking-item-missing`
  (oncall_staffed); warnings `condition-no-owner`, `area-not-covered`.
- `readiness-pass.json --blocking dpia_complete` → NO_GO, exit 1 (`blocking-item-missing`): the
  same checklist fails once the project makes a DPIA a launch blocker.

## Escalation and stop conditions
- NO_GO with a fixed launch date → escalate to the service owner's manager and the accountable
  executive with the blocking list; do not reclassify blocking items to make the date.
- Security item without sign-off → `security-reviewer`; reliability items → `reliability-engineer`.
- The final GO is a human decision recorded with names; never present the script output as approval.

## References
- `google-sre` — SRE book Part III practices and launch coordination concepts *(chapter references
  unverified; source INACCESSIBLE — `sources/audits/google-sre.md`)*. Claimed licence CC BY-NC-ND 4.0:
  no text adapted; the checklist areas, blocking rules and recommendation logic are this library's
  own, written from general industry practice. Source ID: `google-sre`.
- Related skills: `sre-service-level-objectives`, `sre-incident-response`, `security-threat-model`,
  `security-asvs-controls`.
- Method notes: [references/readiness-areas.md](references/readiness-areas.md).
