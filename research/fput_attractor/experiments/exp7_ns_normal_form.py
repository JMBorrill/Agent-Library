"""Experiment 7 (Priority 3a) - the Floquet crossing near F = 0.004693158 and its criticality.

1. Reproduce F_c (DOP853 variational shooting + brentq) and track the critical pair:
   |mu|, arg mu over F_c + {-3e-5 .. +3e-5}; transversality d|mu|/dF (central +-1e-6, cf. review 17.92);
   non-resonance (theta/2pi vs 1/1..1/4).
2. First Lyapunov coefficient d = Re(e^{-i theta} c1) of the period map at F_c (formula validated on
   test maps, tests/test_normal_form.py), with RK4 800/1600/3200 and DOP853 variational equations;
   also for the {1..4} and {1..5} truncations at their own F_c.
3. Parameter-free falsification test: for F < F_c the normal form predicts an unstable invariant
   circle |z| = r(F) = sqrt((1 - |mu(F)|)/d), so the basin of the locked orbit along a critical-plane
   direction d_phi should end at eps_phi = r / |<p, d_phi>|. Compare with the 20 bisected radii of
   Exp 3b (same RK4/200 discrete map, same canonical directions). Also predicted rotation number of
   the unstable circle: (theta(F) + Im(e^{-i theta} c1) r^2)/(2 pi), for comparison with Exp 8.
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

from fputv.floquet import critical_F, multipliers, newton_orbit, period_map  # noqa: E402
from fputv.io import Timer, save  # noqa: E402
from fputv.model import FPUT  # noqa: E402
from fputv.normal_form import critical_vectors, fput_ns_coefficient  # noqa: E402

PHIS = [0.0, np.pi / 4, np.pi / 2, 3 * np.pi / 4]


def canonical(v):
    v = v / np.linalg.norm(v)
    a = -0.5 * np.angle(np.sum(v * v))
    w = np.exp(1j * a) * v
    return w if np.linalg.norm(w.real) >= np.linalg.norm(w.imag) else 1j * w


def seed(modes, F, steps=400):
    s0 = FPUT(0.0, modes=modes)
    y = np.zeros(s0.dim)
    for FF in np.r_[np.arange(0, F, 2e-4), F]:
        y, _, _ = newton_orbit(s0.with_F(FF), y, steps)
    return s0, y


def dop_orbit(s, y):
    y, M, info = newton_orbit(s, y, method="DOP853", rtol=1e-12, atol=1e-14)
    return y, M


def crossing(modes, bracket):
    s0, y = seed(modes, bracket[0])
    Fc1600, y, mu, _ = critical_F(s0, bracket, y, steps=1600)
    st = {"y": y}

    def g(F):
        st["y"], M = dop_orbit(s0.with_F(F), st["y"])
        return float(abs(multipliers(M)[0]) - 1)

    Fc = brentq(g, Fc1600 - 2e-7, Fc1600 + 2e-7, xtol=1e-14)
    track = []
    for dF in (-3e-5, -1e-5, -3e-6, -1e-6, 0.0, 1e-6, 3e-6, 1e-5, 3e-5):
        yy, M = dop_orbit(s0.with_F(Fc + dF), st["y"])
        mu = multipliers(M)[0]
        track.append({"dF": dF, "abs_mu": float(abs(mu)), "arg_mu": float(abs(np.angle(mu)))})
    slope = (track[5]["abs_mu"] - track[3]["abs_mu"]) / 2e-6
    yc, Mc = dop_orbit(s0.with_F(Fc), st["y"])
    th = track[4]["arg_mu"]
    return s0, Fc, yc, Mc, {"F_c_dop853": Fc, "F_c_rk4_1600": Fc1600, "track": track,
                             "d_abs_mu_dF": slope, "theta": th, "theta_over_2pi": th / (2 * np.pi),
                             "local_modulation_period_2pi_over_theta": 2 * np.pi / th,
                             "distance_to_strong_resonances": {f"1/{k}": abs(th / (2 * np.pi) - 1 / k) for k in (1, 2, 3, 4)}}


def basin_prediction(d_full, c1_rot):
    rows = json.loads((ROOT / "results/exp3b_subcritical_scaling.json").read_text())["rows"]
    out = []
    y = None
    for row in rows:
        F = row["F"]
        s = FPUT(F)
        if y is None:
            _, y = seed(None, F, 200)
        y, M, _ = newton_orbit(s, y, 200)
        w, V = np.linalg.eig(M)
        i = int(np.argmax(np.abs(w) * (w.imag > 0)))
        v = canonical(V[:, i])
        mu = w[i]
        _, q, p = critical_vectors(M)
        # renormalise p so that <p, v> = 1 for the canonical v (same span as q, phase differs)
        p = p / np.conj(np.vdot(p, v))
        r = np.sqrt((1 - abs(mu)) / d_full)
        pred, meas = [], []
        for k, ph in enumerate(PHIS):
            dvec = np.real(np.exp(1j * ph) * v); dvec /= np.linalg.norm(dvec)
            pred.append(float(r / abs(np.vdot(p, dvec))))
            meas.append(float(row["radius_by_direction"][k]))
        out.append({"F": F, "abs_mu_rk4_200": float(abs(mu)), "r_normal_form": float(r),
                    "eps_predicted": pred, "eps_measured_exp3b": meas, "status_exp3b": row["status"],
                    "ratio_measured_over_predicted": list(np.array(meas) / np.array(pred)),
                    "predicted_unstable_circle_rotation_number": float((abs(np.angle(mu)) + c1_rot * r ** 2) / (2 * np.pi))})
    return out


def main():
    tm = Timer()
    res = {}
    for label, modes, br in (("full", None, (0.0046, 0.0048)), ("modes12345", (1, 2, 3, 4, 5), (0.0047, 0.0049)),
                             ("modes1234", (1, 2, 3, 4), (0.0050, 0.0052))):
        s0, Fc, yc, Mc, info = crossing(modes, br)
        s = s0.with_F(Fc)
        nf = {}
        for steps in ((800, 1600, 3200) if label == "full" else (1600,)):
            _, Mr = period_map(s, yc, steps)
            r = fput_ns_coefficient(s, yc, Mr, steps=steps)
            nf[f"RK4/{steps}"] = {"d": r["d"], "c1": [r["c1"].real, r["c1"].imag], "abs_mu": r["abs_mu"],
                                  "rotation_shift_coefficient": r["rotation_shift_coefficient"],
                                  "terms_in_d": r["terms_in_d"], "first_order_check": r["first_order_check_supdiff_U_vs_Mq"]}
        r = fput_ns_coefficient(s, yc, Mc, method="DOP853")
        nf["DOP853"] = {"d": r["d"], "c1": [r["c1"].real, r["c1"].imag], "abs_mu": r["abs_mu"],
                        "rotation_shift_coefficient": r["rotation_shift_coefficient"], "terms_in_d": r["terms_in_d"]}
        info["normal_form"] = nf
        info["criticality"] = "subcritical (d > 0)" if r["d"] > 0 else "supercritical (d < 0)"
        res[label] = info
        print(label, Fc, info["d_abs_mu_dF"], {k: v["d"] for k, v in nf.items()}, flush=True)
        tm.mark(label)
    dfull = res["full"]["normal_form"]["DOP853"]["d"]
    rot = res["full"]["normal_form"]["DOP853"]["rotation_shift_coefficient"]
    # d is computed with |q| = 1, matching the unit-norm canonical v used in the prediction
    bp = basin_prediction(dfull, rot)
    tm.mark("basin_prediction")
    for b in bp:
        print(b["F"], np.round(b["eps_predicted"], 4), np.round(b["eps_measured_exp3b"], 4),
              np.round(b["ratio_measured_over_predicted"], 3), round(b["predicted_unstable_circle_rotation_number"], 5))
    save("exp7_ns_normal_form", {"config": {"note": "d < 0 supercritical, d > 0 subcritical; |q| = 1, <p,q> = 1"},
                                 "crossings": res, "basin_radius_prediction_vs_exp3b": bp}, tm)


if __name__ == "__main__":
    main()
