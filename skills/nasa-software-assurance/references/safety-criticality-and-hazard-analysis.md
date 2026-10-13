# Software safety-criticality assessment and hazard analysis

Pages: NASA-STD-8739.8B unless marked NPR (NPR 7150.2D).

## Criteria (4.2, pp. 15-16; also the definition in 3.2, pp. 12-13)

Software is classified as safety-critical if it meets at least one of:

| Letter | Criterion |
|---|---|
| a | Causes or contributes to a system hazardous condition/event |
| b | Provides control or mitigation for a system hazardous condition/event |
| c | Controls safety-critical functions |
| d | Mitigates damage if a hazardous condition/event occurs |
| e | Detects, reports, and takes corrective action if the system reaches a potentially hazardous state |

Note (p. 16): software is classified as safety-critical if it is determined by and traceable to hazard
analysis; consider other independent means of protection (software, hardware, barriers, administrative)
in the hazard definition process. NPR SWE-205 (NPR p. 26) assigns the determination to the project
manager in conjunction with the SMA organization.

Related definitions (3.2): Safety-Critical (p. 12, from NPR 8715.3), Mission Critical (p. 11), Hazard,
Hazard Analysis, Hazard Control, Inhibit (p. 11), Safe State (p. 12).

## Procedure

1. List software components and the system hazards / hazard reports they relate to.
2. For each component answer a-e with evidence (hazard report id, cause/control id).
3. `python -m agentlib nasa-swe sc-assess --criteria b,e` (or `--answers` YAML a..e: yes/no).
4. Record `Safety-critical determination: Yes|No`, the letters met, the hazard trace, SMA concurrence.
5. If Yes: SWE-023, SWE-134 (a-l), SWE-219 (MC/DC 100 %), SWE-220 (complexity <= 15) and the related
   SA tasks apply; check the class is D or higher (NPR p. 85).
6. Re-assess when hazards, design or operations change; keep the software safety analysis current
   (SWE-205 task 5, p. 27).

## SA tasks for SWE-205 (pp. 26-27)

1. Confirm hazard reports / safety data packages contain all known software contributions or events
   (action, inaction or incorrect action leading to a hazard).
2-3. Assess that hazard reports and hazard analyses identify the software components associated with
   system hazards per Appendix A.
4. Confirm traceability between software requirements and hazards with software contributions.
5. Develop and maintain a software safety analysis throughout the life cycle.

## Appendix A - software in hazard analyses (pp. 58-65)

- A.1.1 (p. 58): consider software's ability to cause or control a hazard; include software in the system
  hazard analysis; consider common-mode failures of redundant computers running the same software.
- A.1.2 (p. 58): software safety analysis supplements the system hazard analysis, assures compliance
  with levied functional requirements including SWE-134, protects independence of inhibits and hardware
  redundancy, identifies must-work and must-not-work functions in Phase 1 hazard reports, checks
  channelization of communication paths and redundancy management (e.g. no single-sensor trigger of a
  critical sequence in a single-fault-tolerant design).
- A.1.3 (p. 58): Phase 2 safety reviews complete the design analysis and support a requirements gap
  analysis (SWE-184); between Phase 2 and 3, test plans are analyzed for off-nominal scenarios
  (SWE-062, SWE-065a); in Phase 3, the final implementation is verified and test results permit closure
  of hazard verifications (SWE-068).
- A.1.4 / Table 2 (pp. 59-65): considerations when identifying software causes, in 12 areas: data errors;
  commanding errors; flight computer errors; operating systems errors; programmable logic device errors;
  flight system time management errors; coding, logic and algorithm failures / algorithm specification
  errors; fault tolerance and fault management errors; software processes errors; human-machine interface
  errors; security and virus errors; unknown/unknowns errors.

`python -m agentlib nasa-swe hazard-causes` prints the full checklist (each cause verbatim) as Markdown
check-boxes; use `--area command` etc. to filter.

## Output pattern

```
Safety-critical determination: Yes
Criteria met: 4.2 b (provides control for hazard HR-12 cause 3), 4.2 e (FDIR safing)
[nasa-software-assurance 4.2, p. 15]
Triggered: SWE-023, SWE-134, SWE-219, SWE-220 [nasa-software-requirements SWE-134, p. 26]
Concurrence: <SMA TA name/date> (pending)
```
