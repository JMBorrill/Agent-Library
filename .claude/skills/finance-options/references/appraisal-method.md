# Options appraisal method notes

Original summary of widely described Green Book practice. The 2026 edition was not readable in this
environment; every specific below is *(unverified)* unless stated otherwise (see
`sources/audits/treasury-green.md`).

## Declining discount factors
For a stepped schedule the factor for year t is the product of one-year factors:
DF_0 = 1, DF_t = DF_(t-1) / (1 + r(t)), where r(t) is the rate of the band containing year t.
So a rate change affects only years inside its band.

Hand-checked values with the default schedule (3.5% to year 30, then 3.0% to year 75, then 2.5%):
| Year | DF | Derivation |
|---|---|---|
| 10 | 0.708919 | 1.035^-10 |
| 30 | 0.356278 | 1.035^-30 |
| 31 | 0.345901 | DF_30 / 1.03 |
| 76 | 0.091916 | DF_30 x 1.03^-45 / 1.025 |

Annuity check: sum of DF_1..DF_10 = (1 - 1.035^-10)/0.035 = 8.316605.

## Real vs nominal
Economic appraisal is normally in real terms at a stated base year. Deflate a nominal series by
(1 + i)^t with an explicit deflator assumption i (GDP deflator forecasts are commonly used -
*(unverified)*; record source and date). Never discount nominal flows with a real rate.

## Optimism bias
Appraisers systematically underestimate costs and durations and overestimate benefits. Historic
supplementary guidance published percentage uplifts by project type and stage *(unverified for 2026)*;
this skill requires the user to enter the % and its source, and reduces it only with evidence of
mitigation.

## Switching values
For option k vs counterfactual: incremental NPSV = dPVB - dPVC.
- Benefits switching value = -NPSV_inc / dPVB (fractional change in incremental benefits that makes
  NPSV_inc = 0).
- Costs switching value = NPSV_inc / dPVC.
Small magnitudes mean a fragile conclusion.

## Non-monetised effects
Effects that cannot be valued credibly must still be described (direction, scale, evidence) and
presented next to the NPSV, not dropped. Multi-criteria analysis can structure them.

## Five case model
Strategic, economic, commercial, financial, management *(case names corroborated only by secondary
sources)*. The economic case holds the appraisal; the financial case is affordability in nominal
cash terms.
