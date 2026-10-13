# Readiness areas: questions and acceptable evidence

Original to this library (general industry practice; the `google-sre` source was not accessible).

| Area | Key questions | Evidence that counts | Weak evidence |
|---|---|---|---|
| slo (blocking) | Which user journey? SLI, target, window, owner, exclusions, budget policy? | Validated SLO spec; dashboard of the SLI | *We aim for high availability* |
| monitoring | Can you see the SLI, saturation, errors, queue ages per tenant? | Dashboard links; synthetic checks | Default host metrics only |
| alerting | Do burn-rate alerts page the right rota? Tested? | Alert test record with synthetic errors | Alert rules never fired |
| capacity | Forecast peak, headroom, scaling limits, quotas (incl. third-party rate limits)? | Load test report vs forecast | Back-of-envelope estimate |
| dependencies | Failure modes, timeouts, retries with backoff, fallbacks, contacts? | Dependency table; game-day notes | Happy-path diagram |
| rollback (blocking) | How fast can we undo, including schema/data migrations? | Timed drill in staging and production canary | *We can redeploy the old version* |
| runbooks | Top alerts and failure modes covered and linked from alerts? | Runbook links in alert definitions | Wiki page with TODOs |
| oncall (blocking) | Who is on call from launch, trained, escalation path? | Rota export; training record | "The team will watch it" |
| security | Threat model reviewed, ASVS map status, sign-off? | Signed security review record | Scan report alone |
| backup_restore (blocking) | Backups exist **and** a restore was performed and timed (RPO/RTO)? | Restore test record | "Backups are enabled" |
| feature_flags | Can the feature be turned off per tenant without a deploy? Owner and removal plan? | Flag config, kill-switch test | Flag exists but untested |

## Why these four block
- **No SLO**: nobody can tell whether the launch is healthy or when to roll back.
- **Untested rollback**: the main mitigation for a bad launch may not work under pressure.
- **No on-call**: incidents will go unanswered.
- **Untested restore**: backups that have never been restored are a hypothesis, not a control.

## Conditions
A condition is acceptable only with an owner and a due date, and the review records whether it must
close before launch or may close after. Untracked conditions tend to become permanent risk.
