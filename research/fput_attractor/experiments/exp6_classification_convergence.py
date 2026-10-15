"""Experiment 6 (Priority 2) - convergence of the classification of the modulated state, F = 0.0045.

1. Lyapunov spectrum (top 4 map exponents) to 1e5 drive periods with RK4/200 and RK4/400:
   second-half slope, 10 block slopes (mean, standard error), running estimates at 1e3..1e5, and
   the bound |lambda_1| <= max_n |log-stretch_1(n)| / t (bounded log-stretch <=> zero exponent).
2. Independent integrator: top-2 exponents with DOP853 variational equations (rtol 1e-10),
   QR every period, 3000 periods.
3. Neutral Lyapunov vector versus the tangent of the invariant curve (angle).
4. Rotation number: NAFF on windows 2^10..2^15 (RK4/800) -> convergence with window length.
5. Locking test: rho(F) at F = 0.0045 + {0, +-1e-6, +-3e-6, +-1e-5}. On an Arnold-tongue plateau rho
   would be constant; quasiperiodic motion gives a strictly monotone rho(F).
6. Circle-map return structure: theta_{n+1} - theta_n as a function of theta_n (Fourier fit
   residual; single-valued?), and the minimum derivative of the lift (homeomorphism if > 0).
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("NUMBA_CACHE_DIR", str(ROOT / ".numba_cache"))
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))

import json  # noqa: E402
from multiprocessing import Pool  # noqa: E402

import numpy as np  # noqa: E402
from scipy.integrate import solve_ivp  # noqa: E402

from fputv import diagnostics as D  # noqa: E402
from fputv.integrate import lyapunov_qr, rk4_flow_tangent, strobe  # noqa: E402
from fputv.io import Timer, save  # noqa: E402
from fputv.model import FPUT, rhs_tangent  # noqa: E402

F = 0.0045
LONG = 100000


def torus_state(F=F, steps=400):
    s = FPUT(F)
    return strobe(s, np.zeros(16), 6000, steps)[-1]


def lyap_long(steps):
    s = FPUT(F)
    y0 = torus_state()
    _, cum = lyapunov_qr(y0, LONG, steps, 4, *s.args)
    T = s.T
    h = LONG // 2
    lam = (cum[-1] - cum[h - 1]) / ((LONG - h) * T)
    blocks = np.array([(cum[(k + 1) * 10000 - 1] - (cum[k * 10000 - 1] if k else 0)) / (10000 * T) for k in range(10)])
    run = {str(n): (cum[n - 1] / (n * T)).tolist() for n in (1000, 3000, 10000, 30000, 100000)}
    t = np.arange(1, LONG + 1) * T
    return {"steps": steps, "second_half_slope": lam.tolist(),
            "block_mean": blocks[2:].mean(0).tolist(), "block_sem": (blocks[2:].std(0, ddof=1) / np.sqrt(8)).tolist(),
            "blocks_lambda1": blocks[:, 0].tolist(), "cumulative_average": run,
            "max_abs_logstretch1_after_1000": float(np.max(np.abs(cum[1000:, 0]))),
            "bound_abs_lambda1_from_bounded_stretch": float(np.max(np.abs(cum[LONG // 2:, 0] - cum[LONG // 2, 0])) / (t[-1] - t[LONG // 2])),
            "logstretch1_samples": cum[::1000, 0].tolist()}


def lyap_dop853(periods=3000, nvec=2):
    s = FPUT(F)
    y = torus_state()
    d = s.dim
    oy = np.empty(d); oW = np.empty((d, nvec))
    args = s.args

    def f(t, z):
        rhs_tangent(t, z[:d], z[d:].reshape(d, nvec), *args, oy, oW)
        return np.concatenate((oy, oW.ravel()))

    W = np.eye(d)[:, :nvec]
    acc = np.zeros(nvec)
    hist = []
    for n in range(periods):
        sol = solve_ivp(f, (0, s.T), np.concatenate((y, W.ravel())), method="DOP853", rtol=1e-10, atol=1e-12)
        z = sol.y[:, -1]
        y = z[:d]
        Q, R = np.linalg.qr(z[d:].reshape(d, nvec))
        acc += np.log(np.abs(np.diag(R)))
        W = Q * np.sign(np.diag(R))
        hist.append(acc.copy())
    hist = np.array(hist)
    h = periods // 2
    return {"periods": periods, "second_half_slope": ((hist[-1] - hist[h - 1]) / ((periods - h) * s.T)).tolist(),
            "cumulative_average": (hist[-1] / (periods * s.T)).tolist()}


def neutral_vector_alignment():
    s = FPUT(F)
    y = torus_state(steps=400)
    W = np.eye(16)[:, :1]
    for _ in range(4000):
        y, W = rk4_flow_tangent(y, W, 0.0, s.T, 400, *s.args)
        W = W / np.linalg.norm(W)
    Y = strobe(s, y, 8192, 400)
    # tangent of the fitted invariant curve at the final point y (= state before the 8192 samples)
    X0 = Y.mean(0)
    _, _, Vt = np.linalg.svd(Y - X0, full_matrices=False)
    th = np.arctan2((Y - X0) @ Vt[1], (Y - X0) @ Vt[0])
    J = 60
    A = np.column_stack([np.ones_like(th)] + [g(j * th) for j in range(1, J + 1) for g in (np.cos, np.sin)])
    coef, *_ = np.linalg.lstsq(A, Y, rcond=None)
    t0 = np.arctan2((y - X0) @ Vt[1], (y - X0) @ Vt[0])
    dA = np.concatenate([[0.0]] + [[-j * np.sin(j * t0), j * np.cos(j * t0)] for j in range(1, J + 1)])
    tang = dA @ coef
    c = abs(W[:, 0] @ tang) / np.linalg.norm(tang)
    return {"abs_cos_angle_lyapunov_vector_vs_curve_tangent": float(c), "angle_rad": float(np.arccos(min(1.0, c)))}


def rho_windows():
    s = FPUT(F)
    Y = strobe(s, torus_state(steps=800), 2 ** 15, 800)
    out = {}
    for k in range(10, 16):
        W = Y[-2 ** k:]
        P, _ = D.pca_plane(W)
        out[str(2 ** k)] = abs(D.refined_frequency(P[:, 0] + 1j * P[:, 1]))
    ref = out[str(2 ** 15)]
    # circle-map return structure from the last 2^14 samples
    W = Y[-2 ** 14:]
    X0 = W.mean(0)
    _, _, Vt = np.linalg.svd(W - X0, full_matrices=False)
    th = np.unwrap(np.arctan2((W - X0) @ Vt[1], (W - X0) @ Vt[0]))
    sgn = np.sign(np.mean(np.diff(th)))
    th = sgn * th
    inc = np.diff(th)
    th0 = np.mod(th[:-1], 2 * np.pi)
    J = 30
    A = np.column_stack([np.ones_like(th0)] + [g(j * th0) for j in range(1, J + 1) for g in (np.cos, np.sin)])
    coef, *_ = np.linalg.lstsq(A, inc, rcond=None)
    res = inc - A @ coef
    grid = np.linspace(0, 2 * np.pi, 4001)
    dA = np.column_stack([np.zeros_like(grid)] + [g(j * grid) for j in range(1, J + 1)
                                                   for g in (lambda x, j=j: -j * np.sin(x), lambda x, j=j: j * np.cos(x))])
    lift_deriv = 1 + dA @ coef
    return {"abs_rho_by_window": out, "abs_diff_from_2^15": {k: abs(v - ref) for k, v in out.items()},
            "circle_map": {"increment_mean_over_2pi": float(inc.mean() / (2 * np.pi)),
                           "increment_range_rad": [float(inc.min()), float(inc.max())],
                           "fourier_fit_rms_residual_rad": float(np.sqrt(np.mean(res ** 2))),
                           "min_lift_derivative": float(lift_deriv.min()), "max_lift_derivative": float(lift_deriv.max())}}


def rho_at(dF):
    s = FPUT(F + dF)
    Y = strobe(s, torus_state(steps=800), 3000 + 2 ** 14, 800)[-2 ** 14:]
    P, _ = D.pca_plane(Y)
    return dF, abs(D.refined_frequency(P[:, 0] + 1j * P[:, 1])), float(np.ptp(s.energies(Y)[:, 0]))


def task(name):
    if name == "lyap200":
        return name, lyap_long(200)
    if name == "lyap400":
        return name, lyap_long(400)
    if name == "lyapdop":
        return name, lyap_dop853()
    if name == "neutral":
        return name, neutral_vector_alignment()
    if name == "rho":
        return name, rho_windows()
    if name.startswith("rhoF"):
        return name, rho_at(float(name[4:]))


def main():
    tm = Timer()
    names = ["lyapdop", "lyap400", "lyap200", "rho", "neutral"] + [f"rhoF{x:g}" for x in (0, -1e-5, -3e-6, -1e-6, 1e-6, 3e-6, 1e-5)]
    with Pool(4) as pool:
        res = dict(pool.map(task, names, chunksize=1))
    tm.mark("all")
    rows = sorted([res[n] for n in names if n.startswith("rhoF")])
    dFs = np.array([r[0] for r in rows]); rhos = np.array([r[1] for r in rows])
    slope, icpt = np.polyfit(dFs, rhos, 1)
    locking = {"rows": [{"dF": a, "abs_rho": b, "E1_range": c} for a, b, c in rows], "linear_slope_drho_dF": float(slope),
               "max_abs_residual_from_line": float(np.max(np.abs(rhos - (slope * dFs + icpt)))),
               "strictly_monotone": bool(np.all(np.diff(rhos) > 0) or np.all(np.diff(rhos) < 0)),
               "smallest_neighbour_difference": float(np.min(np.abs(np.diff(rhos))))}
    out = {"lyapunov_rk4_200": res["lyap200"], "lyapunov_rk4_400": res["lyap400"], "lyapunov_dop853": res["lyapdop"],
           "neutral_vector": res["neutral"], "rotation_number": res["rho"], "locking_test": locking}
    save("exp6_classification_convergence", {"config": {"F": F, "long_periods": LONG}, "results": out}, tm)
    print(json.dumps({"l200": res["lyap200"]["second_half_slope"], "l400": res["lyap400"]["second_half_slope"],
                      "sem": res["lyap400"]["block_sem"], "bound": res["lyap400"]["bound_abs_lambda1_from_bounded_stretch"],
                      "dop": res["lyapdop"], "neutral": res["neutral"], "rho": res["rho"], "lock": locking}, indent=1))


if __name__ == "__main__":
    main()
