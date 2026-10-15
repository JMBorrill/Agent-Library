"""Neimark-Sacker normal-form coefficient (first Lyapunov coefficient) for the stroboscopic map.

For a map x -> A x + B(x,x)/2 + C(x,x,x)/6 + O(4) with a simple pair e^{+-i theta} on the unit circle,
A q = e^{i theta} q, A^T p = e^{-i theta} p, <p,q> = conj(p).q = 1 (|q| = 1), the invariant form
(Kuznetsov, Elements of Applied Bifurcation Theory, NS bifurcation of n-dim maps) is
    c1 = 1/2 <p, C(q,q,qb) + 2 B(q,(I-A)^{-1}B(q,qb)) + B(qb,(e^{2 i theta} I - A)^{-1} B(q,q))>,
    d  = Re(e^{-i theta} c1);   d < 0 supercritical, d > 0 subcritical.
The formula is written from memory; its constants and sign convention are therefore validated
against direct iteration of test maps (tests/test_normal_form.py): for x -> (1+beta)R x + ...,
the invariant circle has |<p,x>|^2 = -beta/d + O(beta^2).

For the forced FPUT chain, B and C of the period map are obtained from second- and third-order
variational equations along the periodic orbit. The bond force V'(r) = r + alpha r^2 is quadratic,
so the third derivative of the vector field vanishes and only D^2 f enters:
    D^2 f(x, z) = -D^T (2 alpha (D x) * (D z))  (positions only), projected with Phi for truncations.
"""
from __future__ import annotations

import numpy as np
from scipy.integrate import solve_ivp


def bond_matrix(N):
    D = np.zeros((N + 1, N))
    for b in range(N + 1):
        if b < N:
            D[b, b] = 1.0
        if b >= 1:
            D[b, b - 1] = -1.0
    return D


class Taylor:
    """Second/third derivatives of the period map of an FPUT system about a state y0 at t = 0."""

    def __init__(self, sys):
        self.s = sys
        self.D = bond_matrix(sys.N)
        self.DP = self.D @ sys.Phi            # bonds from generalised positions
        self.m = sys.m

    def _accel_lin(self, r, ua):
        # Phi^T (-D^T diag(1 + 2 alpha r) D Phi) ua
        return -self.DP.T @ ((1 + 2 * self.s.alpha * r) * (self.DP @ ua))

    def _second(self, ua, va):
        return -self.DP.T @ (2 * self.s.alpha * (self.DP @ ua) * (self.DP @ va))

    def _rhs(self, t, Z, nv, pairs, triples):
        s, m = self.s, self.m
        dim = 2 * m
        y = Z[:dim].real
        f = s.rhs(t, y)
        r = self.DP @ y[:m]
        out = np.empty_like(Z)
        out[:dim] = f
        U = Z[dim:dim + nv * dim].reshape(nv, dim)
        off = dim + nv * dim
        W = Z[off:off + len(pairs) * dim].reshape(len(pairs), dim)
        off2 = off + len(pairs) * dim
        V = Z[off2:].reshape(len(triples), dim)

        def L(X):
            return np.concatenate((X[m:], self._accel_lin(r, X[:m]) - s.eta * X[m:]))

        oU = np.array([L(u) for u in U]) if nv else np.zeros((0, dim))
        oW = []
        for k, (i, j) in enumerate(pairs):
            src = np.zeros(dim, complex)
            src[m:] = self._second(U[i][:m], U[j][:m])
            oW.append(L(W[k]) + src)
        oV = []
        widx = {p: k for k, p in enumerate(pairs)}
        for k, (i, j, l) in enumerate(triples):
            src = np.zeros(dim, complex)
            src[m:] = (self._second(W[widx[(i, j)]][:m], U[l][:m]) + self._second(W[widx[(i, l)]][:m], U[j][:m]) +
                       self._second(W[widx[(j, l)]][:m], U[i][:m]))
            oV.append(L(V[k]) + src)
        out[dim:dim + nv * dim] = oU.ravel()
        if pairs:
            out[off:off2] = np.concatenate(oW)
        if triples:
            out[off2:] = np.concatenate(oV)
        return out

    def run(self, y0, vecs, pairs=(), triples=(), steps=1600, method="rk4", rtol=1e-12, atol=1e-14):
        """Integrate one period. Returns dict with 'y', 'U' (first order), 'B' {pair: vec}, 'C' {triple: vec}."""
        pairs = [tuple(p) for p in pairs]
        for (i, j, l) in triples:
            for p in ((i, j), (i, l), (j, l)):
                if p not in pairs:
                    pairs.append(p)
        dim = 2 * self.m
        nv = len(vecs)
        Z0 = np.concatenate([np.asarray(y0, complex)] + [np.asarray(v, complex) for v in vecs] +
                            [np.zeros(dim, complex)] * (len(pairs) + len(triples)))
        T = self.s.T
        if method == "rk4":
            h = T / steps
            Z = Z0.copy()
            for k in range(steps):
                t = k * h
                k1 = self._rhs(t, Z, nv, pairs, triples)
                k2 = self._rhs(t + h / 2, Z + h / 2 * k1, nv, pairs, triples)
                k3 = self._rhs(t + h / 2, Z + h / 2 * k2, nv, pairs, triples)
                k4 = self._rhs(t + h, Z + h * k3, nv, pairs, triples)
                Z = Z + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        else:
            sol = solve_ivp(lambda t, z: self._rhs(t, z, nv, pairs, triples), (0, T), Z0, method=method,
                            rtol=rtol, atol=atol)
            Z = sol.y[:, -1]
        U = Z[dim:dim + nv * dim].reshape(nv, dim)
        off = dim + nv * dim
        W = Z[off:off + len(pairs) * dim].reshape(len(pairs), dim)
        V = Z[off + len(pairs) * dim:].reshape(len(triples), dim)
        return {"y": Z[:dim].real, "U": U, "B": {p: W[k] for k, p in enumerate(pairs)},
                "C": {t: V[k] for k, t in enumerate(triples)}}


def critical_vectors(A):
    """q (|q|=1) for the eigenvalue of largest modulus with Im > 0, and p with <p,q> = 1."""
    w, V = np.linalg.eig(A)
    cand = [i for i in range(len(w)) if w[i].imag > 1e-12]
    i = max(cand, key=lambda k: abs(w[k]))
    mu = w[i]
    q = V[:, i] / np.linalg.norm(V[:, i])
    wl, Vl = np.linalg.eig(A.T)
    j = int(np.argmin(np.abs(wl - np.conj(mu))))
    p = Vl[:, j]
    p = p / np.conj(np.vdot(p, q))  # vdot(p, q) = conj(p).q
    return mu, q, p


def ns_coefficient(A, Bf, Cf, mu=None, q=None, p=None):
    """c1 and d for map derivatives given as callables Bf(a,b), Cf(a,b,c)."""
    if q is None:
        mu, q, p = critical_vectors(A)
    th = np.angle(mu)
    n = A.shape[0]
    qb = np.conj(q)
    Bqqb = Bf(q, qb)
    Bqq = Bf(q, q)
    h1 = np.linalg.solve(np.eye(n) - A, Bqqb)
    h2 = np.linalg.solve(np.exp(2j * th) * np.eye(n) - A, Bqq)
    c1 = 0.5 * np.vdot(p, Cf(q, q, qb) + 2 * Bf(q, h1) + Bf(qb, h2))
    d = float(np.real(np.exp(-1j * th) * c1))
    return {"mu": mu, "theta": float(th), "abs_mu": float(abs(mu)), "c1": c1, "d": d,
            "rotation_shift_coefficient": float(np.imag(np.exp(-1j * th) * c1)), "q": q, "p": p,
            "terms": {"C": np.vdot(p, Cf(q, q, qb)) / 2, "B_h1": np.vdot(p, Bf(q, h1)),
                      "B_h2": np.vdot(p, Bf(qb, h2)) / 2}}


def fput_ns_coefficient(sys, y_star, M, steps=1600, method="rk4"):
    """First Lyapunov coefficient of the NS point of the period map of `sys` at fixed point y_star."""
    tay = Taylor(sys)
    mu, q, p = critical_vectors(M)
    qb = np.conj(q)
    th = np.angle(mu)
    n = M.shape[0]
    R = tay.run(y_star, [q, qb], pairs=[(0, 0), (0, 1)], triples=[(0, 0, 1)], steps=steps, method=method)
    Bqq, Bqqb, Cqqqb = R["B"][(0, 0)], R["B"][(0, 1)], R["C"][(0, 0, 1)]
    h1 = np.linalg.solve(np.eye(n) - M, Bqqb)
    h2 = np.linalg.solve(np.exp(2j * th) * np.eye(n) - M, Bqq)
    R2 = tay.run(y_star, [q, h1, qb, h2], pairs=[(0, 1), (2, 3)], steps=steps, method=method)
    Bqh1, Bqbh2 = R2["B"][(0, 1)], R2["B"][(2, 3)]
    c1 = 0.5 * np.vdot(p, Cqqqb + 2 * Bqh1 + Bqbh2)
    d = float(np.real(np.exp(-1j * th) * c1))
    return {"mu": mu, "theta": float(th), "abs_mu": float(abs(mu)), "c1": c1, "d": d,
            "rotation_shift_coefficient": float(np.imag(np.exp(-1j * th) * c1)), "q": q, "p": p,
            "terms_in_d": {"C(q,q,qb)/2": float(np.real(np.exp(-1j * th) * np.vdot(p, Cqqqb) / 2)),
                           "B(q,h1)": float(np.real(np.exp(-1j * th) * np.vdot(p, Bqh1))),
                           "B(qb,h2)/2": float(np.real(np.exp(-1j * th) * np.vdot(p, Bqbh2) / 2))},
            "first_order_check_supdiff_U_vs_Mq": float(np.max(np.abs(R["U"][0] - M @ q)))}
