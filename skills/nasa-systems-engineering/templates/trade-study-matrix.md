# Trade study / decision report: <Decision title>

> Sections follow Table 6.8-1 "Typical Information to Capture in a Decision Report"
> [nasa-se 6.8, p. 213-214]. Compute the matrix with
> `python -m agentlib nasa-se trade-study trade.yaml` (input format below) and paste the output.

## 1. Executive summary
- Recommendation (one sentence):
- Problem/issue requiring a decision (one sentence):

## 2. Problem/issue description
Background, history, decision maker(s) (board/panel/forum), decision recommendation team; mission and
system context; intended outcome in performance, cost and schedule.

## 3. Decision matrix setup rationale
- Criteria selected (objective, measurable, discriminating) and why; **mandatory** criteria are pass/fail
  screens - an option failing one is disregarded [nasa-se 6.8.1.2.1, p. 210].
- Options selected (incl. options considered and dropped, and do-nothing where relevant) [p. 210-211].
- Weights selected (sum to 1.0 or 100) and evaluation methods selected [p. 211].
- Scoring scale with operational definitions (e.g. 1 / 3 / 9 with a measurable meaning for each) [p. 211].

| Criterion | Type (mandatory / weighted) | Weight | Scale and operational definition | Evaluation method |
|---|---|---|---|---|

## 4. Decision matrix scoring rationale
Per cell: evidence and reasoning for each score; uncertainties.

## 5. Final decision matrix
Raw scores in alternative columns; the weighted-total row must equal sum(normalised weight x score).

| Criterion | Weight | <Alternative A> | <Alternative B> | <Alternative C> |
|---|---|---|---|---|
| <criterion 1> | 0.40 | | | |
| <criterion 2> | 0.35 | | | |
| <criterion 3> | 0.25 | | | |
| **Weighted total** | 1.00 | | | |

Mandatory screens: <criterion: pass/fail per alternative>.

## 6. Risks / benefits of the final options

## 7. Recommendation and/or final decision
Highest score is typically recommended; if not, explain why. If alternatives are close or uncertainty could
change the ranking, present all closely ranked alternatives [nasa-se 6.8.1.2.5, p. 212]. Include
sensitivity of the ranking to weights and to uncertain scores.

## 8. Dissent
Any dissent and how it was addressed.

## 9. References

## Appendix: tool input
```yaml
criteria:
  - {name: Cost, weight: 40}
  - {name: Mass margin, weight: 35}
  - {name: Technology maturity, weight: 25}
  - {name: Fits launch envelope, mandatory: true}
alternatives:
  - {name: Option A, scores: {Cost: 7, Mass margin: 5, Technology maturity: 9, Fits launch envelope: yes}}
  - {name: Option B, scores: {Cost: 5, Mass margin: 8, Technology maturity: 6, Fits launch envelope: yes}}
```
