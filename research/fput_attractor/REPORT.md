# Independent verification of FPUT attractor dynamics — findings

**Date:** 14 October 2026 · **System:** fixed-end α-FPUT chain, N = 8, α = 0.25, η = 0.0025, Ω = 0.347, uniform drive F cos Ωt.
**Baseline:** `baseline/` (Stage 1 + Stage 2 package, verbatim, SHA-256 verified). **New code:** `fputv/`, `experiments/`, `tests/`.

## Recommendation: **GO** for a bounded next stage · **HOLD** on any novelty or publication claim

The apparent coexistence at F = 0.0045 is **genuine dynamical multistability, not a numerical artefact or a long
transient**. It reproduces with three independent integrator families and two independent implementations. All
observables converge, and the mechanism is identified to the extent stated below. Nothing here is claimed as new
physics. The ingredients are standard: Krein collisions in weakly damped near-Hamiltonian systems, a subcritical
Neimark–Sacker bifurcation, and a resonance-curve fold. Whether this specific picture for the driven FPUT chain is
already published needs the literature review in `baseline/Nonlinear_Waves_Stage2/NEXT_HANDOFF.md`.

## Robust conclusions (each independently verified)

1. **The modulated state is a quasiperiodic attractor (an attracting invariant circle of the stroboscopic map,
   i.e. a 2-torus of the flow), not chaos and not a transient.**
   - **Frequency:** its rotation number, |ρ| = 0.0240418497 ± 2.4×10⁻⁹, is identical across RK4, DOP853 and LSODA.
   - **Line spectrum and circle fit:** the spectrum is a pure line spectrum (99.998 % of power on harmonics of ρ).
     A Fourier-in-angle fit converges exponentially (relative residual 3×10⁻⁸ at 120 harmonics), which only a
     smooth invariant circle can do.
   - **Lyapunov exponents:** λ₁ = 0 to within the ~10⁻⁵ estimator resolution, while λ₂…λ₁₅ ≈ −η/2 = −1.25×10⁻³.
   - **No transient:** there is no drift over 1.3×10⁵ drive periods (≈ 6 000 damping times), and every sampled
     initial condition that ends modulated lands on the same torus.
2. **At F = 0.0045 the full chain has three coexisting attractors:**
   - the drive-locked orbit continued from F = 0 (max |μ| = 0.99615);
   - the quasiperiodic torus;
   - a previously unreported high-amplitude drive-locked orbit (E₁ = 1.29, all multipliers at e^{−ηT/2}).
   A saddle orbit is also present.
3. **The locked branch loses stability through a subcritical Neimark–Sacker-type bifurcation at
   F_c = 0.004693158232 (± 10⁻¹²), and this produces a hysteresis loop.**
   - **Upward continuation:** the state stays locked to F_c and then jumps to the large torus.
   - **Downward continuation:** the torus persists down to F ≈ 0.00425 (lost between 0.0043 and 0.0042).
   - **Shrinking basin below F_c:** the locked orbit's basin radius shrinks as (F_c − F)^½. The measured local
     log-log slopes are 0.54, 0.50 and 0.49 as F → F_c⁻.
   - **Jump above F_c:** a 10⁻⁶ perturbation grows directly to the pre-existing large torus with no small-torus
     stage.
4. **Mechanism of the stability loss.** Uniform damping makes the flow conformally symplectic
   (Mᵀ J M = e^{−ηT} J, verified to 10⁻¹³). Every Floquet multiplier therefore sits on |μ| = e^{−ηT/2} until two
   pairs collide (Krein collision at F_K ≈ 0.004095). They then split radially with |μ₁||μ₂| = e^{−ηT}, and the
   outer pair reaches 1 at F_c.
5. **The 8- vs 4-mode threshold gap (8.34 %) is real and is an omitted-mode effect, not an implementation error.**
   - **Agreement:** both thresholds agree with the baseline to 8×10⁻¹⁰, the size of the baseline's own RK4/720
     bias.
   - **Where the gap sits:** the whole gap comes from an earlier Krein collision in the full chain.
   - **Which modes:** mode 5 carries 73 % of it and mode 6 25 %; modes 7–8 contribute < 5 %.
   - **Same structure in the truncation:** the 4-mode model shows the same subcritical hysteresis, shifted up by
     ~0.0004–0.0005 in F.

## Experiment 0 — baseline preserved and rerun

`baseline/` is byte-identical to the supplied zip (41 files, `SHA256SUMS`). In a temporary copy, the 4/4 baseline
unit tests pass. The Toda benchmark and the Floquet, refine and basin scripts reproduce every stored number to
≤ 6×10⁻¹⁴ relative difference; two files are byte-identical. Raw: `results/exp0_baseline_rerun.json`.

**Governing equations checked.** Several properties are verified by independent tests:
- **Force law:** the projected physical force law equals the baseline's C[k,i,j] tensor form to 10⁻¹³ for the
  full chain and for the {1–4}, {1,2,4,6} and {1–5} truncations.
- **Jacobian:** it matches finite differences.
- **Z₂ symmetry:** q_n(t) → −q_{N+1−n}(t+T/2) is an exact symmetry, and all locked orbits found are symmetric.
- **Conformal symplecticity:** holds as stated above.

## Experiment 1 — independent reproduction (F = 0.0045, 3 500 periods)

New implementation: physical coordinates (baseline: modal). Integrators: own RK4 (160–1280 steps/period), DOP853
(rtol 10⁻¹⁰, 10⁻¹²), LSODA (Adams/BDF, rtol 10⁻¹⁰, 10⁻¹¹), plus the baseline's own code.

| Observable (last 750 periods) | Converged value (DOP853/LSODA/RK4-1280 spread) | Baseline report (RK4/320) |
|:--|:--|:--|
| From rest: E₁ range | **0.4295181341** (2×10⁻¹⁰) | 0.4295205853 (bias 2.5×10⁻⁶; our RK4/320 gives the same) |
| From rest: rotation frequency | **0.02404185** (all methods) | — |
| Locked + 10⁻³: E₁ range | 5.109×10⁻⁹ (decaying transient; LSODA/1e-10 gives 4.3×10⁻⁹) | 5.108×10⁻⁹ |
| Locked orbit max \|μ\| | **0.996154026** (RK4-1600 vs DOP853: 7×10⁻¹⁰) | 0.996153725 (RK4/360) |

- **Convergence:** RK4 errors fall by ×7, ×9 and ×14 per step halving, approaching the 4th-order ×16
  (`figures/fig2_convergence.png`).
- **Pointwise vs on-attractor divergence:** after 3 500 periods, DOP853 and LSODA differ from RK4-1280 pointwise by
  2×10⁻⁶. That difference is a 3×10⁻⁶ rad phase lag *along* the torus, the expected neutral drift of quasiperiodic
  motion; no exponential separation is seen.
- **Discrepancy noted:** LSODA at rtol 10⁻¹⁰ misestimates the tiny decaying-transient amplitude by 16 %. Tighten it
  before using LSODA for small residuals.

Raw: `results/exp1_reproduction.json`, `results/exp1_trajectories_E.npz`.

## Experiment 2 — classification of the modulated state

| Diagnostic | Result at F = 0.0045 (also run at 0.0044, 0.0050) | Limitation |
|:--|:--|:--|
| Stroboscopic section | closed curve; monotone winding (100 % of increments) | projection could hide structure |
| Invariant-circle Fourier fit | residual 0.18 → 1.6×10⁻⁴ → 3×10⁻⁸ (J = 2, 40, 120): exponential | assumes the PCA angle parametrises the curve (checked: monotone) |
| Windowed NAFF frequency (8 windows) | drift 2.8×10⁻¹³ (0.0044: 7×10⁻¹¹; 0.0050: 7×10⁻¹¹) | at fixed discretisation; step error 2.4×10⁻⁹ |
| Line-spectrum test, E₁ and Q₁ | 99.998 % / 99.995 % of power on k ρ lines; strongest peak at 2ρ (explains the Stage 1 "20.8-period" harmonic) | sampling folds frequencies into [0, ½] |
| Exact periodicity | no recurrence < 10⁻⁶ for lags ≤ 2 000; no p/q with q ≤ 10⁶ within the frequency drift | cannot exclude locking with period > 10⁶ |
| Lyapunov spectrum (16 exps, QR) | λ₁ = +2×10⁻⁶ (quarters −5×10⁻⁶, +9×10⁻⁶); λ₂..λ₁₅ = −1.25×10⁻³; pair sums λᵢ+λ₁₇₋ᵢ = −η ± 4×10⁻⁶ | λ₁ resolution ~10⁻⁵ per time unit; a zero exponent cannot be proven |
| Transient bound | E₁ range constant to 1.2×10⁻⁷ over 8 windows of 16 384 periods | no finite run excludes an arbitrarily long transient |
| Z₂ symmetry | S-image of half-period samples lies on the attractor (6.6×10⁻⁵ < sample spacing 1.3×10⁻⁴) | resolution set by sampling |

**Validation of the Lyapunov code** on the locked orbit:
- **Pair sum:** λ₁+λ₂ matches the Floquet value 2 ln|μ₁|/T to 3.7×10⁻⁷.
- **Total sum:** equals −Nη up to the RK4/200 damping error of 1.25×10⁻⁵.
- **Estimator:** the slope over the second half of the run removes the initial-frame transient. Individual
  exponents inside degenerate multiplier groups converge only slowly; this is expected.

**Classification: quasiperiodic (attracting smooth invariant circle).** It is *not* chaotic (no positive exponent
above 10⁻⁵ and a pure line spectrum). It is *not* a transient within 1.3×10⁵ periods: the circle is normally
attracting at rate η/2, and its relaxation time is ~44 periods. A very-high-order resonance (period > 10⁶) is
not excluded. Raw: `results/exp2_classification.json`, `results/exp2_*.npz`; `figures/fig3_classification.png`.

## Experiment 3 — multistability, hysteresis, bifurcation type

**Locked-orbit catalogue at F = 0.0045** (51 Newton starts, seed 20261014):

| Orbit | Hits | max \|μ\| | Unstable | E₁ | Exists for F in |
|:--|--:|--:|--:|--:|:--|
| continued branch (from F = 0) | 31 | 0.996151 | 0 | 0.114 | [0.003, 0.006], stable for F < F_c |
| high-amplitude orbit | 8 | 0.977618 (= e^{−ηT/2}) | 0 | 1.286 | F ≥ 0.0031148 (fold with saddle), stable throughout |
| saddle | 2 | 1.0817 | 1 | 0.313 | F ≥ 0.0031148 |

- **High-orbit stability is real:** it is confirmed dynamically (10⁻³ and 3×10⁻² kicks decay to 10⁻¹⁴).
- **The 4-mode truncation has the same three-orbit structure:** its fold is at F ≈ 0.00305 and its high orbit has
  E₁ = 3.09.

**Basin sample at F = 0.0045** (84 ICs, 8 000 periods each):
- **Random ICs:**
  - scale 0.25: 16/16 modulated (Wilson 95 % CI 0.81–1.00);
  - scale 0.5: 4/16 (0.10–0.50);
  - scale 1.0: 8/16 (0.28–0.72).
- **Segment from locked orbit to torus:** a single boundary crossing between λ = 0.45 and 0.50.
- **Along the critical eigenvector:** the orbit is recovered up to ε = 0.56.
- **No sampled IC reached the high-amplitude orbit.** The sampling design does not resolve its basin.

**Hysteresis** (dF = 10⁻⁴, seeded 10⁻⁷ noise, ≤ 30 000 periods/step), `figures/fig4_hysteresis.png`:

| Model | Upward: locked → torus between | Downward: torus → locked between | Bistable window |
|:--|:--|:--|:--|
| Full chain | 0.0046 / 0.0047 (F_c = 0.004693) | 0.0043 / 0.0042 | ≈ 0.00425 – 0.004693 |
| 4-mode | 0.0050 / 0.0051 (F_c = 0.005085) | 0.0048 / 0.0047 | ≈ 0.00475 – 0.005085 |

- **Torus family is continuous:** along the downward branch the rotation frequency varies smoothly
  (0.02393 → 0.02421).
- **Match to the quoted modulation period:** at F = 0.0050 the period is 1/ρ = 41.30 drive cycles. This matches
  the 41.3 quoted in the Stage 1 README for that case; the paper itself was not re-checked here.
- **Stage 1 rest-start result explained:** the 4-mode model locks from rest at F = 0.0045 because 0.0045 lies below
  its bistable window, not because the truncation cannot produce the modulated state.

**Bifurcation type**, `figures/fig5_subcritical.png`. Raw: `results/exp3_multistability.json`,
`results/exp3b_subcritical_scaling.json`.
- **Exp 3b (supersedes 3 D1):** four probe directions in the critical plane, canonical eigenvector phase, nine
  log-bisections each. The basin radius scales with local slopes 0.54, 0.50, 0.49 (mean) and 0.44–0.52 (per
  direction) over the three closest F values (F_c − F = 9×10⁻⁵ … 1.3×10⁻⁵). This is consistent with an unstable
  invariant circle collapsing onto the orbit, i.e. the **subcritical** prediction of ½.
- **D2:** above F_c (0.0048, 0.0050, 0.0052), 10⁻⁶ kicks grow exponentially and saturate only on the large torus.
  That torus matches the downward-continuation state to 10⁻⁵ in E₁ range and 10⁻⁸ in ρ.
- **Nondegeneracy checks:**
  - transversality d|μ|/dF ≈ 17.9 ≠ 0;
  - critical angle 0.1739 rad (θ/2π = 0.0277), far from the strong resonances 1/2, 1/3, 1/4.
- **Criticality is established only numerically:** the first Lyapunov coefficient was not computed.

## Experiment 4 — Floquet thresholds and the reduced model

**Verification** (`results/exp4_floquet_reduced.json`, own Newton + brentq):

| Model | RK4 200 / 400 / 800 / 1600 | Richardson | DOP853 variational | Baseline (RK4/720) |
|:--|:--|:--|:--|:--|
| Full | 0.004693311646 / 0.004693166962 / 0.004693158751 / 0.004693158264 | 0.004693158232 | **0.004693158233** | 0.0046931590 (+7.7×10⁻¹⁰) |
| {1,2,3,4} | 0.005084784024 / 0.005084653008 / 0.005084645160 / 0.005084644680 | 0.005084644648 | **0.005084644649** | 0.0050846454 (+7.5×10⁻¹⁰) |

Truncations {1,2} and {1,2,3} show no Krein collision and no instability of the locked branch up to F = 0.0066.
This is consistent with the locked responses of those truncations reported in Stage 1.

Checks performed at the DOP853 thresholds:
- **Finite-difference monodromy:** |μ| = 1 ± 10⁻⁹; matrix agrees with the variational one to 10⁻⁹.
- **det M:** equals e^{−mηT} to 5×10⁻¹³.
- **Multiplier pairing:** holds to 2×10⁻¹³.
- **Half-period symmetric map:** (DG)² = M. At equal step size it agrees with the full map by construction, so it
  checks the symmetry algebra, not discretisation error.

**Mechanism — predeclared hypotheses** (`figures/fig6_krein_modes.png`):

| Hypothesis | Test | Outcome |
|:--|:--|:--|
| H4a: the gap is a shift of the Krein collision point F_K, not of post-collision growth | F_K and F_c − F_K for both models | **Supported.** F_K shifts by −4.58×10⁻⁴ against a gap of −3.91×10⁻⁴; F_c − F_K differs by only +6.6×10⁻⁵ (17 %, opposite sign) |
| H4b: one omitted mode carries ≥ 50 % of the gap | add mode k to {1–4}; remove mode k from full | **Supported.** Mode 5: 73 % / 73 %; mode 6: 25 % / 23 %; mode 7: 0.3 % / 4 %; mode 8: 0 % / 1 % (additive within 2 %) |
| H4c: the gap is carried by the perturbation (tangent) dynamics rather than by the base orbit | hybrid monodromies (`exp4b`) | **Rejected as ill-posed.** The channels are strongly non-additive: 4-mode perturbations about the projected full orbit give F_c = 0.00794 (7× the gap); full perturbations about the 4-mode orbit do not destabilise up to F = 0.008 |

Interpretation, labelled as such and not separately tested:
- **Coupling route:** by the selection rule C[k,i,j] ≠ 0 only if k ± i ± j ≡ 0 (mod 18), mode 5 is forced directly
  by products of the most excited modes (2×3, 1×4), and mode 6 by 3×3 and 2×4.
- **Small but not negligible:** these slaved modes hold only 0.5 % of the orbit's linear energy and 3 % of the
  critical eigenvector's. They nevertheless enter the Krein-collision condition at second order, and must be
  included consistently in both the orbit and its linearisation.
- **Next test:** an explicit slaved-mode (normal-form) correction is the natural follow-up, but it was not built.

## Counterexamples, failed hypotheses and corrections

- **Baseline picture of two states is incomplete.** There are three attractors at F = 0.0045 (plus a saddle), and
  the high-amplitude orbit was not in the baseline.
- **Stage 1 "four modes cannot predict recurrence" is too strong.** The 4-mode model shows the same subcritical
  hysteresis; its loop is shifted by ~0.0004–0.0005. What it gets wrong is the location, not the mechanism.
- **H4c rejected** (see above).
- **Errors in my own work that were caught and corrected before results were accepted:**
  - *Exp 3, first run:* reference orbits were computed at RK4/800 but trajectories ran at RK4/200, so every
    locked outcome was mislabelled "other fixed point". The run was discarded and fixed (discretisation-consistent
    references).
  - *Exp 3 D1:* used an arbitrary eigenvector phase, which produced the anomalous F = 0.0044 point. It is superseded
    by Exp 3b.
  - *Exp 2, first run:* compared rotation numbers with opposite PCA orientations, which made the phase-locking bound
    vacuous. It was rerun with |ρ|.
  - *Exp 4b, first run:* crashed on a variant without a crossing. The verdict is now recorded explicitly.
  - *Tests:* four initially failing tests were test-design errors, not code errors:
    - RK4 is not conformally symplectic; the identity is checked with DOP853 plus RK4 convergence instead;
    - the Benettin initial-frame transient needed the slope estimator;
    - the synthetic circle fit used too few harmonics.

## Limitations

- **Single-parameter scope:** a single (N, α, η, Ω) point was studied, with continuation in F only. No claim is
  made for other N, η or Ω.
- **Classification limits:** the classification cannot exclude a phase-locked torus with period > 10⁶ drive
  periods, or a positive exponent below ~10⁻⁵ per time unit.
- **Lower edge of the loop:** the mechanism by which the torus disappears near F ≈ 0.00425 (saddle-node of tori or
  other) was not identified.
- **Basin geography:** the basin of the high-amplitude orbit was not mapped. Basin fractions depend on the
  predeclared sampling box and are not invariant measures.
- **Pairing rule:** the conformal-symplectic Lyapunov pairing rule is a known general result for constant viscous
  damping (U. Dressler, Phys. Rev. A 38, 1988 — cited from memory; verify). It is used here as a check, not
  claimed.
- **Toda reference:** the conservative Toda soliton benchmark is untouched and was not used for any driven/damped
  conclusion. Integrability of the unforced Toda chain says nothing about these attractors.

## Compute log (4-core container, ordinary CPU)

| Run | Wall time |
|:--|--:|
| Baseline rerun (Exp 0) | 35 s |
| Exp 1 | 290 s |
| Exp 2 (×2 runs) | 195 s + 218 s |
| Exp 3 (aborted + final) | ~120 s + 221 s |
| Exp 3b | 186 s |
| Exp 4 + 4b | 45 s |
| Exploration and tests | ~250 s |
| **Total** | **≈ 26 min**, within the 30-minute budget |

Seeds: 20261014 (Exp 3, 3b), 12345 (tests). Configurations, versions and per-stage timings are stored in every
results JSON.

## What a further budget would establish (not started)

1. **~5 min:** continue the unstable invariant circle directly. Use a Newton–Fourier invariant-circle solver, or
   bisection between basins along the boundary. This would confirm it connects the NS point to the lower edge of
   the loop via a fold of tori, which turns the subcritical inference into a direct computation.
2. **~2 min:** compute the first Lyapunov coefficient of the NS point analytically or numerically. That would give
   criticality without relying on dynamics.
3. **~10 min:** a predeclared held-out check of whether a 4-mode model plus consistently slaved modes 5–6 recovers
   F_c(8). Only worth doing if a reduced theory is the goal.
4. **No compute:** the literature review before any novelty statement.

Reproduction: see `REPRODUCE.md`.
