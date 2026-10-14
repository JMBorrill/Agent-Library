# Stage 1 — FPUT recurrence and reduced-order wave dynamics

**Status (2026-10-14):** Baseline reproduced, first mechanistic hypothesis generated, no originality claim. **Gate: continue focused screening, not the entire 8–12-week programme.**

## The question

Can a compact, physically derived reduced model predict the boundary and modulation frequency of long-lived multimode energy exchange in a periodically forced, weakly damped alpha-FPUT chain? Can mode-coupling structure explain when naive reductions fail?

This is *not* a conservative FPUT recurrence experiment and *not* proof of integrability; the driven-damped system has non-Hamiltonian attractors. The Toda and KdV soliton work is a distinct **conservative-system reference**, not an integrable benchmark once forcing and damping are applied.

## Published baseline

Y. Shi and H. Ren, *Recurrence in a periodically driven and weakly damped Fermi-Pasta-Ulam-Tsingou chain*, Phys. Rev. E **113**, 034221 (26 March 2026), DOI: `10.1103/mbbf-ll5l`. Open manuscript: https://arxiv.org/html/2510.06568.

Parameters used here match their representative case: `N=8`, `alpha=0.25`, damping `eta=0.0025`, uniform forcing amplitude `F=0.005`, frequency `Omega=0.347`, fixed boundaries and zero initial conditions. Integrate 2,500 drive periods; assess last 500 drive-period stroboscopic samples. The paper reports long-time coherent modulation with a characteristic approximate 41.3 forcing-period timescale. **Our discrete modal energy spectrum can contain a ~20.8-period harmonic; these are not automatically the same observable and must not be conflated.**

## Physics and mathematical reduction

The N-particle equations are

```
q̈_n = (q_(n+1) - 2q_n + q_(n-1))
       + alpha[(q_(n+1)-q_n)^2 - (q_n-q_(n-1))^2]
       - eta*q̇_n + F*cos(Omega*t)
q_0 = q_(N+1) = 0
```

Use normal coordinates `q_n = Σ_k phi[n,k] Q_k` with `phi[n,k] = sqrt(2/(N+1)) sin(pi*n*k/(N+1))`. The exact full-order modal equations are

```
Q̈_k + eta Q̇_k + omega_k² Q_k + alpha Σ_i Σ_j C[k,i,j] Q_i Q_j
    = F*g[k] cos(Omega*t)

C[k,i,j] = Σ_{bond b} D[b,k]*D[b,i]*D[b,j]
D[b,k] = phi[b+1,k]-phi[b,k]   (zero-padded boundaries)
g[k] = Σ_n phi[n,k]
omega_k = 2 sin(k*pi/(2*(N+1)))
```

A *Galerkin truncation* keeps only chosen normal coordinates, dropping interactions with absent coordinates; no coefficients are fitted. This changes the dynamical system and does **not** guarantee identical attractors. The full `m=8` modal representation is algebraically equivalent to the original physical-coordinate system, which is checked in the code at a nontrivial random state.

## Results (RK4 with 160 steps per driving period)

At the baseline `F=0.005`, last 500 stroboscopic mode-1 energy ranges:

| Kept modes | E1 range | E2 range | Interpretation |
|---|---:|---:|---|
| 1,2 | `4.56e-10` | `1.84e-9` | Stroboscopically drive-locked response, not multimode long-period exchange |
| 1,2,3 | `3.32e-10` | `1.21e-9` | Similarly locked |
| 1,2,3,4 | `0.6833` | `1.1848` | Strong long-period modulation but not quantitatively identical to full system |
| 1–8 | `0.4851` | `0.9537` | Strong long-period modulation, consistent with published case |

`RK4/320` steps gave corresponding ranges of `0.68335/1.18502` (4 modes) and `0.48505/0.95370` (8 modes). A conservative nonzero-energy FPUT simulation in DOP853 had max relative energy spread `1.48e-12`. An **independent physical-coordinate** DOP853 integration checked a shorter 60-period forced trajectory, agreeing with RK4/320 within `2.29e-5` max coordinate/momentum absolute error at the final time. This does **not** certify the long-time attractor to the same error; stronger checks remain due.

### Crucial falsification

The four-mode truncation *does not reliably predict the existence region*. At `F=0.0045`, the eight-mode chain still displayed stroboscopic modulation (mode-1 E range `0.4295`), whereas the four-mode chain showed a drive-locked response (range `2.59e-10`). At `F=0.0055`, both displayed modulation. Thus **“retain the first four modes and predict recurrence” fails**. This negative result motivates an actual mechanistic investigation instead of describing a superficial successful fit as discovery.

An *exploratory/in-sample* mode-subset search found that `(1,2,4,6)` also yields modulated behaviour at `F=0.005`, whereas `(1,2,3,5)` does not. These are not controlled held-out tests, and the exact mode-set dependence must be assessed across other parameters and initial states. It may be a truncation artefact. The search does not prove a minimal number of modes.

## Run on normal hardware

Install Python 3.10+ and `numpy`, `scipy`, `numba`, `matplotlib`. No API services required.

```bash
python stage1.py --periods 2500 --steps 160 --window 500 --output results
python stage1.py --periods 2500 --steps 320 --window 500 --output results_highres
python dop_check.py        # 60-drive-period independent physical-coordinate check
python subset_scan.py      # exploratory mode sets at paper parameters
python amplitude_scan.py   # nearby F=0.0045, 0.005, 0.0055
```

The first executable runs algebraic-equivalence, mode orthogonality and conservative-energy tests, then computes the reference comparison. The separate DOP853 test is only short-time. `--full-dop` exists for a much longer independent solver run and may take considerable CPU time.

## Interpretation and novelty hazards

- The 2026 authors explicitly distinguish their modulated attractor from Hamiltonian FPUT recurrence and say constructing perturbative analytical approximations within recurrence regions is an open theoretical challenge.
- Reduced two-mode and higher-mode FPUT models and resonant normal forms are longstanding techniques. A 2024 article explicitly built a **two-mode model** for disordered conservative FPUT; a paper accepted on 2 October 2026 built a reduced model for **diatomic** FPUT recurrence. No new theorem or physics has been established here.
- In classic weakly nonlinear, long-wavelength conservative systems, FPUT/soliton relationships have been described via Toda and the KdV hierarchy (Gallone, Ponno & Rink, J. Phys. A 54, 305701, 2021). The driven-damped eight-particle case is not within those assumptions.
- Simply observing modulation in a Galerkin truncation is not evidence of novelty; numerical stability, bifurcations, parameter sensitivity, multiple basins and literature precedence must be checked.
- `periodogram` uses a finite, 500-point stroboscopic window; dominant harmonic estimates are not precise fundamental periods, bifurcation classifications or Lyapunov exponents.

## First decision gate (before any 8–12-week commitment)

1. **Confirm** the long-time driven-damped attractors using longer independent runs, interval comparisons, shifted initial states, and a stable diagnostic distinguishing phase-locked periodic, quasiperiodic and chaotic motion.
2. **Determine** periodic forced solutions (stroboscopic map fixed points), compute Floquet multipliers, and follow their loss of stability as amplitude or damping changes. Classify the bifurcation only if numerics support it.
3. **Derive and challenge** an averaging/normal-form model with explicit, unfitted coefficients. Pre-register a small holdout grid of F, eta, Omega, N before fitting or selecting a reduced closure. Beat simple 2-,3-,4-mode Galerkin models on those cases.
4. **Separate soliton track:** in a conservative Toda chain reproduce an exact solitary-wave solution and collision; perturb the potential towards FPUT, quantify radiation with grid/time-step/size convergence, and check the published perturbed Toda scattering literature before an originality claim.
5. **Stop** if neither track produces a genuinely unaddressed testable mathematical question or a demonstrable predictive improvement.

## Source notes for independent literature check

- Shi & Ren 2026: https://doi.org/10.1103/mbbf-ll5l
- Deng, Pezzi, Lin & Onorato, accepted 2 Oct 2026, diatomic FPUT reduced dynamics: https://doi.org/10.1103/ctvj-t6s7
- Gallone, Ponno & Rink 2021, KdV/FPUT asymptotic integrability: https://doi.org/10.1088/1751-8121/ac0a2e
- McGinnis & Wright 2024, random FPUT KdV approximation: https://doi.org/10.1016/j.physd.2024.134154
- Campos, Mohammadi & Romanczukiewicz 2026, QNM-mediated kink resonances: https://doi.org/10.1140/epjc/s10052-026-15330-x
- 2016 work on perturbed Toda scattering: https://www.sciencedirect.com/science/article/pii/S0167278916301439

**Bottom line: GO for the small Stage 1 theoretical-screening gate; HOLD on claiming novelty, a complete reproduction, or committing months.**
