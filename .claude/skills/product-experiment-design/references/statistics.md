# Statistics notes for two-proportion experiments

Original wording. These are standard results (normal approximation to the binomial); they are not
taken from any registered source. `gov-service` is cited only for the general principle of measuring
outcomes, and it was inaccessible in this environment.

## Notation
p1 = control (baseline) rate, p2 = treatment rate, d = p2 − p1, q = 1 − p, n = units per arm
(equal allocation), z_x = standard normal quantile (`statistics.NormalDist().inv_cdf(x)`).

## Sample size per arm
**Pooled (default)** — variance under H0 uses p̄ = (p1+p2)/2; under H1 uses each arm's rate:

    n = [ z(1−α/2)·√(2·p̄·q̄) + z(1−β)·√(p1·q1 + p2·q2) ]² / d²

**Unpooled** — both terms use the H1 variance:

    n = ( z(1−α/2) + z(1−β) )² · (p1·q1 + p2·q2) / d²

Round up to the next integer. Neither applies a continuity correction (which would increase n).

### Hand-verified known answer (used in tests)
p1 = 0.10, p2 = 0.12, α = 0.05 two-sided, power = 0.80.
z(0.975) = 1.959964, z(0.80) = 0.841621.
- p̄ = 0.11 → √(2·0.11·0.89) = √0.1958 = 0.442493
- √(0.10·0.90 + 0.12·0.88) = √0.1956 = 0.442267
- Pooled: (1.959964·0.442493 + 0.841621·0.442267)² / 0.0004 = (0.867271 + 0.372222)² / 0.0004
  = 1.536343 / 0.0004 = 3,840.85 → **3,841 per arm**
- Unpooled: (2.801585)² · 0.1956 / 0.0004 = 7.848879 · 0.1956 / 0.0004 = 3,838.10 → **3,839 per arm**

The commonly quoted "about 3,839" is the unpooled formula; tools differ by a few units depending on
formula and rounding. Always state which you used.

## Minimum detectable effect
Given n, the script finds the smallest d (bisection, 200 iterations) whose required n ≤ the given n.
For p1 = 0.10 and n = 3,841 (pooled) the MDE is ≈ 0.0200, as expected from the example above.
Returns "not reachable" when even the largest possible effect needs more than n.

## Evaluating a result
- Test statistic with pooled rate p̂ = (x1+x2)/(n1+n2): z = d̂ / √(p̂q̂(1/n1 + 1/n2)); two-sided
  p = 2(1 − Φ(|z|)).
- Confidence interval on the difference uses the unpooled SE: d̂ ± z(1−α/2)·√(p1q1/n1 + p2q2/n2).
- Known answer: 100/1000 vs 130/1000 → p̂ = 0.115, SE0 = 0.014267, z = 2.1027, p = 0.0355;
  SE1 = 0.014251, CI = 0.03 ± 0.027932 = [0.002068, 0.057932].
- If both groups have 0% or 100% conversion the test is not computable (p reported as null).

## Pitfalls the checker cannot see
- **Peeking**: repeatedly testing and stopping at the first p < 0.05 inflates false positives well
  above α. Fix n in advance or use a sequential method designed for it.
- **Sample-ratio mismatch**: unequal arm sizes beyond chance usually mean a bucketing bug.
- **Unit of randomisation vs analysis**: randomising walkers but analysing walks violates
  independence (clustered data) and makes CIs too narrow; analyse at the randomisation unit or use
  cluster-robust methods.
- **Multiple metrics**: one primary metric; treat the rest as exploratory or guardrails.
- **Novelty and weekly cycles**: run whole weeks.
- **Small expected counts**: when n·p < ~10 in any arm, use an exact test instead.
