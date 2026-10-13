# AI risk register

> Template (library convention). Machine-checkable forms: `python -m agentlib ai-rmf register-template
> --format yaml|csv|md`. Validate: `python -m agentlib ai-rmf check-register <file>`.
> Treatment options per MANAGE 1.3 (PDF p. 37): mitigate, transfer, avoid, accept.
> Residual risks to downstream acquirers and end users must be documented (MANAGE 1.4).

| Field | Value |
|---|---|
| System / version | |
| Register owner | |
| Risk matrix | organisation's matrix: ______ / library convention (L x I: 1-4 low, 5-9 medium, 10-16 high, 20-25 critical) |
| Escalation body for high/critical residual risk | |
| Last reviewed | |

| ID | Description | Affected stakeholders | Trustworthiness characteristics | Likelihood | Impact | Inherent rating | Treatment | Controls | Residual likelihood | Residual impact | Residual rating | Residual justification | Owner | Escalated to | Accepted by | Linked subcategories | Review date |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| R-01 | | | | | | | | | | | | | | | | | |

Guidance:
- Description = event + cause + consequence ("Because X, Y may happen, leading to Z for <group>").
- Characteristics: valid-reliable, safe, secure-resilient, accountable-transparent,
  explainable-interpretable, privacy-enhanced, fair-bias-managed.
- Link at least one MAP subcategory (where identified) and one MEASURE or MANAGE subcategory
  (how measured / treated), e.g. `MAP 5.1; MEASURE 2.11; MANAGE 1.3`.
- High/critical residual: record `Escalated to` or `Accepted by` (name, role, date).
- Residual higher than inherent needs a justification (e.g. new context).
