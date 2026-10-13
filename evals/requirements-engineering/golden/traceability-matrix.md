# Rover mobility traceability matrix

Bidirectional: each requirement lists its parent; children are shown for the system level
[nasa-se 6.2, p. 163]. Stakeholder needs NGO-3 and NGO-4 are the baselined external parents.
Check: `python -m agentlib nasa-se trace mobility.csv --external NGO- --matrix`.

| ID | Level | Requirement | Parent | Children | Verification method |
|---|---|---|---|---|---|
| MOB-001 | system | The rover shall traverse at least 5 km over the mission on slopes up to 15 deg. | NGO-3 | WHL-001, WHL-002 | Test, Analysis |
| MOB-002 | system | The rover shall survive at least 14 Earth days of lunar night at -170 C. | NGO-4 | THM-001, THM-002 | Analysis |
| WHL-001 | subsystem | Each wheel motor shall deliver at least 3 Nm continuous torque. | MOB-001 | - | Test |
| WHL-002 | subsystem | The wheels shall have a grouser height of 10 mm +/- 1 mm. | MOB-001 | - | Inspection |
| THM-001 | subsystem | The RHU heater set shall provide at least 20 W to the battery enclosure. | MOB-002 | - | Analysis, Test |
| THM-002 | subsystem | The battery enclosure insulation shall limit heat loss to no more than 18 W at -170 C. | MOB-002 | - | Test |

Status: 6 requirements, no orphans, no dangling links, 100 % with a verification method; every system
requirement is allocated to subsystem requirements.
