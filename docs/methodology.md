# NASA-inspired systems engineering process

This is an adapted methodology, not an assertion of NASA compliance. Primary links: [NASA chapter 4](https://www.nasa.gov/reference/4-0-system-design-processes/), [chapter 5](https://www.nasa.gov/reference/5-0-product-realization/), [chapter 6](https://www.nasa.gov/reference/6-0-crosscutting-technical-management/).

NASA's 17 processes:
- **Design (1–4):** stakeholder expectations; technical requirements; logical decomposition; design solution definition.
- **Realisation (5–9):** implementation; integration; verification; validation; transition.
- **Management (10–17):** technical planning; requirements management; interface management; technical risk management; configuration management; technical data management; technical assessment; decision analysis.

## Lightweight life cycle

1. **Discovery/feasibility:** problem, stakeholder expectations, use cases, ConOps, critical assumptions, plausible alternatives and technology risks. Output `mission-brief.md`.
2. **Requirements definition / SRR-style review:** unique testable requirements, ownership, source/rationale, acceptance method, explicit unknowns. Output `requirements.csv`, a draft verification matrix and review disposition.
3. **Preliminary design / PDR-style review:** functional decomposition, proposed architecture and interfaces, trade-off analysis, risk reduction tests, cost/schedule estimates. Output `architecture.md`, `interface-control.md`, `trade-study.md`.
4. **Detailed design / CDR-style review:** specifications, drawings/code plans, test procedures, updated interfaces and risk controls. Output approved implementation baseline and change-control plan.
5. **Test readiness / TRR-style review:** safety check, test setup, instrumentation and calibrations, pass/fail limits, operator roles, emergency stops, evidence capture. **Do not automatically authorise physical tests.**
6. **Verification then validation:** verification = did we meet **specified requirements**; validation = does it meet **real stakeholder needs** in the intended environment? Record *fail*, *pass*, *blocked* or *not tested*, and the actual evidence location. A proposed plan is not test evidence.
7. **Transition / retrospective:** transfer deliverables, known limitations, user documentation, issues, lessons and next baseline.

## Minimum schema

A requirement includes `id`, `statement`, `rationale`, `source`, `owner`, `status` (proposed/approved/retired), `verification_method` (test/analysis/inspection/demonstration), `acceptance_criteria`, `verification_id`, `evidence`, and `result` (not_tested/pass/fail/blocked). For every requirement changed after baseline approval, identify impacted design, interfaces, test cases, risks and schedule.

## Explicit gate policy

A review chair may recommend **GO**, **GO with conditions**, or **NO-GO**. Only an authorised human project owner records a final gate disposition. A checklist with no evidence is not grounds for a GO recommendation. Review independently where feasible.

## Scaling

- **Quick prototype:** charter, 5–20 requirements, interface notes, top risks, minimum test matrix.
- **Moderate risk/complexity:** add structured trade studies, versioned ICDs, design reviews and automated trace checks.
- **Safety-critical / regulated / investor-facing:** formal review evidence, deeper FMEA, external domain review and human approvals. Do not claim certification.
