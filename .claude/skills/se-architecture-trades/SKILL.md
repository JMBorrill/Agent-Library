---
name: se-architecture-trades
description: Define design solutions by generating a morphological trade space of concept options per function, screening combinations with compatibility and maturity (TRL) rules, then evaluating survivors with decision analysis and recording the selected concept with a requirement compliance view. Use when choosing a system or subsystem architecture, comparing build/buy/reuse concepts, or documenting why a design concept was selected before preliminary design.
metadata:
  pack: systems-engineering
  version: "1.1.0"
  sources: "nasa-se-design nasa-se"
---

# Architecture trades and design solution definition

## Purpose
Avoid locking onto the first idea: generate the space of feasible concepts systematically, eliminate
incompatible or immature combinations transparently, evaluate the rest on agreed criteria, and record a
design solution traceable to requirements. Corresponds to the NASA process *Design Solution
Definition*, with evaluation via *Decision Analysis* (see References).

## When to use
- After logical decomposition (`se-logical-decomposition`) when functions must be mapped to concepts.
- Make/buy/reuse or technology choices for a subsystem.
- A design review asks "what alternatives did you consider?".

**Do not use when:** a constraint already fixes the solution (record the constraint), or for pure
software architecture decisions with low physical coupling (an ADR in the codebase may suffice — still
use `se-decision-analysis` for contested choices).

## Inputs
Required: function list (from decomposition), allocated requirements, candidate options per function
with TRL estimates and source, known incompatibilities/dependencies.
Optional: evaluation criteria list (for the decision skeleton), heritage data, vendor data, analyses.
Templates: `assets/examples/trade-space.json` (shape), `assets/templates/design-solution.md`.

## Procedure
1. **List options per key function** (2–4 each), including heritage/COTS and "do nothing differently".
   Record TRL basis — TRL is an estimate unless assessed.
2. **Write compatibility rules**: `incompatible` pairs, `requires` dependencies. Keep rules physical and
   explain each in notes.
3. **Enumerate and screen**: `python3 scripts/trade_space.py trade.json`
   Inspect `option-never-feasible` (rules may be too strict) and immature options (below `trl_threshold`).
4. **Prune to 3–5 concepts** using must-criteria; justify each pruning in writing.
5. **Export for evaluation**:
   `python3 scripts/trade_space.py trade.json --export-decision decision.json --criteria criteria.json`
   then fill in scores with evidence and run `se-decision-analysis` (`decision_matrix.py`).
6. **Analyse the leading concepts**: key equations/models, budgets (`space-technical-budgets`),
   physics checks (`space-low-gravity-mobility` for small-body mobility), with assumptions stated.
7. **Record the design solution** (`design-solution.md`): compliance matrix requirement → predicted
   value → margin → basis (estimate/analysis/test); new interfaces → `se-interface-control`; new risks
   → `se-risk-analysis`. All design parameters remain *proposed* until the owner approves.

## Decision criteria
| Situation | Rule |
|---|---|
| Concept relies on option below TRL threshold | Keep only with a technology maturation plan and risk entry |
| Rules eliminate all combinations | Re-examine rules and requirements; never drop a must silently |
| > 50 feasible concepts | Prune with musts before scoring (warning) |
| Predicted compliance based only on estimates | Mark as such; plan analysis/test before PDR |
| Leading concepts within decision margin | Run targeted analysis/test on the deciding criterion |

## Outputs
`trade-space.json`, screening report (`--json`), `decision.json` (exported skeleton → scored),
decision record (from `se-decision-analysis`), `design-solution.md`, updated ICD and risk register.

## Validation
`trade_space.py` exit 0 ⇒ trade space well-formed with ≥ 1 feasible concept. Generation and screening
only — evaluation quality depends on the decision analysis and the evidence behind the scores.

## Examples
- `assets/examples/trade-space.json` → 18 combinations, 10 feasible, 2 with immature options (cold gas).
- `assets/examples/trade-space-fail.json` → exit 1: `duplicate-function`, `duplicate-option`, `trl-range`,
  `unknown-option`, `bad-requires`.

## Escalation and stop conditions
- Selected concept affects safety, cost or schedule beyond agreed thresholds → decision owner decides
  (`se-decision-analysis` record); author is `systems-architect`, challenger `independent-reviewer`.
- Stop if requirements are not stable enough to define criteria — return to `se-requirements`.

## References
- `nasa-se-design` — Design Solution Definition §4.4; `nasa-se-manage` Decision Analysis §6.8 *(secondary
  corroboration only; see `sources/audits/nasa-se-design.md`)*.
- Morphological analysis background: [references/trade-space-method.md](references/trade-space-method.md).
