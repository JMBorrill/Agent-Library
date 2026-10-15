"""Experiment 8b - scaling tests of the fold of invariant circles at the lower edge F_low (follow-up
to Exp 8, which found the unstable edge circle within 0.008 of the stable torus at F = 0.0042165625
with both normal rates near zero). Full chain, RK4/200, same decision rules as Exp 8.

Generic saddle-node of invariant circles predicts, with an unknown F_low:
  lambda_2(F)^2, sigma_u(F)^2 and dist(F)^2  are linear in F and vanish at the SAME F_low,
  ghost transit time below F_low  tau = b + a (F_low - F)^(-1/2).
F_low is fitted independently from each quantity and compared with the bisection bracket
(0.00421625, 0.0042165625) of Exp 8. The ghost exponent is fitted with F_low fixed to the mean
of the three fold-side estimates.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("NUMBA_CACHE_DIR", str(ROOT / ".numba_cache"))
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments"))

import json  # noqa: E402

import numpy as np  # noqa: E402
from scipy.optimize import curve_fit  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402

from exp8_edge_and_fold import STEPS, edge_state, locked, lyap_top, settle_torus  # noqa: E402
from fputv.floquet import newton_orbit  # noqa: E402
from fputv.integrate import strobe  # noqa: E402
from fputv.io import Timer, save  # noqa: E402
from fputv.model import FPUT  # noqa: E402

LO, HI = 0.00421625, 0.0042165625
OFFS = [1e-4, 3e-5, 1e-5, 3e-6, 1e-6, 3e-7]  # above HI


def ghost_time(F, y0, y_lock, maxp=400000, chunk=20):
    s = FPUT(F)
    y = y0.copy()
    p = 0
    while p < maxp:
        Y = strobe(s, y, chunk, STEPS)
        d = np.max(np.abs(Y - y_lock), axis=1)
        hit = np.nonzero(d < 0.1)[0]
        if len(hit):
            return p + int(hit[0]) + 1
        p += chunk
        y = Y[-1]
    return None


def main():
    tm = Timer()
    z = np.load(ROOT / "results/exp8_edge_histories.npz")
    tor_hi = z["torus_F0.0042165625"]
    # locked orbit near F_low (RK4/200 map)
    yl0 = np.zeros(16)
    s0 = FPUT(0.0)
    for F in np.arange(0, 0.0042, 2e-4):
        yl0, _, _ = newton_orbit(s0.with_F(F), yl0, STEPS)
    rows = []
    torus_state = {}
    # continue the torus downward from F = HI + 1e-4 (start from the Exp 8 torus near F_low)
    Fs = [HI + o for o in OFFS]
    yt = settle_torus(Fs[0], tor_hi[-1], periods=8000, keep=10)[0][-1]
    for F in Fs:
        W, r1 = settle_torus(F, yt, periods=8000, keep=4096)
        yt = W[-1]
        yl, M = locked(F, yl0)
        L, _ = lyap_top(F, W[-1], periods=16000, nvec=3)
        e, H = edge_state(F, yl, M, W)
        tr = cKDTree(W)
        rows.append({"F": F, "lambda2_per_time": float(L["lambda"][1]), "lambda2_q3_q4": [float(L["third_quarter"][1]), float(L["fourth_quarter"][1])],
                     "lambda1": float(L["lambda"][0]), "torus_E1_range": r1,
                     "edge": {k: e.get(k) for k in ("is_fixed_point", "abs_z_mean", "rotation_number_critical_plane", "abs_rho_naff",
                                                    "distance_to_stable_torus_min_median", "instability_rate_per_period", "error", "start")}})
        print(json.dumps(rows[-1], default=str), flush=True)
        tm.mark(f"F{F:.10f}")
    T = FPUT(0.0042).T
    F = np.array([r["F"] for r in rows])
    fits = {}
    quantities = {"lambda2_squared": np.array([(r["lambda2_per_time"] * T) ** 2 for r in rows]),
                  "sigma_u_squared": np.array([(r["edge"]["instability_rate_per_period"] or np.nan) ** 2 for r in rows]),
                  "edge_torus_distance_median_squared": np.array([r["edge"]["distance_to_stable_torus_min_median"][1] ** 2
                                                                  if r["edge"]["distance_to_stable_torus_min_median"] else np.nan for r in rows])}
    for name, q in quantities.items():
        ok = np.isfinite(q)
        sel = ok & (F - HI <= 1.01e-5)  # asymptotic region
        if sel.sum() >= 3:
            k, c = np.polyfit(F[sel], q[sel], 1)
            fits[name] = {"slope": float(k), "F_low_from_zero_crossing": float(-c / k), "n_points": int(sel.sum()),
                          "loglog_exponent_vs_F_minus_HI": None}
    Flow = float(np.nanmean([f["F_low_from_zero_crossing"] for f in fits.values()])) if fits else 0.5 * (LO + HI)
    # local exponents (q ~ (F-F_low)^gamma, gamma = 1 predicted for squared quantities)
    for name, q in quantities.items():
        ok = np.isfinite(q) & (F > Flow)
        if ok.sum() >= 3:
            fits.setdefault(name, {})["loglog_exponent_vs_F_minus_Flow"] = float(np.polyfit(np.log(F[ok] - Flow), np.log(q[ok]), 1)[0])
    tm.mark("fits")

    ghost = []
    y_start = tor_hi[-1]
    for dF in (3e-7, 1e-6, 3e-6, 1e-5, 3e-5):
        Fg = LO - dF
        yl, _ = locked(Fg, yl0)
        tau = ghost_time(Fg, y_start, yl)
        ghost.append({"F": Fg, "F_low_minus_F": Flow - Fg, "transit_periods": tau})
        print("ghost", Fg, tau, flush=True)
    tm.mark("ghost")
    g = [(r["F_low_minus_F"], r["transit_periods"]) for r in ghost if r["transit_periods"]]
    gf = None
    if len(g) >= 4:
        x = np.array([a for a, _ in g]); yv = np.array([b for _, b in g], float)
        p_half, _ = curve_fit(lambda x, a, b: b + a * x ** -0.5, x, yv, p0=(3, 500))
        p_free, cov = curve_fit(lambda x, a, b, gam: b + a * x ** -gam, x, yv, p0=(3, 500, 0.5), maxfev=20000)
        res_half = yv - (p_half[1] + p_half[0] * x ** -0.5)
        gf = {"fit_gamma_fixed_0.5": {"a": float(p_half[0]), "b": float(p_half[1]), "max_rel_residual": float(np.max(np.abs(res_half) / yv))},
              "fit_gamma_free": {"a": float(p_free[0]), "b": float(p_free[1]), "gamma": float(p_free[2]),
                                 "gamma_std": float(np.sqrt(cov[2, 2])) if np.all(np.isfinite(cov)) else None}}
    out = {"fold_side": rows, "fits": fits, "F_low_estimate_from_fold_side_fits": Flow,
           "bisection_bracket_exp8": [LO, HI], "ghost": ghost, "ghost_fit": gf}
    save("exp8b_fold_scaling", {"config": {"rk4_steps": STEPS, "offsets_above_HI": OFFS}, "results": out}, tm)
    print(json.dumps({"fits": fits, "Flow": Flow, "ghost_fit": gf}, indent=1))


if __name__ == "__main__":
    main()
