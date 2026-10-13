# Economic appraisal summary: shortlisted options (Green Book 2026)

Computed with `python -m agentlib greenbook npv fixtures/appraisal_flows.csv --bau "Business as usual"`.
Values are £m, real terms (the fixture states they are already real, so no GDP deflator conversion was applied).

## Parameters used

- Standard discount rate: STPR 3.5% for years 1-30, 3.0% for years 31-75 and 2.5% from year 76 onwards; year 0 is undiscounted and factors compound across bands (Green Book 2026, para 6.54, PDF p.46). Source id: treasury-green.
- Health/life effects (the QALY-valued health benefits of New build): 1.5% in every year (para 6.58, PDF p.46).
- The 40-year horizon crosses the year-30 band boundary, so years 31-40 are discounted at 3.0% on top of the year-30 factor (e.g. year 31 factor 0.3459, not the flat-rate 0.3442).

## Results (ranked by NPSV)

| Rank | Option | PVB | PVC | NPSV | BCR | RPSC |
|---|---|---|---|---|---|---|
| 1 | New build | 463.63 | 216.26 | 247.37 | 2.14 | 2.18 |
| 2 | Do minimum | 306.97 | 213.88 | 93.09 | 1.44 | 1.44 |
| 3 | Business as usual | 214.31 | 269.17 | -54.86 | 0.80 | 0.80 |

NPSV = PVB - PVC; BCR = PVB / PVC; RPSC = (PVB - PVC non-public) / PVC public (Table 10, PDF p.52).
Options are shown in absolute terms; BAU is not normalised to zero (para 4.19).

## Interpretation

- **New build** has the highest NPSV and is the preferred option on the monetised evidence. Its lead depends partly on health benefits (PV 115.72), which are discounted at the 1.5% health rate.
- This NPSV ranking is an initial ranking only. The Green Book requires a balanced judgement on value for money that also weighs unmonetisable impacts, risks and uncertainty, public sector financial impact and distributional effects (Box 1; paras 6.96-6.97).
- No BCR threshold is applied (para 6.98).
- Next steps: run switching values and sensitivity analysis on the preferred option (para 6.104), and check that optimism bias adjustments were made before these figures were produced (para 6.79).
