"""Normal-mode (tensor) form of the chain with selectively removable couplings, for causal tests.

    Q_k'' = -w_k^2 Q_k - eta Q_k' + F g_k cos(Omega t) - alpha sum_ij C[k,i,j] Q_i Q_j,
    C[k,i,j] = sum_b Dm[b,k] Dm[b,i] Dm[b,j],  Dm = (bond matrix) @ (sine basis)  (fully symmetric).
Knocking out a triad {i,j,k} zeroes all permutations, so the model stays Hamiltonian (+ uniform
damping); knocking out g_k removes direct forcing of mode k. With nothing removed this equals the
physical-coordinate model (tested).
"""
from __future__ import annotations

from itertools import permutations

import numpy as np
from numba import njit
from scipy.optimize import brentq

from .model import mode_frequencies, sine_basis
from .normal_form import bond_matrix


def coupling_tensor(N=8):
    Dm = bond_matrix(N) @ sine_basis(N)
    return np.einsum("bk,bi,bj->kij", Dm, Dm, Dm)


def knock(C, triads):
    C = C.copy()
    for t in triads:
        for p in set(permutations([x - 1 for x in t])):
            C[p] = 0.0
    return C


@njit(cache=True)
def _rhs(t, y, w, C, g, alpha, eta, F, Omega, out):
    m = w.shape[0]
    c = np.cos(Omega * t)
    for k in range(m):
        a = -w[k] * w[k] * y[k] - eta * y[m + k] + F * g[k] * c
        for i in range(m):
            for j in range(m):
                a -= alpha * C[k, i, j] * y[i] * y[j]
        out[k] = y[m + k]
        out[m + k] = a


@njit(cache=True)
def _jac(y, w, C, alpha, eta, J):
    m = w.shape[0]
    J[:, :] = 0.0
    for k in range(m):
        J[k, m + k] = 1.0
        J[m + k, m + k] = -eta
        J[m + k, k] = -w[k] * w[k]
        for i in range(m):
            s = 0.0
            for j in range(m):
                s += C[k, i, j] * y[j]
            J[m + k, i] -= 2.0 * alpha * s


@njit(cache=True)
def flow_tangent(y0, steps, w, C, g, alpha, eta, F, Omega):
    m = w.shape[0]
    n = 2 * m
    T = 2.0 * np.pi / Omega
    h = T / steps
    y = y0.copy()
    W = np.eye(n)
    J = np.empty((n, n))
    k = np.empty((4, n)); kW = np.empty((4, n, n))
    for s in range(steps):
        t = s * h
        _rhs(t, y, w, C, g, alpha, eta, F, Omega, k[0]); _jac(y, w, C, alpha, eta, J); kW[0] = J @ W
        y1 = y + 0.5 * h * k[0]; W1 = W + 0.5 * h * kW[0]
        _rhs(t + 0.5 * h, y1, w, C, g, alpha, eta, F, Omega, k[1]); _jac(y1, w, C, alpha, eta, J); kW[1] = J @ W1
        y2 = y + 0.5 * h * k[1]; W2 = W + 0.5 * h * kW[1]
        _rhs(t + 0.5 * h, y2, w, C, g, alpha, eta, F, Omega, k[2]); _jac(y2, w, C, alpha, eta, J); kW[2] = J @ W2
        y3 = y + h * k[2]; W3 = W + h * kW[2]
        _rhs(t + h, y3, w, C, g, alpha, eta, F, Omega, k[3]); _jac(y3, w, C, alpha, eta, J); kW[3] = J @ W3
        y += h / 6 * (k[0] + 2 * k[1] + 2 * k[2] + k[3])
        W += h / 6 * (kW[0] + 2 * kW[1] + 2 * kW[2] + kW[3])
    return y, W


class TensorFPUT:
    def __init__(self, modes=tuple(range(1, 9)), knock_triads=(), knock_forcing=(), N=8, alpha=0.25, eta=0.0025,
                 Omega=0.347):
        idx = np.array(modes) - 1
        C = knock(coupling_tensor(N), knock_triads)
        self.C = np.ascontiguousarray(C[np.ix_(idx, idx, idx)])
        g = sine_basis(N).sum(axis=0)
        for k in knock_forcing:
            g[k - 1] = 0.0
        self.g = g[idx].copy()
        self.w = mode_frequencies(N)[idx].copy()
        self.alpha, self.eta, self.Omega = alpha, eta, Omega
        self.dim = 2 * len(idx)

    def period(self, y, F, steps=800):
        return flow_tangent(np.asarray(y, float), steps, self.w, self.C, self.g, self.alpha, self.eta, F, self.Omega)

    def newton(self, y, F, steps=800, tol=1e-12, maxit=40):
        y = np.asarray(y, float).copy()
        for _ in range(maxit):
            yT, M = self.period(y, F, steps)
            r = yT - y
            if np.max(np.abs(r)) < tol:
                return y, M, True
            dy = np.linalg.solve(M - np.eye(self.dim), -r)
            y = y + min(1.0, 0.5 / np.max(np.abs(dy))) * dy
        return y, M, False

    def critical_F(self, Fmax=0.0075, dF=1e-4, steps=800):
        """Continue the locked branch from F=0; F at which max|mu| first reaches 1 (None if not)."""
        y = np.zeros(self.dim)
        prev = None
        for F in np.arange(0.0, Fmax + 1e-12, dF):
            y, M, ok = self.newton(y, F, steps)
            if not ok:
                return None, f"branch lost at {F:.6f}"
            m = np.max(np.abs(np.linalg.eigvals(M)))
            if m > 1 and prev is not None:
                st = {"y": prev[1]}

                def g(FF):
                    st["y"], MM, _ = self.newton(st["y"], FF, steps)
                    return np.max(np.abs(np.linalg.eigvals(MM))) - 1

                return brentq(g, prev[0], F, xtol=1e-12), "ok"
            prev = (F, y.copy())
        return None, f"no crossing up to {Fmax}"
