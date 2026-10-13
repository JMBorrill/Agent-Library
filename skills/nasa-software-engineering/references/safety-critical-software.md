# Safety-critical software under NPR 7150.2D

Pages: NPR 7150.2D (`nasa-software-requirements`) unless marked 8739.8B (`nasa-software-assurance`).

## Determination

- SWE-205 (p. 26, Classes A-E): the project manager, with the SMA organization, determines whether each
  software component is safety-critical per the criteria in NASA-STD-8739.8.
- NASA-STD-8739.8B 4.2 (8739.8B pp. 15-16): software is safety-critical if it meets at least one of:
  a. causes or contributes to a system hazardous condition/event; b. provides control or mitigation for
  a system hazardous condition/event; c. controls safety-critical functions; d. mitigates damage if a
  hazardous condition/event occurs; e. detects, reports and takes corrective action if the system
  reaches a potentially hazardous state. The determination is traceable to hazard analysis (Note, 8739.8B
  p. 16).
- Tool: `python -m agentlib nasa-swe sc-assess --criteria b,e` (or `--answers file.yaml` with a..e).
- Class E software cannot be safety-critical; safety-critical software is Class D or higher (p. 85).
- The Center SMA Director assures hazard analyses include software; differences in independent
  safety-critical determinations are worked through the ETA and SMA TA (2.1.6.2 and Note, pp. 15-16).

## Triggered requirements (Classes A-D in Appendix C)

| SWE | Para, p. | Requirement in brief |
|---|---|---|
| SWE-023 | 3.7.2, p. 26 | Implement the safety-critical software requirements in NASA-STD-8739.8. |
| SWE-134 | 3.7.3, p. 26 | For safety- or mission-critical software, implement items a-l: known safe state at start/restart; safe transitions between predefined states; termination to a safe state; operator overrides need two independent actions; reject hazardous out-of-sequence commands; detect inadvertent memory modification and recover; integrity checks on inputs/outputs; prerequisite checks before safety-critical commands; no single event or action initiates an identified hazard; respond to off-nominal conditions in time; error handling; ability to place the system in a safe state. |
| SWE-219 | 3.7.4, pp. 26-27 | 100 percent code test coverage using MC/DC for all identified safety-critical components; deviations reviewed and waived with rationale by the TAs (Note, p. 27). |
| SWE-220 | 3.7.5, p. 27 | Cyclomatic complexity of 15 or lower for identified safety-critical components; any exceedance reviewed and waived with rationale by the project manager or technical approval authority. |

Related requirements that carry hazard content: SWE-184 safety constraints in requirements (p. 32),
SWE-052 traceability of software requirements to hazards (p. 31), SWE-192 test requirements that trace to
hazards (p. 37), SWE-062 unit testing of safety-critical software following 3.7.4 (Note, pp. 34-35),
SWE-135 static analysis including complexity and coverage (p. 34).

## What software assurance does (NASA-STD-8739.8B Table 1)

- SWE-205 tasks (8739.8B pp. 26-27): confirm hazard reports contain all known software contributions;
  assess that hazard analyses identify software components per Appendix A; confirm traceability between
  software requirements and hazards; develop and maintain a software safety analysis.
- SWE-134 tasks (p. 27): analyze requirements/design for items a-l; assess source code at inspections and
  reviews; confirm testing of safety-critical loaded/uplinked data; analyze partitioning/isolation.
- SWE-219 / SWE-220 tasks (p. 28): confirm 100 % coverage or a developer risk assessment; confirm
  complexity <= 15 or a developer risk assessment.

Use `python -m agentlib nasa-swe sa-tasks --swe SWE-134` for the verbatim tasks.

## Planning checklist

- [ ] Safety-critical determination per component recorded with SMA concurrence and hazard-report trace.
- [ ] SWE-134 items a-l allocated to requirements and design elements, with verification method.
- [ ] MC/DC tooling selected, coverage reported per component; uncovered code dispositioned.
- [ ] Complexity measured; components > 15 restructured or waived with rationale.
- [ ] Hazard-tracing requirements verified by test (SWE-192); test witnessing by SA planned.
