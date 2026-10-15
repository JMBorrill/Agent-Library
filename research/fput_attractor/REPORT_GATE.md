# Validation gate — findings (FPUT attractor dynamics)

**Date:** 15 October 2026 · **Scope:** the bounded gate approved after the adversarial review
(`inputs/Nonlinear_Waves_Adversarial_Review_2026-10-14.pdf`).
**System:** fixed-end α-FPUT chain, N = 8, α = 0.25, η = 0.0025, Ω = 0.347, uniform drive F cos Ωt.
**Earlier work:** Exp 0–4 in `REPORT.md`, not repeated here. **New in this gate:** Exp 5–9 (`experiments/exp5…exp9`).
**Compute:** ≈ 2.7 CPU-hours (upper bound) against an 8-hour cap. Raw results and timings are in `results/exp5…exp9*.json`.

## Decision: **HOLD** on the full programme — the validation gate itself **passed**

The coexistence is genuine and the connecting bifurcation mechanism is identified by direct computation. That
mechanism is, however, a *generic, textbook* scenario: a subcritical Neimark–Sacker bifurcation plus a saddle-node of
invariant circles, giving hysteresis. By the review's own criterion, a routine known scenario does not earn the
8–12-week programme.

The only open question with a plausible claim to new insight is the modal one (Q4 below). It justifies at most one
further narrow gate, and only if a correction is derived before it is tested on held-out (η, Ω).

---

## Q1. Is there convincing evidence for two distinct attracting invariant sets? — **Yes.**

At F = 0.0045 the drive-locked orbit and the modulated state are both attracting invariant sets. The evidence is
quantitative, not visual (Exp 5; `figures/fig7_long_time_validation.png`).

**Long-time integration.** Five initial conditions were each run to 30 000 drive periods with five methods: DOP853 at
rtol 10⁻¹⁰ and 10⁻¹², and RK4 at 400, 800 and 1600 steps per period. The ICs were:
- rest;
- the locked orbit + 10⁻³ and + 10⁻² in Q₁;
- the locked orbit + 0.5 and + 0.8 along the critical direction (basin radius 0.633 along that direction).

**Same final state everywhere.** Each IC reaches the same final state under all five methods: rest and +0.8 go to the
torus; the other three go to the locked orbit.

**Drive phase is exact.** DOP853 restarts the clock every 500 periods. Absolute-time and phase-reset solutions agree
to 5×10⁻¹² (3 500 periods) and 1×10⁻¹¹ (10 000 periods).

**Locked set — attraction at the Floquet rate:**
- distance to the fixed point decays at a fitted −0.0038508 per period, against ln|μ_max| = −0.0038534;
- it reaches 10⁻¹⁰ by period 3 850–5 804 and the 10⁻¹⁴ round-off floor after that (RK4/1600, DOP853 1e-12).

**Modulated set — converged at 3 500, 10 000 and 30 000 periods:**
- **Rotation number:** |ρ| = 0.024041850 at every checkpoint. DOP853 1e-10 vs 1e-12 differ by 7×10⁻¹³, and RK4 converges
  at 4th order (1.3×10⁻⁸, 8.4×10⁻¹⁰, 5.4×10⁻¹¹ for 400/800/1600 steps).
- **E₁ range:** 0.42951905 / 0.42951926 / 0.42951917; the variation is window sampling, and methods agree to < 10⁻⁸.
- **Pointwise differences are drift along the curve:** RK4/1600 vs DOP853 differ by 8.6×10⁻⁶ at 30 000 periods. That
  is a 1.6×10⁻⁵ rad phase lag along the curve (≈ 2πΔρ·n). The distance to the reference invariant curve stays at the
  3×10⁻⁶ fit floor throughout.

**Transient.** The 1.3×10⁵-period run (Exp 2) shows no drift. Exp 6 below establishes normal attraction at rate η/2.
A transient longer than ≈ 2×10⁶ time units is not excluded by any finite run, but it is incompatible with a normally
attracting smooth invariant circle.

## Q2. Best-supported classification of the modulated state — **quasiperiodic: an attracting smooth invariant circle of the stroboscopic map (a 2-torus of the flow)**

Exp 6 and Exp 2; `figures/fig8_lyapunov_convergence.png`.

| Test | Result | Resolution / limitation |
|:--|:--|:--|
| Neutral map exponent λ₁ (10⁵ periods, RK4/200 and /400) | −2.0×10⁻⁷ and −3.0×10⁻⁷ (second-half slope); 10-block mean 0.4 ± 2.2×10⁻⁶ (2 s.e.) | finite-time; cannot prove exactly 0 |
| Bounded log-stretch | max \|log-stretch\| = 5.7 over 10⁵ periods; cumulative λ₁ falls exactly as 1/t (2.6×10⁻⁴ → 2.7×10⁻⁶) | ⇒ \|λ₁\| ≤ 1.1×10⁻⁶ per time unit |
| Independent integrator (DOP853 tangent, 3 000 periods) | λ₁ = +1.0×10⁻⁶, λ₂ = −1.254×10⁻³ | shorter run |
| Transverse exponents | λ₂…λ₄ = −1.2504×10⁻³ ± 4×10⁻⁷ = −η/2; pairing λᵢ + λ₁₇₋ᵢ = −η | — |
| Neutral direction | top Lyapunov vector ∥ curve tangent to 7.6×10⁻⁵ rad | — |
| Return structure | circle-map lift derivative ∈ [0.60, 1.35] > 0: a circle diffeomorphism | angle from PCA projection (monotone) |
| Rotation-number convergence | NAFF error 1.1×10⁻⁹ (2¹⁰ periods) → 9×10⁻¹¹ (2¹³–2¹⁴) | RK4/800 discretisation error ~10⁻⁹ |
| Locking test | ρ(F) strictly monotone over F = 0.0045 ± 10⁻⁵ (dρ/dF = 0.585); any Arnold-tongue plateau < 10⁻⁶ wide in F | very high-order resonances are undetectable |
| Periodicity | no p/q with q ≤ 10⁶ within the 3×10⁻¹³ frequency drift (Exp 2) | period > 10⁶ not excluded |
| Line spectrum | 99.998 % of power on harmonics of ρ (Exp 2) | — |

**Rejected:**
- *Chaos:* no exponent > 1.1×10⁻⁶, and the spectrum is a pure line spectrum.
- *Low-order periodic orbit:* excluded by the periodicity and locking tests.
- *Long transient:* rejected within the integrated window.

**Unresolved:** phase-locking with period > 10⁶ drive periods.

## Q3. Is there evidence for a specific bifurcation connecting the states? — **Yes: subcritical NS → unstable invariant circle → saddle-node of circles at F_low**

The connection is established by direct computation, not inferred from hysteresis (Exp 7, 8, 8b, 8c;
`figures/fig9_normal_form.png`, `figures/fig10_edge_fold.png`).

1. **Crossing reproduced** (Exp 7):
   - F_c = 0.004693158233 (DOP853 shooting);
   - d|μ|/dF = 17.920 (review: 17.92);
   - θ/2π = 0.0277, which is non-resonant.
2. **First Lyapunov coefficient** d = Re(e^{−iθ}c₁) = **+0.0084656 > 0 (subcritical)**:
   - converged to 10⁻⁸ relative across RK4 800/1600/3200 and DOP853;
   - the 4-mode and 5-mode truncations are also subcritical (+0.00586, +0.00773).
   - **How the formula was validated:** it was written from memory, so it was checked by direct iteration of random
     4-D test maps. On both the supercritical and subcritical sides, the predicted invariant-circle radius matches to
     < 1 %, with error O(β). The map's second and third derivatives match finite differences.
3. **Parameter-free falsification test passed.** The normal form predicts where the locked orbit's basin ends in each
   direction, ε_φ = √((1−|μ|)/d) / |⟨p, d_φ⟩|. Against the 20 independently bisected radii of Exp 3b, the
   measured/predicted ratio tends to 1 as F → F_c⁻: at F = 0.00468 it is 1.011, 0.873, 0.920 and 0.998, with the
   deviation shrinking roughly ∝ r.
4. **The basin boundary contains an unstable invariant circle, not the saddle orbit** (edge tracking, Exp 8):
   - At every F from 0.00465 down to 0.0042166, the edge state is a smooth circle (Fourier-fit residual down to 10⁻⁸).
   - It is not a fixed point; the saddle orbit lies 0.54 away.
   - The same circle is reached from two different starting lines (ρ agreeing to 10⁻¹⁰).
   - **Near F_c it matches the normal form without fitting** (F = 0.00465): rotation number 0.027308 vs predicted
     0.02731; instability rate 1.50×10⁻³ vs 2(1−|μ|) = 1.59×10⁻³.
5. **Fold of invariant circles at F_low = 0.0042164 ± 2×10⁻⁷** (Exp 8/8b/8c):
   - **Location:** the torus is lost between 0.00421625 and 0.0042165625 (bisection).
   - **Collision:** the unstable edge circle approaches the stable torus. Their median distance falls 0.63 (F = 0.0045) → 0.026, with
     distance² linear in F (exponent 0.505) and extrapolating to F_low = 0.00421646, inside the bracket. The
     rotation numbers merge (gap 9×10⁻⁴ → 2.4×10⁻⁵).
   - **Normal rates:** the stable torus's slow exponent λ₂ leaves −η/2 between F = 0.0043 and 0.00425, then tends to 0.
     The edge circle's instability rate is non-monotone: it rises from 0 at F_c and falls back to 0 at F_low.
   - **Saddle-node symmetry:** the ratio of the two normal rates → 1 (1.49, 1.23, 1.05, 0.97). Their mean scales with
     exponent 0.49–0.50 (prediction ½).
   - **Ghost transit times below F_low:** exponent γ = 0.49 ± 0.002 at the bracket midpoint (0.47–0.53 for the
     fit-based F_low). Because it is sensitive to F_low, γ ranges 0.35–0.62 across the full bracket: consistent with ½,
     not a precise measurement.

**Limitations of Q3:**
- **Sampled, not continued:** the branch is sampled at 12 values of F by edge tracking, not followed by pseudo-arclength
  continuation of invariant circles, so smoothness between samples is inferred.
- **Possible locking along the branch:** rotation numbers along both branches pass through rationals, where the
  circles would contain phase-locked orbits in tongues too thin to resolve here.

## Q4. What mathematical question remains unexplained?

**Why the coupling pathway sets the bifurcation locations.**
- **What is known:** the 8- vs 4-mode shift of F_c (8.34 %) is a shift of the Krein collision. Symmetric knockouts
  attribute it mainly to the triad {2,3,5} (Exp 9, `figures/fig11_knockouts.png`):
  - within the {1–5} truncation, removing {2,3,5} cancels 96 % of mode 5's shift ({1,4,5}: 37 %);
  - in the full chain, {2,3,5} alone reopens 67 % of the gap, and {2,4,6} + {3,3,6} another 23 %;
  - direct forcing of modes 5 and 7 accounts for 1.3 % (**the review's forcing caveat is rejected**).
- **What is not derived:** attributions are non-additive, and nothing derives — before testing — how these couplings
  set F_c, the coefficient d, or F_low. The modulation frequency (ρ ≈ 0.024) is also unexplained.
- **Retraction:** my earlier "second-order slaving" interpretation is withdrawn. As the review notes, all modes share
  the decay rate η/2, so rapid slaving cannot be assumed.

## Q5. Does the evidence justify further research?

- **Numerically:** yes. The coexistence and the connecting mechanism are robust, reproducible and verified several
  independent ways.
- **Scientifically:** only narrowly. The bifurcation scenario is generic. A contribution would need the predictive
  modal explanation of Q4: derive a coupling-based correction for F_c (and ideally d and F_low) from the {2,3,5}/{2,4,6}
  pathway, then test it on predeclared held-out (η, Ω) values.
- **Stop rule:** stop if the correction fails out of sample.

---

## Failed hypotheses, invalid analyses and corrections (this gate)

- **Review caveat "direct forcing of modes 5 and 7 drives the gap":** rejected (1.3 %).
- **Exp 5 "decay-to-curve" rate for the torus:** invalid, not used. The trajectories were already on the curve
  (fit floor ~5×10⁻⁶) before the fit window. Transverse attraction is established by λ₂ instead.
- **Exp 5 decay-rate fit for DOP853 rtol 10⁻¹⁰ locked runs:** invalid, because the fit window hit the tolerance floor
  of 1.2×10⁻¹⁰. The rtol 10⁻¹² and RK4 fits are used instead.
- **Exp 8 coarse ghost exponent (−0.36):** superseded by Exp 8b/8c. It was contaminated by a constant exit time and
  F_low uncertainty.
- **Exp 8b separate F_low extrapolations from λ₂² and σ_u²:** these miss the bracket by about 2–3×10⁻⁷ on opposite sides
  (local exponents 1.25 and 0.79). This is pre-asymptotic stable/unstable asymmetry. Only the distance fit and the rate
  mean / ratio are used as fold evidence.
- **Earlier hybrid-monodromy decomposition (H4c, Stage 3):** remains rejected.
- **Errors of my own, caught before use:**
  - the normal-form test harness initially iterated to an unconverged radius; the formula was correct;
  - one toy-test expectation was mis-derived.

## Limitations (overall)

- **Scope:** one (N, α, η, Ω) point with continuation in F only. No held-out parameters were tested.
- **Classification bounds:** |λ₁| ≤ 1.1×10⁻⁶ and locking period > 10⁶ are numerical bounds, not proofs. There is no
  rigorous enclosure.
- **Not mapped:** the high-amplitude locked orbit found in Stage 3 (a third attractor) remains outside this gate's
  mechanism analysis, and its basin is unmapped.
- **No novelty claimed:** the scenario is standard; see the review's references for precedent.

## Reproduction

`REPRODUCE.md` covers all runs. The gate-only commands are:
`python experiments/exp5_long_time_validation.py` (24 min wall, 4 cores), `exp6…` (3.5 min), `exp7…` (≤ 1 min),
`exp8…` (8 min), `exp8b…` (5 min), `exp8c…` (seconds), `exp9…` (40 s), then `make_figures_gate.py`.

Tests: `python -m pytest` runs 35 tests (24 earlier + 7 normal-form + 4 gate-tool).
