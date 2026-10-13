# Real terms, discounting and summary metrics (Green Book 2026)

## Real terms (paras 6.45-6.51, PDF pp.44-45)

- Estimate social costs and benefits in **real prices**. In year 0, nominal and real values are the same.
- Forecast nominal values, then remove general inflation with the **GDP deflator** (para 6.47):

  `real_t = nominal_t × deflator(price year) / deflator(t)`

- Table 7 (PDF p.45) illustrates this with 2% inflation. The deflator factors are 1.000, 0.9804, 0.9612,
  0.9423, 0.9238 and 0.9057, so £1,000 rising 2% a year in nominal terms stays at £1,000 in real terms.
- **The Green Book gives no deflator values.** Use the OBR Economic and Fiscal Outlook for the first 5 years
  and the OBR Long-term economic determinants for up to 50 years (para 6.49).
- Tool: `python -m agentlib greenbook real nominal.csv --deflators deflators.csv [--price-year Y]`.
  The deflators file needs a `year` column, plus either an `index` column (levels) or a `growth_pct` column
  (annual % change). By default the price year is the first year in the data.
- Include significant **relative price effects** (para 6.50). Quality changes can be reflected in real prices
  (para 6.51).

## Discounting (paras 6.52-6.59, PDF pp.46-47 / printed pp.40-41)

| Years | STPR (real) | Source |
|---|---|---|
| 0 | none (factor 1.0) | para 6.10 (year 0 = first year with costs or benefits) |
| 1-30 | 3.50% | para 6.54 |
| 31-75 | 3.00% | para 6.54 |
| 76 onwards | 2.50% | para 6.54 |
| Health and life effects, every year | 1.50% | para 6.58 |

The 2026 text says 2.50% applies "for year 76 onwards". **No further step-down is stated.** Do not import the
older schedules (126-200, 201-300 and so on).

### How factors compound across bands

`DF(t) = Π_{k=1..t} 1/(1 + r_k)`, where `r_k` is the rate for year k. That gives:

- DF(t) = 1.035^-t for t ≤ 30;
- DF(t) = 1.035^-30 × 1.03^-(t-30) for 31 ≤ t ≤ 75;
- DF(t) = 1.035^-30 × 1.03^-45 × 1.025^-(t-75) for t ≥ 76.

Hand-checked values (the tests assert these):

| Year | DF (2026 STPR) | DF if 3.5% were wrongly used throughout |
|---|---|---|
| 5 | 0.8420 (matches Table 8) | 0.8420 |
| 30 | 0.3563 | 0.3563 |
| 31 | 0.3459 | 0.3442 |
| 75 | 0.0942 | 0.0758 |
| 76 | 0.0919 | 0.0732 |

Health factors are 1.015^-t, so year 10 is 0.8617 and year 40 is 0.5513.

### Rules

- Only discount values that are already real. Never add the inflation rate to the discount rate (para 6.56).
- Do not discount retrospectively, and do not include sunk costs (paras 6.59, 6.32).
- Pre-calculated factor tables are in the supplementary guidance on discounting (para 6.55). The tool
  calculates factors from the bands, so the two should agree to rounding.
- **Private finance options.** If the shortlist includes both a private finance option and a public sector
  option, run an additional sensitivity that discounts **costs only** at the risk-free real gilt rate matching
  the contract's weighted average duration (paras A.10, A.17-A.18, PDF pp.84-85). The rate is not in the Green
  Book: ask HM Treasury and pass it as `--gilt-rate`.
- Tools: `greenbook factors --years N` and `greenbook npv` (with `--rate` for a custom flat rate, which must be
  labelled as non-STPR, `--health-rate` to override, or `--no-health-rate`).

## Summary metrics (para 6.93, Table 10, PDF p.52 / printed p.46)

| Metric | Formula | Use |
|---|---|---|
| NPSV | PVB − PVC | Main CBA measure |
| BCR | PVB / PVC | Social return per £ of social cost; sensitive to sign convention (para 6.95) |
| RPSC | (PVB − PVC non-public) / PVC public | Social value relative to cost to the public sector |
| NPUC | PVC relative to quantifiable benefits | CEA when benefits are not monetised |

### Input format for `greenbook npv` and `greenbook switching`

The CSV is in long format, with these columns:

- `option`;
- `year`, as the appraisal year index (or `calendar_year` together with `--base-year`);
- `type`: `benefit` or `cost`;
- `value`;
- optional `item`;
- optional `stream`: `standard` or `health`;
- optional `bearer`: `public` or `non-public`. Tag every cost to get RPSC.

YAML or JSON input is also accepted: `options: [{name, flows: [{item, type, stream, bearer, values}]}]`, where
`values` is either a list indexed by year or a mapping from year to value.

## Interpreting results (paras 6.96-6.101, PDF pp.53-54)

- Ranking by NPSV is only a first step. Value for money needs the balanced judgement in Box 1.
- **Never use BCR thresholds** to accept or reject options (for example, "BCR below 2"). A BCR below 1 can
  still be value for money if there are significant unmonetisable benefits, subject to rigorous scrutiny
  (paras 6.98-6.99).
- Compare metrics only between options that share the same objectives (para 6.100).
- Decision makers may give extra weight to public sector financial impact, distribution or risk appetite
  (para 6.101).

## Sensitivity and switching values (paras 6.102-6.105, PDF p.54)

- Stress-test the uncertain assumptions. A **switching value** is the value a variable would have to reach for
  an option to stop being value for money. Examples: the point where NPSV turns negative, or where another
  option overtakes the preferred one.
- At minimum, report sensitivity analysis and switching values for the preferred option.
- For unmonetisable benefits, a switching value is the monetary value the benefit would need for NPSV to exceed
  zero. Judge how plausible that value is.
- Tool: `greenbook switching flows.csv --pcts -20 -10 10 20`. It outputs:
  - the % change in total benefits or total costs that makes NPSV zero;
  - item-level switching values;
  - the change at which the preferred option would be overtaken;
  - sensitivity tables.
