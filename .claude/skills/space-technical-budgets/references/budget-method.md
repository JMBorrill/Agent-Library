# Budget method notes (contingency, margin, TPMs)

Original wording; general engineering practice. No values here come from ECSS or NASA documents
(neither was readable in this environment — see `sources/audits/ecss-se.md`, `sources/audits/nasa-se.md`).

## Terms used by `budget_calc.py`
| Term | Meaning in this skill |
|---|---|
| Allocation (limit) | The amount of a resource the item, mode or system may use, flowed down from requirements. |
| CBE | Current best estimate: quantity × per-unit value, from the best evidence available today. |
| Maturity | How the CBE was obtained: `estimated` (judgement/scaling), `calculated` (analysis/CAD), `heritage` (same design flown/used before), `measured` (weighed/measured on representative hardware). Programmes may define their own classes; the policy keys define the valid set. |
| Contingency | Allowance added to a CBE for expected growth at its maturity: CBE × contingency % / 100. Owned by the item/subsystem. |
| Predicted value | CBE + contingency. |
| System margin | Allocation − predicted value; held by the system level for unknowns (new requirements, integration surprises). Reported as a % of the allocation (`margin_basis: allocation`) or of the predicted value (`predicted`). The two give different numbers — state which one your programme uses. |

Programmes differ in vocabulary (some call contingency "maturity margin" or "design allowance"); map
your terms explicitly in the policy `label` or a note.

## Example arithmetic (matches the known-answer test)
| Item | CBE | Maturity | Contingency (example %) | Contingency |
|---|---|---|---|---|
| Structure | 12.0 kg × 1 | calculated | 10 | 1.200 |
| Wheels | 0.9 kg × 4 = 3.6 | heritage | 5 | 0.180 |
| Harness | 2500 g = 2.5 kg | estimated | 20 | 0.500 |
| Camera | 1.5 kg | measured | 3 | 0.045 |
| **Total** | **19.6** | | | **1.925** → predicted **21.525 kg** |

Allocation 30 kg → margin 8.475 kg = 28.25 % of allocation. Allocation 25 kg → 3.475 kg = 13.9 % (below
an example 15 % policy).

## Modes, power and energy
- Power is checked per mode: items with mode `all` (always-on loads) are added to every mode.
- Energy per mode is not derived by the script: compute `P × duty × duration` per mode (and battery
  depth-of-discharge, eclipse/night durations) upstream and enter the results as `energy` rows. Keep
  the calculation sheet as evidence.
- For a rover on a rotating small body, "night" length follows the rotation period — link the energy
  budget to the `space-low-gravity-mobility` body parameters.

## RSS combination
`combine: rss` takes the root-sum-square of item values (with contingency applied to each item before
combining). This is appropriate only for independent, zero-mean error contributors of the same
statistical interpretation (e.g. all 3-sigma). Biases add linearly. A real pointing budget usually
separates bias, temporal and random terms — use a dedicated pointing error engineering method for that.

## TPM tracking
Technical performance measures are the few budget totals (e.g. rover mass, drive-mode power, link
margin) tracked at each design iteration against their allocation and a policy line. The NASA SE
handbook discusses TPMs as part of technical assessment *(unverified — primary inaccessible)*.
`budget_calc.py --snapshot` fits a least-squares straight line through the predicted values and:
- projects it to `--project-to` (or the last snapshot + `--horizon-days`, default 180);
- warns `trend-projects-breach` if the projection exceeds the allocation, or
  `trend-projects-margin-shortfall` if it falls inside the policy margin;
- reports the projected allocation-breach date when the trend is rising.
A straight line is a crude model: step changes (a new instrument) are not trends. Treat the projection as
a prompt for discussion, not a forecast.

## What the script does not do
- Judge whether the item list is complete (run a product-tree completeness review).
- Verify CBE evidence or maturity claims.
- Choose policy values. These belong to the programme and must be signed off by it.
