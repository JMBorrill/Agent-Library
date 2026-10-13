# Process tailoring — ASTER-01 low-gravity locomotion demonstrator (synthetic)

| ID | Process | Rigour | Skill | Artifacts |
|---|---|---|---|---|
| SE-01 | Stakeholder Expectations Definition | standard | `se-stakeholder-conops` | conops.md + stakeholders.csv + needs.csv |
| SE-02 | Technical Requirements Definition | standard | `se-requirements` | full register linted, traced to needs |
| SE-03 | Logical Decomposition | standard | `se-logical-decomposition` | function tree with allocation |
| SE-04 | Design Solution Definition | rigorous | `se-architecture-trades` | trade space + sensitivity + compliance matrix |
| SE-05 | Product Implementation | standard | `se-implementation-integration` | make/buy/reuse with unit acceptance |
| SE-06 | Product Integration | standard | `se-implementation-integration` | integration plan checked |
| SE-07 | Product Verification | rigorous | `se-verification-validation` | matrix + procedures + independent witness for critical items |
| SE-08 | Product Validation | standard | `se-verification-validation` | validation plan against MOEs |
| SE-09 | Product Transition | standard | `se-transition` | transition checklist |
| SE-10 | Technical Planning | standard | `se-technical-planning` | engineering plan + milestones |
| SE-11 | Requirements Management | standard | `se-requirements` | baseline + change control |
| SE-12 | Interface Management | rigorous | `se-interface-control` | ICDs baselined, both owners sign |
| SE-13 | Technical Risk Management | rigorous | `se-risk-analysis` | register + FMEA/hazard analysis + acceptance records |
| SE-14 | Configuration Management | rigorous | `se-configuration-management` | CI list + audits + baseline_diff on every release |
| SE-15 | Technical Data Management | standard | `se-technical-data-management` | data register |
| SE-16 | Technical Assessment | rigorous | `se-technical-assessment` | TPMs + independent reviews at each milestone |
| SE-17 | Decision Analysis | rigorous | `se-decision-analysis` | decision matrix + sensitivity + owner sign-off |

Reviews: SRR, PDR, CDR, TRR, SAR

Authorities:
- decision owner: ASTER Phase 1 project lead (synthetic) — approves baselines, gate decisions, tailoring
- safety authority: Laboratory test-safety authority (synthetic) — approves hazard analysis, physical test authorisation, residual safety risk

_Proposed by tailor_process.py; requires approval by the decision owner._
Scope: library heuristic; the decision owner approves the tailoring.
