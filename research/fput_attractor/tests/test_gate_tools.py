"""Tests for the validation-gate tools: phase-reset DOP853, tensor model with knockouts, edge tracking."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("NUMBA_CACHE_DIR", str(ROOT / ".numba_cache"))
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from fputv.edge import bisect_edge, separation_rate, track_edge  # noqa: E402
from fputv.floquet import newton_orbit, multipliers  # noqa: E402
from fputv.integrate import scipy_strobe, scipy_strobe_segmented  # noqa: E402
from fputv.model import FPUT  # noqa: E402
from fputv.tensor_model import TensorFPUT, coupling_tensor, knock  # noqa: E402


def test_segmented_dop853_equals_absolute_time():
    s = FPUT(0.0045)
    y0 = np.random.default_rng(4).uniform(-.3, .3, 16)
    a, _ = scipy_strobe_segmented(s, y0, 30, segment=7)
    b, _ = scipy_strobe(s, y0, 30, rtol=1e-12, atol=1e-14)
    assert np.max(np.abs(a - b)) < 1e-10


def test_coupling_tensor_symmetric_and_selection_rule():
    C = coupling_tensor()
    assert np.max(np.abs(C - C.transpose(1, 0, 2))) < 1e-14 and np.max(np.abs(C - C.transpose(2, 1, 0))) < 1e-14
    for k, i, j in zip(*np.nonzero(np.abs(C) > 1e-12)):
        a, b, c = k + 1, i + 1, j + 1
        assert any((x % 18) == 0 for x in (a + b + c, a + b - c, a - b + c, -a + b + c))
    Ck = knock(C, [(2, 3, 5)])
    for p in [(1, 2, 4), (2, 1, 4), (4, 1, 2), (4, 2, 1), (1, 4, 2), (2, 4, 1)]:
        assert Ck[p] == 0.0
    assert Ck[0, 0, 1] == C[0, 0, 1]


def test_tensor_model_equals_physical_model_monodromy():
    s = FPUT(0.0045)
    y, M, _ = newton_orbit(s, np.zeros(16), 800)
    tm = TensorFPUT()
    Yq = np.r_[s.B.T @ y[:8], s.B.T @ y[8:]]
    yq, Mq, ok = tm.newton(Yq, 0.0045, 800)
    assert ok and np.max(np.abs(yq - Yq)) < 1e-9
    assert abs(np.max(np.abs(multipliers(Mq))) - np.max(np.abs(multipliers(M)))) < 1e-10


def _toy(beta=-0.01, dd=1.0, e=1.0, th=0.7):
    """z -> e^{i th} z (1 + beta + dd|z|^2 - e|z|^4): attracting origin, unstable circle r_u, stable circle r_s."""
    def step(X):
        z = X[:, 0] + 1j * X[:, 1]
        a = np.abs(z) ** 2
        z = np.exp(1j * th) * z * (1 + beta + dd * a - e * a * a)
        return np.c_[z.real, z.imag]
    disc = np.sqrt(dd * dd + 4 * e * beta)
    ru = np.sqrt((dd - disc) / (2 * e))
    rs = np.sqrt((dd + disc) / (2 * e))
    return step, ru, rs


def test_edge_tracking_finds_unstable_circle_of_toy_map():
    step, ru, rs = _toy()

    def decide(X):
        X = np.array(X, float)
        lab = ["U"] * len(X)
        for _ in range(5000):
            X = step(X)
            r = np.hypot(X[:, 0], X[:, 1])
            for i in range(len(X)):
                if lab[i] == "U":
                    lab[i] = "A" if r[i] < 0.1 * ru else ("B" if abs(r[i] - rs) < 1e-3 else "U")
            if "U" not in lab:
                break
        return lab

    a, b, st = bisect_edge(np.array([0.05, 0.0]), np.array([0.9, 0.0]), decide, 1e-12)
    assert st["final_gap"] <= 1e-12
    H, seps, stats = track_edge(np.array([0.05, 0.0]), np.array([0.9, 0.0]), decide, step, tol=1e-12, delta=1e-6, total=600)
    r = np.hypot(H[100:, 0], H[100:, 1])
    assert np.max(np.abs(r - ru)) < 1e-6
    rate, _ = separation_rate(seps)
    # radial map r -> r(1+beta+dd r^2-e r^4); on the invariant circle the factor is 1, so the radial
    # derivative is 1 + 2 dd a - 4 e a^2 with a = r_u^2 (dd = e = 1 here)
    a2 = ru ** 2
    expected = np.log(1 + 2 * a2 - 4 * a2 * a2)
    assert rate is not None and abs(rate - expected) < 0.1 * expected
