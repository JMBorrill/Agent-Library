# FPUT attractor verification (research workspace)

Independent verification of the Stage 2 claim that a driven, damped α-FPUT chain (N=8, α=0.25, η=0.0025,
Ω=0.347, F≈0.0045) shows coexisting drive-locked and modulated states.

- **`REPORT_GATE.md`**: validation-gate findings after the adversarial review (answers Q1-Q5; decision **HOLD**). Start here.
- `REPORT.md`: earlier verification (Exp 0-4), partly superseded.
- `inputs/`: the adversarial review PDF that defined the gate.
- **`REPRODUCE.md`**: how to rerun everything (`bash run_all.sh`).
- `baseline/`: the supplied Stage 1+2 package, verbatim (`SHA256SUMS`). Never modified.
- `fputv/`: new implementation, written independently of the baseline (physical coordinates; projected-force
  Galerkin truncation):
  - `model.py`: model;
  - `integrate.py`: RK4, DOP853, LSODA and Lyapunov integrators;
  - `floquet.py`: periodic orbits and Floquet analysis;
  - `diagnostics.py`: classification diagnostics;
  - `hybrid.py`: hybrid monodromies;
  - `normal_form.py`: Neimark-Sacker coefficient via higher-order variational equations;
  - `edge.py`: edge tracking;
  - `tensor_model.py`: normal-mode model with coupling knockouts.
- `experiments/`: one script per experiment (Exp 0-9) plus `make_figures.py` and `make_figures_gate.py`.
- `tests/`: 35 independent tests (`python -m pytest`).
- `results/`: raw JSON/NPZ outputs with configuration, seeds, versions and timings, plus run logs.
- `figures/`: figures generated only from `results/`.

This directory is not part of the `agentlib` package. The repository-level pytest configuration (`testpaths =
["tests"]`) does not collect it.
