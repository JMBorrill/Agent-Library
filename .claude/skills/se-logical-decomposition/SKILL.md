---
name: se-logical-decomposition
description: Decompose system requirements into a functional architecture (verb-object function tree with inputs/outputs), allocate leaf functions to physical or software elements, and check data-flow closure and requirement coverage. Use after system requirements and before architecture trades or interface definition, when building a function tree or functional flow, or when checking that every requirement is realised by some function and every function by some element.
metadata:
  pack: systems-engineering
  version: "1.0.0"
  sources: "nasa-se-design nasa-se"
---

# Logical decomposition

## Purpose
Describe *what the system must do* independent of *how*, so that alternative architectures can be
compared fairly and nothing required is left unallocated. Corresponds to the NASA process *Logical
Decomposition* (see References).

## When to use
- System requirements exist (`se-requirements`) and design alternatives are about to be generated.
- An architecture exists but nobody can show which component performs which required function.
- Before interface definition: function outputs crossing element boundaries become interfaces.

**Do not use when:** decomposing software code structure (use design docs/ADRs) or breaking work into
tasks (that is a work breakdown structure — `se-technical-planning`).

## Inputs
Required: approved/proposed system requirements; functions CSV (`assets/templates/functions.csv`).
Optional: component list (from architecture work), ConOps scenarios (to derive functional flows).

## Procedure
1. **Start from scenarios**: walk each ConOps scenario and list what the system must do at each step
   (verb–object: "Measure displacement", "Interrupt power").
2. **Build the tree**: top function = system purpose; decompose until each leaf can be allocated to one
   element (or a clearly shared set). Typical depth 2–4 levels.
3. **Define flows**: each function's inputs and outputs (matter, energy, information). Mark items that
   cross the system boundary with `EXT:`.
4. **Trace** each function to the requirement(s) it satisfies; untraced functions are gold-plating or
   reveal missing requirements.
5. **Allocate** leaves to elements (after/with `se-architecture-trades`); shared functions need an
   explicit owner.
6. **Check**: `python3 scripts/function_check.py functions.csv --components components.csv --requirements requirements.csv`
7. **Derive interfaces**: every flow between functions allocated to different elements becomes an
   interface row in the ICD (`se-interface-control`).
8. **Derive lower-level requirements** for each element from allocated functions (`se-requirements`).

## Decision criteria
| Situation | Rule |
|---|---|
| Leaf input produced nowhere | Error — missing function or missing EXT: boundary item |
| Output consumed nowhere | Warning — dead function or missing consumer |
| Approved system requirement not realised | Warning — add function or challenge the requirement |
| Leaf unallocated | Error before PDR; acceptable only during early concept work |
| Function name is a noun ("Power system") | Rename to verb–object to avoid smuggling in a design |

## Outputs
`functions.csv` (function tree with flows and allocation), function tree diagram (optional), list of
derived interfaces and derived requirements, check report.

## Validation
Exit 0 ⇒ tree consistent, leaves allocated, flows closed, references valid. Not evidence that the
decomposition is complete or optimal.

## Examples
- `assets/examples/functions-pass.csv` (+ `components.csv`) → exit 0.
- `assets/examples/functions-fail.csv` → exit 1: `duplicate-id`, `unknown-parent`, `unallocated-leaf`,
  `unproduced-input`, `unknown-element`; warnings `not-verb-object`, `untraced-function`.

## Escalation and stop conditions
- Safety functions (e.g. interrupt power) must be identified explicitly and reviewed by
  `safety-risk-reviewer`.
- Stop and return to `se-stakeholder-conops` if scenarios are too vague to derive functions.

## References
- `nasa-se-design` — Logical Decomposition §4.3 *(secondary corroboration only; see
  `sources/audits/nasa-se-design.md`)*.
