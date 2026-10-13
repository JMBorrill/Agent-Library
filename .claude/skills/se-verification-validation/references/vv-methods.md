# V&V methods and evidence notes (library guidance)

Original text. Concepts follow common systems-engineering practice; NASA SE Handbook §5.3–5.4 is the
registered source but was not readable in-session (see `sources/audits/nasa-se-realize.md`).

## Verification vs validation
| | Verification | Validation |
|---|---|---|
| Question | Does the product meet its specified requirements? | Does the product satisfy stakeholder needs in its intended use? |
| Traces to | Requirements (system, subsystem, component) | Stakeholder needs / ConOps scenarios / MOEs |
| Typical evidence | Test reports, analysis reports, inspection records | Operational demonstrations, user trials, field data |
| Can pass while the other fails? | Yes — a product can meet a wrong specification | Yes — users may be satisfied while a requirement is unmet |

## Levels and sequencing
Verify at the lowest level where the property is observable, then re-verify emergent properties at the
assembled level. Unit-level verification normally precedes integration (`se-implementation-integration`).

## Qualification vs acceptance (general practice)
*Qualification* demonstrates the design meets requirements with margin, often on a dedicated unit and
beyond operational levels; *acceptance* shows each produced unit is free of workmanship defects.
Programme standards (NASA, ECSS, customer) define the actual levels — not this library.

## Evidence record minimum
activity ID · requirement/need IDs · configuration (hardware rev, software version, setup) · procedure
reference and version · environment/conditions · raw data location · result · deviations · performer ·
independent reviewer · date.

## Simulation and models
A simulation result is analysis evidence only when the model is itself validated for the regime used,
inputs are configuration-controlled, and uncertainty is reported. Label "expected", "simulated" and
"measured" values separately in every report.

## Common failure patterns the checker catches
- Validation activity standing in for verification of a system requirement.
- "PASS" recorded from a planned procedure, not an executed one (no evidence/date).
- Results with no configuration — cannot be reproduced or re-used after a change.
- Same person performs and reviews.
