# Discounting under the Green Book 2026 edition

**Rates (Green Book 2026, para 6.54, PDF p.46; source id treasury-green)**

- Standard STPR (real): 3.5% for years 1 to 30, 3.0% for years 31 to 75, 2.5% for year 76 onwards. Year 0 is undiscounted.
- Health and life effects: 1.5% in every year of the appraisal (para 6.58). The wealth-effect component is excluded. All other effects use the standard STPR.
- The 2026 text has no further step-down after year 76. Earlier-edition schedules should not be imported.

**Discount factors** (from `python -m agentlib greenbook factors --years 80`; factors compound across bands, so DF(t) = DF(30) x 1.03^-(t-30) for years 31-75)

| Year | Rate applying in that year | STPR discount factor |
|---|---|---|
| Year 30 | 3.5% | 0.3563 |
| Year 31 | 3.0% | 0.3459 |
| Year 76 | 2.5% | 0.0919 |

Health factor for year 10 at 1.5%: 0.8617.

So £1m (real) of non-health benefit in year 76 has a present value of about £91,900, and £1m of health benefit in year 10 is worth about £861,700.

Both rates are real rates and apply only to values that are already in real terms (para 6.56). Pre-calculated factor tables are in the supplementary guidance on discounting (para 6.55).
