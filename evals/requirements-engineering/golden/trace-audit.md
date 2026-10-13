# Traceability and verification audit

Tool run: `python -m agentlib nasa-se trace trace-set.csv --external NGO-` - 9 requirements, 4 errors,
1 info; 88.9 % with a parent; 77.8 % with a valid verification method (Test 4, Analysis 1, Inspection 2).

| Req | Issue | Handbook basis | Action |
|---|---|---|---|
| SUB-003 | Dangling parent: SYS-099 does not exist in the set | bidirectional traceability [nasa-se 6.2, p. 163] | Correct the parent (likely SYS-002 pointing) or add the missing system requirement |
| SUB-004 | Orphan: no parent and not marked self-derived | trace to a parent or treat as gold plating [nasa-se 6.2.1.2.3, p. 165] | Find the stakeholder need for spare mounting points or delete as gold plating |
| SUB-005 | Self-derived (coding standard) | self-derived requirements need concurrence from the next higher level [nasa-se 6.2.1.2.3, p. 165] | Obtain concurrence and record it |
| SUB-006 | No verification method | Table 4.2-2 verification method [nasa-se 4.2, p. 83] | Assign Test (momentum storage measurement) or Analysis |
| SUB-007 | "Simulation" is not a verification method | Methods of Verification [nasa-se 5.3, p. 121] | Record as Analysis (modeling and simulation are analysis) |

## Bidirectional status
- SYS-001 is allocated to SUB-001 and SUB-002; SYS-002 to SUB-006 and SUB-007. Both system requirements
  trace up to stakeholder needs NGO-1 and NGO-2.
- After the actions above, re-run `trace` and expect 0 errors.
