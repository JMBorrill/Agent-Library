"""Experiment 5 (validation gate, Priority 1) - long-time integration to 30 000 drive periods.

F = 0.0045, full N = 8 chain in physical coordinates. Five initial conditions:
  zero        : rest
  L1e-3, L1e-2: locked orbit + 1e-3 / 1e-2 in the first normal-mode coordinate (baseline ICs)
  Ein, Eout   : locked orbit + 0.5 / 0.8 along d = Re(e^{i pi/2} v)/|.| (canonical critical
                eigenvector of Exp 3b, whose measured basin radius along d is 0.633)
Methods: DOP853 rtol 1e-10 and 1e-12 (atol = 1e-2 rtol) with the clock reset to t = 0 every 500
periods (exact drive phase at each restart; checked against absolute-time solves), and RK4 with
400 / 800 / 1600 steps per period.
Diagnostics at checkpoints n = 3500, 10000, 30000 (window: preceding 2048 periods):
  E1 range/mean, E2 range, |rho| (NAFF), invariant-circle fit residual, sup-distance to the
  locked fixed point OF THE SAME DISCRETE MAP (Newton with the same method), cross-method
  pointwise difference and phase lag along the attractor.
Attraction (not visual persistence):
  locked ICs  - fitted exponential decay rate of |y_n - y*| vs ln|mu_max| (Floquet);
  zero IC     - decay of the distance to the fitted invariant curve vs the transverse
                Lyapunov rate lambda_2 T = -(eta/2) T (Exp 2).
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("NUMBA_CACHE_DIR", str(ROOT / ".numba_cache"))
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))

import json  # noqa: E402
import time  # noqa: E402
from multiprocessing import Pool  # noqa: E402

import numpy as np  # noqa: E402

from fputv import diagnostics as D  # noqa: E402
from fputv.floquet import multipliers, newton_orbit  # noqa: E402
from fputv.integrate import scipy_strobe, scipy_strobe_segmented, strobe  # noqa: E402
from fputv.io import RESULTS, Timer, save, save_npz  # noqa: E402
from fputv.model import FPUT  # noqa: E402

F = 0.0045
PERIODS = 30000
CHECK = (3500, 10000, 30000)
WIN = 2048
METHODS = ["DOP853/1e-10", "DOP853/1e-12", "RK4/400", "RK4/800", "RK4/1600"]


def canonical(v):
    v = v / np.linalg.norm(v)
    a = -0.5 * np.angle(np.sum(v * v))
    w = np.exp(1j * a) * v
    return w if np.linalg.norm(w.real) >= np.linalg.norm(w.imag) else 1j * w


def fixed_point(method):
    s = FPUT(F)
    y, M, _ = newton_orbit(s, np.zeros(16), 800)
    if method.startswith("RK4"):
        y, M, info = newton_orbit(s, y, int(method.split("/")[1]))
    else:
        rt = float(method.split("/")[1])
        y, M, info = newton_orbit(s, y, method="DOP853", rtol=rt, atol=rt * 1e-2)
    return y, M


def initial_conditions():
    s = FPUT(F)
    y, M = fixed_point("DOP853/1e-12")
    w, V = np.linalg.eig(M)
    v = canonical(V[:, int(np.argmax(np.abs(w)))])
    d = np.real(1j * v); d /= np.linalg.norm(d)
    e1 = np.r_[s.B @ np.r_[1.0, np.zeros(7)], np.zeros(8)]
    return {"zero": np.zeros(16), "L1e-3": y + 1e-3 * e1, "L1e-2": y + 1e-2 * e1,
            "Ein": y + 0.5 * d, "Eout": y + 0.8 * d}


def run_one(job):
    label, y0, method = job
    s = FPUT(F)
    t0 = time.perf_counter()
    if method.startswith("RK4"):
        Y = strobe(s, y0, PERIODS, int(method.split("/")[1]))
        nfev = None
    else:
        rt = float(method.split("/")[1])
        Y, nfev = scipy_strobe_segmented(s, y0, PERIODS, rtol=rt, atol=rt * 1e-2, segment=500)
    return label, method, Y, nfev, time.perf_counter() - t0


def phase_check(y0):
    """Absolute-time single solve vs phase-reset segments (DOP853, rtol 1e-12)."""
    s = FPUT(F)
    out = {}
    for n in (3500, 10000):
        Ya, _ = scipy_strobe(s, y0, n, rtol=1e-12, atol=1e-14)
        Ys, _ = scipy_strobe_segmented(s, y0, n, rtol=1e-12, atol=1e-14, segment=500)
        Ea, Es = s.energies(Ya[-750:])[:, 0], s.energies(Ys[-750:])[:, 0]
        out[str(n)] = {"E1_range_abs_time": float(np.ptp(Ea)), "E1_range_segmented": float(np.ptp(Es)),
                       "final_pointwise_supdiff": float(np.max(np.abs(Ya[-1] - Ys[-1]))),
                       "drive_phase_arg_at_final_sample_abs_time_rad": float(s.Omega * n * s.T),
                       "drive_phase_mod_2pi_abs_time": float(np.mod(s.Omega * n * s.T + np.pi, 2 * np.pi) - np.pi)}
    return out


def window_diag(s, W, y_lock):
    E = s.energies(W)
    r = {"E1_range": float(np.ptp(E[:, 0])), "E1_mean": float(E[:, 0].mean()), "E2_range": float(np.ptp(E[:, 1])),
         "supdist_to_locked": float(np.max(np.abs(W[-1] - y_lock)))}
    if r["E1_range"] > 1e-2:
        P, _ = D.pca_plane(W)
        r["abs_rho"] = abs(D.refined_frequency(P[:, 0] + 1j * P[:, 1]))
        r["circle_fit_rel_residual_J40"] = D.invariant_circle_fit(W, (40,))["relative_rms_residual_by_harmonics"]["40"]
    return r


def curve_distance(Yref, Y, J=60):
    """Distance of states Y to the invariant curve fitted (Fourier in PCA angle) to Yref."""
    X0 = Yref.mean(0)
    _, _, Vt = np.linalg.svd(Yref - X0, full_matrices=False)
    ang = lambda Z: np.arctan2((Z - X0) @ Vt[1], (Z - X0) @ Vt[0])  # noqa: E731
    basis = lambda th: np.column_stack([np.ones_like(th)] + [f(j * th) for j in range(1, J + 1) for f in (np.cos, np.sin)])  # noqa: E731
    coef, *_ = np.linalg.lstsq(basis(ang(Yref)), Yref, rcond=None)
    return np.max(np.abs(Y - basis(ang(Y)) @ coef), axis=1)


def main():
    tm = Timer()
    ics = initial_conditions()
    locks = {m: fixed_point(m) for m in METHODS}
    mu = {m: float(abs(multipliers(locks[m][1])[0])) for m in METHODS}
    tm.mark("fixed_points")
    jobs = [(lab, y0, m) for m in METHODS for lab, y0 in ics.items()]
    jobs.sort(key=lambda j: 0 if j[2].startswith("DOP") else 1)  # long jobs first
    with Pool(4) as pool:
        res = pool.map(run_one, jobs, chunksize=1)
    tm.mark("integrations")
    traj = {(lab, m): Y for lab, m, Y, _, _ in res}
    meta = {f"{lab}|{m}": {"nfev": nf, "wall_s": round(w, 1)} for lab, m, _, nf, w in res}
    s = FPUT(F)

    diag = {}
    for (lab, m), Y in traj.items():
        y_lock = locks[m][0]
        diag[f"{lab}|{m}"] = {str(n): window_diag(s, Y[n - WIN:n], y_lock) for n in CHECK}
    # cross-method comparison against DOP853/1e-12 at each checkpoint
    cross = {}
    for lab in ics:
        ref = traj[(lab, "DOP853/1e-12")]
        for m in METHODS:
            if m == "DOP853/1e-12":
                continue
            Y = traj[(lab, m)]
            c = {}
            for n in CHECK:
                a, b = diag[f"{lab}|{m}"][str(n)], diag[f"{lab}|DOP853/1e-12"][str(n)]
                c[str(n)] = {"pointwise_supdiff": float(np.max(np.abs(Y[n - 1] - ref[n - 1]))),
                             "E1_range_diff": a["E1_range"] - b["E1_range"],
                             "E1_mean_diff": a["E1_mean"] - b["E1_mean"],
                             "abs_rho_diff": (a.get("abs_rho", 0) - b.get("abs_rho", 0)) if "abs_rho" in a else None}
                if "abs_rho" in a:
                    W = ref[n - WIN:n]
                    X0 = W.mean(0); _, _, Vt = np.linalg.svd(W - X0, full_matrices=False)
                    ph = lambda Z: np.arctan2((Z - X0) @ Vt[1], (Z - X0) @ Vt[0])  # noqa: E731
                    c[str(n)]["phase_lag_rad"] = float(np.angle(np.exp(1j * (ph(Y[n - 1:n]) - ph(ref[n - 1:n])))[0]))
                    c[str(n)]["distance_to_reference_curve"] = float(curve_distance(W, Y[n - 1:n])[0])
            cross[f"{lab}|{m}"] = c
    tm.mark("diagnostics")

    # attraction rates
    attraction = {}
    lnmu = {m: float(np.log(mu[m])) for m in METHODS}
    for (lab, m), Y in traj.items():
        dist = np.max(np.abs(Y - locks[m][0]), axis=1)
        key = f"{lab}|{m}"
        if dist[-1] < 1e-8:  # converged to the locked orbit: fit decay above round-off
            n = np.arange(1, PERIODS + 1)
            sel = (dist > 1e-11) & (dist < 1e-4)
            k = np.polyfit(n[sel], np.log(dist[sel]), 1)[0] if sel.sum() > 50 else None
            attraction[key] = {"outcome": "locked", "fit_rate_per_period": k, "floquet_ln_mu": lnmu[m],
                               "periods_to_1e-10": int(np.argmax(dist < 1e-10)) + 1 if (dist < 1e-10).any() else None,
                               "final_dist": float(dist[-1])}
        else:
            dc = curve_distance(Y[-8192:], Y)
            n = np.arange(1, PERIODS + 1)
            sel = (dc > 1e-6) & (dc < 1e-2) & (n < 5000)
            k = np.polyfit(n[sel], np.log(dc[sel]), 1)[0] if sel.sum() > 20 else None
            attraction[key] = {"outcome": "modulated", "fit_rate_per_period_to_curve": k,
                               "lambda2_T_from_exp2": -0.0025 / 2 * s.T,
                               "curve_distance_at_[1000,3500,10000,30000]": [float(dc[i - 1]) for i in (1000, 3500, 10000, 30000)],
                               "curve_distance_floor_last1000_median": float(np.median(dc[-1000:])),
                               "final_supdist_to_locked": float(dist[-1])}
    tm.mark("attraction")
    ph = phase_check(np.zeros(16))
    tm.mark("phase_check")

    save("exp5_long_time_validation",
         {"config": {"F": F, "periods": PERIODS, "checkpoints": CHECK, "window": WIN, "methods": METHODS,
                     "dop853_segment_periods": 500, "initial_conditions": {k: v for k, v in ics.items()}},
          "locked_fixed_points_max_abs_mu": mu, "run_meta": meta, "diagnostics": diag,
          "cross_method_vs_DOP853_1e-12": cross, "attraction": attraction, "drive_phase_check": ph}, tm)
    keep = {}
    for (lab, m), Y in traj.items():
        tag = f"{lab}__{m.replace('/', '_')}"
        keep[tag + "__E"] = s.energies(Y)[:, :4].astype(np.float32)
        if m in ("DOP853/1e-12", "RK4/1600"):
            keep[tag + "__Y_last4096"] = Y[-4096:]
            keep[tag + "__Y_checkpoints"] = Y[np.array(CHECK) - 1]
    keep["t_strobe_over_T"] = np.arange(1, PERIODS + 1)
    save_npz("exp5_trajectories", **keep)
    summary = {k: {n: (round(v[n]["E1_range"], 10), v[n].get("abs_rho"), "%.1e" % v[n]["supdist_to_locked"]) for n in v}
               for k, v in diag.items()}
    print(json.dumps(summary, indent=1))
    print(json.dumps(attraction, indent=1, default=str))
    print(json.dumps(ph, indent=1))


if __name__ == "__main__":
    main()
