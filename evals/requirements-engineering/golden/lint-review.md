# Review of communications requirements (draft C)

Tool run: `python -m agentlib nasa-se lint-requirements review-reqs.md` - 4 errors, 5 warnings.

| Req | Finding | Severity | Handbook basis | Suggested rewrite |
|---|---|---|---|---|
| COM-001 | No findings: single "shall", measurable bound, rationale and Test method | - | - | keep |
| COM-002 | Uses "will", which states a fact or purpose, so it is not a requirement; no rationale | error | C.1 [nasa-se C.1, p. 249] | The radio shall receive S-band uplink at <data rate> with BER no more than <value>. |
| COM-003 | Negative ("shall not") and passive voice | warning | C.3 / C.2 [nasa-se C.3, p. 250] | The antenna deployment mechanism shall remain stowed until the separation switch signal is received. |
| COM-004 | Two "shall" statements in one requirement (compound) | error | single "shall" per statement [nasa-se 4.2.1.2.3, p. 81] | Split into COM-004a (transmit telemetry) and COM-004b (receive commands), each with a measurable criterion |
| COM-005 | TBD value; minimise TBDs, use a best estimate marked TBR with owner and date | warning | C.3 [nasa-se C.3, p. 250] | The modem shall achieve a bit error rate of no more than 1E-6 (TBR) at the link-budget margin. |
| COM-006 | Ambiguous "etc." and unverifiable "user-friendly"; no rationale | error | C.4 Clarity and Verifiability [nasa-se C.4, p. 252] | The ground software shall display the start time, end time and maximum elevation of each pass for the next 7 days. |

## Summary
- Errors to fix before SRR: COM-002, COM-004, COM-006.
- Warnings to fix or disposition: COM-003, COM-005, missing rationale on COM-002 and COM-006.
- Human review still needed for technical correctness, feasibility and completeness (C.4), which the linter
  cannot judge.
