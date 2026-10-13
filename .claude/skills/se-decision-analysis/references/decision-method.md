# Decision method notes (library guidance)

Original text based on standard multi-criteria decision analysis (MCDA) practice; NASA SE Handbook
§6.8 is the registered source but was not readable in-session.

## What the script computes
1. **Screen**: alternatives violating a `must` threshold are removed (reported, never silently dropped).
2. **Normalise** (default min-max over feasible alternatives): best = 1, worst = 0 per criterion;
   `direction: min` inverts. `normalisation: none` divides by `scale_max` (use when scores are already
   on a common scale such as 1–5 or 0–10).
3. **Aggregate**: weighted sum Σ wᵢ·nᵢ (additive value model — assumes criteria are preferentially
   independent).
4. **Sensitivity**: each weight scaled by (1 ± p), others rescaled proportionally to keep Σw = 1.
5. **Switching weight**: scan wᵢ from 0 to 1 (step 0.001) and report the nearest value at which the
   winner changes.
6. **Evidence share**: fraction of the winner's total contributed by estimate/judgement/vendor scores.

## Pitfalls
- **Rank reversal**: min-max normalisation depends on which alternatives are in the set; adding or
  removing an alternative can change the order of others. Re-run when the set changes.
- **Double counting**: "mass" and "launch cost" may measure the same thing.
- **Weights after scores**: setting weights after seeing scores invites rationalisation — fix weights
  first, record who set them.
- **False precision**: three significant figures on judgement scores mean nothing; report margin.
- **Missing baseline**: without a do-nothing/current option you cannot show the change is worthwhile.

## Alternatives to weighted sums
Pairwise comparison (AHP), outranking, expected-value analysis under uncertainty (decision trees),
or cost-effectiveness ratios may suit better; document why the chosen method fits.
