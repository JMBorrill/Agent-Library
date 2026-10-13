---
name: product-shaping
description: Shape a product idea into a bounded, bet-able pitch - problem with evidence, explicit time appetite, rough solution elements (breadboard / fat-marker sketch), rabbit holes with resolutions and explicit no-gos - and check scope lists for must-haves vs nice-to-haves. Use when turning a validated problem into delivery work, writing or reviewing a pitch, setting an appetite, deciding what to cut, or challenging unbounded "and more" scope. Shape Up-inspired; fixed cycles are optional.
metadata:
  pack: product
  version: "1.0.0"
  sources: "shape-up"
---

# Product shaping (bounded pitches)

## Purpose
Convert a problem the team has evidence for into a pitch that people can bet on: the time it is worth
is fixed first, the solution is concrete enough to show what will be built but rough enough to leave
design room, the known risks are already resolved or cut, and what is out of bounds is explicit. The
approach follows ideas popularised by *Shape Up* (Ryan Singer) — known here only from secondary
sources, so terminology is *(unverified)*. Fixed-length cycles (e.g. six weeks) are **not required**:
the appetite cap is your team's own setting.

## When to use
- After discovery has shown a problem worth solving (`product-discovery`) and before committing
  delivery capacity.
- Reviewing a pitch, feature request or roadmap item that has no time limit or no explicit cut list.
- Mid-build: checking a scope list so must-haves are distinguished from nice-to-haves (`~`).

**Do not use when:** the problem itself is unproven (go back to discovery); you need detailed
acceptance criteria and requirements for implementation (use `product-requirements-brief` after
the bet); the work is a regulatory/safety obligation whose scope is not negotiable (shape the *how*,
but the obligation is not cut-able — escalate).

## Inputs
- Pitch Markdown with sections `## Problem`, `## Appetite`, `## Solution`, `## Rabbit holes`,
  `## No-gos` — template `assets/templates/pitch.md`.
- Evidence IDs from the discovery evidence log (e.g. `DWS-EV-001`) or links.
- Team's maximum single bet in weeks (default 6; any value).
- Optional scope list Markdown — template `assets/templates/scopes.md` (`## Scope: <name>` headings,
  task bullets, nice-to-haves prefixed with `~`).

## Procedure
1. **Set the appetite first.** Decide how much time the problem is worth (e.g. "2 weeks, one
   designer + one developer") before sketching. Appetite is a budget, not an estimate: if the
   solution does not fit, change the solution.
2. **Narrow the problem.** One specific situation for specific users, with evidence links. Remove
   "and also" problems into separate pitches.
3. **Rough out elements.** Describe places (screens), affordances (buttons, fields) and connections
   (breadboard), or a fat-marker sketch description. Stay at the level of "what elements exist and
   how they connect", not visual design.
4. **Walk through for rabbit holes.** For each technical, design or policy unknown, write a bullet
   with `-> Decision:` / `Resolution:` / `Patch:` — cut it, simplify it, or decide it now.
5. **Declare no-gos** — functionality and use cases deliberately excluded.
6. **Check the pitch:**
   `python3 scripts/pitch_check.py pitch.md --max-appetite-weeks <your cap>`
   Fix all errors; resolve or justify warnings (vague words, missing evidence, thin solution).
7. **Bet** — the decision to commit capacity is made by the people accountable for the roadmap
   (often called a betting table *(unverified term)*); record the decision and date.
8. **During build, map scopes** — slices of the feature that can each be finished on its own. Mark
   nice-to-haves with `~`. Check with `pitch_check.py --scopes scopes.md`. When time runs short, cut
   `~` items first; if must-haves do not fit, stop and re-shape rather than silently extending
   (a "circuit breaker" *(unverified term)*).

## Decision criteria
| Situation | Rule |
|---|---|
| Appetite missing, open-ended ("as long as it takes", TBD) | Error — not ready to bet |
| Appetite > team cap | Error — split into smaller bets or reduce the problem |
| Several appetites stated | Warning — pick one |
| Rabbit hole without resolution | Error — decide, patch or declare a no-go |
| No-gos missing | Error — at least one explicit exclusion |
| "etc", "and more", "everything" in Solution/Appetite | Error — unbounded scope |
| Problem with no evidence link | Warning — accept only for small bets; otherwise go back to discovery |
| Scope with only `~` tasks, or no tasks | Error |
| Scope named after a layer (Backend, UI, Misc) | Warning — slice by user-visible capability |
| Must-haves exceed remaining appetite | Stop and re-shape; do not extend by default |

## Outputs
- `pitch.md` (template `assets/templates/pitch.md`) and the check report
  (`pitch_check.py --json`, schema `assets/schemas/pitch-check.output.schema.json`).
- `scopes.md` during delivery (template `assets/templates/scopes.md`).
- Bet decision record (who, when, appetite, conditions) — held by the product owner.

## Validation
- `python3 scripts/pitch_check.py pitch.md [--scopes scopes.md] --json` → exit 0 no errors,
  1 errors (`--strict` also fails on warnings), 2 unreadable input or no input given.
- PASS does **not** mean the bet is wise, the appetite realistic or the solution feasible; it means
  the pitch has all ingredients, a bounded appetite, resolved rabbit holes and explicit exclusions.

## Examples
- `assets/examples/pitch-pass.md` + `assets/examples/scopes-pass.md` (synthetic dog-walking
  "walker marks a day off" pitch, 2-week appetite) → exit 0, no warnings.
- `assets/examples/pitch-fail.md` → exit 1 with `appetite-unbounded`, `appetite-exceeds-cycle`
  (8 > 6 weeks), `rabbit-hole-unresolved`, `no-gos-empty`, `unbounded-scope`; warnings
  `appetite-after-solution`, `problem-without-evidence`, `solution-no-elements`, `vague-term`.
- `assets/examples/scopes-fail.md` → exit 1 with `duplicate-scope`, `scope-no-must-have`,
  `scope-empty`; warning `scope-is-layer`.

## Escalation and stop conditions
- **Stop** when the problem cannot be linked to any evidence and the appetite exceeds a small bet —
  return to `product-discovery`.
- **Stop** when a rabbit hole involves security, privacy, safety or legal exposure that cannot be
  resolved by cutting scope — escalate to the accountable owner before betting.
- Hand pitches to `product-lead`; ask `independent-reviewer` to challenge large bets. After the bet,
  write the brief with `product-requirements-brief`.

## References
- `shape-up` — *Shape Up* by Ryan Singer (Basecamp). **INACCESSIBLE in this environment**: the
  concepts used (appetite, pitch ingredients problem/appetite/solution/rabbit holes/no-gos,
  breadboarding, fat-marker sketches, scopes, nice-to-haves marked with `~`, betting, circuit
  breaker, six-week cycles with cool-down) are taken from secondary sources listed in
  `sources/audits/shape-up.md` and are all *(unverified)*. No chapter numbers or quotations are used.
- Method notes and adaptation choices: [references/shaping-notes.md](references/shaping-notes.md).
