# Distributional analysis and valuation (Green Book 2026)

## Distributional and place-based analysis (Chapter 7, PDF pp.55-58)

### Distributional analysis

- **Proportionality** (para 7.3). Match the effort to the effect:
  - small effects: describe them qualitatively or quantitatively;
  - significant effects: analyse them in monetary terms;
  - redistribution as an objective, or highly significant effects: present the welfare effects clearly.
- **Duties.** Apply the PSED for groups with protected characteristics (Equality Act 2010) and consider the
  Family Test (para 7.4).
- **Equivalisation** (Figure 7, PDF p.56). Scores are: first adult 0.67, each additional adult 0.33, child aged
  14 or over 0.33, child under 14 0.20. A couple with no children is the 1.00 reference. Divide household
  income by the total score.
- **Welfare weights** (paras 7.10-7.15, PDF pp.56-57):

  `weight = (national median equivalised income / group median equivalised income)^1.3`

  `weighted impact = change in group income × weight`

  The 1.3 is the elasticity of marginal utility of income. **Always present weighted estimates alongside
  unweighted ones** (para 7.13), and test the uncertainty in the weights (para 7.14).
  Tool: `python -m agentlib greenbook welfare-weight --national 600 --group 400 --income-change 1000`.
- **Transfers.** These must appear in distributional analysis (para 6.37).

### Place-based analysis

- **Additionality** (paras 7.16-7.20). Assess additionality, deadweight, displacement, substitution and
  leakage.
- **Sub-national metrics.** Always present them alongside UK-wide values (para 7.19).
- **Local authority funding** (paras 7.21-7.24). Follow the funding simplification doctrine; use allocation or
  competition.

## Valuation (Chapter 8, PDF pp.59-74)

- **Starting point.** Use opportunity cost, beginning from market prices **excluding taxes and subsidies**
  (paras 8.1-8.5).
- **Hierarchy of methods** (Figure 8), from most to least reliable:
  1. market prices;
  2. generic prices;
  3. revealed preference;
  4. stated preference or wellbeing valuation.
  Use stated preference only where robust revealed preference data are unavailable (para 8.18).
- **Generic values not stated in the Green Book.** Obtain current values from the named source and record them
  in the assumptions log:

  | Value | Source |
  |---|---|
  | Social value of carbon | DESNZ |
  | QALY | Green Book supplementary guidance on health |
  | VPF | DfT TAG data book |
  | SLY/VOLY | — |
  | WELLBY | Green Book supplementary guidance on wellbeing |
  | Value of travel time | DfT |
  | Costs of crime and fire | Home Office |

- **Inputs** (paras 8.25-8.34):
  - Labour cost includes on-costs.
  - Redundancy payments are transfers.
  - Include residual values at the end of the appraisal period.
  - Base maintenance costs on the asset maintenance policy.
- **Economy** (paras 8.35-8.52):
  - Demand-side spending has no national productivity effect.
  - Assume **full displacement of jobs**; any exception needs evidence signed off by the chief economist
    (paras 8.41-8.43).
  - For housing, use land value uplift as set out in the MHCLG Appraisal Guide.
- **Climate and environment** (paras 8.63-8.87):
  - Value energy use as quantity × LRVC.
  - Value emissions as quantity × emissions factor × social value of carbon. Report emission levels as well
    as monetised values.
  - Emissions below 0.1 MtCO2e in every year are generally negligible, but basic analysis is still needed
    (para 8.75).
  - Apply the natural capital screening questions and ENCA.
  - Use climate scenarios of 2°C, or 2°C and 4°C (para 8.86).
- **Government** (paras 8.88-8.99):
  - Efficiency savings must not come from cutting outputs.
  - Treat fraud proceeds as a one-sided transfer or a social cost.
  - Treat over- and under-payments as transfers, with additional remediation costs.
