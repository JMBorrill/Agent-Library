# Validating requirements

Source: NASA SE Handbook, NASA/SP-2016-6105 Rev 2 (`nasa-se`); PDF pages. Requirements validation checks
the requirements against stakeholder expectations, mission objectives and constraints, the ConOps and the
mission success criteria (4.2.1.2.4, PDF p. 83). (Validation of *requirements* is distinct from validation
of the *product*, 5.4.)

## Six validation questions (4.2.1.2.4, PDF pp. 83-84)

The lead-in says "five steps" but the handbook lists six:

1. **Written correctly?** Fix "shall" format and editorial errors -> `lint-requirements`.
2. **Technically correct?** A few trained reviewers remove technical errors before stakeholder review;
   check bidirectional traceability to baselined stakeholder expectations, valid assumptions, and that each
   requirement is essential to and consistent with the product solution form for the phase.
3. **Satisfy stakeholders?** All relevant stakeholder groups identify and remove defects.
4. **Feasible?** Technically sensible and achievable.
5. **Verifiable?** Enough information to verify after implementation -> method and success criteria.
6. **Redundant or over-specified?** Unique and necessary.

Before proceeding to logical decomposition/design, the team should be able to demonstrate that requirements
are complete and understandable, evaluation criteria are consistent with requirements and the operations
and logistics concepts, requirements and MOEs are consistent with stakeholder needs, operations and
architecture concepts support mission needs, and the change process is established and communicated
(PDF p. 84).

## Appendix C.4 validation checklist (PDF pp. 250-252) - what is automated

| Category | Items | Tool support |
|---|---|---|
| Clarity | clear/unambiguous (no this/these, as appropriate, etc., and/or, but not limited to); concise; one thought; one subject and one predicate | ambiguous-term, indefinite-pronoun, multiple-shall, compound-statement, multiple-sentences |
| Completeness | TBD/TBR captured and listed; missing requirement areas (functional, performance, interface, environment, facility, transportation, training, personnel, operability, safety, security, appearance and physical characteristics, design); assumptions stated | tbd, tbr; areas are a human review |
| Compliance | correct level; free of implementation; free of operations; free of personnel/task assignments | operational-statement (partial) |
| Consistency | no contradictions; terminology consistent with users/sponsor, glossary and document | human review |
| Traceability | needed ("what is the worst that could happen if not included?"); bidirectionally traceable to higher-level requirements or scope (needs, goals, objectives, constraints, ConOps); uniquely numbered | `trace` (orphans, dangling, cycles); missing-id, duplicate-id |
| Correctness | correct; assumptions correct; feasible | human review |
| Functionality | functions necessary and together sufficient | human review |
| Performance | performance specifications and margins (timing, throughput, storage, latency, accuracy, precision); realistic; tolerances not overly tight ("worst thing if the tolerance was doubled or tripled?") | missing-tolerance (partial) |
| Interfaces | external and internal interfaces defined; necessary, sufficient, consistent | human review |
| Maintainability | measurable, verifiable; weakly coupled to minimise ripple effects | human review |
| Reliability | measurable reliability; error detection/reporting/handling/recovery; undesired events (SEU, data loss, operator error); sequence assumptions; survivability after faults | human review |
| Verifiability/Testability | testable/demonstrable/inspectable/analysable at the stated level; measurable; precise; free of unverifiable terms | unverifiable-term, ly-ize-word, missing/invalid verification method |
| Data usage | "don't care" conditions truly don't care and stated explicitly | human review |

Run `python -m agentlib nasa-se req-checklist -o c-checklist.md` to get every item verbatim as a checkbox
list, and record a disposition for the human-review items.

## Product validation (for context)

Validation of the realized product is planned with a validation requirements matrix (Appendix E, PDF p. 256)
using sources such as the ConOps, NGOs, rationale statements, lessons learned and test-as-you-fly goals.
