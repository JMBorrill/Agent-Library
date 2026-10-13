# Requirements Verification Matrix: SRD-ADCS rev B

Columns follow Table D-1 [nasa-se Appendix D, p. 254]. Only "shall" requirements are included
[nasa-se Appendix D, p. 253]; ADCS-006 is a goal ("should") and is excluded - track it as a goal or rewrite
it as a measurable "shall" requirement.

| Requirement No. | Document | Paragraph | Shall Statement | Verification Success Criteria | Verification Method | Facility or Lab | Phase | Performing Organization |
|---|---|---|---|---|---|---|---|---|
| ADCS-001 | SRD-ADCS rev B | 3.2.1 | The ADCS shall point the payload boresight to within 0.1 deg (3 sigma) of the commanded attitude. | Pointing error no more than 0.1 deg (3 sigma) over the science-mode cases in the pointing budget; HIL confirms controller performance | Analysis, Test | GNC lab (HIL) | 5 | GNC team |
| ADCS-002 | SRD-ADCS rev B | 3.2.2 | The ADCS shall detumble the spacecraft from 10 deg/s to below 0.5 deg/s within 3 orbits. | Monte Carlo detumble analysis shows rates below 0.5 deg/s within 3 orbits in all cases; on-orbit confirmation | Analysis | GNC lab | 8 | GNC team |
| ADCS-003 | SRD-ADCS rev B | 3.2.3 | The ADCS shall have a mass of no more than 1.8 kg. | Measured flight-unit mass of no more than 1.8 kg | Test | Integration lab scale | 2 | I&T team |
| ADCS-004 | SRD-ADCS rev B | 3.2.4 | The ADCS shall carry a red "Remove Before Flight" tag on the reaction wheel lock pin. | Tag present, red, legible | Inspection | Integration lab | 7 | Quality assurance |
| ADCS-005 | SRD-ADCS rev B | 3.2.5 | The ADCS shall allow the operator to command safe mode from the ground console within 5 seconds of a fault alarm. | Trained operator commands safe mode within 5 s in an end-to-end rehearsal | Demonstration | Mission operations center | 6 | Operations team |

Phase codes follow the Table D-1 footnote example (2 box-level functional, 5 system-level functional, 6
end-to-end, 7 integrated vehicle, 8 on-orbit) [nasa-se Appendix D, p. 255].

Coverage: 5 of 5 "shall" requirements have a method from Test, Analysis, Inspection or Demonstration
[nasa-se 5.3, p. 121].
