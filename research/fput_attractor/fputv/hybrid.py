"""Hybrid monodromy matrices for decomposing the truncation-induced Floquet-threshold shift.

The base periodic orbit is integrated in one model (basis Phi_b) while linear perturbations are
restricted to another mode set (basis Phi_t). The bond stiffness V''(r) = 1 + 2 alpha r is
evaluated at positions Pq @ q_base, where Pq optionally projects the base orbit onto a mode set.
All variants are linear periodic Hamiltonian systems with uniform damping (symmetric projected
stiffness), so they inherit the multiplier pairing |mu_i||mu_j| = exp(-eta T).
"""
from __future__ import annotations

import numpy as np
from numba import njit

from .model import _positions, rhs


@njit(cache=True)
def _tangent_from_q(q, W, Phi_t, alpha, eta, outW):
    N = Phi_t.shape[0]
    m = Phi_t.shape[1]
    kb = np.empty(N + 1)
    kb[0] = 1.0 + 2.0 * alpha * q[0]
    for i in range(N):
        nxt = q[i + 1] if i + 1 < N else 0.0
        kb[i + 1] = 1.0 + 2.0 * alpha * (nxt - q[i])
    dq = np.empty(N)
    df = np.empty(N)
    for c in range(W.shape[1]):
        for k in range(m):
            outW[k, c] = W[m + k, c]
        for n in range(N):
            s = 0.0
            for k in range(m):
                s += Phi_t[n, k] * W[k, c]
            dq[n] = s
        for i in range(N):
            left = dq[i - 1] if i > 0 else 0.0
            right = dq[i + 1] if i + 1 < N else 0.0
            df[i] = kb[i + 1] * (right - dq[i]) - kb[i] * (dq[i] - left)
        for k in range(m):
            s = 0.0
            for n in range(N):
                s += Phi_t[n, k] * df[n]
            outW[m + k, c] = s - eta * W[m + k, c]


@njit(cache=True)
def _hyb(t, y, W, Phi_b, phys_b, Phi_t, Pq, alpha, eta, F, Omega, oy, oW):
    N = Phi_b.shape[0]
    mb = Phi_b.shape[1]
    rhs(t, y, Phi_b, phys_b, alpha, eta, F, Omega, oy)
    q0 = np.empty(N)
    _positions(y[:mb], Phi_b, phys_b, q0)
    q = Pq @ q0
    _tangent_from_q(q, W, Phi_t, alpha, eta, oW)


@njit(cache=True)
def hybrid_monodromy(y0, steps, Phi_b, phys_b, Phi_t, Pq, alpha, eta, F, Omega):
    T = 2.0 * np.pi / Omega
    h = T / steps
    nt = 2 * Phi_t.shape[1]
    y = y0.copy()
    W = np.eye(nt)
    n = y.shape[0]
    ky = np.empty((4, n)); kW = np.empty((4, nt, nt))
    for s in range(steps):
        t = s * h
        _hyb(t, y, W, Phi_b, phys_b, Phi_t, Pq, alpha, eta, F, Omega, ky[0], kW[0])
        _hyb(t + h / 2, y + h / 2 * ky[0], W + h / 2 * kW[0], Phi_b, phys_b, Phi_t, Pq, alpha, eta, F, Omega, ky[1], kW[1])
        _hyb(t + h / 2, y + h / 2 * ky[1], W + h / 2 * kW[1], Phi_b, phys_b, Phi_t, Pq, alpha, eta, F, Omega, ky[2], kW[2])
        _hyb(t + h, y + h * ky[2], W + h * kW[2], Phi_b, phys_b, Phi_t, Pq, alpha, eta, F, Omega, ky[3], kW[3])
        y += h / 6 * (ky[0] + 2 * ky[1] + 2 * ky[2] + ky[3])
        W += h / 6 * (kW[0] + 2 * kW[1] + 2 * kW[2] + kW[3])
    return y, W
