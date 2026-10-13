# SLO arithmetic (generic)

Written independently for this library; no text from the Google SRE books is used (source
inaccessible here; see `sources/audits/google-sre.md`).

## Definitions
- **SLI** = good events / valid events, in [0, 1].
- **Target** t, e.g. 0.999. **Error budget fraction** = 1 − t.
- **Allowed bad minutes** over a window of W days = (1 − t) × W × 1440.
- **Allowed bad events** = (1 − t) × total valid events.
- **Budget consumed** = bad / allowed (events or minutes). Remaining = 1 − consumed.
- **Burn rate** over a window = observed error rate / (1 − t). A burn rate of 1 spends exactly the
  budget over the SLO window; 2 spends it in half the window.
- **Average burn so far** = consumed / (elapsed / window).

## Worked values (hand-checked)
| Target | Window | Allowed bad minutes |
|---|---|---|
| 99% | 30 d | 432 |
| 99.5% | 30 d | 216 |
| 99.9% | 30 d | 43.2 |
| 99.9% | 28 d | 40.32 |
| 99.95% | 30 d | 21.6 |
| 99.99% | 30 d | 4.32 |

Event example: 99.9% target, 2,000,000 valid requests → 2,000 allowed bad requests; 500 bad so
far → 25% consumed, 1,500 remaining. If 7.5 of 30 days have elapsed, average burn = 0.25 / 0.25 = 1.0.

## Multi-window, multi-burn-rate alerts
A rule (long window L, short window S, threshold B) fires when burn(L) ≥ B **and** burn(S) ≥ B.
- The long window gives significance (enough budget spent to matter).
- The short window makes the alert reset quickly once the problem stops.
- Budget spent by the time the rule can fire ≈ B × L / SLO window. For B = 14.4, L = 1 h, window
  30 d: 14.4 × 60 / 43,200 = 0.02 (2%).

Example policy values used in `assets/examples/alert-policy-example.json` (commonly cited for a
99.9%/30-day SLO, **examples only, unverified against the primary source**):

| Name | Severity | Long | Short | Burn rate | Budget spent at detection |
|---|---|---|---|---|---|
| fast-burn-page | page | 1 h | 5 m | 14.4 | 2% |
| slow-burn-page | page | 6 h | 30 m | 6 | 5% |
| budget-ticket | ticket | 3 d | 6 h | 1 | 10% |

## Pitfalls
- Low-traffic services: a handful of failures produces huge burn rates — use longer windows,
  minimum request counts or synthetic traffic.
- Measuring at the server misses failures users see (DNS, CDN, client); say where the SLI is measured.
- Averages of percentages across tenants hide a single tenant's outage; consider per-tenant SLIs for
  multi-tenant platforms.
