# Unit economics method notes

Definitions below are common SaaS industry practice. They vary between companies; always state
the definition used. Nothing here is quoted from a registered source.

## Formulas (monthly)
| Metric | Formula | Undefined when |
|---|---|---|
| Blended CAC | S&M spend / new customers | new customers = 0 |
| Paid CAC | paid spend / paid-attributed new customers | paid customers = 0 |
| Gross margin per account | ARPA x GM% | - |
| Contribution per account | ARPA x GM% - other variable cost per account | - |
| Expected lifetime | expected active months within horizon H: sum over t=1..H of (1-churn)^(t-1) = (1-(1-churn)^H)/churn; 1/churn reported as untruncated reference | churn = 0 (= H, flagged) |
| LTV (simple) | contribution x lifetime (equals discounted LTV at 0%: same survival curve and horizon) | - |
| LTV (discounted) | sum over t=1..H of c (1-churn)^(t-1) / (1+d)^t, d = monthly equivalent of annual rate | - |
| LTV:CAC | LTV / CAC | CAC undefined or 0 |
| CAC payback | CAC / contribution per month | contribution <= 0 -> "never" |

## Worked check (hand-computed)
ARPA 100, GM 80%, variable cost 10 -> contribution 70. Churn 2%, horizon 60 -> lifetime
(1-0.98^60)/0.02 = 35.12 months (untruncated 1/churn = 50) -> LTV 2,458.56.
S&M 30,000 / 30 new = CAC 1,000 -> LTV:CAC 2.46; payback 1,000/70 = 14.29 months.
Discounted check: churn 50%, rate 0, horizon 2 -> c x (1 + 0.5) = 1.5c.

## Pitfalls
- **Lifetime from 1/churn** assumes constant churn; early-life churn is usually higher. Use cohorts.
- **Average retention across cohorts** mixes cohorts of different ages; later months are averaged
  over fewer (older) cohorts. Treat the implied churn as indicative.
- **Revenue-based LTV** (no margin) overstates value; this tool always uses contribution.
- **Blended CAC** includes organic sign-ups; scaling paid channels moves you toward paid CAC.
- **Expansion revenue / net revenue retention** are not modelled; add them as an ARPA scenario.
- **Heuristics** such as LTV:CAC >= 3 or payback <= 12 months are folklore, not standards.
