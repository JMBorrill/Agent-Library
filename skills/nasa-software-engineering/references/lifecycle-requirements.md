# Life-cycle requirements by activity (NPR 7150.2D Chapters 3-5)

Paraphrased guide to what each group of requirements asks of the project, with the SWE ids and the PDF
page where each paragraph starts. Classes show where Appendix C marks the requirement `X`
(abbreviated: "A-E" = A, B, C, D, E). For exact wording run `python -m agentlib nasa-swe show SWE-nnn`;
the full table is [requirements-index.md](requirements-index.md).

The NPR does not mandate a life-cycle model (1.1.4, p. 8; 1.3.3, pp. 9-10); map the requirements onto
the project's model (waterfall, iterative, agile) in the software development/management plan.

## 3.1 Planning (pp. 20-23)

| SWE | p. | Classes | What it asks |
|---|---|---|---|
| SWE-033 | 20 | A-F | Assess acquisition vs development options (acquire, develop in-house or by contract, enhance, reuse, external source). |
| SWE-013 | 20 | A-F | Develop, maintain and execute software plans (incl. security plans) covering the whole life cycle and the NPR with approved tailoring. |
| SWE-024 | 20 | A-D, F | Track actual results against plans; manage corrective actions and commitment changes to closure. |
| SWE-034 | 21 | A-D, F | Define and document software acceptance criteria. |
| SWE-036 | 21 | A-D, F | Establish processes, documentation plans, deliverables and tasks, and the Government action on each deliverable. |
| SWE-037 | 21 | A-D, F | Define milestones at which developer progress is reviewed and audited. |
| SWE-039 | 21 | A-D, F | Require developer status reporting and insight (integration, verification, trade studies, audits, reviews) for the PM and SA. |
| SWE-040, SWE-042 | 21 | 040: A-D, F; 042: A-F | Require electronic delivery of products, traceability, change and non-conformance data, metrics, and modifiable source code. |
| SWE-139, SWE-121, SWE-125 | 22 | A-F | Comply with `X` requirements; reflect approved tailoring in plans; maintain the requirements mapping matrix. |
| SWE-027 | 22 | A-D, F | Conditions for COTS/GOTS/MOTS/OSS/reused components (requirements, documentation, rights and licences with IP counsel, support, V&V to the same level, vendor defect monitoring). |

## 3.2-3.4 Cost, schedule, training (pp. 23-24)

- SWE-015 (p. 23): two cost models for Class A and B projects with estimated cost >= $2 million, one for
  smaller A/B projects and for C, D and F. SWE-151 (p. 23): estimates cover the whole life cycle, project
  attributes, technology maturation, risk and uncertainty (incl. cybersecurity), SA support and other
  direct costs. SWE-174 (p. 24): submit planning parameters to the Center measurement repository at major
  milestones (A-D).
- SWE-016, SWE-018, SWE-046 (p. 24): integrated software schedule with dependencies; regular schedule
  reviews; developer schedules on request. SWE-018 is A-C, F.
- SWE-017 (p. 24): plan, track and ensure project-specific training, including SA personnel (A-C, F).

## 3.5-3.6 Classification, assurance, IV&V (pp. 24-26)

- SWE-020, SWE-176: classification and records (see [software-classification.md](software-classification.md)).
- SWE-022 (p. 25): plan and implement SA, software safety and IV&V (if required) per NASA-STD-8739.8.
- SWE-141 (p. 25, A-B, HQ OSMA): IV&V for projects reaching KDP A that are Category 1, Category 2 with
  Class A/B payload risk classification, or selected by the MDAA. SWE-131 (p. 25): IV&V Project Execution
  Plan (IPEP). SWE-178 (p. 25) access for IV&V; SWE-179 (p. 26) respond to and track IV&V issues.

## 3.7 Safety-critical software (pp. 26-27)

See [safety-critical-software.md](safety-critical-software.md): SWE-205, SWE-023, SWE-134, SWE-219, SWE-220.

## 3.8-3.10 Auto-generated code, CMMI, reuse (pp. 27-29)

- SWE-146 (p. 27, A-C, F): approach to auto-generated code (tool V&V, CM of tools/inputs/outputs, limits,
  V&V of generated code as for hand code, monitoring use, manual-change policy). SWE-206 (pp. 27-28): access
  to models/simulations used as auto-generation inputs.
- SWE-032 (p. 28, A-B, HQ OCE and HQ OSMA): developer organisation with a non-expired CMMI-DEV rating -
  Maturity Level 3 for Class A, Level 2 for Class B (except Class B software on NASA Class D payloads);
  a "best in class provider" exception for Class B uses an evaluation against ML2 practices (pp. 28-29).
- SWE-147, SWE-148 (p. 29): reusability requirements; evaluate and contribute reuse candidates with the
  listed information.

## 3.11 Cybersecurity (pp. 30-31)

SWE-156 cybersecurity assessment incl. COTS/OSS risks (A-F); SWE-154 identify risks and mitigations in
flight and ground systems (A-D); SWE-157 protect systems with communications against unauthorized access
per NASA-STD-1006 (A-D); SWE-159 test and record mitigation implementations (A-D, F); SWE-207 secure coding
practices (A-D, p. 31); SWE-185 verify code against the secure coding standard with static analysis
(A-D, F, p. 31); SWE-210 requirements for detecting adversarial actions (A-C, F, p. 31).

## 3.12 Bi-directional traceability (p. 31)

SWE-052 with Table 1: higher-level to software requirements (A-C, F); software requirements to system
hazards (A-D); requirements to design (A-C); design to code (A-C); requirements to verification (A-D, F);
requirements to non-conformances (A-D, F).

## Chapter 4 engineering life cycle (pp. 32-38)

| Activity | SWEs (page) |
|---|---|
| Requirements | SWE-050 establish/approve/maintain incl. COTS etc. (32); SWE-051 requirements analysis from system, safety, reliability and hardware inputs (32, A-C); SWE-184 safety constraints and controls in requirements (32, A-C); SWE-053 manage changes (32); SWE-054 resolve inconsistencies (32); SWE-055 requirements validation (32) |
| Architecture | SWE-057 recorded architecture (33, A-C); SWE-143 architecture review for Category 1 and qualifying Category 2 projects (33, A-C) |
| Design | SWE-058 detailed design (34, A-C) |
| Implementation | SWE-060 code (34, A-C, F); SWE-061 coding standards (34); SWE-135 static analysis (34); SWE-062 unit test (34); SWE-186 repeatable unit tests (35); SWE-063 version description (35); SWE-136 validate/accredit development tools (35, A-C) |
| Testing | SWE-065 test plans, procedures, tests, reports (35); SWE-066 test against requirements (35); SWE-187 CM before test (35, A-C, F); SWE-068 evaluate results (36); SWE-070 accredited models/simulations for flight qualification (36, A-C); SWE-071 keep test plans consistent (36); SWE-073 validate on target/high-fidelity simulation (36, A-C); SWE-189 code coverage measurement (36); SWE-190 coverage from test execution (37, A-C); SWE-191 regression testing (37, A-C, F); SWE-192 test hazard-related requirements (37); SWE-193 acceptance tests for uploaded data/rules/code (37, A-B, F); SWE-211 test embedded COTS etc. to the same level (37, A-C) |
| Operations/maintenance/retirement | SWE-075 plan O&M&R (37); SWE-077 deliver with as-built records (37); SWE-194 pre-delivery verification (37); SWE-195 maintain per class (38); SWE-196 archive/retirement (38) |

Classes not stated above are A-D (and F where the table in [requirements-index.md](requirements-index.md)
shows it).

## Chapter 5 supporting processes (pp. 39-43)

- CM: SWE-079 SCM plan, SWE-080 track/evaluate changes, SWE-081 configuration items, SWE-082 control
  levels and authorities (p. 39); SWE-083 status accounting, SWE-084 configuration audits, SWE-085
  release procedures, SWE-045 joint NASA/developer audits (p. 40, SWE-045 A-C, F).
- Risk: SWE-086 record, analyze, plan, track, control and communicate software risks (p. 40, A-C, F).
- Peer reviews: SWE-087 reviews of requirements, plans, selected design, code and test procedures
  (p. 40, A-C, F); SWE-088 checklists, readiness/completion criteria, action tracking, participants
  (p. 41, A-C); SWE-089 record measurements (p. 41, A-C, F).
- Measurement: SWE-090 (p. 41), SWE-093, SWE-094, SWE-199, SWE-200 (p. 42) - all A-C except SWE-200 (A-B).
- Non-conformances: SWE-201 track (A-D, F), SWE-202 severity levels (A-C, F), SWE-203 assess reported
  COTS/OSS non-conformances (A-C) (p. 42); SWE-204 process assessment for high-severity non-conformances
  (p. 43, A-B).

## Chapter 6 records (pp. 44-45)

Typical products: SDP/SMP, schedule, cost estimate, SCM plan, change reports, test plans/procedures/
reports, version descriptions, maintenance plan, SA plan(s), safety plan, SRS, data dictionary,
interface/architectural design, design description, user's manual, risk records, measurement results,
make/buy trade records, acceptance criteria, status reports, developer's manual, reuse report, model and
simulation documentation. Content recommendations are in NASA-HDBK-2203 (not bundled).
