# FPUT attractor verification (research workspace)

Independent verification of the Stage 2 claim that a driven, damped α-FPUT chain (N=8, α=0.25, η=0.0025,
Ω=0.347, F≈0.0045) shows coexisting drive-locked and modulated states.

- **`REPORT.md`**: findings, verdicts and the **GO / HOLD** recommendation. Start here.
- **`REPRODUCE.md`**: how to rerun everything (`bash run_all.sh`).
- `baseline/`: the supplied Stage 1+2 package, verbatim (`SHA256SUMS`). Never modified.
- `fputv/`: new implementation, written independently of the baseline (physical coordinates; projected-force
  Galerkin truncation):
  - `model.py`: model;
  - `integrate.py`: RK4, DOP853, LSODA and Lyapunov integrators;
  - `floquet.py`: periodic orbits and Floquet analysis;
  - `diagnostics.py`: classification diagnostics;
  - `hybrid.py`: hybrid monodromies.
- `experiments/`: one script per experiment (Exp 0-4b) plus `make_figures.py`.
- `tests/`: 24 independent tests (`python -m pytest`).
- `results/`: raw JSON/NPZ outputs with configuration, seeds, versions and timings, plus run logs.
- `figures/`: figures generated only from `results/`.

This directory is not part of the `agentlib` package. The repository-level pytest configuration (`testpaths =
["tests"]`) does not collect it.
