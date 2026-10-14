"""Drive-locked periodic orbits (fixed points of the stroboscopic map) and Floquet multipliers.

Three independent routes to the monodromy matrix M = dP/dy:
  1. RK4 variational equations (fixed steps per period);
  2. DOP853 variational equations (adaptive, tight tolerance);
  3. Central finite differences of the DOP853 period map (no variational equations at all).
And an independent route to the multipliers of symmetric orbits:
  4. Half-period symmetric map G = S o P_{0->T/2};  M = (DG)^2, so mu = lambda^2.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import brentq

from .integrate import rk4_flow_tangent, scipy_flow_tangent, scipy_strobe


def period_map(sys, y, steps=400, half=False, method="rk4", rtol=1e-12, atol=1e-14):
    """(P(y), M) for the full period, or (G(y), DG) for the half-period symmetric map."""
    d = sys.dim
    t1 = sys.T / 2 if half else sys.T
    if method == "rk4":
        n = steps // 2 if half else steps
        yT, M = rk4_flow_tangent(np.asarray(y, float), np.eye(d), 0.0, t1, n, *sys.args)
    else:
        yT, M, _ = scipy_flow_tangent(sys, y, t1, method=method, rtol=rtol, atol=atol)
    if half:
        return sys.S @ yT, sys.S @ M
    return yT, M


def newton_orbit(sys, y0, steps=400, half=False, method="rk4", tol=1e-12, maxit=40, **kw):
    """Newton iteration on P(y) - y = 0 (or G(y) - y = 0). Returns (y, M, info)."""
    y = np.array(y0, float)
    d = sys.dim
    hist = []
    for it in range(maxit):
        yT, M = period_map(sys, y, steps, half, method, **kw)
        r = yT - y
        res = float(np.max(np.abs(r)))
        hist.append(res)
        if res < tol:
            return y, M, {"converged": True, "iterations": it, "residual": res, "history": hist}
        dy = np.linalg.solve(M - np.eye(d), -r)
        # damped step if the update is very large (far from a solution)
        scale = min(1.0, 0.5 / max(1e-300, float(np.max(np.abs(dy)))))
        y = y + scale * dy
    yT, M = period_map(sys, y, steps, half, method, **kw)
    res = float(np.max(np.abs(yT - y)))
    return y, M, {"converged": res < tol, "iterations": maxit, "residual": res, "history": hist}


def multipliers(M):
    mu = np.linalg.eigvals(M)
    return mu[np.argsort(-np.abs(mu))]


def fd_monodromy(sys, y, eps=1e-6, rtol=1e-12, atol=1e-14, method="DOP853"):
    """Central finite-difference monodromy from the plain period map (no variational ODE)."""
    d = sys.dim
    M = np.empty((d, d))
    for j in range(d):
        e = np.zeros(d); e[j] = eps
        yp, _ = scipy_strobe(sys, y + e, 1, method=method, rtol=rtol, atol=atol)
        ym, _ = scipy_strobe(sys, y - e, 1, method=method, rtol=rtol, atol=atol)
        M[:, j] = (yp[-1] - ym[-1]) / (2 * eps)
    return M


def continue_branch(sys0, Fs, y0=None, steps=400, half=False):
    """Natural-parameter continuation of the drive-locked branch through the list Fs."""
    y = np.zeros(sys0.dim) if y0 is None else np.array(y0, float)
    rows = []
    for F in Fs:
        s = sys0.with_F(F)
        y, M, info = newton_orbit(s, y, steps, half)
        mu = multipliers(M)
        if half:
            mu = multipliers(M @ M)  # full-period multipliers from the half map
        rows.append({"F": float(F), "y": y.copy(), "mu": mu, "converged": info["converged"],
                     "residual": info["residual"]})
        if not info["converged"]:
            break
    return rows


def critical_F(sys0, bracket, y_seed, steps=400, half=False, xtol=1e-13):
    """F at which the largest Floquet modulus of the continued branch equals 1 (brentq)."""
    state = {"y": np.array(y_seed, float)}

    def g(F):
        y, M, info = newton_orbit(sys0.with_F(F), state["y"], steps, half)
        if not info["converged"]:
            raise RuntimeError(f"Newton failed at F={F}: {info['residual']}")
        state["y"] = y
        mu = multipliers(M @ M if half else M)
        return float(np.abs(mu[0]) - 1.0)

    Fc = brentq(g, *bracket, xtol=xtol, rtol=4 * np.finfo(float).eps)
    y, M, info = newton_orbit(sys0.with_F(Fc), state["y"], steps, half)
    mu = multipliers(M @ M if half else M)
    return Fc, y, mu, info
