"""Experiment 4 - independent verification of the Floquet thresholds and one narrow mechanism test.

Part A (verification). Critical drive F_c where max |mu| = 1 on the drive-locked branch, for the
full N=8 chain (physical coordinates) and the {1,2,3,4} Galerkin truncation (projected force),
by four routes: RK4 variational map (200-1600 steps, Richardson), RK4 half-period symmetric map
G = S o P_{T/2} with mu = lambda^2, DOP853 variational map, and finite-difference monodromy.
Structural checks: det M = exp(-m eta T); multipliers pair as |mu_i||mu_j| = exp(-eta T).

Part B (mechanism; predeclared hypotheses).
  Uniform damping makes the flow conformally symplectic, so all multipliers sit on
  |mu| = exp(-eta T/2) until two pairs collide (Krein collision at F_K) and split radially;
  F_c is reached when the outer member reaches 1.
  H4a: F_c(8) - F_c(4) is dominated by the shift in F_K, i.e.
       |(F_c - F_K)_8 - (F_c - F_K)_4| < 0.25 |F_c(8) - F_c(4)|.
  H4b: a single omitted mode k in {5..8} added to {1,2,3,4} recovers >= 50% of the gap.
       Counter-hypothesis: the shift is cumulative over several omitted modes.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("NUMBA_CACHE_DIR", str(ROOT / ".numba_cache"))
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))

import json  # noqa: E402

import numpy as np  # noqa: E402
from scipy.optimize import brentq  # noqa: E402

from fputv.floquet import critical_F, fd_monodromy, multipliers, newton_orbit  # noqa: E402
from fputv.io import Timer, save  # noqa: E402
from fputv.model import FPUT  # noqa: E402

BASELINE = {"full": 0.0046931590, "modes1234": 0.0050846454}


def branch_seed(s0, F_target, steps=400, dF=2e-4):
    y = np.zeros(s0.dim)
    for F in np.r_[np.arange(0.0, F_target, dF), F_target]:
        y, M, info = newton_orbit(s0.with_F(F), y, steps)
        if not info["converged"]:
            raise RuntimeError(f"branch lost at F={F}")
    return y


def modal_fractions(s, v):
    """Fraction of (linear) modal energy of a complex Floquet eigenvector per normal mode 1..N."""
    q = v[: s.m] @ s.Phi.T if s.m else None
    p = v[s.m:] @ s.Phi.T
    Q = s.B.T @ q; P = s.B.T @ p
    e = 0.5 * (np.abs(P) ** 2 + (s.omega * np.abs(Q)) ** 2)
    return e / e.sum()


def part_a(tm):
    out = {}
    for label, modes, bracket in (("full", None, (0.0046, 0.0048)), ("modes1234", (1, 2, 3, 4), (0.0050, 0.0052))):
        s0 = FPUT(0.0, modes=modes)
        seed = branch_seed(s0, bracket[0])
        r = {"rk4_full_period": {}, "rk4_half_period_map": {}}
        for n in (200, 400, 800, 1600):
            Fc, y, mu, info = critical_F(s0, bracket, seed, steps=n)
            r["rk4_full_period"][str(n)] = {"F_c": Fc, "mu_crit": [mu[0].real, mu[0].imag], "residual": info["residual"]}
            if n == 1600:
                y1600 = y
        v = [r["rk4_full_period"][str(n)]["F_c"] for n in (200, 400, 800, 1600)]
        r["rk4_richardson_800_1600"] = (16 * v[3] - v[2]) / 15
        r["rk4_successive_diffs"] = list(np.abs(np.diff(v)))
        for n in (400, 800):
            Fc, y, mu, info = critical_F(s0, bracket, seed, steps=n, half=True)
            r["rk4_half_period_map"][str(n)] = {"F_c": Fc, "mu_crit": [mu[0].real, mu[0].imag]}
        tm.mark(f"{label}_rk4")
        # DOP853 variational: brentq with adaptive integration for both orbit and monodromy
        st = {"y": y1600}

        def g(F):
            yy, M, info = newton_orbit(s0.with_F(F), st["y"], method="DOP853", rtol=1e-12, atol=1e-14)
            st["y"] = yy
            return float(abs(multipliers(M)[0]) - 1)

        Fd = brentq(g, v[3] - 2e-7, v[3] + 2e-7, xtol=1e-14)
        sd = s0.with_F(Fd)
        yd, Md, infod = newton_orbit(sd, st["y"], method="DOP853", rtol=1e-12, atol=1e-14)
        mud = multipliers(Md)
        Mfd = fd_monodromy(sd, yd, eps=1e-6)
        mufd = multipliers(Mfd)
        c = np.exp(-sd.eta * sd.T)
        r["dop853"] = {"F_c": Fd, "residual": infod["residual"], "mu_crit": [mud[0].real, mud[0].imag]}
        r["finite_difference_monodromy_at_dop853_Fc"] = {
            "max_abs_mu": float(abs(mufd[0])), "max_entry_diff_vs_variational": float(np.max(np.abs(Mfd - Md)))}
        r["det_M_vs_exp(-m eta T)"] = {"det": float(np.linalg.det(Md)), "predicted": float(c ** (sd.dim // 2))}
        mags = np.sort(np.abs(mud))[::-1]
        r["pairing_max_dev_|mu_i||mu_(2m+1-i)|_minus_exp(-eta T)"] = float(np.max(np.abs(mags * mags[::-1] - c)))
        r["baseline_reported_RK4_720"] = BASELINE[label]
        r["baseline_minus_dop853"] = BASELINE[label] - Fd
        w, V = np.linalg.eig(Md)
        i = int(np.argmax(np.abs(w)))
        r["critical_eigvec_modal_energy_fraction"] = modal_fractions(sd, V[:, i])
        j = int(np.argmin(np.abs(np.abs(w) - c / np.abs(w[i])) + 10 * (np.abs(np.angle(w) - np.angle(w[i])) > 1e-3)))
        r["partner_inner_eigvec_modal_energy_fraction"] = modal_fractions(sd, V[:, j])
        r["base_orbit_modal_energy_fraction"] = sd.energies(yd) / sd.energies(yd).sum()
        out[label] = r
        tm.mark(f"{label}_dop853")
    return out


def krein_and_critical(modes, steps=800, Fmax=0.0066, dF=1e-4):
    """F_K (first departure of max|mu| from exp(-eta T/2) by >1e-4 relative) and F_c on the branch."""
    s0 = FPUT(0.0, modes=modes)
    rc = np.exp(-s0.eta * s0.T / 2)
    y = np.zeros(s0.dim)
    prev = None
    FK = Fc = None
    ys = {}
    scan = []
    for F in np.arange(0.0, Fmax + 1e-12, dF):
        y, M, info = newton_orbit(s0.with_F(F), y, steps)
        if not info["converged"]:
            return {"modes": modes, "branch_lost_at": float(F), "F_K": FK, "F_c": Fc, "scan": scan}
        m = float(abs(multipliers(M)[0]))
        scan.append([float(F), m])
        ys[round(F, 8)] = y.copy()
        if FK is None and m / rc - 1 > 1e-4 and prev is not None:
            ylo = ys[round(prev, 8)]

            def gk(FF):
                yy, MM, _ = newton_orbit(s0.with_F(FF), ylo, steps)
                return abs(multipliers(MM)[0]) / rc - 1 - 1e-4
            FK = brentq(gk, prev, F, xtol=1e-10)
        if Fc is None and m > 1 and prev is not None:
            Fc, _, mu, _ = critical_F(s0, (prev, F), ys[round(prev, 8)], steps=steps, xtol=1e-12)
            theta = float(abs(np.angle(mu[0])))
            break
        prev = F
    return {"modes": modes, "F_K": FK, "F_c": Fc, "theta_crit_rad": theta if Fc else None,
            "F_c_minus_F_K": (Fc - FK) if (Fc and FK) else None, "scan": scan}


def part_b(tm, partA):
    models = [tuple(range(1, m + 1)) for m in range(2, 9)]
    models += [(1, 2, 3, 4, k) for k in (6, 7, 8)]
    models += [tuple(i for i in range(1, 9) if i != k) for k in (5, 6, 7, 8)]
    res = {}
    for mset in models:
        key = "".join(map(str, mset))
        res[key] = krein_and_critical(None if len(mset) == 8 else mset)
        r = res[key]
        print(key, "F_K", r["F_K"], "F_c", r["F_c"], flush=True)
    tm.mark("subset_scan")
    full, red = res["12345678"], res["1234"]
    gap = full["F_c"] - red["F_c"]
    dK = full["F_K"] - red["F_K"]
    growth_diff = full["F_c_minus_F_K"] - red["F_c_minus_F_K"]
    recov = {}
    for k in (5, 6, 7, 8):
        r = res["1234" + str(k)]
        if r["F_c"] is not None:
            recov[str(k)] = (r["F_c"] - red["F_c"]) / gap
    loo = {}
    for k in (5, 6, 7, 8):
        r = res["".join(str(i) for i in range(1, 9) if i != k)]
        if r["F_c"] is not None:
            loo[str(k)] = (r["F_c"] - full["F_c"]) / gap
    verdict = {
        "gap_Fc8_minus_Fc4": gap, "shift_in_F_K": dK, "difference_in_Fc_minus_FK": growth_diff,
        "H4a_supported": bool(abs(growth_diff) < 0.25 * abs(gap)),
        "fraction_of_gap_recovered_by_adding_mode_k_to_1234": recov,
        "fraction_of_gap_reopened_by_removing_mode_k_from_full": loo,
        "H4b_single_mode_recovers_ge_50pct": bool(max(recov.values(), default=0) >= 0.5)}
    return res, verdict


def main():
    tm = Timer()
    A = part_a(tm)
    print(json.dumps({k: {"dop853": v["dop853"]["F_c"], "rich": v["rk4_richardson_800_1600"],
                          "half800": v["rk4_half_period_map"]["800"]["F_c"]} for k, v in A.items()}, indent=1), flush=True)
    B, verdict = part_b(tm, A)
    print(json.dumps(verdict, indent=1))
    save("exp4_floquet_reduced", {"config": {"N": 8, "alpha": .25, "eta": .0025, "Omega": .347,
                                             "krein_detection_threshold_relative": 1e-4,
                                             "subset_scan_rk4_steps": 800, "subset_scan_dF": 1e-4},
                                  "partA_threshold_verification": A, "partB_subsets": B,
                                  "partB_verdict": verdict}, tm)


if __name__ == "__main__":
    main()
