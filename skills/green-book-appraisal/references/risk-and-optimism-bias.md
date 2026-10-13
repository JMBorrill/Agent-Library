# Risk, uncertainty, optimism bias and contingency (Green Book 2026)

## Risk and uncertainty (paras 6.60-6.77, PDF pp.47-49)

- Risk and uncertainty must form part of the value-for-money judgement.
  - **Uncertainty**: assumptions that are not fully known.
  - **Risk**: the effect of uncertainty on objectives (para 6.61). This is consistent with the Orange Book.
- Risk types include commercial, legal and fraud risk (para 6.64). Orange Book Annex 4 gives a fuller list.
- Risk costs (para 6.65):
  - **impact costs**, incurred when a risk materialises;
  - **correction costs**, for putting things right;
  - **prevention costs**, for preventing, reducing, transferring or avoiding the risk.
  Weigh mitigation and transfer by their costs and benefits. Allocate each risk to the party best able to
  manage it (para 6.66).
- Contingent liabilities belong in the expected cost of risk (para 6.67).
- Express uncertainty with any of: a central estimate and range, expected values, confidence intervals or P90
  values. Consider tail risks proportionately (paras 6.68-6.73).
- Advanced methods include scenario analysis, decision trees, real options analysis and Monte Carlo
  simulation (paras 6.74-6.77).
- Fraud: pay particular attention when grants, loans or payments are made (para 2.24). Treat fraud proceeds as
  a one-sided transfer or as a social cost. If in doubt, assume fraud rather than error (paras 8.90-8.99,
  PDF pp.73-74).

## Optimism bias (paras 6.78-6.82, PDF p.50 / printed p.44)

- **What it is.** A demonstrated, systematic tendency to underestimate costs and durations and overestimate
  benefits (para 6.78).
- **Requirement.** Make explicit adjustments **at the outset**: increase costs and timeframes and decrease
  benefits (para 6.79; also para 2.25).
- **Sizing the adjustment.** Use the originating organisation's evidence on average historical forecast errors
  for similar proposals (para 6.80; evaluation evidence, para 10.5).
- **If there is no evidence.** Use the *generic values in the Green Book supplementary guidance on optimism
  bias* (para 6.81). An example of adjusting benefits locally is in the supplementary guidance for local
  partnerships, and some departments publish their own values (for example DfT).
- **The 2026 Green Book contains no optimism bias percentages.** The tool therefore requires them as inputs:

  ```
  python -m agentlib greenbook optimism-bias --capex 120 --upper-pct 66 --mitigation 40 \
      --source "Supplementary guidance table X, standard buildings, upper bound"
  ```

  It calculates applied % = upper % × (1 − mitigation % / 100), then adjusted = base × (1 + applied %), or
  (1 − applied %) for benefits. Optional `--opex/--opex-upper-pct`, `--benefits/--benefits-pct` and
  `--duration/--duration-upper-pct` handle the other elements.
- **Mitigation.** As specific risks are estimated and prevention costs added, reduce the adjustment in
  proportion to the risk prevented, but only where prevention costs are lower than the risk they prevent
  (para 6.82). Record the evidence for the mitigation % in the assumptions log.
- **Private finance.** Apply optimism bias to every shortlisted option, including the public sector option
  (para A.14).

## Contingency (paras 6.83-6.84, PDF pp.50-51)

- Contingency is a **financial-case** allowance for residual risk. It equals the remaining optimism bias
  adjustment plus the value of any unprevented risk, converted to nominal prices.
- It is typically **not allocated** to the project, because government self-insures. Instead it informs the
  organisation's risk liabilities and reserves.
- Prevention costs go into the proposal's core costs.
