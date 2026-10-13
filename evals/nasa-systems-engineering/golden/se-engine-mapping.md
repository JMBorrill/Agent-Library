# Mapping current practice to the NASA SE engine

The NASA SE Handbook Rev 2 describes 17 common technical processes in three groups: system design
(1-4), product realization (5-9) and technical management (10-17); processes 1-9 are the tasks that
execute the project and 10-17 are crosscutting [nasa-se 2.1, p. 18]. List: `python -m agentlib nasa-se processes`.

| # | Process | Group | What you do today | Gap / recommendation |
|---|---|---|---|---|
| 1 | Stakeholder Expectations Definition | System Design | Customer interviews, vision memo | Partial: capture needs, goals and objectives, MOEs and a ConOps incl. off-nominal scenarios |
| 2 | Technical Requirements Definition | System Design | User stories in tracker | Gap: no "shall" baseline; write validated requirements with rationale and verification method |
| 3 | Logical Decomposition | System Design | Architect's block diagrams | Partial: allocate requirements to airframe, avionics, ground software |
| 4 | Design Solution Definition | System Design | Whiteboard design reviews | Partial: record alternatives and trade studies; baseline the design |
| 5 | Product Implementation | Product Realization | Buy or build parts, code firmware | In place |
| 6 | Product Integration | Product Realization | Nightly hardware-in-the-loop | Partial: integration plan and procedures |
| 7 | Product Verification | Product Realization | HIL and flight tests | Partial: no requirement-by-requirement verification evidence |
| 8 | Product Validation | Product Realization | Flight tests at range | Partial: validate against the ConOps with representative users |
| 9 | Product Transition | Product Realization | Ship with quick-start guide | Partial: transition plan, training, acceptance documentation |
| 10 | Technical Planning | Technical Management | none | Gap: SEMP-like technical plan |
| 11 | Requirements Management | Technical Management | none | Gap: bidirectional traceability and change control |
| 12 | Interface Management | Technical Management | Ad hoc chat agreements | Gap: ICDs under control |
| 13 | Technical Risk Management | Technical Management | Stale spreadsheet | Gap: risk records with scenario, likelihood, consequence; periodic review |
| 14 | Configuration Management | Technical Management | Git for software only | Gap: CAD and documents under release control |
| 15 | Technical Data Management | Technical Management | Shared drive | Gap: controlled data repository |
| 16 | Technical Assessment | Technical Management | Informal reviews | Gap: life-cycle reviews with entry/success criteria and TPMs |
| 17 | Decision Analysis | Technical Management | Decisions in chat | Gap: decision matrices and decision reports |

## Priorities

1. Requirements Management and Technical Requirements Definition (largest gap, enables verification).
2. Configuration Management and Interface Management (uncontrolled CAD and interfaces).
3. Technical Risk Management and Technical Assessment (stale risks, informal reviews).

The engine is applied recursively and iteratively at each product layer [nasa-se 2.1, p. 20]; scale the
formality to the company (customisation, [nasa-se 3.11, p. 55]). This mapping supports, but does not replace,
your engineering leadership's judgement.
