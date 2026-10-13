# Green Book 2026: framework implementation notes

**Source:** HM Treasury, *The Green Book: UK government guidance on appraisal*, 2026 edition. Source id
`treasury-green`; file `sources/pdfs/hm-treasury-green-book-2026.pdf` (88 pages, OGL v3.0).

## Components

| Path | What it is |
|---|---|
| `catalog/green-book.json` | 17 groups and 121 items covering: the 4 appraisal stages; the 5 cases (contents and what each must demonstrate); SOC/OBC/FBC; 3 statutory duties; rationale concepts; 5 CSFs; longlist and OFF; shortlist rules; inflation and discounting; risk and optimism bias; summary metrics; distributional analysis; valuation; AST; M&E; private finance. It also holds `parameters` (numeric values stated in the 2026 text) and `parameters.not_in_edition`. |
| `scripts/extract/greenbook.py` | Reproducible extraction. Every item has an anchor regex that must match exactly one body page of `pdftotext -layout`. Printed folios are verified (printed = PDF − 6). Parameters are regex-parsed and asserted. `--check` detects drift. |
| `agentlib/frameworks/greenbook.py` | Deterministic tools, the `greenbook` CLI and the eval graders. |
| `tests/test_greenbook.py` | Catalog integrity, hand-calculated discounting across band boundaries, tools, CLI and graders. |
| `skills/green-book-appraisal/` | The skill: procedure, 6 references and 8 templates (SOC, OBC, FBC, long-list matrix, AST/economic summary, assumptions log, benefits register, M&E plan). |
| `agents/economic-appraisal-analyst.md` | The subagent. |
| `evals/green-book-appraisal/` | 6 cases, each with a golden and a negative output. |

## CLI

```
python -m agentlib greenbook npv FILE [--bau NAME] [--rate R] [--health-rate R] [--no-health-rate] [--gilt-rate R] [--base-year Y] [--format md|json] [--out F]
python -m agentlib greenbook switching FILE [--pcts -20 -10 10 20] [rate options]
python -m agentlib greenbook real FILE --deflators FILE [--price-year Y] [--year-col year] [--columns ...] [--format csv|json|md]
python -m agentlib greenbook optimism-bias --capex X --upper-pct U [--mitigation M] [--opex/--opex-upper-pct] [--benefits/--benefits-pct] [--duration/--duration-upper-pct] [--source TEXT]
python -m agentlib greenbook check-case FILE.md [--strict] [--format md|json]
python -m agentlib greenbook params | factors --years N | welfare-weight --national X --group Y [--income-change Z]
```

Input errors exit with status 2 and a message. `check-case --strict` exits with status 1 if any error-severity
check fails.

Cash-flow input is either a long CSV or YAML/JSON:

- Long CSV columns: `option`, `year` (or `calendar_year` with `--base-year`), `type`, `value`, plus optional
  `item`, `stream` and `bearer`.
- YAML/JSON: `options: [{name, flows: [{item, type, stream, bearer, values}]}]`.

## Discounting implementation

- The factor for year t is DF(t) = ∏_{k=1..t} 1/(1+r_k).
- r_k is taken from the 2026 bands (para 6.54): 3.5% for k ≤ 30, 3.0% for 31 ≤ k ≤ 75, 2.5% for k ≥ 76.
- Year 0 has a factor of 1. Year 0 is the first year with costs or benefits (para 6.10).
- So the factor at year 31 is DF(30)/1.03, i.e. the rate steps down for subsequent years only and is not
  re-applied from year 0. The tests assert hand-calculated values (DF(31) = 0.3459, DF(76) = 0.0919) and Table 8.
- Flows tagged `stream=health` use a constant 1.5% (para 6.58: the health rate "applies in every year of the
  appraisal").
- Negative years are rejected: no retrospective discounting (para 6.59) and no sunk costs (para 6.32).
- RPSC = (PVB − PVC non-public) / PVC public (Table 10). It is calculated only when every cost has a `bearer`.

## Assumptions

- Optimism bias: applied % = upper % × (1 − mitigation %), which implements para 6.82. Mitigation reduces the
  adjustment in proportion to the risk prevented. The upper % and mitigation % are user inputs. The remaining
  cost adjustment is reported as the contingency input (para 6.83).
- Switching values are linear scalings of total PVB, total PVC or a single item's PV, against two targets:
  NPSV = 0, and parity with each challenger's NPSV. Sensitivity tables scale all benefits or all costs by ±%.
- `real` uses real = nominal × D(price year)/D(year). The price year defaults to the first year in the data, so
  nominal equals real in year 0 (para 6.47). Deflators can be index levels or `growth_pct` (base 100).
- `check-case` is a keyword and structure heuristic: 36 checks, including anti-patterns such as BCR thresholds,
  sunk costs, inflation-inclusive discounting, multipliers/GVA as benefits, and BAU normalised to zero. It does
  not replace expert review.

## Gaps: what the 2026 edition does not state (users must supply)

- Optimism bias percentages: supplementary guidance or organisational evidence (paras 6.80-6.81).
- Risk-free real gilt rate for the Annex A private finance sensitivity: HM Treasury (para A.17).
- GDP deflator series: OBR (para 6.49).
- Pre-calculated discount factor table and the STPR derivation: supplementary guidance on discounting
  (paras 6.54-6.55).
- Social value of carbon, QALY, VPF, WELLBY and value of travel time: the respective supplementary guidance.
- No STPR step-down after year 76, and no declining health rate, is stated in 2026. The tools deliberately do
  not implement either.

## Known limitations and possible extensions

- The detailed business case guidance (Five Case Model), the Magenta, Teal and Orange Books, and the
  supplementary guidance are not bundled. Template sections beyond Table 2 and Table 3 follow common practice.
- No NPUC calculation for CEA, because quantified benefits are not part of the input schema. No Monte Carlo
  simulation.
- Relative price effects must be applied by the user before `npv`. `real` removes only general inflation.
- The welfare-weight tool does not equivalise incomes. Supply incomes that are already equivalised.
