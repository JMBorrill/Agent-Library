# Reproduction instructions

Requirements: Python ≥ 3.10 and the packages in `requirements.txt` (numpy, scipy, numba, matplotlib, pytest).
There are no API calls, no network access and no GPU. Tested with Python 3.13.16, numpy 2.5.4, scipy 1.18.1,
numba 0.68.0 and matplotlib 3.11.2 on 4 CPU cores.

```sh
cd research/fput_attractor
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python -m pytest            # 24 independent tests, ~1-2 min (first run includes numba compilation)
bash run_all.sh --quick     # tests + baseline rerun + Floquet verification, ~3 min
bash run_all.sh             # everything, ~25 min; rewrites results/*.json|npz and figures/*.png
```

| Script | Produces | Wall time |
|:--|:--|--:|
| `experiments/exp0_baseline_rerun.py` | `results/exp0_baseline_rerun.json`: SHA-256 integrity, baseline tests/scripts rerun in a temp copy, numeric diff | 40 s |
| `experiments/exp1_reproduction.py` | `results/exp1_reproduction.json`, `exp1_trajectories_E.npz` | 5 min |
| `experiments/exp2_classify.py` | `results/exp2_classification.json`, `exp2_*.npz` | 4 min |
| `experiments/exp3_multistability.py` | `results/exp3_multistability.json`, `exp3_basin_ics.npz` | 4 min |
| `experiments/exp3b_subcritical_scaling.py` | `results/exp3b_subcritical_scaling.json` (needs Exp 3 output) | 3 min |
| `experiments/exp4_floquet_reduced.py` | `results/exp4_floquet_reduced.json` | 30 s |
| `experiments/exp4b_mechanism_decomposition.py` | `results/exp4b_mechanism_decomposition.json` | 15 s |
| `experiments/make_figures.py` | `figures/fig1..fig6*.png` from the result files only | 10 s |

`results/*.log` are the console logs of the runs used in `REPORT.md`.

**Determinism.** Fixed-step RK4 runs and all Newton/brentq results are deterministic. Random initial conditions use
`numpy.random.default_rng(20261014)` (Exp 3/3b). Numba's `parallel=True` batch integrator gives results identical
to the serial integrator (tested). Adaptive scipy results can differ in the last digits across library versions.

**Baseline.** `baseline/` is the supplied package, unmodified. Do not run its scripts in place, because they
overwrite their own result files. `exp0_baseline_rerun.py` runs them in a temporary copy. To check integrity:
`cd baseline && sha256sum -c SHA256SUMS`.

**Quick spot checks for a reviewer** (each under 1 min):
- `python -m pytest -k critical_F` reproduces the full-chain Floquet threshold from scratch.
- `python -m pytest -k conformally` checks the structure behind the Krein-collision mechanism.
- In `results/exp3_multistability.json`, look at `results.full.C_hysteresis` for the up/down hysteresis branches.
