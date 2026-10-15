"""Time integrators.

Three numerically independent families are provided:
  * rk4_*   : fixed-step classical RK4 (numba), steps per drive period chosen by caller;
  * DOP853  : scipy explicit adaptive Runge-Kutta 8(5,3) with dense output;
  * LSODA   : scipy variable-order Adams/BDF linear multistep (Fortran ODEPACK).
All RK4 integrations restart the local clock at every drive period (t mod T), so the
forcing phase is exact at stroboscopic times nT and no floating-point drift accumulates.
"""
from __future__ import annotations

import numpy as np
from numba import njit, prange
from scipy.integrate import solve_ivp

from .model import rhs, rhs_tangent


@njit(cache=True)
def _rk4_step(t, y, h, Phi, physical, alpha, eta, F, Omega, k1, k2, k3, k4, tmp):
    n = y.shape[0]
    rhs(t, y, Phi, physical, alpha, eta, F, Omega, k1)
    for i in range(n):
        tmp[i] = y[i] + 0.5 * h * k1[i]
    rhs(t + 0.5 * h, tmp, Phi, physical, alpha, eta, F, Omega, k2)
    for i in range(n):
        tmp[i] = y[i] + 0.5 * h * k2[i]
    rhs(t + 0.5 * h, tmp, Phi, physical, alpha, eta, F, Omega, k3)
    for i in range(n):
        tmp[i] = y[i] + h * k3[i]
    rhs(t + h, tmp, Phi, physical, alpha, eta, F, Omega, k4)
    for i in range(n):
        y[i] += h * (k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i]) / 6.0


@njit(cache=True)
def rk4_strobe(y0, periods, steps, Phi, physical, alpha, eta, F, Omega, half=False):
    """Integrate `periods` drive periods; return states at t = T, 2T, ... (shape periods x dim).

    If half is True, also return states at t = (n + 1/2)T (steps must be even)."""
    n = y0.shape[0]
    T = 2.0 * np.pi / Omega
    h = T / steps
    y = y0.copy()
    out = np.empty((periods, n))
    outh = np.empty((periods if half else 0, n))
    k1 = np.empty(n); k2 = np.empty(n); k3 = np.empty(n); k4 = np.empty(n); tmp = np.empty(n)
    for p in range(periods):
        for j in range(steps):
            _rk4_step(j * h, y, h, Phi, physical, alpha, eta, F, Omega, k1, k2, k3, k4, tmp)
            if half and j == steps // 2 - 1:
                outh[p] = y
        out[p] = y
    return out, outh


@njit(cache=True)
def rk4_flow_tangent(y0, W0, t0, t1, nsteps, Phi, physical, alpha, eta, F, Omega):
    """Integrate state and tangent matrix W (dim x p) from t0 to t1 with nsteps RK4 steps."""
    n = y0.shape[0]
    p = W0.shape[1]
    h = (t1 - t0) / nsteps
    y = y0.copy(); W = W0.copy()
    ky = np.empty((4, n)); kW = np.empty((4, n, p))
    ty = np.empty(n); tW = np.empty((n, p))
    for s in range(nsteps):
        t = t0 + s * h
        rhs_tangent(t, y, W, Phi, physical, alpha, eta, F, Omega, ky[0], kW[0])
        ty[:] = y + 0.5 * h * ky[0]; tW[:, :] = W + 0.5 * h * kW[0]
        rhs_tangent(t + 0.5 * h, ty, tW, Phi, physical, alpha, eta, F, Omega, ky[1], kW[1])
        ty[:] = y + 0.5 * h * ky[1]; tW[:, :] = W + 0.5 * h * kW[1]
        rhs_tangent(t + 0.5 * h, ty, tW, Phi, physical, alpha, eta, F, Omega, ky[2], kW[2])
        ty[:] = y + h * ky[2]; tW[:, :] = W + h * kW[2]
        rhs_tangent(t + h, ty, tW, Phi, physical, alpha, eta, F, Omega, ky[3], kW[3])
        y += h * (ky[0] + 2.0 * ky[1] + 2.0 * ky[2] + ky[3]) / 6.0
        W += h * (kW[0] + 2.0 * kW[1] + 2.0 * kW[2] + kW[3]) / 6.0
    return y, W


@njit(cache=True)
def lyapunov_qr(y0, periods, steps, nvec, Phi, physical, alpha, eta, F, Omega):
    """Benettin/QR Lyapunov spectrum (first nvec exponents), re-orthonormalised every period.

    Returns (final state, cumulative log-stretch array of shape (periods, nvec)).
    Exponents per unit time at period n are cum[n] / ((n+1) T)."""
    n = y0.shape[0]
    T = 2.0 * np.pi / Omega
    y = y0.copy()
    W = np.eye(n)[:, :nvec].copy()
    cum = np.zeros((periods, nvec))
    acc = np.zeros(nvec)
    for p in range(periods):
        y, W = rk4_flow_tangent(y, W, 0.0, T, steps, Phi, physical, alpha, eta, F, Omega)
        Q, R = np.linalg.qr(W)
        for i in range(nvec):
            d = R[i, i]
            acc[i] += np.log(abs(d))
            if d < 0:
                for r in range(n):
                    Q[r, i] = -Q[r, i]
        W = np.ascontiguousarray(Q)
        cum[p] = acc
    return y, cum


@njit(parallel=True, cache=True)
def rk4_batch(Y0, Fs, periods, steps, keep, Phi, physical, alpha, eta, Omega):
    """Independent trajectories in parallel (one F per trajectory); returns the last `keep`
    stroboscopic states of each, shape (batch, keep, dim)."""
    nb, n = Y0.shape
    T = 2.0 * np.pi / Omega
    h = T / steps
    out = np.empty((nb, keep, n))
    for b in prange(nb):
        y = Y0[b].copy()
        k1 = np.empty(n); k2 = np.empty(n); k3 = np.empty(n); k4 = np.empty(n); tmp = np.empty(n)
        for p in range(periods):
            for j in range(steps):
                _rk4_step(j * h, y, h, Phi, physical, alpha, eta, Fs[b], Omega, k1, k2, k3, k4, tmp)
            if p >= periods - keep:
                out[b, p - (periods - keep)] = y
    return out


def batch(sys, Y0, periods, steps=200, keep=1000, Fs=None):
    Y0 = np.ascontiguousarray(np.atleast_2d(Y0), dtype=float)
    Fs = np.full(len(Y0), sys.F) if Fs is None else np.asarray(Fs, float)
    Phi, physical, alpha, eta, _, Omega = sys.args
    return rk4_batch(Y0, Fs, int(periods), int(steps), int(keep), Phi, physical, alpha, eta, Omega)


# --- scipy reference integrators -----------------------------------------------------------

def scipy_strobe(sys, y0, periods, method="DOP853", rtol=1e-11, atol=1e-13, t_eval_every=1):
    """Stroboscopic samples y(nT), n = 1..periods, from scipy's adaptive integrators."""
    args = sys.args
    out = np.empty(sys.dim)

    def f(t, y):
        rhs(t, y, *args, out)
        return out.copy()

    t_eval = np.arange(1, periods + 1, t_eval_every) * sys.T
    sol = solve_ivp(f, (0.0, periods * sys.T), np.asarray(y0, float), method=method, rtol=rtol,
                    atol=atol, t_eval=t_eval)
    if not sol.success:
        raise RuntimeError(sol.message)
    return sol.y.T, int(sol.nfev)


def scipy_strobe_segmented(sys, y0, periods, method="DOP853", rtol=1e-12, atol=1e-14, segment=500):
    """Like scipy_strobe, but restarts the clock at t = 0 every `segment` drive periods so the drive
    phase Omega*t is evaluated with arguments <= 2*pi*segment (exact phase at every restart).
    Returns (Y at t = nT for n = 1..periods, total nfev)."""
    args = sys.args
    out = np.empty(sys.dim)

    def f(t, y):
        rhs(t, y, *args, out)
        return out.copy()

    y = np.asarray(y0, float).copy()
    Y = np.empty((periods, sys.dim))
    nfev = 0
    done = 0
    while done < periods:
        k = min(segment, periods - done)
        sol = solve_ivp(f, (0.0, k * sys.T), y, method=method, rtol=rtol, atol=atol,
                        t_eval=np.arange(1, k + 1) * sys.T)
        if not sol.success:
            raise RuntimeError(sol.message)
        Y[done:done + k] = sol.y.T
        y = sol.y[:, -1].copy()
        nfev += int(sol.nfev)
        done += k
    return Y, nfev


def scipy_flow_tangent(sys, y0, t1, method="DOP853", rtol=1e-12, atol=1e-14, t0=0.0):
    """State and full monodromy-type matrix from t0 to t1 via the augmented variational ODE."""
    d = sys.dim
    args = sys.args
    oy = np.empty(d); oW = np.empty((d, d))

    def f(t, z):
        rhs_tangent(t, z[:d], z[d:].reshape(d, d), *args, oy, oW)
        return np.concatenate((oy, oW.ravel()))

    z0 = np.concatenate((np.asarray(y0, float), np.eye(d).ravel()))
    sol = solve_ivp(f, (t0, t1), z0, method=method, rtol=rtol, atol=atol)
    if not sol.success:
        raise RuntimeError(sol.message)
    z = sol.y[:, -1]
    return z[:d], z[d:].reshape(d, d), int(sol.nfev)


def strobe(sys, y0, periods, steps=400, half=False):
    out, outh = rk4_strobe(np.asarray(y0, float), int(periods), int(steps), *sys.args, half)
    return (out, outh) if half else out
