# Requirement quality reference

Original guidance written for this library. Concepts align with widely used systems-engineering
practice (NASA SE Handbook §4.2/§6.2 and appendices on requirement writing — *not verified against the
primary text in this repository; see `sources/audits/nasa-se.md`*).

## Characteristics checked by `req_lint.py` (and those it cannot check)

| Characteristic | Meaning | Machine-checkable? |
|---|---|---|
| Unique | One ID, never reused after retirement | Yes (`duplicate-id`, `id-format`) |
| Atomic | One obligation per statement | Partly (`not-atomic`, `possible-compound`) |
| Unambiguous | Single interpretation | Partly (`ambiguous-term`, `open-ended`, `escape-clause`) |
| Verifiable | Method + pass/fail threshold | Partly (`no-verification-method`, `unmeasurable-acceptance`) |
| Traceable | Parent need and rationale | Yes for links (`unknown-parent`, `orphan`, `trace-cycle`) |
| Owned | Accountable person/role | Yes for presence only |
| Necessary | Removing it loses a needed capability | **No** — reviewer judgement |
| Feasible | Achievable within constraints | **No** — analysis/test |
| Correct | Reflects the real need | **No** — validation with stakeholders |
| Complete (set) | All needs covered | **No** — compare against ConOps scenarios |
| Consistent (set) | No conflicts between requirements | **No** — reviewer judgement; look for same subject with incompatible limits |

## Statement pattern

`[Condition,] <subject> shall <action> <object> <performance + unit> [tolerance] [environment].`

Good: "During a hop in the 1e-4 g analogue, the leg actuator shall deliver an impulse of 0.20 N·s ± 0.02 N·s."
Poor: "The leg shall be strong enough for reliable hopping." (no metric, ambiguous, unverifiable)

## Verification methods
- **Test** — measured under controlled conditions against a quantitative threshold.
- **Analysis** — models/calculations, with stated assumptions and validated models.
- **Inspection** — visual/documentary examination (drawings, certificates, code).
- **Demonstration** — operation showing a function is performed, typically qualitative pass/fail.

## TBD / TBR / TBC
- `TBD` — value not yet determined. `TBR` — value proposed but to be reviewed. `TBC` — to be confirmed.
- Every open item gets an owner and target closure date in `requirements-review.md`.

## Levels and IDs
`STK` stakeholder need · `SYS` system · `SUB` subsystem · `HW`/`SW` component · `IF` interface
requirement. Children inherit the project prefix; the `parent` column may hold several IDs separated by `;`.

## Common anti-patterns
- Writing the design ("shall use a brushless DC motor") without a constraint rationale.
- Copying stakeholder wording verbatim ("robust", "fast") into system requirements.
- Approving requirements with TBD values to "keep the baseline moving".
- Putting test results in the register — results live in the verification matrix.
