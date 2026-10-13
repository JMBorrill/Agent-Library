# Parameters: what the 2026 edition states and what it does not

Run `python -m agentlib greenbook params` (or add `--format json`) to print this table from
`catalog/green-book.json`. The extraction script parses each value from the PDF and asserts it.

## Stated in the 2026 text

| Parameter | 2026 value | Paragraph / PDF page |
|---|---|---|
| STPR | 3.50% years 1-30; 3.00% years 31-75; 2.50% year 76 onwards | 6.54 / p.46 |
| Year 0 | First year with costs or benefits; undiscounted | 6.10 / p.39 |
| Health/life discount rate | 1.5% in every year | 6.58 / p.46 |
| Table 8 worked factors (years 0-5) | 1.000, 0.9662, 0.9335, 0.9019, 0.8714, 0.8420 | Table 8 / p.46 |
| Time horizons after year 0 | Infrastructure 60; refurbishment 30; regulations 10; other 10 (years) | 6.11 / p.39 |
| Climate scenarios | 2°C if horizon ends before 2040; 2°C and 4°C if 2040 or later | 6.14 / p.39; 8.86 / p.72 |
| Shortlist size | Around five options | 5.17 / p.32 |
| Welfare weight elasticity | 1.3 | 7.11-7.15 / pp.56-57 |
| Equivalisation scores | 0.67, 0.33, 0.33, 0.20 | Figure 7 / p.56 |
| Negligible GHG | < 0.1 MtCO2e in every year | 8.75 / p.70 |
| BCR threshold | None (thresholds must not be used) | 6.98 / p.53 |
| GMPP business case publication | Within 4 months of HM Treasury approval | 10.12 / p.80 |
| M&E budget | No fixed proportion; assess case by case | 10.9 / p.79 |

## NOT stated in the 2026 text (user must supply, with source)

| Parameter | Where the Green Book points | Paragraph / PDF page |
|---|---|---|
| Optimism bias percentages | Organisation forecast-error evidence, otherwise supplementary guidance on optimism bias (or departmental, e.g. DfT) | 6.80-6.81 / p.50 |
| Risk-free real gilt rate (private finance sensitivity) | HM Treasury; match the weighted average contract duration | A.17 / p.85 |
| GDP deflator series | OBR EFO (5 years) and Long-term economic determinants (50 years) | 6.49 / p.45 |
| Pre-calculated discount factor table | Supplementary guidance on discounting (the tools compute factors from the bands) | 6.55 / p.46 |
| STPR derivation | Supplementary guidance on discounting | 6.54 / p.46 |
| Social value of carbon, LRVC, emissions factors | DESNZ supplementary guidance | 8.10, 8.63-8.69 / pp.60, 69-70 |
| QALY value | Supplementary guidance on health | 8.17, 8.57 / pp.61, 68 |
| VPF | DfT TAG data book | 8.55 / p.68 |
| WELLBY value | Supplementary guidance on wellbeing | 8.22 / p.62 |
| Value of travel time | DfT supplementary guidance | 8.52 / p.68 |

## Edition traps to avoid

- Some earlier editions had further STPR step-downs, with bands such as 76-125, 126-200 and 201-300, and a
  declining health rate schedule. The 2026 text has **neither**. It gives 2.50% "for year 76 onwards" and says
  the health rate "applies in every year of the appraisal".
- Do not describe optimism bias percentages as "Green Book values". In 2026 they come from supplementary
  guidance or organisational evidence.
- Do not apply "minimum BCR" rules. Paragraph 6.98 rules them out.
