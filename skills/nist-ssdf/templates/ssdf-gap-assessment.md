# SSDF v1.1 gap assessment report

> Framework: NIST SP 800-218, Secure Software Development Framework (SSDF) Version 1.1 (February 2022).
> Worksheet generated with `python -m agentlib ssdf assessment-template`; figures below are copied from
> `python -m agentlib ssdf check-assessment` - do not recompute by hand.

## 1. Scope and method

| Field | Value |
|---|---|
| Organisation | |
| Products / services in scope | |
| Teams | |
| SDLC model and delivery model | |
| Shared-responsibility providers (who does which tasks) | |
| Assessment period / date | |
| Assessor(s) and independence | |
| Evidence sources inspected | |
| Definitions adopted (sensitive data, qualified person, environments) | |

Method: task-by-task review of the 42 SSDF v1.1 tasks; statuses `implemented`, `partial`, `planned`,
`not-implemented`, `not-applicable`; evidence inspected for every implemented/partial task.

## 2. Overall result

- Self-assessed coverage: __% (tool formula: (implemented + 0.5 x partial) / applicable tasks)
- Fully implemented: __% of __ applicable tasks
- Counts by status: implemented __, partial __, planned __, not-implemented __, not-applicable __
- Validation: PASS / FAIL (list open errors in section 4)

This is a self-assessment against a framework that is "not ... a checklist"; it is not a compliance or
certification statement.

## 3. Results by practice group

| Group | Applicable | Implemented | Partial | Planned | Not implemented | Coverage |
|---|---|---|---|---|---|---|
| PO Prepare the Organization | | | | | | |
| PS Protect the Software | | | | | | |
| PW Produce Well-Secured Software | | | | | | |
| RV Respond to Vulnerabilities | | | | | | |

Practices with the lowest coverage: ...

## 4. Validation issues

| Level | Task | Issue | Resolution |
|---|---|---|---|
| | | | |

## 5. Prioritised gaps

Ordering starts from the tool heuristic (status severity, then EO 14028 Section 4e relevance from SP 800-218
Appendix A) and is adjusted for our risk context. SSDF itself does not prioritise practices.

| Rank | Task (PDF page) | Status | Why it matters here | Proposed action / evidence to produce | Owner | Target date |
|---|---|---|---|---|---|---|
| 1 | | | | | | |

## 6. Roadmap

| Horizon | Actions (task ids) | Dependencies | Owner |
|---|---|---|---|
| 0-30 days | | | |
| 31-90 days | | | |
| 3-12 months | | | |

## 7. Assumptions and limitations

- Self-assessment; evidence sampled, not exhaustively tested.
- Notional implementation examples were used as prompts, not requirements.
- Output supports, but does not replace, qualified professional judgement or formal attestation/approval.

## Appendix: evidence matrix

Attach the output of `python -m agentlib ssdf evidence-matrix <worksheet>`.
