# Independent Verification and Validation (IV&V)

Pages: NASA-STD-8739.8B section 4.4 (pp. 48-56) unless marked NPR.

## When IV&V applies (NPR 7150.2D)

- SWE-141 (NPR p. 25; Classes A-B; Authority HQ OSMA): for projects reaching Key Decision Point A, the
  program manager ensures software IV&V for (a) Category 1 projects per NPR 7120.5, (b) Category 2
  projects with Class A or Class B payload risk classification per NPR 8705.4, (c) projects selected by
  the Mission Directorate Associate Administrator.
  Note: the NPR body (p. 25) names the MDAA as selecting projects for IV&V, while the Appendix C row
  (p. 62) lists the NASA Chief, Safety and Mission Assurance as authority; confirm the current process with OSMA.
- The NASA Chief, SMA makes the final decision on tailoring of SWE-141 (SWE-223, NPR p. 12).
- If IV&V is required: an IPEP is developed, approved, maintained and executed with NASA IV&V (SWE-131,
  NPR p. 25); IV&V gets access to artefacts, source code and data (SWE-178, NPR p. 25); the project
  responds to and tracks IV&V issues and risks (SWE-179, NPR p. 26).
- SA tasks: confirm the 4.4 IV&V requirements are complete on projects required to have IV&V (SWE-141
  task 1, p. 25); confirm the IPEP exists (SWE-131 task 1, p. 26); confirm access (SWE-178, p. 26);
  confirm responses and tracking (SWE-179, p. 26).

## Principles (4.4.1, pp. 48-49)

- IV&V is a technical discipline of software assurance providing an independent assessment of critical
  products and processes throughout the life cycle (4.4.1.1).
- Independence has three parameters: technical, managerial and financial (4.4.1.2, p. 48).
- It starts early (4.4.1.3), performs verification and validation (4.4.1.4), centres on objective
  evidence (4.4.1.5), follows the principles of life-long IV&V and "appropriate assurance" (4.4.1.6) and is
  scoped by risk assessment captured in the IPEP (4.4.1.7, p. 49).

## The 49 IV&V requirements (4.4.2.1-4.4.2.49, pp. 50-56)

| Range | Topic | Pages |
|---|---|---|
| 4.4.2.1-4.4.2.4 | Planning and risk assessment, IPEP development and negotiation, SMA TA concurrence with the IPEP (4.4.2.3), reporting results | 50 |
| 4.4.2.5-4.4.2.15 | Participation in reviews and peer reviews, insight for project/SA, measurements, tracking plans and changes, life-cycle suitability, risk management per NPR 8000.4, verifying NPR 7150.2 implementation, defect tracking and closure | 51-52 |
| 4.4.2.16-4.4.2.21 | Reuse fit, architecture completeness, operations basis, trade studies, software hazard causes/controls traced to requirements, security threats | 52 |
| 4.4.2.22-4.4.2.27 | Requirements and architecture V&V (correctness, security mitigations, dependability/fault tolerance, hazard control, traceability) | 53 |
| 4.4.2.28-4.4.2.39 | Detailed design, interfaces, code (standards, security, OSS, vulnerabilities, analysis tools), design-to-unit and code-to-requirements relationships | 53-55 |
| 4.4.2.40-4.4.2.47 | Test plans/procedures/cases/environments, acceptance criteria, results, security mitigation tests, code coverage from test execution, independent testing of hazard-related requirements, acceptance tests for uploaded data/rules/code | 55-56 |
| 4.4.2.48-4.4.2.49 | Participation in NASA quality audits; maintenance and operational risk | 56 |

All are "The IV&V Provider shall ..." except 4.4.2.3 ("The NASA SMA Technical Authority (TA) shall review
and concur with the IPEP"). Full text: `python -m agentlib nasa-swe sa-tasks --ivv` or
`python -m agentlib nasa-swe show 4.4.2.22`.

## IPEP checklist (from 4.4.2.2 Note, p. 50)

- [ ] Activities, methods, level of rigor and environments.
- [ ] Tailoring (if any) of the IV&V requirements; which products get which analyses; requirements
      wholly, partially or not applied after risk assessment and resource constraints.
- [ ] Criteria for V&V of in-scope behaviours and responsible components.
- [ ] Communication of expected IV&V products through the life cycle; update triggers.
- [ ] SMA TA concurrence recorded (4.4.2.3).
