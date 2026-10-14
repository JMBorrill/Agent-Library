"""Independent implementation of the driven, damped alpha-FPUT chain with fixed ends.

    q_n'' = V'(r_n) - V'(r_{n-1}) - eta q_n' + F cos(Omega t),   V'(r) = r + alpha r^2,
    r_n = q_{n+1} - q_n,  q_0 = q_{N+1} = 0,  n = 1..N.

States are y = (a, b) with q = Phi a and q' = Phi b.

* Full system: Phi = I (physical site coordinates).  This deliberately differs from the
  baseline, which integrates the full system in normal-mode coordinates via a C[k,i,j] tensor.
* Galerkin truncation on a mode set S: Phi = sine-basis columns S, and
      b' = Phi^T f(Phi a) - eta b + F cos(Omega t) Phi^T 1,
  i.e. the physical force is projected.  Because f is quadratic this is algebraically the
  same truncation as the baseline tensor form, but it is computed by a different route.

Spatio-temporal symmetry (verified in tests): with R q_n = -q_{N+1-n},
    if y(t) solves the system then R y(t - T/2) also does.
In normal modes R = diag((-1)^k), i.e. odd modes change sign.
"""
from __future__ import annotations

import numpy as np
from numba import njit

PARAMS = dict(N=8, alpha=0.25, eta=0.0025, Omega=0.347)


def sine_basis(N: int) -> np.ndarray:
    n = np.arange(1, N + 1)[:, None]
    k = np.arange(1, N + 1)[None, :]
    return np.sqrt(2.0 / (N + 1)) * np.sin(np.pi * n * k / (N + 1))


def mode_frequencies(N: int) -> np.ndarray:
    return 2.0 * np.sin(np.pi * np.arange(1, N + 1) / (2 * (N + 1)))


class FPUT:
    """Parameter container for one (F, mode set) configuration."""

    def __init__(self, F, N=8, alpha=0.25, eta=0.0025, Omega=0.347, modes=None):
        self.F, self.N, self.alpha, self.eta, self.Omega = float(F), int(N), float(alpha), float(eta), float(Omega)
        self.T = 2.0 * np.pi / self.Omega
        self.B = sine_basis(self.N)
        self.omega = mode_frequencies(self.N)
        if modes is None:
            self.modes = None
            self.Phi = np.eye(self.N)
            self.physical = True
        else:
            self.modes = tuple(int(k) for k in modes)
            self.Phi = np.ascontiguousarray(self.B[:, np.array(self.modes) - 1])
            self.physical = False
        self.m = self.Phi.shape[1]
        self.dim = 2 * self.m
        R = -np.fliplr(np.eye(self.N))
        Sg = self.Phi.T @ R @ self.Phi
        self.S = np.zeros((self.dim, self.dim))
        self.S[: self.m, : self.m] = Sg
        self.S[self.m:, self.m:] = Sg

    def with_F(self, F):
        return FPUT(F, self.N, self.alpha, self.eta, self.Omega, self.modes)

    @property
    def args(self):
        return (self.Phi, self.physical, self.alpha, self.eta, self.F, self.Omega)

    @property
    def label(self):
        return "full" if self.modes is None else "modes" + "".join(str(k) for k in self.modes)

    # --- coordinate helpers -------------------------------------------------------------
    def modal(self, Y):
        """Normal-mode (Q, P) of states Y (..., dim) for all N modes."""
        Y = np.asarray(Y)
        q = Y[..., : self.m] @ self.Phi.T
        p = Y[..., self.m:] @ self.Phi.T
        return q @ self.B, p @ self.B

    def energies(self, Y):
        """Linear normal-mode energies E_k = (P_k^2 + omega_k^2 Q_k^2)/2, shape (..., N)."""
        Q, P = self.modal(Y)
        return 0.5 * (P ** 2 + (self.omega * Q) ** 2)

    def from_modal(self, Q, P):
        """Generalised state from full modal (Q, P) (projected onto the mode set)."""
        q = np.asarray(Q) @ self.B.T
        p = np.asarray(P) @ self.B.T
        return np.r_[q @ self.Phi, p @ self.Phi]

    def rhs(self, t, y):
        out = np.empty(self.dim)
        rhs(t, np.asarray(y, dtype=float), *self.args, out)
        return out

    def jac(self, t, y):
        """Dense Jacobian (dim x dim) of the vector field at (t, y)."""
        W = np.eye(self.dim)
        oy = np.empty(self.dim)
        oW = np.empty_like(W)
        rhs_tangent(t, np.asarray(y, dtype=float), W, *self.args, oy, oW)
        return oW


@njit(cache=True)
def _positions(a, Phi, physical, q):
    N = Phi.shape[0]
    m = Phi.shape[1]
    if physical:
        for n in range(N):
            q[n] = a[n]
    else:
        for n in range(N):
            s = 0.0
            for k in range(m):
                s += Phi[n, k] * a[k]
            q[n] = s


@njit(cache=True)
def rhs(t, y, Phi, physical, alpha, eta, F, Omega, out):
    N = Phi.shape[0]
    m = Phi.shape[1]
    q = np.empty(N)
    f = np.empty(N)
    _positions(y[:m], Phi, physical, q)
    drive = F * np.cos(Omega * t)
    prev = q[0] + alpha * q[0] * q[0]  # V'(r_0), r_0 = q_1 - q_0
    for i in range(N):
        nxt = q[i + 1] if i + 1 < N else 0.0
        r = nxt - q[i]
        cur = r + alpha * r * r
        f[i] = cur - prev + drive
        prev = cur
    for k in range(m):
        out[k] = y[m + k]
    if physical:
        for k in range(m):
            out[m + k] = f[k] - eta * y[m + k]
    else:
        for k in range(m):
            s = 0.0
            for n in range(N):
                s += Phi[n, k] * f[n]
            out[m + k] = s - eta * y[m + k]


@njit(cache=True)
def rhs_tangent(t, y, W, Phi, physical, alpha, eta, F, Omega, outy, outW):
    """Vector field and variational field d/dt W = J(t, y) W for W of shape (dim, p)."""
    N = Phi.shape[0]
    m = Phi.shape[1]
    p = W.shape[1]
    rhs(t, y, Phi, physical, alpha, eta, F, Omega, outy)
    q = np.empty(N)
    _positions(y[:m], Phi, physical, q)
    kb = np.empty(N + 1)  # bond stiffness V''(r_b) = 1 + 2 alpha r_b, b = 0..N
    kb[0] = 1.0 + 2.0 * alpha * q[0]
    for i in range(N):
        nxt = q[i + 1] if i + 1 < N else 0.0
        kb[i + 1] = 1.0 + 2.0 * alpha * (nxt - q[i])
    dq = np.empty(N)
    df = np.empty(N)
    for c in range(p):
        for k in range(m):
            outW[k, c] = W[m + k, c]
        if physical:
            for n in range(N):
                dq[n] = W[n, c]
        else:
            for n in range(N):
                s = 0.0
                for k in range(m):
                    s += Phi[n, k] * W[k, c]
                dq[n] = s
        for i in range(N):
            left = dq[i - 1] if i > 0 else 0.0
            right = dq[i + 1] if i + 1 < N else 0.0
            df[i] = kb[i + 1] * (right - dq[i]) - kb[i] * (dq[i] - left)
        if physical:
            for k in range(m):
                outW[m + k, c] = df[k] - eta * W[m + k, c]
        else:
            for k in range(m):
                s = 0.0
                for n in range(N):
                    s += Phi[n, k] * df[n]
                outW[m + k, c] = s - eta * W[m + k, c]
