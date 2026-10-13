# Safety-criticality assessment - PIVC software

Assessed with `python -m agentlib nasa-swe sc-assess --criteria b,e`.

Safety-critical determination: **Yes**

| 4.2 | Criterion | Met | Evidence |
|---|---|---|---|
| a | Causes or contributes to a system hazardous condition/event | Not claimed (an erroneous open command could contribute - examine in the software safety analysis) | HR-07 |
| b | Provides control or mitigation for a system hazardous condition/event | Yes | HR-07 control 2.1 (valve closure) |
| c | Controls safety-critical functions | Not assessed separately | - |
| d | Mitigates damage if a hazardous condition/event occurs | No | - |
| e | Detects, reports, and takes corrective action if the system reaches a potentially hazardous state | Yes | Over-pressure detection, alarm telemetry, autonomous closure |

Rule: software is safety-critical if it meets at least one of criteria a-e [nasa-software-assurance 4.2 b, p. 15]
[nasa-software-assurance 4.2 e, p. 16]; the determination must be traceable to hazard analysis - here HR-07
(Note to 4.2). The independent burst disk is recorded as another means of protection but does not change
the determination.

## Consequences

- NPR 7150.2D SWE-023, SWE-134 (items a-l), SWE-219 (100 % MC/DC) and SWE-220 (cyclomatic complexity
  15 or lower) apply to the PIVC components [nasa-software-requirements SWE-134, p. 26]
  [nasa-software-requirements SWE-219, p. 26] [nasa-software-requirements SWE-220, p. 27].
- Requirements tracing to HR-07 must be verified by test (SWE-192) [nasa-software-requirements SWE-192, p. 37].
- SA tasks for SWE-205: confirm the hazard report contains the software contributions, confirm
  requirement-to-hazard traceability and maintain the software safety analysis
  [nasa-software-assurance Table 1 SWE-205, p. 26].

The determination is made by the project manager with the SMA organization (SWE-205); this assessment is
the SA input, pending SMA Technical Authority concurrence.
