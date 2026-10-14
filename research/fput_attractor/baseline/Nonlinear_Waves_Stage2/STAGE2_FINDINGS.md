# Nonlinear wave research — Stage 2 numerical findings

**Date:** 14 October 2026. **Status:** focused research gate **GO**; publication claim and full 8–12-week commitment **HOLD**.

## The exact problem we tested

For the fixed-end, uniformly forced, weakly damped α-FPUT chain described in Shi & Ren, *Physical Review E* **113**, 034221 (2026), DOI: 10.1103/mbbf-ll5l, use N=8, α=0.25, η=0.0025, Ω=0.347. Work in normal-mode coordinates. The full 8-mode system is an exact coordinate transform of the 8-site mechanical system; four modes is a Galerkin truncation, not an equally accurate representation.

At fixed drive amplitude F, solve for the phase-locked periodic orbit as a fixed point of the one-period stroboscopic map:

    P_F(y*) - y* = 0.

Integrate the exact variational equations alongside the orbit and determine the eigenvalues of its monodromy matrix M = dP_F/dy. A phase-locked orbit is linearly asymptotically stable when every Floquet multiplier has modulus strictly below 1.

## Numerical finding 1: reduced model shifts a local stability threshold

Along the phase-locked branch continued from zero forcing, a complex-conjugate pair of Floquet multipliers crosses the unit circle. Estimates from RK4 with 720 steps per drive period:

| Model | Drive F where largest Floquet modulus reaches 1 |
|:--|--:|
| Full eight-mode FPUT | **0.0046931590** |
| Four-mode Galerkin truncation | **0.0050846454** |

At that crossing the leading multipliers are, respectively, about `0.984914 ± 0.173044i` and `0.983327 ± 0.181847i`. This **suggests a Neimark–Sacker-type local loss of stability** but is not enough to prove the bifurcation type, super/subcritical nature or the creation of the observed recurrent attractor.

Convergence for F at the threshold:

| Model | RK4 180 | RK4 360 | RK4 720 |
|:--|--:|--:|--:|
| Eight modes | 0.0046933966 | 0.0046931717 | 0.0046931590 |
| Four modes | 0.0050848589 | 0.0050846575 | 0.0050846454 |

An independently implemented adaptive DOP853 integration of the variational map at the RK4/720 threshold gave largest multipliers 1.0000000143 (8 modes) and 1.0000000166 (4 modes); the map's root residual was under 1e-15. The 8-mode DOP853 root helper returned `success: false` on a very tight internal stopping criterion despite a ~7e-16 fixed-point residual. The above digits beyond ~1e-7 in drive amplitude are **not** a rigorous error bound.

The reduced model overestimates the full-model threshold by approximately 8.3% relative to the full-model F, evidence that a simple 4-mode truncation misplaces an important local stability boundary.

## Numerical finding 2: evidence for coexisting attractors

At **N=8, F=0.0045**, the drive-locked phase-locked orbit is linearly stable (largest Floquet multiplier approximately 0.99615). Nevertheless, zero initial displacement and velocity evolved over 3,500 driving periods into a trajectory retaining large long-period modal-energy modulation:

| Initial condition | Mode-1 energy range over last 750 driving periods |
|:--|--:|
| All zeros | 0.4295205853 |
| Locked orbit plus 0.001 in first coordinate | 5.1 × 10⁻⁹ |
| Locked orbit plus 0.01 in first coordinate | 5.1 × 10⁻⁸ |

Computed at 320 RK4 steps per drive period. Both perturbed locked states return close to the periodic orbit. The zero-start solution does not. This supports **initial-condition-dependent long-lived dynamics, consistent with coexistence of a stable drive-locked orbit and another attractor**. A rigorous classification of the modulated state (quasiperiodic torus, higher-period orbit, weak chaos, exceptionally long transient) remains outstanding. The data must not be reported as a proven novel physical phenomenon.

Independent solver check: on a 20-drive-period segment beginning late in the zero-start trajectory, DOP853 vs RK4/320 terminal phase-space error was about 1.1 × 10⁻⁵. Longer global independent integrations would improve confidence.

## Numerical finding 3: exact Toda single-soliton benchmark

For the unforced conservative infinite Toda chain in the potential/sign convention

    q̈_n = exp(q_(n-1)-q_n) - exp(q_n-q_(n+1)),

an exact travelling one-soliton solution was implemented using the softplus/sigmoid representation in `toda_benchmark.py`. The benchmark uses an interior N=120 grid whose boundary displacements are prescribed by the known **infinite-chain** solution, avoiding spurious reflected-boundary effects. With κ=0.4 and simulation t ∈ [0,45]:

- Pointwise residual of the exact solution in the Toda equations: **< 1e-14**.
- Max displacement/momentum error under independent DOP853 integration: **4.7 × 10⁻¹⁰**.
- DOP853 vs RK45 difference at final time: **7.1 × 10⁻⁸**.

This is a validated reference solver, **not a novel soliton discovery**. Perturbations of Toda/FPUT soliton scattering have been substantially studied (e.g. Bilman & Nenciu, *Physica D*, 2016).

## Reproduction

From the root of the unzipped package, Python 3.10+:

    pip install -r requirements.txt
    python -m unittest discover -s Nonlinear_Waves_Stage2 -p test_stage2.py -v
    python Nonlinear_Waves_Stage2/toda_benchmark.py
    python Nonlinear_Waves_Stage2/floquet.py
    python Nonlinear_Waves_Stage2/refine.py
    python Nonlinear_Waves_Stage2/basin_check.py
    python Nonlinear_Waves_Stage2/make_plots.py

The `refine.py` and `basin_check.py` scripts intentionally perform long numerical integrations. `floquet_detailed.json`, `floquet_scan.csv`, `floquet_refined.json`, `basin_check.json`, `solver_crosscheck.json`, `rest_initial_condition_test.json` and `toda_validation.json` contain the raw diagnostics.

**Tests executed:** 4/4 deterministic unit checks passed, including directional finite-difference verification of the monodromy, Liouville's formula, Floquet threshold ordering and the Toda exact-force residual.

## Immediate hypotheses to challenge

1. The Floquet instability of the drive-locked branch is *not* the sole boundary of long-lived modulation; the model may exhibit multistability and hysteresis.
2. A 4-mode truncation is insufficient to predict the loss of stability; sparse nonconsecutive modes or higher-order effective interactions may offer a better small model.
3. A minimal reduced theory could predict both the local fixed-point stability threshold and the basin structure in held-out {F, η, Ω, N} cases.

**Disconfirmation / next gate:** Independently rerun both attractors with adaptive integration; classify the stroboscopic modulation by frequency analysis and Lyapunov exponents; map hysteresis and basin boundaries near F=0.0045; verify candidate bifurcation (crossing transversality and nondegeneracy) before deriving any purported new law. Search older bifurcation studies of driven nonlinear lattices; novelty cannot be inferred from the 2026 source alone.

### Essential citations

- Y. Shi & H. Ren (2026), https://doi.org/10.1103/mbbf-ll5l and https://arxiv.org/html/2510.06568
- Guo Deng et al., *Phys. Rev. E*, accepted Oct. 2, 2026 (diatomic reduced-model recurrence): https://doi.org/10.1103/ctvj-t6s7
- G. Bilman & I. Nenciu (2016), *On the evolution of scattering data under perturbations of the Toda lattice*: https://www.sciencedirect.com/science/article/pii/S0167278916301439
- A. Hofstrand (2024), *Near-integrable dynamics of the Fermi-Pasta-Ulam-Tsingou problem*: https://doi.org/10.1103/PhysRevE.109.034204
- K. Geist & W. Lauterborn (1988), *The nonlinear dynamics of the damped and driven Toda chain. I. Energy bifurcation diagrams*, cited in Shi & Ren, bibliographic reference (confirm DOI independently).
