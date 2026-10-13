# DCF method notes (finance-npv-irr)

Written independently from standard corporate-finance practice. The `damodaran` source was not
readable in this environment; nothing here is quoted from it *(unverified)*.

## Formulas implemented in `scripts/cashflow.py`
| Metric | Formula (rate r per period) |
|---|---|
| NPV, t0 | sum over k of CF_k / (1+r)^k, k = 0..N (CF_0 undiscounted) |
| NPV, t1 | sum over k of CF_k / (1+r)^(k+1) (spreadsheet `NPV()` style) |
| IRR | r such that NPV(r) = 0; grid scan over (-99%, 1000%] then bisection of each bracket |
| MIRR | (FV of inflows at reinvest rate / PV of outflows at finance rate)^(1/N) - 1 |
| Payback | first period where cumulative flow >= 0, interpolated linearly inside the period |
| Discounted payback | same, on discounted flows (t0 convention) |
| PI | PV(CF_1..CF_N) / -CF_0 |
| CAPM | k_e = r_f + beta x ERP |
| WACC | E/(D+E) x k_e + D/(D+E) x k_d x (1 - t) |
| DCF EV | sum FCF_t/(1+r)^t, t=1..N, + [FCF_N (1+g)/(r-g)] / (1+r)^N; requires g < r |
| Switching value | value of one variable at which NPV = 0, by bisection |

## Worked check (hand-computed)
Flows -1000, 300, 400, 500 at 10%, t0:
- PVs: -1000, 272.727, 330.579, 375.657 -> NPV = -21.037.
- IRR: NPV(8.896%) is about 0 (NPV(8%) = +17.63, NPV(10%) = -21.04).
- MIRR: FV inflows = 363 + 440 + 500 = 1303; (1303/1000)^(1/3) - 1 = 9.223%.
- Payback: cumulative -1000, -700, -300, +200 -> 2 + 300/500 = 2.6 periods.
- Discounted cumulative ends at -21.04 -> discounted payback never.
- Inflow switching value: 1000 / 978.963 = 1.0215 (inflows must rise 2.15%).

## Pitfalls the script guards against
- **Timing convention**: spreadsheet `NPV()` discounts the first cell; mixing conventions shifts NPV
  by a factor (1+r). The convention is printed with every result.
- **No IRR**: all-negative or all-positive flows have no IRR (Descartes' rule of signs).
- **Multiple IRRs**: more than one sign change can produce several roots; reporting one is misleading.
- **Gordon model**: undefined for g >= r; a g close to r makes EV explode.
- **Rate <= -100%**: discount factors are undefined; rejected as input error.

## Pitfalls the script cannot detect
Sunk costs included, missing working capital, nominal/real mismatch, optimistic forecasts, double
counting of financing costs in flows and in WACC, tangent IRR roots (NPV touching zero), roots above
1000% per period.
