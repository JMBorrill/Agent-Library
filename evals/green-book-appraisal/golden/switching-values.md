# Switching values and sensitivity: preferred option New build

Computed with `python -m agentlib greenbook switching fixtures/appraisal_flows.csv` (£m, real, discounted at the 2026 STPR bands, with health effects at 1.5%; source id treasury-green).

## Switching values for the preferred option (NPSV 247.37)

| Variable | Change needed for NPSV = 0 | Change needed to fall behind Do minimum |
|---|---|---|
| Total monetised benefits | fall by 53.4% | fall by 33.3% |
| Total monetised costs | rise by 114.4% | rise by 71.3% |
| Service benefits only | fall by 71.1% | n/a |
| Operating costs only | rise by 241.7% | n/a |

## Sensitivity table (NPSV, £m)

| Change | New build (benefits flexed) | Do minimum (benefits flexed) | New build (costs flexed) | Do minimum (costs flexed) |
|---|---|---|---|---|
| -20% | 154.64 | 31.70 | 290.62 | 135.87 |
| -10% | 201.00 | 62.39 | 268.99 | 114.48 |
| +10% | 293.73 | 123.79 | 225.74 | 71.70 |
| +20% | 340.09 | 154.49 | 204.11 | 50.32 |

New build stays top in every tested case.

## Interpretation

- Benefits would have to fall by more than half (53.4%), or costs more than double (114.4%), before New build's NPSV turned negative. A 33.3% shortfall in benefits would let Do minimum overtake it. Compare these switching values with the forecast-error evidence behind the optimism bias adjustment to judge how likely they are (para 6.103).
- The Green Book says sensitivity analysis and switching values must at least be reported for the preferred option in the shortlist results (para 6.104, PDF p.54).
- Switching values can also be used for unmonetisable benefits: state the monetary value they would need to have, and say whether that is plausible (para 6.105).
