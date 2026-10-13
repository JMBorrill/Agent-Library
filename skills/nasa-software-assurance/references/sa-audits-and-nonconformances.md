# SA audits, assessments and non-conformances

Pages: NASA-STD-8739.8B Table 1 unless marked NPR (NPR 7150.2D).

## Audits SA performs (Table 1 tasks)

| Audit / assessment | SWE (task) | Page |
|---|---|---|
| Software development processes and practices, at least once every two years | SWE-039 (5) | 19 |
| Software development and SA processes (CMMI context, Class A/B) | SWE-032 (3) | 30 |
| Risk management process | SWE-086 (2) | 44 |
| Peer-review process | SWE-088 (3) | 45 |
| Configuration audits performed by the project (confirm) | SWE-084 (1) | 43 |
| Participate in or assess results of joint NASA/developer audits; track findings to closure | SWE-045 (1) | 44 |
| Delivery: approve or sign off delivered products | SWE-194 (5) | 41 |

Confirm the audit scope with `python -m agentlib nasa-swe sa-tasks --swe SWE-xxx`. Include a
`check-matrix` run on the project's Requirements Mapping Matrix in any compliance audit:
`python -m agentlib nasa-swe check-matrix rmm.csv --class <X> --format md`.

## Non-conformance requirements and SA tasks

- NPR SWE-201 (NPR p. 42): track and maintain software non-conformances (incl. tools and ground software).
  SA: confirm all are recorded and tracked to resolution; accepted ones carry rationale (p. 46).
- NPR SWE-202 (NPR p. 42): clear severity levels for all non-conformances (incl. tools, COTS, GOTS, MOTS,
  OSS, reused components, ground systems). The Note says classes should at minimum include loss of life or
  loss of vehicle, mission success, visible to the user with operational workarounds, and an "other" class.
  SA: confirm levels are defined, assess their application and accuracy, confirm severities on tool/COTS
  non-conformances, maintain counts per severity per configuration item (pp. 46-47).
- NPR SWE-203 (NPR p. 42): mandatory assessment of reported non-conformances for COTS/GOTS/MOTS/OSS/reused
  components. SA: confirm evaluations throughout the life cycle and assess impact on safety, quality and
  reliability (p. 47).
- NPR SWE-204 (NPR p. 43): process assessments for all high-severity non-conformances (closed loop). SA:
  perform or confirm root cause analysis, confirm process analysis, assess improvement opportunities,
  perform or confirm corrective-action tracking to closure (p. 47).
- NPR SWE-080 (NPR p. 39) changes: SA analyzes proposed changes for safety and security impact and
  confirms change control (p. 42).

## Finding severity used in SA audit reports (library convention)

The standard does not define audit-finding categories. A common convention, used in the templates:

| Category | Meaning |
|---|---|
| Non-conformance | A requirement (NPR SWE, plan commitment, standard) is not met - needs corrective action |
| Observation | Weakness or risk that could lead to a non-conformance |
| Best practice | Noteworthy practice |

Map each software non-conformance to the project's defined SWE-202 severity levels; escalate
disagreements per NPR 2.1.6.7 (NPR p. 16).

## Reporting

- SA status reports and a maintained list of SA discrepancies, risks, issues, findings and concerns
  (SWE-039 tasks 6-7, p. 19); confirm the project manager responds and tracks them to closure (task 8).
- Metrics trending and analysis (SWE-090 task 2, p. 45).
