# Rewritten EPS requirements

Each original statement broke Appendix C rules (unverifiable or ambiguous terms, "will" instead of "shall",
two "shall"s, TBD, passive voice, operational statement, no rationale or verification method)
[nasa-se C.4, p. 252]. Rewritten set (lint: 0 errors, `python -m agentlib nasa-se lint-requirements`):

| ID | Requirement | Rationale | Verification method | Change |
|---|---|---|---|---|
| PWR-001 | The EPS shall provide at least 45 W orbit-average power to the loads listed in ICD-PWR-01 at end of life. | Power budget v3 sums bus and payload loads with 20 % margin. | Analysis, Test | Replaced "sufficient" and "as appropriate" with a value and the load list |
| PWR-002 | The battery assembly shall be replaceable by one technician within 30 minutes using standard hand tools. | Integration and test flow needs battery swaps without disassembly. | Demonstration | "will" is not a requirement; removed "user-friendly" and "and/or" |
| PWR-003 | The solar array shall complete deployment within 60 seconds of receiving the deploy command. | Power-positive attitude must be reached before battery depth of discharge exceeds 30 %. | Test | Split from the original compound statement |
| PWR-007 | The solar array shall have a first natural frequency of at least 50 Hz in the deployed configuration. | Avoids coupling with ADCS control bandwidth. | Analysis, Test | Replaced "robust" with a measurable criterion; "Simulation" recorded as Analysis |
| PWR-004 | The EPS shall dissipate no more than 12 W (TBR) in any operating mode. | Thermal design allocation; TBR to be closed by the power lead after the EM test, due at PDR. | Test | TBD replaced by best estimate marked TBR; stated positively |
| PWR-005 | The EPS shall regulate the main bus voltage to 28 V ± 0.5 V. | Load equipment input range per ICD-PWR-01. | Test | Active voice with tolerance |
| PWR-006 | The EPS shall report battery temperature in telemetry at least once every 10 seconds with an accuracy of ± 1 °C. | Enables ground monitoring of battery health described in the ConOps. | Test | Operator monitoring moved to the ConOps; product capability stated instead |

## TBR list

| ID | Item | Best estimate | Owner | Due |
|---|---|---|---|---|
| PWR-004 | EPS dissipation | 12 W | Power lead | PDR |

Notes: PWR-007 is a new ID because the original PWR-003 contained two requirements. The rationale values are
proposals for the team to confirm; this rewrite supports, but does not replace, the team's engineering review.
