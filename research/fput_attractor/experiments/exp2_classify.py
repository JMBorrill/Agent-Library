"""Experiment 2 - classify the modulated state at F = 0.0045 (and spot checks at 0.0044, 0.0050).

Diagnostics (each with its stated limitation in fputv/diagnostics.py and the report):
  stroboscopic section geometry and invariant-circle Fourier fit; rotation number and windowed
  NAFF frequencies (frequency diffusion); line-spectrum test; exact-periodicity search plus a
  rational-approximation bound on any phase-locked period; window drift over 2^17 periods
  (transient bound); Z2-symmetry of the attractor; full Lyapunov spectrum (16 exponents) at two
  step sizes, validated on the drive-locked orbit against ln|mu|/T and the conformal-symplectic
  pairing rule lambda_i + lambda_(17-i) = -eta.
"""
import os
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("NUMBA_CACHE_DIR", str(ROOT / ".numba_cache"))
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))

import json  # noqa: E402

import numpy as np  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402

from fputv import diagnostics as D  # noqa: E402
from fputv.floquet import multipliers, newton_orbit  # noqa: E402
from fputv.integrate import lyapunov_qr, strobe  # noqa: E402
from fputv.io import Timer, save, save_npz  # noqa: E402
from fputv.model import FPUT  # noqa: E402

TRANSIENT = 5000
LONG = 2 ** 17


def lyap(s, y0, periods, steps, nvec=16):
    y, cum = lyapunov_qr(np.asarray(y0, float), periods, steps, nvec, *s.args)
    t = (np.arange(1, periods + 1) * s.T)[:, None]
    run = cum / t
    h = periods // 2
    # Primary estimator: slope of the accumulated log-stretch over the second half, which removes
    # the O(1)/t bias from the arbitrary initial tangent frame (Benettin transient).
    lam = (cum[-1] - cum[h - 1]) / ((periods - h) * s.T)
    q = periods // 4
    lam_q3 = (cum[3 * q - 1] - cum[h - 1]) / (q * s.T)
    lam_q4 = (cum[-1] - cum[3 * q - 1]) / ((periods - 3 * q) * s.T)
    return {"exponents_per_time": lam, "estimator": "second-half slope",
            "third_quarter_slope": lam_q3, "fourth_quarter_slope": lam_q4,
            "cumulative_average_cum_over_t": run[-1],
            "lambda1_running_at_[1k,2k,5k,10k,end]": [float(run[min(k, periods) - 1, 0]) for k in (1000, 2000, 5000, 10000, periods)],
            "sum": float(lam.sum()), "pair_sums_i_plus_17-i": (lam + lam[::-1])[:8],
            "periods": periods, "steps": steps}, y, run[:, :3]


def rational_bound(rho, err, qmax=10 ** 6):
    """Smallest denominator q <= qmax with |rho - p/q| <= err (periodic orbit of period q would be
    indistinguishable from the measurement); None if no such q."""
    x = abs(rho)
    best = None
    for q in range(1, qmax + 1):
        p = round(x * q)
        if abs(x - p / q) <= err:
            best = q
            break
    cf = Fraction(x).limit_denominator(10 ** 7)
    return {"smallest_period_consistent_with_measurement": best, "limit_denominator_1e7": [cf.numerator, cf.denominator]}


def classify_F(F, tm, long_periods, lyap_periods, lyap_steps, steps_long=300):
    s = FPUT(F)
    y_lock, M, _ = newton_orbit(s, np.zeros(16), 800)
    mu = multipliers(M)
    Y0 = strobe(s, np.zeros(16), TRANSIENT, steps_long)
    Y = strobe(s, Y0[-1], long_periods, steps_long)
    tm.mark(f"F{F}_long_run")
    E = s.energies(Y)
    res = {"F": F, "locked_orbit_max_abs_mu": float(abs(mu[0])),
           "final_supdist_to_locked": float(np.max(np.abs(Y[-1] - y_lock))),
           "rotation": D.rotation_number(Y),
           "frequency_diffusion_8win": D.frequency_diffusion(Y, nwin=8),
           "window_drift_E1": D.window_drift(E[:, 0], nwin=8),
           "window_drift_E2": D.window_drift(E[:, 1], nwin=8)}
    rho = res["frequency_diffusion_8win"]["window_frequencies"][-1]
    res["line_spectrum_E1"] = D.line_spectrum(E[-2 ** 16:, 0], rho)
    res["line_spectrum_Q1"] = D.line_spectrum(s.modal(Y[-2 ** 16:])[0][:, 0], rho)
    res["invariant_circle_fit_last16384"] = D.invariant_circle_fit(Y[-2 ** 14:])
    res["recurrence_lag_le_2000_tol1e-6"] = D.recurrence_periods(Y[-8192:], 2000, 1e-6)
    # Z2 symmetry of the attractor: is S y((n+1/2)T) on the stroboscopic attractor?
    Ys, Yh = strobe(s, Y[-1], 4000, steps_long, half=True)
    tree = cKDTree(Y[-2 ** 15:])
    d_img, _ = tree.query((s.S @ Yh.T).T)
    d_self, _ = cKDTree(Y[-2 ** 15:]).query(Ys)
    res["z2_symmetry"] = {"median_dist_of_S_image_to_attractor": float(np.median(d_img)),
                          "max_dist_of_S_image": float(d_img.max()),
                          "median_dist_of_new_samples_to_attractor_(sampling_scale)": float(np.median(d_self))}
    tm.mark(f"F{F}_diagnostics")
    L, ylast, run = lyap(s, Y[-1], lyap_periods, lyap_steps)
    res["lyapunov"] = L
    tm.mark(f"F{F}_lyapunov")
    return s, y_lock, mu, Y, res, run


def main():
    tm = Timer()
    out = {}
    # --- validation of the Lyapunov code on the stable drive-locked orbit at F = 0.0045 -------
    s = FPUT(0.0045)
    y_lock, M, _ = newton_orbit(s, np.zeros(16), 800)
    mu = multipliers(M)
    Lk, _, _ = lyap(s, y_lock, 10000, 200)
    floq = np.sort(np.log(np.abs(mu)) / s.T)[::-1]
    lk = np.sort(Lk["exponents_per_time"])[::-1]
    # Individual exponents inside degenerate (equal-modulus) groups converge only as O(log(cond)/t);
    # partial sums over complete groups (k = 2, 14, 16 here) are the well-posed comparison.
    out["lyapunov_validation_locked_orbit"] = {
        "lyapunov": lk, "floquet_ln|mu|/T": floq, "periods": 10000,
        "lambda1_abs_diff": float(abs(lk[0] - floq[0])),
        "partial_sum_abs_diff_k2_k14_k16": [float(abs(lk[:k].sum() - floq[:k].sum())) for k in (2, 14, 16)],
        "max_individual_abs_diff": float(np.max(np.abs(lk - floq))),
        "sum": Lk["sum"], "expected_sum_-N_eta": -8 * s.eta}
    tm.mark("lyap_validation")

    # --- main classification at F = 0.0045 ----------------------------------------------------
    s, y_lock, mu, Y, res, run = classify_F(0.0045, tm, LONG, 20000, 200)
    # step-size convergence of rotation frequency and Lyapunov spectrum
    Y2 = strobe(s, Y[-1], 2 ** 14, 600)
    P, _ = D.pca_plane(Y2)
    rho600 = abs(D.refined_frequency(P[:, 0] + 1j * P[:, 1]))  # PCA orientation is arbitrary: use |rho|
    P, _ = D.pca_plane(Y[-2 ** 14:])
    rho300 = abs(D.refined_frequency(P[:, 0] + 1j * P[:, 1]))
    L400, _, run400 = lyap(s, Y2[-1], 20000, 400)
    res["step_convergence"] = {"rho_RK4_300": rho300, "rho_RK4_600": rho600, "abs_diff": abs(rho300 - rho600),
                               "lyapunov_RK4_400": L400,
                               "max_abs_diff_exponents_200_vs_400": float(np.max(np.abs(
                                   res["lyapunov"]["exponents_per_time"] - L400["exponents_per_time"])))}
    fd = res["frequency_diffusion_8win"]
    rho_rich = rho600 + (rho600 - rho300) / 15  # RK4 global error O(h^4)
    res["abs_rho"] = {"RK4_300": rho300, "RK4_600": rho600, "richardson": rho_rich,
                      "discretisation_error_estimate": abs(rho600 - rho300) / 15,
                      "window_drift_at_fixed_discretisation": fd["max_abs_drift"],
                      "exp1_DOP853_reference": 0.02404185}
    # Phase-locking test is done at fixed discretisation: a periodic orbit of the discrete map would
    # have an exactly rational, window-independent rho; the window drift bounds |rho - p/q|.
    res["phase_locking_bound_fixed_discretisation"] = rational_bound(rho300, max(fd["max_abs_drift"], 1e-13))
    tm.mark("F0.0045_convergence")
    out["F0.0045"] = res
    save_npz("exp2_F0.0045_strobe_last16384", Y=Y[-16384:], E=s.energies(Y[-16384:]), y_lock=y_lock,
             lyap_running_200=run, lyap_running_400=run400)

    # --- spot checks at other drive amplitudes (from rest) --------------------------------------
    for F in (0.0044, 0.0050):
        s2, yl2, mu2, Y2, r2, _ = classify_F(F, tm, 2 ** 15, 8000, 200)
        out[f"F{F}"] = r2
        save_npz(f"exp2_F{F}_strobe_last4096", Y=Y2[-4096:], E=s2.energies(Y2[-4096:]))

    save("exp2_classification", {"config": {"N": 8, "alpha": .25, "eta": .0025, "Omega": .347,
                                            "transient_periods": TRANSIENT, "long_periods_F0.0045": LONG,
                                            "initial_condition": "rest (zero)"}, "results": out}, tm)
    r = out["F0.0045"]
    print(json.dumps({"rho": r["rotation"]["rho"], "fd": r["frequency_diffusion_8win"]["max_abs_drift"],
                      "line": r["line_spectrum_E1"]["power_fraction_on_predicted_lines"],
                      "circle": r["invariant_circle_fit_last16384"], "lyap": r["lyapunov"]["exponents_per_time"][:4],
                      "pairs": r["lyapunov"]["pair_sums_i_plus_17-i"], "sym": r["z2_symmetry"],
                      "lockbound": r["phase_locking_bound_fixed_discretisation"], "abs_rho": r["abs_rho"],
                      "conv": r["step_convergence"]["max_abs_diff_exponents_200_vs_400"],
                      "valid": out["lyapunov_validation_locked_orbit"]}, indent=1, default=str))


if __name__ == "__main__":
    main()
