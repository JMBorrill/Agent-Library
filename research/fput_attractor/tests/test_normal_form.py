"""Validation of the Neimark-Sacker coefficient code (formula constants/sign checked by iteration)."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("NUMBA_CACHE_DIR", str(ROOT / ".numba_cache"))
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pytest  # noqa: E402

from fputv.floquet import newton_orbit, period_map  # noqa: E402
from fputv.integrate import scipy_strobe  # noqa: E402
from fputv.model import FPUT  # noqa: E402
from fputv.normal_form import Taylor, critical_vectors, ns_coefficient  # noqa: E402


def make_test_map(seed, theta=0.9, n=4):
    """x -> A(beta) x + B(x,x)/2 + C(x,x,x)/6 in R^n, A similar to diag((1+beta)R(theta), 0.5 R(2.0), ...)."""
    rng = np.random.default_rng(seed)
    S = np.eye(n) + 0.3 * rng.standard_normal((n, n))
    Bt = 0.4 * rng.standard_normal((n, n, n)); Bt = (Bt + Bt.transpose(0, 2, 1)) / 2
    Ct = 0.4 * rng.standard_normal((n, n, n, n))
    Ct = sum(Ct.transpose(0, *p) for p in [(1, 2, 3), (1, 3, 2), (2, 1, 3), (2, 3, 1), (3, 1, 2), (3, 2, 1)]) / 6

    def A(beta):
        R = lambda a, r: r * np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])  # noqa: E731
        L = np.zeros((n, n)); L[:2, :2] = R(theta, 1 + beta)
        for k in range(2, n, 2):
            L[k:k + 2, k:k + 2] = R(2.0 + k, 0.5)
        return S @ L @ np.linalg.inv(S)

    Bf = lambda a, b: np.einsum("ijk,j,k->i", Bt, a, b)  # noqa: E731
    Cf = lambda a, b, c: np.einsum("ijkl,j,k,l->i", Ct, a, b, c)  # noqa: E731
    return A, Bf, Cf


def iterate(A, Bf, Cf, beta, x, n):
    M = A(beta)
    for _ in range(n):
        x = M @ x + Bf(x, x) / 2 + Cf(x, x, x) / 6
        if not np.all(np.abs(x) < 10):
            break
    return x


def oriented_map(seed, want_sign):
    A, Bf, Cf = make_test_map(seed)
    res = ns_coefficient(A(0.0), Bf, Cf)
    if np.sign(res["d"]) != want_sign:
        Cf = (lambda f: (lambda a, b, c: -f(a, b, c)))(Cf)
        res = ns_coefficient(A(0.0), Bf, Cf)
    return A, Bf, Cf, res


@pytest.mark.parametrize("seed", [3, 11, 5])
def test_supercritical_circle_radius_matches_minus_beta_over_d(seed):
    A, Bf, Cf, res = oriented_map(seed, -1)
    if res["d"] >= 0:
        pytest.skip("sign reversal did not give d < 0")
    errs = []
    for beta in (4e-4, 1e-4):
        r0 = np.sqrt(-beta / res["d"])
        x = iterate(A, Bf, Cf, beta, 2 * np.real(r0 * 1.1 * res["q"]), int(20 / beta))
        zs = []
        M = A(beta)
        for _ in range(2000):
            x = M @ x + Bf(x, x) / 2 + Cf(x, x, x) / 6
            zs.append(abs(np.vdot(res["p"], x)))
        errs.append(abs(np.mean(zs) / r0 - 1))
    assert errs[1] < 0.01 and errs[1] < errs[0] + 1e-3, errs


@pytest.mark.parametrize("seed", [1, 11])
def test_subcritical_unstable_circle_at_predicted_radius(seed):
    A, Bf, Cf, res = oriented_map(seed, +1)
    if res["d"] <= 0:
        pytest.skip("sign reversal did not give d > 0")
    beta = -2e-4
    r0 = np.sqrt(-beta / res["d"])
    inside = iterate(A, Bf, Cf, beta, 2 * np.real(0.8 * r0 * res["q"]), 60000)
    outside = iterate(A, Bf, Cf, beta, 2 * np.real(1.25 * r0 * res["q"]), 60000)
    assert abs(np.vdot(res["p"], inside)) < 0.3 * r0
    assert not np.all(np.abs(outside) < 10) or abs(np.vdot(res["p"], outside)) > 3 * r0


def test_quadratic_terms_matter_in_test_map():
    """Sensitivity: dropping the B-terms changes d appreciably, so the test above exercises them."""
    A, Bf, Cf = make_test_map(3)
    full = ns_coefficient(A(0.0), Bf, Cf)["d"]
    noB = ns_coefficient(A(0.0), lambda a, b: 0 * a, Cf)["d"]
    assert abs(full - noB) > 0.2 * abs(full)


@pytest.fixture(scope="module")
def fput_orbit():
    s = FPUT(0.0045)
    y, M, _ = newton_orbit(s, np.zeros(16), 800)
    _, Md = period_map(s, y, method="DOP853")
    return s, y, Md


def test_first_order_and_second_order_match_finite_differences(fput_orbit):
    s, y, M = fput_orbit
    mu, q, p = critical_vectors(M)
    u, w = q.real / np.linalg.norm(q.real), q.imag / np.linalg.norm(q.imag)
    R = Taylor(s).run(y, [u, w], pairs=[(0, 0), (0, 1)], triples=[(0, 0, 0)], steps=1600)
    assert np.max(np.abs(R["U"][0] - M @ u)) < 1e-6
    P = lambda x: scipy_strobe(s, x, 1, rtol=1e-13, atol=1e-15)[0][-1]  # noqa: E731
    e = 1e-3
    Buu = (P(y + e * u) - 2 * P(y) + P(y - e * u)) / e ** 2
    Buw = (P(y + e * u + e * w) - P(y + e * u - e * w) - P(y - e * u + e * w) + P(y - e * u - e * w)) / (4 * e ** 2)
    scale = np.max(np.abs(R["B"][(0, 0)]))
    assert np.max(np.abs(R["B"][(0, 0)] - Buu)) < 1e-4 * scale
    assert np.max(np.abs(R["B"][(0, 1)] - Buw)) < 1e-4 * max(scale, np.max(np.abs(Buw)))
    e = 1e-2
    Cuuu = (P(y + 2 * e * u) - 2 * P(y + e * u) + 2 * P(y - e * u) - P(y - 2 * e * u)) / (2 * e ** 3)
    assert np.max(np.abs(R["C"][(0, 0, 0)] - Cuuu)) < 2e-3 * np.max(np.abs(R["C"][(0, 0, 0)]))
