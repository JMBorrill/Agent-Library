#!/usr/bin/env bash
# Reproduce every result in results/ and every figure in figures/ (about 70 min wall on 4 cores).
# Usage: bash run_all.sh            (full)
#        bash run_all.sh --quick    (tests + baseline rerun + Floquet verification only, ~3 min)
set -euo pipefail
cd "$(dirname "$0")"
export NUMBA_CACHE_DIR="$PWD/.numba_cache"
PY="${PYTHON:-python}"
"$PY" -m pytest -q
"$PY" experiments/exp0_baseline_rerun.py
"$PY" experiments/exp4_floquet_reduced.py
"$PY" experiments/exp4b_mechanism_decomposition.py
if [[ "${1:-}" == "--quick" ]]; then exit 0; fi
"$PY" experiments/exp1_reproduction.py
"$PY" experiments/exp2_classify.py
"$PY" experiments/exp3_multistability.py
"$PY" experiments/exp3b_subcritical_scaling.py   # reads results/exp3_multistability.json
"$PY" experiments/make_figures.py
# validation gate (after the adversarial review), ~45 min wall on 4 cores
"$PY" experiments/exp5_long_time_validation.py
"$PY" experiments/exp6_classification_convergence.py
"$PY" experiments/exp7_ns_normal_form.py          # reads results/exp3b_subcritical_scaling.json
"$PY" experiments/exp8_edge_and_fold.py           # reads results/exp3_multistability.json
"$PY" experiments/exp8b_fold_scaling.py           # reads results/exp8_edge_histories.npz
"$PY" experiments/exp8c_fold_analysis.py
"$PY" experiments/exp9_modal_knockouts.py
"$PY" experiments/make_figures_gate.py
