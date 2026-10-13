# The SE engine: 17 common technical processes

Source: NASA SE Handbook, NASA/SP-2016-6105 Rev 2 (`nasa-se`). PDF page first, printed page in
brackets. Machine-readable version: `catalog/nasa-se-processes.json`
(`python -m agentlib nasa-se processes --id <number|slug>` prints inputs, outputs and activity headings).

## How the engine is used

- Three sets of processes from NPR 7123.1: **system design**, **product realization** and **technical
  management** (2.1, PDF p. 18). Processes 1-9 are the tasks executing the project; 10-17 are
  crosscutting tools for carrying them out (PDF p. 18).
- System design processes are applied top-down to each product layer until products can be built, bought
  or reused; product realization processes are applied bottom-up from the lowest product (PDF pp. 18-19).
- The processes are used **iteratively** (re-applied to the same product to correct a discrepancy) and
  **recursively** (applied to the next lower/upper layer, and again in the next life-cycle phase to mature
  the system definition) (PDF p. 20).
- The engine cycles five times through the technical development processes from Pre-Phase A to Phase D
  (Phases C and D split the left and right halves) and seven times through the technical management
  processes from Pre-Phase A to Phase F (2.2, PDF p. 22).
- Verification vs validation (2.4, PDF pp. 24-25): verification proves compliance with each "shall"
  by test, analysis, inspection or demonstration; validation shows the product accomplishes its intended
  purpose in the intended environment and relates back to the ConOps.

## Process table

| # | Process | Section | PDF (printed) | Typical inputs | Typical outputs |
|---|---|---|---|---|---|
| 1 | Stakeholder Expectations Definition | 4.1 | 66 (53) | Initial Customer Expectations; Other Stakeholder Expectations; Customer Flow-down Requirements | Validated Stakeholder Expectations; Concept of Operations; Enabling Product Support Strategies; Measures of Effectiveness; Human/Systems Function Allocation |
| 2 | Technical Requirements Definition | 4.2 | 76 (63) | Baselined Stakeholder Expectations; Baselined Concept of Operations; Baselined Enabling Support Strategies; Measures of Effectiveness | Validated Technical Requirements; Measures of Performance; Technical Performance Measures |
| 3 | Logical Decomposition | 4.3 | 86 (73) | Technical Requirements; Technical Measures | Logical Decomposition Models; Derived Technical Requirements; Logical Decomposition Work Products |
| 4 | Design Solution Definition | 4.4 | 90 (77) | Technical Requirements; Logical Decomposition Models | System Specification; System External Interface Specifications; End-Product (and Interface) Specifications; Initial Subsystem Specifications; Enabling Product Requirements; Product Verification Plan; Product Validation Plan; Logistics and Operate-to Procedures |
| 5 | Product Implementation | 5.1 | 104 (91) | Inputs for purchasing, making/coding or reusing the end product; Enabling Products | End Product for Verification; End Product Documents and Manuals; Work Products |
| 6 | Product Integration | 5.2 | 110 (97) | Lower-level products; design specifications and configuration documentation (ICDs, integration plan); integration-enabling products | Integrated product(s) with interactions identified and balanced; documentation and manuals; work products |
| 7 | Product Verification | 5.3 | 116 (103) | Product to be verified; Verification plan; Specified requirements baseline; Enabling products | Verified product; verification results; verification report(s); work products |
| 8 | Product Validation | 5.4 | 129 (116) | End product to be validated; Validation plan; Baselined stakeholder expectations; enabling products | Validated end product; validation results; validation report; work products |
| 9 | Product Transition | 5.5 | 137 (124) | End product(s) to be transitioned; accompanying documentation; transition-enabling products | Delivered end product with documentation; transition work products; realized enabling products |
| 10 | Technical Planning | 6.1 | 145 (132) | Project technical effort requirements and resource constraints; agreements and life-cycle phase; policies and standards; prior plans; replanning needs | Cost estimates, schedules, resource needs; product and process measures; SEMP and other technical plans; technical work directives |
| 11 | Requirements Management | 6.2 | 163 (150) | Expectations and requirements; change requests; TPM results; V&V results | Requirements documents; approved baseline changes; work products (e.g. bidirectional traceability status) |
| 12 | Interface Management | 6.3 | 169 (156) | Interface requirements; interface change requests; system description and boundaries; organisation and boards structure | Interface control documentation (IRD, ICD, IDD, ICP); approved interface changes; work products |
| 13 | Technical Risk Management | 6.4 | 173 (160) | Risk Management Plan; technical risk issues; status measurements; reporting requirements | Mitigation/contingency actions; technical risk reports; work products |
| 14 | Configuration Management | 6.5 | 180 (167) | CM plan; engineering change proposals; baselined documents; approved changes; designated configuration items | Configuration status accounting reports; current baselines; CM reports; audit results |
| 15 | Technical Data Management | 6.6 | 188 (175) | Technical data products; data requests | Form of data products; exchange formats; delivered technical data |
| 16 | Technical Assessment | 6.7 | 196 (183) | Technical plans; technical process and product measures (MOEs, MOPs, KPPs, TPMs); reporting requirements | Assessment results, findings and recommendations; technical review reports/minutes |
| 17 | Decision Analysis | 6.8 | 206 (193) | Decision need, alternatives, issues and supporting data; analysis support requests | Alternative selection and decision support recommendations and impacts (decision report) |

Inputs/outputs are the handbook's bullet labels (some shortened here; exact labels in the catalog).

## Process notes that matter in practice

- **Stakeholder expectations (4.1)**: identify stakeholders, capture needs/goals/objectives, establish the
  ConOps and support strategies, define MOEs, validate bidirectional traceability, obtain commitments and
  baseline (activity headings PDF pp. 67-75). MOEs are measures whose failure makes stakeholders deem the
  system unacceptable (PDF p. 75).
- **Technical requirements (4.2)**: single-"shall" statements with rationale; identify Key Driving
  Requirements (PDF pp. 81-82); validate requirements in six questions (PDF pp. 83-84); define MOPs and
  TPMs (PDF p. 84); baseline, typically at SRR (PDF p. 85). Use `skills/requirements-engineering/`.
- **Design solution (4.4)**: define alternatives, analyse each, select the best, increase resolution,
  fully describe, verify and validate the design, identify enabling products, baseline (PDF pp. 91-100).
- **Product verification (5.3)**: completion criteria are documented objective evidence of compliance
  (or waiver) and closure of all discrepancy and nonconformance reports (PDF p. 128). Methods: analysis,
  demonstration, inspection, test (box, PDF p. 121).
- **Product validation (5.4)**: complete only when objective evidence is documented and all issues and
  actions are resolved (PDF p. 136).
- **Technical planning (6.1)**: plans are updated at least at every KDP (PDF p. 145); the SEMP must be
  approved by the appropriate authority (PDF p. 162).
- **Requirements management (6.2)**: bidirectional traceability; changes after SRR go through a CCB
  (PDF p. 166); requirements creep countermeasures (PDF p. 167).
- **Technical assessment (6.7)**: six assessment criteria - strategic alignment, management approach,
  technical approach, integrated cost/schedule and funding, non-budgetary resources, risk management
  approach (PDF p. 196); track technical measures with red/yellow/green alert zones (PDF p. 198).
- **Configuration management (6.5)**: note the handbook misnumbers two CM activity headings as 6.4.1.2.5
  and 6.4.1.2.6 (PDF p. 187); cite them by page.
