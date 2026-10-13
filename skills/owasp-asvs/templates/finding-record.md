# Finding record - <F-nn>: <short title>

| Field | Value |
|---|---|
| Finding id | F-<nn> |
| Status | <Open / Remediated / Risk accepted (by whom, date)> |
| Severity (verifier rating) | <Critical/High/Medium/Low + method, e.g. CVSS v4 vector> |
| ASVS requirement(s) failed | v5.0.0-<id> (L<n>) [owasp-asvs V<id>, p. <pdf page>] |
| Mapping confidence | <Confirmed by verifier / Suggested by map-findings, not yet confirmed> |
| Affected component / location | <URL, endpoint, file:line, commit> |
| Discovered / verifier | <date>, <name> |

## Description

<What is wrong, in terms of the requirement's security goal (use `asvs show <id>` for the exact text).>

## Evidence

<Requests/responses, screenshots, code excerpts, log lines; environment and timestamp. Reproducible steps.>

## Impact

<Plausible attacker, preconditions, consequence. Do not derive severity from the ASVS level.>

## Remediation guidance

<Goal-oriented fix; reference OWASP Cheat Sheet where helpful; how the retest will verify it.>

## Retest

| Date | Result | Evidence |
|---|---|---|
