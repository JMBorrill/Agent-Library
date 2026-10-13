# Optimism bias adjustment: depot rebuild capital costs

Computed with `python -m agentlib greenbook optimism-bias --capex 120 --upper-pct 66 --mitigation 40 --source "user-supplied upper bound from the Green Book supplementary guidance on optimism bias"`.

| Element | Base (£m) | Upper bound % | Mitigation | Applied % | Adjustment (£m) | Adjusted (£m) |
|---|---|---|---|---|---|---|
| Capital costs | 120.00 | 66% | 40% | 39.6% | 47.52 | 167.52 |

Applied % = 66% x (1 - 40%) = 39.6%. Adjusted capex = £120m x 1.396 = **£167.52m**.

## Basis and caveats

- **Where the percentage comes from.** The 2026 Green Book requires explicit optimism bias adjustments at the outset: costs and durations go up and benefits go down (paras 6.78-6.79, PDF p.50; source id treasury-green). It gives no percentages. It says to use the organisation's own historical forecast errors, or the generic values in the Green Book supplementary guidance on optimism bias where no such evidence exists (paras 6.80-6.81). The 66% upper bound is your user-supplied input from that supplementary guidance. Record the table and project type it comes from in the assumptions log.
- **Mitigation.** The 40% reduction must be evidenced by specific risks you have prevented, reduced, transferred or avoided (para 6.82). Prevention costs go into core costs.
- **Contingency.** The remaining £47.52m adjustment, plus the value of any unprevented risk, informs contingency in the financial case. It is converted to nominal terms there and is typically not allocated to the project, because government self-insures (paras 6.83-6.84).
- **Other adjustments.** Consider matching adjustments to operating costs, delivery duration and benefits.
