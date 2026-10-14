"""Experiment 0 - rerun the baseline package unchanged in a temporary copy and compare numerically.

The baseline scripts write their outputs next to themselves, so they are never run in place:
baseline/ stays byte-identical to the supplied package (checked against baseline/SHA256SUMS).
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fputv.io import Timer, save  # noqa: E402

BASE = ROOT / "baseline"
FILES = ["floquet_scan.csv", "floquet_detailed.json", "floquet_refined.json", "rest_initial_condition_test.json",
         "basin_check.json", "solver_crosscheck.json", "toda_validation.json"]


def numbers(path):
    txt = path.read_text()
    if path.suffix == ".csv":
        import csv
        rows = list(csv.DictReader(txt.splitlines()))
        out = []
        for r in rows:
            for v in r.values():
                try:
                    out.append(float(v))
                except ValueError:
                    pass
        return out
    out = []

    def walk(x):
        if isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
        elif isinstance(x, (int, float)) and not isinstance(x, bool):
            out.append(float(x))
    walk(json.loads(txt))
    return out


def main():
    tm = Timer()
    checks = {}
    for line in (BASE / "SHA256SUMS").read_text().splitlines():
        h, f = line.split(maxsplit=1)
        checks[f] = hashlib.sha256((BASE / f).read_bytes()).hexdigest() == h
    integrity = {"files": len(checks), "all_match": all(checks.values())}
    tmp = Path(tempfile.mkdtemp(prefix="baseline_rerun_"))
    shutil.copytree(BASE, tmp / "pkg")
    s2 = tmp / "pkg/Nonlinear_Waves_Stage2"
    env = dict(os.environ, NUMBA_CACHE_DIR=str(tmp / "numba"))
    runs = {}
    cmds = [("unittest", [sys.executable, "-m", "unittest", "discover", "-s", "Nonlinear_Waves_Stage2", "-p", "test_stage2.py"], tmp / "pkg"),
            ("toda_benchmark", [sys.executable, "toda_benchmark.py"], s2),
            ("floquet", [sys.executable, "floquet.py"], s2),
            ("refine", [sys.executable, "refine.py"], s2),
            ("basin_check", [sys.executable, "basin_check.py"], s2)]
    for name, cmd, cwd in cmds:
        t0 = time.perf_counter()
        p = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
        runs[name] = {"returncode": p.returncode, "wall_seconds": round(time.perf_counter() - t0, 2),
                      "tail": (p.stdout + p.stderr).strip().splitlines()[-3:]}
        tm.mark(name)
    comp = {}
    for f in FILES:
        a, b = numbers(BASE / "Nonlinear_Waves_Stage2" / f), numbers(s2 / f)
        if len(a) != len(b):
            comp[f] = {"same_length": False}
            continue
        a, b = map(lambda x: __import__("numpy").array(x), (a, b))
        rel = abs(a - b) / __import__("numpy").maximum(1e-300, abs(a))
        comp[f] = {"n_values": len(a), "max_abs_diff": float(abs(a - b).max()) if len(a) else 0.0,
                   "max_rel_diff_values_gt_1e-6": float(rel[abs(a) > 1e-6].max()) if (abs(a) > 1e-6).any() else 0.0,
                   "byte_identical": (BASE / "Nonlinear_Waves_Stage2" / f).read_bytes() == (s2 / f).read_bytes()}
    shutil.rmtree(tmp, ignore_errors=True)
    save("exp0_baseline_rerun", {"baseline_integrity_sha256": integrity, "runs": runs, "output_comparison": comp}, tm)
    print(json.dumps({"integrity": integrity, "runs": {k: (v["returncode"], v["wall_seconds"]) for k, v in runs.items()},
                      "comparison": comp}, indent=1))


if __name__ == "__main__":
    main()
