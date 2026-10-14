"""Result recording: every experiment writes JSON with configuration, versions, seeds, timings."""
from __future__ import annotations

import json
import platform
import subprocess
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"


def _git_commit():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True, timeout=10).stdout.strip()
    except Exception:  # pragma: no cover
        return None


def environment():
    import numba
    import scipy
    return {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
            "numba": numba.__version__, "platform": platform.platform(), "git_commit": _git_commit()}


def jsonable(x):
    if isinstance(x, dict):
        return {str(k): jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [jsonable(v) for v in x]
    if isinstance(x, np.ndarray):
        return jsonable(x.tolist())
    if isinstance(x, (np.floating,)):
        return float(x)
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.bool_,)):
        return bool(x)
    if isinstance(x, complex):
        return [x.real, x.imag]
    return x


class Timer:
    def __init__(self):
        self.t0 = time.perf_counter()
        self.marks = {}

    def mark(self, name):
        self.marks[name] = round(time.perf_counter() - self.t0, 3)
        return self.marks[name]


def save(name, payload, timer=None):
    RESULTS.mkdir(exist_ok=True)
    out = {"experiment": name, "environment": environment(), **payload}
    if timer is not None:
        out["wall_seconds"] = timer.marks | {"total": round(time.perf_counter() - timer.t0, 3)}
    path = RESULTS / f"{name}.json"
    path.write_text(json.dumps(jsonable(out), indent=1))
    return path


def save_npz(name, **arrays):
    RESULTS.mkdir(exist_ok=True)
    path = RESULTS / f"{name}.npz"
    np.savez_compressed(path, **arrays)
    return path
