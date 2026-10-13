# Decision report: LunaSat-12 solar array configuration

Computed with `python -m agentlib nasa-se trade-study solar-array-trade.yaml`; structure per Table 6.8-1
[nasa-se 6.8, p. 213].

## 1. Executive Summary
- Recommendation: carry Body-mounted panels and Single-wing deployable to the decision-maker as closely
  ranked options, with Body-mounted panels highest on the stated weights.
- Problem: select the solar array configuration before PDR given a 4 % power margin.

## 2. Problem/Issue Description
End-of-life power margin is the top project risk. The decision-maker is the project chief engineer; the
recommendation team is the power and structures leads.

## 3. Decision Matrix Setup Rationale
- Criteria: life-cycle cost (weight 0.35), mass (0.25), end-of-life power margin (0.25), technology
  maturity (0.15); scores 1-10 with operational definitions in the trade plan.
- Mandatory criterion: fits the 12U dispenser envelope. An option that fails a mandatory criterion is
  disregarded [nasa-se 6.8.1.2.1, p. 210], so the roll-out flexible array is screened out.
- Evaluation methods: vendor quotes, mass roll-up, power analysis, TRL evidence.

## 4. Decision Matrix Scoring Rationale
Body-mounted panels score high on cost, mass and maturity but only 3 on power margin; the double-wing array
maximises power but costs most.

## 5. Final Decision Matrix

| Criterion | Weight | Body-mounted panels | Single-wing deployable | Double-wing deployable |
|---|---|---|---|---|
| Life-cycle cost | 0.35 | 9 | 6 | 4 |
| Mass | 0.25 | 8 | 6 | 5 |
| End-of-life power margin | 0.25 | 3 | 8 | 10 |
| Technology maturity | 0.15 | 9 | 8 | 7 |
| **Weighted total** | 1.00 | 7.25 | 6.80 | 6.20 |

Disregarded: Roll-out flexible array (fails the mandatory envelope criterion).

## 6. Risk/Benefits
Body-mounted panels keep the power risk open; the single-wing deployable reduces it at higher cost and a
deployment mechanism risk.

## 7. Recommendation
The top two differ by about 6 %. Sensitivity: raising the power-margin weight to 0.35 and lowering cost to
0.25 gives Body-mounted 6.65 vs Single-wing 7.00, so the ranking flips. Because uncertainty in the weights
could change the ranking, present both closely ranked alternatives to the decision-maker [nasa-se 6.8.1.2.5, p. 212].

## 8. Dissent
The power lead dissents from the body-mounted option because of the open power risk; recorded for the
decision-maker.

## 9. References
Trade plan v1; power analysis 2025-09; vendor quotes. Assumptions: scores reflect current vendor data.
