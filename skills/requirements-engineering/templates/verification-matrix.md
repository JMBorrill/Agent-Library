# Requirements Verification Matrix (VCRM): <Product / document>

> Columns follow NASA SE Handbook Rev 2 Table D-1 [nasa-se Appendix D, p. 254]. Include only "shall"
> requirements, each with a unique ID and its source document [nasa-se Appendix D, p. 253]. Verification
> Method must be Test, Analysis, Inspection or Demonstration (or a combination) [nasa-se 5.3, p. 121];
> modelling/simulation/similarity = Analysis.

| Requirement No. | Document | Paragraph | Shall Statement | Verification Success Criteria | Verification Method | Facility or Lab | Phase | Acceptance Requirement? | Preflight Acceptance? | Performing Organization | Results |
|---|---|---|---|---|---|---|---|---|---|---|---|
| <SYS-001> | <SRD-xxx> | <3.2.1> | <The ... shall ...> | <measurable pass/fail criteria> | <Test> | <lab> | <phase code> | Yes/No | Yes/No | <org> | <report id> |

Phase codes (example from Table D-1 footnote, p. 255): 1 Pre-Declared Development; 2 Formal Box-Level
Functional; 3 Formal Box-Level Environmental; 4 Formal System-Level Environmental; 5 Formal System-Level
Functional; 6 Formal End-to-End Functional; 7 Integrated Vehicle Functional; 8 On-Orbit Functional.

## Coverage summary
Paste `python -m agentlib nasa-se trace <file>` statistics: % with valid method, count per method,
% verified.

## Completion
Verification is complete when objective evidence of compliance (or an approved waiver) is documented and all
discrepancy and nonconformance reports are closed [nasa-se 5.3, p. 128].
