"""Experiment 1 - independent reproduction of the drive-locked and modulated trajectories.

N=8, alpha=0.25, eta=0.0025, Omega=0.347, F=0.0045.
Integrators: RK4 (own, physical coordinates; 160-1280 steps/period), DOP853 (rtol 1e-10, 1e-12),
LSODA (rtol 1e-10, 1e-11) and the baseline's own modal RK4 code (cross-implementation check).
Observables (not pointwise states) are compared; pointwise divergence is decomposed into a
phase shift along the attractor versus a distance off the attractor.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("NUMBA_CACHE_DIR", str(ROOT / ".numba_cache"))
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))

import json  # noqa: E402

import numpy as np  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402

from fputv import diagnostics as D  # noqa: E402
from fputv.floquet import multipliers, newton_orbit  # noqa: E402
from fputv.integrate import scipy_strobe, strobe  # noqa: E402
from fputv.io import Timer, save, save_npz  # noqa: E402
from fputv.model import FPUT  # noqa: E402

PERIODS, WINDOW = 3500, 750


def observables(sys_, Y, y_lock):
    E = sys_.energies(Y)
    w = E[-WINDOW:]
    out = {"E1_range_last750": float(np.ptp(w[:, 0])), "E2_range_last750": float(np.ptp(w[:, 1])),
           "E1_mean_last750": float(w[:, 0].mean()), "E2_mean_last750": float(w[:, 1].mean()),
           "total_linear_energy_mean_last750": float(w.sum(1).mean()),
           "final_supdist_to_locked_orbit": float(np.max(np.abs(Y[-1] - y_lock)))}
    if out["E1_range_last750"] > 1e-2:
        P, _ = D.pca_plane(Y[-2048:])
        out["rotation_frequency_last2048"] = D.refined_frequency(P[:, 0] + 1j * P[:, 1])
    return out


def main():
    tm = Timer()
    s = FPUT(0.0045)
    # Drive-locked orbit: own Newton solver, converged in step size
    y = np.zeros(s.dim)
    lock = {}
    for n in (200, 400, 800, 1600):
        y, M, info = newton_orbit(s, y, n)
        mu = multipliers(M)
        lock[n] = {"y": y.copy(), "max_abs_mu": float(abs(mu[0])), "residual": info["residual"]}
    y_lock = lock[1600]["y"]
    yd, Md, infod = newton_orbit(s, y_lock, method="DOP853", rtol=1e-12, atol=1e-14)
    base = json.loads((ROOT / "baseline/Nonlinear_Waves_Stage2/floquet_detailed.json").read_text())
    Qb = np.array(base["8_0.0045"]["fixed_point"])
    yb = np.r_[s.B @ Qb[:8], s.B @ Qb[8:]]  # baseline modal fixed point -> physical coordinates
    locked_orbit = {
        "rk4": {str(n): {"max_abs_mu": v["max_abs_mu"], "residual": v["residual"],
                         "supdiff_to_rk4_1600": float(np.max(np.abs(v["y"] - y_lock)))} for n, v in lock.items()},
        "dop853": {"max_abs_mu": float(abs(multipliers(Md)[0])), "residual": infod["residual"],
                   "supdiff_to_rk4_1600": float(np.max(np.abs(yd - y_lock)))},
        "baseline_fixed_point_supdiff_to_rk4_1600": float(np.max(np.abs(yb - y_lock))),
        "baseline_reported_max_abs_mu": 0.996153725221742,
        "y_lock_physical": y_lock}
    tm.mark("locked_orbit")

    # Initial conditions exactly as in the baseline (perturbations in the first MODAL coordinate)
    pert = lambda eps: y_lock + np.r_[s.B @ np.r_[eps, np.zeros(7)], np.zeros(8)]  # noqa: E731
    ics = {"zero": np.zeros(16), "locked_plus_1e-3": pert(1e-3), "locked_plus_1e-2": pert(1e-2)}
    runs = {}
    traj = {}
    for label, y0 in ics.items():
        r = {}
        for n in (160, 320, 640, 1280):
            Y = strobe(s, y0, PERIODS, n)
            r[f"RK4/{n}"] = observables(s, Y, y_lock)
            traj[f"{label}|RK4/{n}"] = Y
        tm.mark(f"{label}_rk4")
        scipy_cfg = [("DOP853", 1e-10), ("DOP853", 1e-12), ("LSODA", 1e-10), ("LSODA", 1e-11)]
        if label == "locked_plus_1e-2":
            scipy_cfg = [("DOP853", 1e-11), ("LSODA", 1e-10)]
        for meth, rt in scipy_cfg:
            Y, nfev = scipy_strobe(s, y0, PERIODS, method=meth, rtol=rt, atol=rt * 1e-2)
            r[f"{meth}/rtol{rt:g}"] = observables(s, Y, y_lock) | {"nfev": nfev}
            traj[f"{label}|{meth}/rtol{rt:g}"] = Y
            tm.mark(f"{label}_{meth}_{rt:g}")
        runs[label] = r

    # Baseline implementation (modal coordinates, C-tensor) as a cross-implementation check
    sys.path.insert(0, str(ROOT / "baseline/Nonlinear_Waves_Stage1"))
    from stage1 import matrices, rk4 as base_rk4  # noqa: E402
    _, _, w, c, g = matrices(8)
    Zb = base_rk4(w, np.ascontiguousarray(c), g, .25, .0025, .0045, .347, PERIODS, 320)
    Yb = np.c_[Zb[:, :8] @ s.B.T, Zb[:, 8:] @ s.B.T]
    runs["zero"]["baseline_code_modal_RK4/320"] = observables(s, Yb, y_lock)
    tm.mark("baseline_code")

    # Pointwise vs on-attractor discrepancy for the modulated trajectory
    ref = traj["zero|RK4/1280"]
    tree = cKDTree(ref[-3000:])
    Pref, _ = D.pca_plane(ref[-3000:])
    X0 = ref[-3000:].mean(0)
    _, _, Vt = np.linalg.svd(ref[-3000:] - X0, full_matrices=False)
    phase = lambda Y: np.unwrap(np.arctan2((Y - X0) @ Vt[1], (Y - X0) @ Vt[0]))  # noqa: E731
    pointwise = {}
    for key, Y in traj.items():
        if not key.startswith("zero|") or key == "zero|RK4/1280":
            continue
        dist_on, _ = tree.query(Y[-750:])
        dphi = phase(Y[-750:]) - phase(ref[-750:])
        pointwise[key.split("|")[1]] = {
            "final_pointwise_supdiff_vs_RK4_1280": float(np.max(np.abs(Y[-1] - ref[-1]))),
            "max_distance_to_reference_attractor_last750": float(dist_on.max()),
            "phase_lag_along_attractor_rad_final": float(dphi[-1])}
    # reference attractor sampling density: typical spacing between consecutive stored samples
    spacing = float(np.median(cKDTree(ref[-3000:-750]).query(ref[-750:])[0]))
    tm.mark("pointwise")

    # Convergence summary: RK4 observable error estimates (Richardson, order 4)
    conv = {}
    for label in ics:
        for q in ("E1_range_last750", "E1_mean_last750"):
            v = [runs[label][f"RK4/{n}"][q] for n in (160, 320, 640, 1280)]
            conv[f"{label}|{q}"] = {"values": v, "successive_diffs": list(np.abs(np.diff(v))),
                                    "richardson_error_estimate_1280": abs(v[3] - v[2]) / 15}
    payload = {"config": {"N": 8, "alpha": .25, "eta": .0025, "Omega": .347, "F": .0045, "periods": PERIODS,
                          "window": WINDOW, "initial_conditions": "zero; y_lock + eps*e(Q1) as in baseline"},
               "locked_orbit": locked_orbit, "runs": runs, "rk4_convergence": conv,
               "modulated_pointwise_vs_on_attractor": pointwise,
               "reference_attractor_sample_spacing": spacing,
               "baseline_reported": {"zero_E1_range": 0.4295205852840628,
                                     "locked_plus_1e-3_E1_range": 5.107568867845913e-09,
                                     "locked_plus_1e-2_E1_range": 5.105865218124617e-08}}
    save("exp1_reproduction", payload, tm)
    save_npz("exp1_trajectories_E", **{k.replace("|", "__").replace("/", "_"): s.energies(v)[:, :4]
                                       for k, v in traj.items()})
    print(json.dumps({k: {kk: vv.get("E1_range_last750") for kk, vv in v.items()} for k, v in runs.items()},
                     indent=1))
    print(json.dumps(pointwise, indent=1))


if __name__ == "__main__":
    main()
