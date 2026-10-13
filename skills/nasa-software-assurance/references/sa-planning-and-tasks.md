# SA planning and the Table 1 tasks

Pages are PDF pages of NASA-STD-8739.8B (= printed "N of 65") unless marked NPR (NPR 7150.2D).

## Who does what

- The SA and software safety organization and the project manager are responsible for developing the SA
  and software safety plan(s); SA contributes to the Software Management/Development Plans; the SMA
  organization has signature authority on software plans and documentation (1.3, p. 6).
- SA/SS plans may be stand-alone or part of other documents (e.g. the SDP/SMP or a Program/Project SMA
  plan); the standard does not prescribe format (1.3, p. 6). Records, reports, metrics, analyses and
  trending results are kept as quality records (1.3, p. 6).
- Management support for SA minimally includes understanding the SA function, providing skilled
  resources, and receiving and acting on SA information (4.1, p. 15).
- SASS-01 (p. 16): the project manager performs the Table 1 activities per the requirements marked
  applicable in the software engineering requirements mapping matrix; the roles may be delegated within
  the project. The Center SMA Director designates SMA TA(s) for programs, facilities and projects.
- In NPR 7150.2D, the Center SMA Director assures hazard analyses include software, reviews the IPEP,
  supports CMMI ratings and makes sure engineering/SA disagreements are elevated (2.1.6, NPR pp. 15-16).

## Task verbs (3.2 definitions, pp. 9-12)

| Verb | Meaning in the standard (paraphrased) |
|---|---|
| Analyze | In-depth review of results, relationships and methods (e.g. FMEA, FTA, trending); examine plans, products and task lists for completeness, consistency, accuracy and compliance (pp. 9-10). |
| Assess | Judge results against plans or requirements, including practicality, timeliness, correctness, completeness, rationale, and independently track corrective actions to closure (p. 10). |
| Assure | SA makes certain that others performed the specified activities (p. 10). |
| Audit | Systematic, independent, documented examination against audit criteria (p. 10). |
| Confirm | Check that the engineering activities were adequately done and that evidence exists; complete, correct, with expected content per approved tailoring (p. 10). |
| Develop | Produce or create a product and mature it (p. 11). |
| Ensure | SA or software safety personnel perform the activities themselves (p. 11). |
| Monitor | Collect performance data against a plan and report it (p. 11). |
| Participate | Be part of the activity, audit, review, meeting or assessment (p. 11). |
| Perform | SA does the action, which may include comparing independent results with engineering's, auditing and reporting to engineering (p. 12). |

## Planning-relevant tasks (verbatim wording via `nasa-swe sa-tasks --swe ...`)

| SWE | Task(s) | Page |
|---|---|---|
| SWE-013 | 1 confirm plans (incl. security) have expected content and proper tailoring for the class; 2 develop and maintain a Software Assurance Plan (content per NASA-HDBK-2203), including software safety | 17 |
| SWE-024 | assess plans for compliance with NPR 7150.2 and NASA-STD-8739.8; confirm closure of corrective actions | 17 |
| SWE-039 | confirm developer reporting; monitor integration; analyze verification; assess trade studies and reviews; perform audits on development processes and practices at least once every two years; status reports; list of SA discrepancies; confirm PM responses to SA issues | 18-19 |
| SWE-121 | confirm tailoring approvals; develop a tailoring matrix of SA and software safety requirements | 20 |
| SWE-125 | confirm the project matrix; maintain the matrix for NASA-STD-8739.8 requirements | 20 |
| SWE-015 | confirm required cost estimates include SA cost, incl. handling safety-critical software and data | 22 |
| SWE-016 | assess the schedule; develop an SA schedule (products, audits, reporting, reviews) | 24 |
| SWE-017 | confirm project training incl. SA; confirm SA/safety personnel completed basic SA/safety training | 24 |
| SWE-020 | perform a classification or concur with engineering's | 25 |
| SWE-022 | perform SA, software safety and IV&V (if required) per the standard and the SA plan | 25 |
| SWE-090 | confirm the measurement program; trend and analyze quality/defect metrics; submit Center metrics | 45 |

## Tailoring (4.5, pp. 56-57)

- The project's SMA TA shall review and concur with any tailored SA/SS requirement (p. 56).
- Three levels: (1) the software classification decision; (2) the project's Requirements Mapping
  Matrix; (3) SA TA tailoring of the SA/SS requirements that correspond to matrix requirements
  (pp. 56-57).
- SA keeps a mapping matrix against the standard's requirements, performs risk assessment to decide
  tasks and rigor, and plans to cover the whole life cycle (p. 57). Relief requests include rationale,
  risk evaluation and supporting material; affected organizations concur (p. 57).
- If the class changes, SA, software safety and IV&V organizations shall update their plans and initiate
  contract adjustments (p. 57).
- Request for relief from the standard itself is approved by the responsible Center TA per NPR 8715.3
  (1.4, p. 6).

## Generating the task plan

```sh
python -m agentlib nasa-swe sa-tasks --class C > sa-tasks-class-c.md        # all tasks for 'X' SWEs
python -m agentlib nasa-swe sa-tasks --class C --safety-only                 # tasks mentioning safety/hazards
python -m agentlib nasa-swe sa-tasks --swe SWE-087 --format json
```

Map each task to life-cycle phase, owner (SA, software safety, IV&V), evidence and frequency in the SA
plan task table. Remove tasks only for requirements tailored out with SMA TA concurrence and record why.
