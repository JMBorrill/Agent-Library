# Shaping notes and adaptation choices

Source: `shape-up` (*Shape Up*, Ryan Singer). The primary text was **inaccessible**; everything
attributed to the method below comes from secondary summaries recorded in
`sources/audits/shape-up.md` and is *(unverified)*. Wording is ours. The book is reportedly free to
read online but not openly licensed — paraphrase and link, never copy chapters.

## Concepts used (secondary, unverified)
| Concept | How this skill uses it |
|---|---|
| Appetite | A fixed time budget decided before the solution. Secondary sources describe "small batch" (1–2 weeks) and "big batch" (6 weeks) bets for a small team. We expose the cap as `--max-appetite-weeks`. |
| Pitch ingredients | Problem, Appetite, Solution, Rabbit holes, No-gos — the five required sections. |
| Breadboard / fat-marker sketch | Ways to describe solution elements at low fidelity. The checker looks for element vocabulary (places, affordances, connections, breadboard, sketch, flow, screen, step). |
| Rabbit holes | Risks found by walking through the solution; resolved before betting. |
| Betting | A decision forum chooses pitches for the next period. We only require that the decision is recorded by an accountable person. |
| Circuit breaker | Unfinished work is not extended automatically; it must be re-shaped and re-bet. Weak secondary source. |
| Scopes and `~` | Work is organised into scopes (finishable slices); nice-to-haves are marked with a tilde. Hill charts track uncertainty per scope (not checked here). |
| Six-week cycle + cool-down | **Optional** in this library. Many teams adapt cadence; the skill never requires it. |

## Adaptations for small SaaS teams
- A 1–2 person team often bets in 1–3 week units; set the cap accordingly.
- Evidence links: we require (warning) that the Problem cites discovery evidence IDs. This is a
  library addition linking shaping to `product-discovery`, not a claim about the book.
- Accessibility, privacy and security are not cut-able by appetite. If a solution cannot meet them
  within appetite, the solution changes, or the bet is not made.

## Writing good rabbit-hole bullets
Bad: "Calendar sync might be hard."
Good: "Two-way sync with phone calendars -> Decision: one-way export (ICS feed) only; two-way is a
no-go for this bet."

## Vague-word list (heuristic)
intuitive, seamless, easy, simple, user-friendly, better, improve, enhance, optimise, robust, smart,
powerful, modern, delightful, streamline, flexible. Each is acceptable only when followed by what
concretely changes for whom.
