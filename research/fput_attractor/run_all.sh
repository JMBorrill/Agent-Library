#!/usr/bin/env bash
# Reproduce every result in results/ and every figure in figures/ (about 25 min on 4 cores).
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
