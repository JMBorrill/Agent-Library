# Profiles, gap analysis and AI risk registers

## AI RMF profiles (Section 6, PDF pp. 38-39, printed pp. 33-34)

- **Use-case profiles** implement the functions, categories and subcategories for a specific setting
  or application (examples given: hiring, fair housing).
- **Temporal profiles**: a **Current Profile** indicates how AI is currently being managed and related
  risks in terms of current outcomes; a **Target Profile** indicates outcomes needed to achieve the
  desired AI risk management goals.
- Comparing Current and Target Profiles reveals **gaps**; action plans address them; prioritisation is
  driven by the user's needs and risk management processes; the comparison also helps gauge resources
  (staffing, funding).
- **Cross-sectoral profiles** cover risks common across sectors (e.g. use of large language models,
  cloud services, acquisition) (PDF p. 39).
- The Framework **does not prescribe profile templates** (PDF p. 39). The worksheet below is a library
  convention.

## Profile worksheet (library convention)

Generate: `python -m agentlib ai-rmf profile-template [--functions GOVERN MAP] --format md|csv|yaml`.

| Column | Meaning |
|---|---|
| subcategory | AI RMF id, e.g. `GOVERN 1.6` |
| outcome | Verbatim outcome from Tables 1-4 (do not edit) |
| current_status / target_status | `not-implemented` < `partially-implemented` < `largely-implemented` < `implemented`; or `not-applicable` |
| priority | `high`, `medium`, `low` |
| owner | Named role accountable for closing the gap |
| evidence | Document, record, log, test report (**required** when current is `implemented`) |
| notes | Rationale; **required** justification for `not-applicable` (warning otherwise) |

Status guidance:
- `implemented` - outcome achieved for the scope, operating, evidenced.
- `largely-implemented` - in place with minor gaps; evidence partial.
- `partially-implemented` - started or ad hoc; significant gaps.
- `not-implemented` - absent.
- `not-applicable` - outcome irrelevant to scope; say why (e.g. no third-party data for GOVERN 6.2 is rare - challenge it).

`python -m agentlib ai-rmf check-profile <file>` returns errors for unknown ids, duplicates, missing
in-scope subcategories, missing/invalid statuses, invalid priority and `implemented` without evidence;
warnings for gaps without owner/priority, target below current, N/A without justification. The report
summarises by function and category and lists gaps (target > current) high priority first. Scope comes
from `--functions`, or `profile.functions` in YAML, else all four functions.

Gap action plan: for each gap give the action (cite Playbook items, e.g. `GOVERN 1.6/action-1`),
owner, due date, dependency, evidence that will prove closure, and the target status.

## AI risk register

AI RMF anchors:
- Risk is a function of the magnitude of harm and likelihood (Section 1.1, PDF p. 9).
- Prioritise treatment by impact, likelihood and available resources (MANAGE 1.2, PDF p. 37).
- Responses: **mitigating, transferring, avoiding, or accepting** (MANAGE 1.3, PDF p. 37).
- Document negative residual risks to downstream acquirers and end users (MANAGE 1.4, PDF p. 37);
  residual risk = risk remaining after treatment (PDF p. 13).
- Likelihood and magnitude of each identified impact are documented (MAP 5.1, PDF p. 32).
- Executive leadership takes responsibility for AI risk decisions (GOVERN 2.3, PDF p. 28).
- Playbook GOVERN 1.3 "About": risk score ≈ impact x likelihood placed on a qualitative (e.g. RAG) or
  quantitative scale (Playbook PDF p. 9).

Required fields checked by `python -m agentlib ai-rmf check-register <file>` (YAML/JSON/CSV/MD):

| Field | Accepted header aliases | Rule |
|---|---|---|
| id | id, risk_id, ref | unique |
| description | description, risk, title | event, cause, consequence |
| stakeholders | affected_stakeholders, stakeholders, affected_parties | include non-users |
| characteristics | trustworthiness_characteristics, characteristics | one or more of the 7 (aliases like "fairness", "privacy" accepted) |
| likelihood, impact | likelihood, impact (or severity) | 1-5 or words (rare..almost certain; negligible..severe) |
| inherent_rating | inherent_rating, inherent | low/medium/high/critical or 1-25 score |
| treatment | treatment, response | mitigate, transfer, avoid, accept |
| residual_rating | residual_rating, residual | as inherent |
| owner | owner, risk_owner | named role |
| subcategories | linked_subcategories, subcategories | valid AI RMF ids, `;`-separated |

Optional fields: controls, residual_likelihood, residual_impact, residual_justification,
escalated_to, accepted_by, review_date.

Consistency rules (errors): residual > inherent requires `residual_justification`; treatment `accept`
requires `accepted_by`; residual `high` or `critical` requires `escalated_to` or `accepted_by`.
Warnings: inherent rating inconsistent with L x I on the library matrix, mitigate/transfer without
controls, mitigate with no rating reduction, no MEASURE/MANAGE link, no review date.

### Library rating matrix (convention - replace with the organisation's)

Score = likelihood (1-5) x impact (1-5): 1-4 **low**, 5-9 **medium**, 10-16 **high**, 20-25 **critical**.
Likelihood: 1 rare, 2 unlikely, 3 possible, 4 likely, 5 almost certain.
Impact: 1 negligible, 2 minor, 3 moderate, 4 major, 5 severe. Rate impact on the most affected
stakeholder group, not the average user; record the rationale.

If the organisation's matrix differs, keep its ratings and note the warnings as "different matrix" -
do not re-rate silently.
