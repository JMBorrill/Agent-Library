# Software Safety-Criticality Assessment - <system / component>

> NASA-STD-8739.8B 4.2 (pp. 15-16): software is safety-critical if it meets at least one criterion a-e;
> the determination is traceable to hazard analysis. NPR 7150.2D SWE-205 (p. 26): project manager with
> the SMA organization determines it. Run `python -m agentlib nasa-swe sc-assess --criteria <letters>`.

| Field | Value |
|---|---|
| Component / CSCI | <name, version> |
| Software class | <Class X> (Class E cannot be safety-critical - NPR p. 85) |
| Hazard analyses / reports reviewed | <ids> |
| Assessor(s) | <engineering>, <SA / software safety> |
| Date | <yyyy-mm-dd> |

## Criteria

| 4.2 | Criterion | Met? | Evidence (hazard report, cause/control id, function) |
|---|---|---|---|
| a | Causes or contributes to a system hazardous condition/event | <yes/no> | <> |
| b | Provides control or mitigation for a system hazardous condition/event | <yes/no> | <> |
| c | Controls safety-critical functions | <yes/no> | <> |
| d | Mitigates damage if a hazardous condition/event occurs | <yes/no> | <> |
| e | Detects, reports, and takes corrective action if the system reaches a potentially hazardous state | <yes/no> | <> |

Safety-critical determination: <Yes / No>

## Consequences if Yes
- NPR 7150.2D SWE-023, SWE-134 (a-l), SWE-219 (100 % MC/DC), SWE-220 (cyclomatic complexity <= 15).
- SA/SS tasks: `python -m agentlib nasa-swe sa-tasks --swe SWE-205` (and SWE-134, SWE-219, SWE-220).
- Traceability of software requirements to hazards (SWE-052) and test of hazard-related requirements (SWE-192).

## Independent means of protection considered (Note to 4.2)
<software, hardware, barriers, administrative controls>

## Concurrence
| Role | Name | Decision | Date |
|---|---|---|---|
| Project manager / software lead | | | |
| SMA (software safety) | | | |

Re-assess when hazards, design, operations or class change.
