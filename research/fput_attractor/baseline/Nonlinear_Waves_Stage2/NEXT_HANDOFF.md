# Next-task briefs (keep implementation and review independent)

## Give this to Codex **or** Claude Code, not both simultaneously

Use the attached Stage 2 package as the initial repository. **Do not start from scratch or overwrite the baseline.** Investigate the apparent coexistence of a stable drive-locked solution and a modulated state in N=8, α=0.25, η=0.0025, Ω=0.347, near F=0.0045.

Deliver working, tested code and raw data that:

1. Independently reproduces both outcomes with two different integrators, comparing convergence as step size and tolerances change.
2. Classifies long-time stroboscopic modulation (periodic, quasiperiodic, chaotic, or unresolved) using frequency analysis, Poincaré sections and a carefully converged Lyapunov exponent test.
3. Measures a small, predeclared initial-condition basin sample and upward/downward F continuation around 0.0043–0.0053 to test hysteresis and coexistence. Report computational cost and seed/configuration.
4. Compares the full 8-mode and 4-mode results on exactly the same parameters, clearly separating local phase-locked Floquet instability from globally accessible recurrence.
5. Delivers a reproducible report, raw results, passing tests and explicit counterevidence. If the claims fail under rechecking, say so and stop.

**Constraints:** ordinary hardware, no paid API calls, no uncontrolled parameter sweeps, no claim of novelty, no external plotting of results without underlying files. Keep the conservative Toda soliton reference untouched; do not conflate its exact integrability with driven/damped dynamics. No publication drafting yet.

**Completion gate:** an independent reviewer can rerun a compact command and verify at least one robust physical conclusion about the coexistence/bifurcation mechanism; otherwise HOLD.

## Give this to ChatGPT Work

Perform an adversarial, independently sourced literature review **through 14 October 2026** on periodically forced and damped α-FPUT lattices, Floquet/Neimark–Sacker bifurcations, coexistence/hysteresis of periodic and quasiperiodic attractors, and perturbed Toda soliton scattering. Start with Shi & Ren (2026), Geist & Lauterborn (1988), Khomeriki–Lepri–Ruffo (2001), Hofstrand (2024), Bilman–Nenciu (2016), Deng et al. (accepted 2 Oct 2026). Identify exactly whether the coexistence and shifted Galerkin Floquet boundary in the attached Stage 2 report are already known. Return a paper-by-paper claim/evidence matrix with primary-source URLs/DOIs, mathematical models/parameter regimes, precise unresolved questions and a GO/HOLD/STOP verdict. Do not assume a missing keyword search establishes novelty. Do not generate code or a long generic research plan.
