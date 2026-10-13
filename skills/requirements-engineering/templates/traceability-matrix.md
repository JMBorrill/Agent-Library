# Requirements traceability matrix: <Product / document set>

> Bidirectional traceability: each requirement traces to its parent and to its allocated children
> [nasa-se 6.2, p. 163]. A requirement without a parent must be marked `self-derived` (with concurrence
> from the next higher level) or removed as gold plating [nasa-se 6.2.1.2.3, p. 165].
> Check with: `python -m agentlib nasa-se trace <file> --external <PARENT-DOC-PREFIX> --matrix`.

| ID | Level | Requirement | Parent | Children | Verification method | Status |
|---|---|---|---|---|---|---|
| <SYS-001> | system | <The ... shall ...> | <NGO-1> | <SUB-001, SUB-002> | <Test> | <open / verified> |
| <SUB-001> | subsystem | <The ... shall ...> | SYS-001 | - | <Analysis> | |

## Trace findings and dispositions

| Req ID | Finding (orphan / dangling / one-way / not allocated / self-derived) | Disposition | Owner | Date |
|---|---|---|---|---|

## Statistics
Requirements; % with parent; % with valid verification method; verified %; orphans; self-derived (awaiting
concurrence).
