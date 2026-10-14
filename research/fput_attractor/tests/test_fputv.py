"""Independent tests for the verification toolkit (run: python -m pytest from research/fput_attractor)."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("NUMBA_CACHE_DIR", str(ROOT / ".numba_cache"))
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pytest  # noqa: E402

from fputv import diagnostics as D  # noqa: E402
from fputv.floquet import critical_F, fd_monodromy, multipliers, newton_orbit, period_map  # noqa: E402
from fputv.hybrid import hybrid_monodromy  # noqa: E402
from fputv.integrate import batch, lyapunov_qr, scipy_strobe, strobe  # noqa: E402
from fputv.model import FPUT, sine_basis  # noqa: E402

RNG = np.random.default_rng(12345)
ETA, T = 0.0025, 2 * np.pi / 0.347


def baseline_modules():
    sys.path.insert(0, str(ROOT / "baseline/Nonlinear_Waves_Stage1"))
    import stage1
    return stage1


# ---------------------------------------------------------------- governing equations --------
def test_physical_force_matches_hand_written_fput_law():
    s = FPUT(0.004)
    q, p, t = RNG.uniform(-.4, .4, 8), RNG.uniform(-.3, .3, 8), 1.234
    qb = np.r_[0.0, q, 0.0]
    acc = np.empty(8)
    for n in range(1, 9):
        rp, rm = qb[n + 1] - qb[n], qb[n] - qb[n - 1]
        acc[n - 1] = (rp + .25 * rp ** 2) - (rm + .25 * rm ** 2) - ETA * p[n - 1] + 0.004 * np.cos(.347 * t)
    assert np.max(np.abs(s.rhs(t, np.r_[q, p])[8:] - acc)) < 1e-14


@pytest.mark.parametrize("modes", [None, (1, 2, 3, 4), (1, 2, 4, 6), (1, 2, 3, 4, 5)])
def test_projected_force_equals_baseline_C_tensor(modes):
    """Our truncation (projected physical force) equals the baseline's C[k,i,j] Galerkin form."""
    st = baseline_modules()
    _, _, w, c, g = st.matrices(8)
    idx = np.arange(8) if modes is None else np.array(modes) - 1
    s = FPUT(0.0045, modes=modes)
    B = sine_basis(8)
    Q, P = RNG.uniform(-.5, .5, len(idx)), RNG.uniform(-.3, .3, len(idx))
    ref = st.dynamics(.77, np.r_[Q, P], w[idx], np.ascontiguousarray(c[np.ix_(idx, idx, idx)]), g[idx],
                      .25, ETA, .0045, .347)
    y = np.r_[B[:, idx] @ Q, B[:, idx] @ P] if modes is None else np.r_[Q, P]
    ours = s.rhs(.77, y)
    if modes is None:
        ours = np.r_[B.T @ ours[:8], B.T @ ours[8:]]
    assert np.max(np.abs(ours - ref)) < 1e-13


@pytest.mark.parametrize("modes", [None, (1, 2, 3, 4)])
def test_jacobian_matches_finite_differences(modes):
    s = FPUT(0.0045, modes=modes)
    y = RNG.uniform(-.5, .5, s.dim)
    J = s.jac(2.0, y)
    eps = 1e-6
    Jfd = np.column_stack([(s.rhs(2.0, y + eps * e) - s.rhs(2.0, y - eps * e)) / (2 * eps) for e in np.eye(s.dim)])
    assert np.max(np.abs(J - Jfd)) < 1e-8


@pytest.mark.parametrize("modes", [None, (1, 2, 3, 4), (1, 2, 4, 6)])
def test_z2_spatiotemporal_symmetry(modes):
    """S f(t, y) = f(t + T/2, S y) with S: q_n -> -q_{N+1-n} (odd modes flip sign)."""
    s = FPUT(0.0045, modes=modes)
    y = RNG.uniform(-.5, .5, s.dim)
    assert np.max(np.abs(s.S @ s.rhs(.3, y) - s.rhs(.3 + T / 2, s.S @ y))) < 1e-13
    assert np.allclose(s.S @ s.S, np.eye(s.dim))


@pytest.mark.parametrize("modes", [None, (1, 2, 3, 4)])
def test_flow_is_conformally_symplectic(modes):
    """Uniform damping: M^T J M = exp(-eta t) J for the period map at ANY state (not only orbits).
    Holds to round-off for DOP853; RK4 is not conformally symplectic, so its defect must converge."""
    s = FPUT(0.0045, modes=modes)
    y = RNG.uniform(-.4, .4, s.dim)
    m = s.m
    J = np.block([[np.zeros((m, m)), np.eye(m)], [-np.eye(m), np.zeros((m, m))]])
    c = np.exp(-ETA * T)
    _, M = period_map(s, y, method="DOP853")
    assert np.max(np.abs(M.T @ J @ M - c * J)) < 1e-11
    assert abs(np.linalg.det(M) - c ** m) < 1e-11
    dev = [np.max(np.abs(period_map(s, y, n)[1].T @ J @ period_map(s, y, n)[1] - c * J)) for n in (400, 800)]
    assert dev[0] / dev[1] > 12


# ---------------------------------------------------------------- integrators ----------------
def test_rk4_fourth_order_against_dop853():
    s = FPUT(0.0045)
    y0 = RNG.uniform(-.3, .3, 16)
    ref, _ = scipy_strobe(s, y0, 5, rtol=1e-13, atol=1e-15)
    errs = [np.max(np.abs(strobe(s, y0, 5, n)[-1] - ref[-1])) for n in (100, 200, 400)]
    ratios = [errs[0] / errs[1], errs[1] / errs[2]]
    assert all(12 < r < 20 for r in ratios), ratios


def test_lsoda_and_dop853_agree():
    s = FPUT(0.0045)
    y0 = RNG.uniform(-.3, .3, 16)
    a, _ = scipy_strobe(s, y0, 10, method="DOP853", rtol=1e-12, atol=1e-14)
    b, _ = scipy_strobe(s, y0, 10, method="LSODA", rtol=1e-12, atol=1e-14)
    assert np.max(np.abs(a - b)) < 1e-8


def test_batch_matches_serial():
    s = FPUT(0.0045)
    Y0 = RNG.uniform(-.3, .3, (3, 16))
    W = batch(s, Y0, 20, 200, 5)
    for i in range(3):
        assert np.max(np.abs(W[i] - strobe(s, Y0[i], 20, 200)[-5:])) < 1e-13


# ---------------------------------------------------------------- Floquet ------------------
@pytest.fixture(scope="module")
def locked():
    s = FPUT(0.0045)
    y, M, info = newton_orbit(s, np.zeros(16), 800)
    return s, y, M, info


def test_newton_converges_and_matches_baseline_multiplier(locked):
    s, y, M, info = locked
    assert info["converged"] and info["residual"] < 1e-12
    assert abs(abs(multipliers(M)[0]) - 0.996154) < 2e-6  # baseline RK4/360: 0.996153725


def test_variational_monodromy_matches_finite_differences(locked):
    s, y, M, _ = locked
    Mfd = fd_monodromy(s, y, eps=1e-6)
    assert np.max(np.abs(M - Mfd)) < 1e-6
    assert abs(abs(multipliers(Mfd)[0]) - abs(multipliers(M)[0])) < 1e-7


def test_half_period_map_squares_to_monodromy(locked):
    s, y, M, _ = locked
    G, DG = period_map(s, y, 800, half=True)
    assert np.max(np.abs(G - y)) < 1e-10  # locked orbit is Z2-symmetric
    assert np.max(np.abs(DG @ DG - M)) < 1e-10


def test_multiplier_pairing(locked):
    s, y, M, _ = locked
    _, Md = period_map(s, y, method="DOP853")
    a = np.sort(np.abs(multipliers(Md)))
    assert np.max(np.abs(a * a[::-1] - np.exp(-ETA * T))) < 1e-10
    a = np.sort(np.abs(multipliers(M)))  # RK4/800: pairing holds to its discretisation error
    assert np.max(np.abs(a * a[::-1] - np.exp(-ETA * T))) < 1e-6


def test_critical_F_full_chain_reproduces_baseline():
    s0 = FPUT(0.0)
    y = np.zeros(16)
    for F in np.arange(0, 0.0046, 2e-4):
        y, _, _ = newton_orbit(s0.with_F(F), y, 400)
    Fc, _, mu, _ = critical_F(s0, (0.0046, 0.0048), y, steps=400)
    assert abs(abs(mu[0]) - 1) < 1e-10
    assert abs(Fc - 0.0046931590) < 2e-8  # baseline RK4/720; converged value 0.00469315823


def test_hybrid_monodromy_reduces_to_standard(locked):
    s, y, M, _ = locked
    _, W = hybrid_monodromy(y, 800, s.Phi, True, np.eye(8), np.eye(8), .25, ETA, .0045, .347)
    assert np.max(np.abs(W - M)) < 1e-12


# ---------------------------------------------------------------- Lyapunov -----------------
def test_lyapunov_on_locked_orbit_matches_floquet(locked):
    s, y, M, _ = locked
    _, cum = lyapunov_qr(y, 1500, 200, 16, *s.args)
    lam = np.sort((cum[-1] - cum[749]) / (750 * s.T))[::-1]  # second-half slope: no frame transient
    fl = np.sort(np.log(np.abs(multipliers(M))) / s.T)[::-1]
    # lambda_1,2 belong to a complex pair: only their sum converges quickly
    assert abs(lam[:2].sum() - fl[:2].sum()) < 1e-6
    assert abs(lam[0] - fl[0]) < 3e-5
    assert abs(lam.sum() + 8 * ETA) < 2e-5  # Liouville; residual is RK4/200 damping error


# ---------------------------------------------------------------- diagnostics (synthetic) ---
def synthetic_circle(rho, n=8192, noise=0.0):
    k = np.arange(n)
    th = 2 * np.pi * rho * k + 0.3
    Y = np.c_[np.cos(th), np.sin(th), 0.3 * np.cos(2 * th + .1), 0.2 * np.sin(3 * th)]
    return Y + noise * np.random.default_rng(1).standard_normal(Y.shape)


def test_diagnostics_quasiperiodic_synthetic():
    rho = (np.sqrt(5) - 1) / 50
    Y = synthetic_circle(rho)
    assert abs(abs(D.rotation_number(Y)["rho"]) - rho) < 1e-6
    assert D.frequency_diffusion(Y)["max_abs_drift"] < 1e-9
    P, _ = D.pca_plane(Y)
    assert abs(abs(D.refined_frequency(P[:, 0] + 1j * P[:, 1])) - rho) < 1e-9
    assert D.line_spectrum(Y[:, 2], rho)["power_fraction_on_predicted_lines"] > 0.999
    assert D.invariant_circle_fit(Y, (20,))["relative_rms_residual_by_harmonics"]["20"] < 1e-10
    assert D.recurrence_periods(Y, 200, 1e-6)["period"] is None


def test_diagnostics_detect_periodic_and_broadband():
    Y = synthetic_circle(3 / 37)
    assert D.recurrence_periods(Y, 100, 1e-9)["period"] == 37
    noise = np.random.default_rng(2).standard_normal(8192)
    assert D.line_spectrum(noise, 0.0241)["power_fraction_on_predicted_lines"] < 0.2
    Y2 = synthetic_circle(0.0241, noise=0.05)
    assert D.invariant_circle_fit(Y2, (20,))["relative_rms_residual_by_harmonics"]["20"] > 1e-2
