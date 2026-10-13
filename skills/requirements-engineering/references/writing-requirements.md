# Writing good requirements

Source: NASA SE Handbook, NASA/SP-2016-6105 Rev 2 (`nasa-se`); PDF pages. Verbatim checklist text:
`python -m agentlib nasa-se req-checklist` (from `catalog/nasa-requirements-checklist.json`).

## Statement form

- Technical requirements are "shall" statements (4.2, PDF p. 76), written as complete sentences with a
  single "shall" per statement; capture the rationale; identify **Key Driving Requirements** - those with a
  large cost or schedule impact, which can have any priority (4.2.1.2.3, PDF pp. 81-82).
- C.1 terms (PDF p. 249): **shall** = requirement, **will** = facts or declaration of purpose,
  **should** = goal.
- C.2 product requirement form: "The product shall <verb> <what>", with consistent terminology for the
  product and its lower-level entities, tolerances on performance values, free of implementation (state the
  problem, not the solution - ask "why do you need the requirement?"), and free of descriptions of
  operations (PDF p. 249). Personnel requirements use "responsible party shall perform ..." in active voice
  (PDF p. 249).
- C.3 general goodness (PDF pp. 249-250): grammatical, no typos, project template and style, stated
  positively, TBDs minimised (best estimate + TBR with rationale, resolution action, owner, date), an
  intelligible rationale with assumptions (confirmed before baselining), located in the proper section.

## Examples from the handbook (PDF p. 79)

Initial function: "The Thrust Vector Controller (TVC) shall provide vehicle control about the pitch and
yaw axes." Decomposed into functional requirements with performance and tolerance, e.g. "The TVC shall
gimbal the engine a maximum of 9 degrees, ± 0.1 degree." Note how each statement has one "shall", a
measurable value and a tolerance.

## Rewriting patterns (library guidance applying C.2-C.4)

| Weak statement pattern | Problem (handbook rule) | Rewrite pattern |
|---|---|---|
| "The system shall be user-friendly." | Unverifiable term (C.4, p. 252) | "The <product> shall allow a trained operator to complete <task> within <N> minutes ± <t>." |
| "The X shall do A and shall do B." | Multiple shalls (4.2.1.2.3, p. 81) | Two requirements, two IDs. |
| "Data shall be stored." | Passive voice, no subject (C.2, p. 249) | "The <product> shall store <data> for at least <N> days." |
| "The X shall not overheat." | Negative, unverifiable (C.3, p. 250) | "The X shall maintain <component> temperature between <T1> and <T2> °C." |
| "The operator shall verify ..." | Operational statement (C.2, p. 249) | Move to the ConOps; state the product capability that enables it. |
| "The X shall provide TBD Mbps." | TBD (C.3, p. 250) | Best estimate + "(TBR)" with owner and closure date in the TBR list. |
| "... as appropriate / etc. / and/or" | Ambiguous (C.4, p. 250) | Enumerate the cases explicitly. |
| "The X will survive launch." | Not a requirement (C.1, p. 249) | "The X shall withstand the launch environment defined in <doc, para> without loss of function." |

## Metadata to capture (Table 4.2-2, PDF p. 83)

| Item | Function (handbook) |
|---|---|
| Requirement ID | Unique numbering for sorting and tracking |
| Rationale | Clarifies intent at the time of writing |
| Traced from | Bidirectional traceability between parent and lower-level (derived) requirements |
| Owner | Person/group responsible for writing, managing and approving changes |
| Verification method | Test, inspection, analysis, demonstration - determined as the requirement is developed |
| Verification lead | Person/group responsible for verifying |
| Verification level | Level of the hierarchy at which it is verified (system, subsystem, element) |

Rationale should record the reason, assumptions (e.g. dependence on a technology development), relationships
to expected operations (link to ConOps) and design constraints, including why a method of implementation is
imposed if it is (Rationale box, PDF p. 83).

## Why it matters (Table 4.2-1, PDF p. 82)

Well-written requirements establish agreement between stakeholders and developers, reduce rework, provide a
basis for cost and schedule estimates, provide the baseline for verification and validation, facilitate
transfer and serve as a basis for enhancement.

## Linter rule map

| Rule (`lint-requirements`) | Severity | Handbook basis |
|---|---|---|
| missing-id, duplicate-id | error | Table 4.2-2 Requirement ID; C.4 Traceability (unique reference), p. 251 |
| no-shall | error | C.1, p. 249 |
| multiple-shall | error | 4.2.1.2.3, p. 81; C.4 Clarity, p. 250 |
| ambiguous-term | error | C.4 Clarity, p. 250 |
| unverifiable-term | error | C.4 Verifiability/Testability, p. 252 |
| invalid-verification-method | error | Methods of Verification box, p. 121 |
| ly-ize-word, indefinite-pronoun | warning | C.4, pp. 250, 252 |
| tbd (warning), tbr (info) | | C.3, p. 250 |
| negative-statement | warning | C.3, p. 250 |
| passive-voice | warning | C.2, p. 249 |
| operational-statement | warning | C.2, p. 249; C.4 Compliance, p. 250 |
| compound-statement, multiple-sentences | warning | C.4 Clarity, p. 250 |
| missing-rationale | warning | C.3, p. 250; Table 4.2-2 |
| missing-verification-method | warning | Table 4.2-2, p. 83 |
| missing-tolerance | info | C.2, p. 249 |
