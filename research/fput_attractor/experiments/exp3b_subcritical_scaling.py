"""Experiment 3b - scaling of the locked orbit's basin radius below F_c (supersedes Exp 3 D1),
and a direct dynamical check of the high-amplitude locked orbit found in Exp 3A.

Exp 3 D1 probed the basin along Re(v) with an arbitrary numpy eigenvector phase, so the probe
direction rotated inside the critical plane from one F to the next. Here the critical eigenvector
is given a canonical phase (|Re v| maximal, Re v . Im v = 0) and four directions
d_phi = Re(e^{i phi} v)/|.|, phi in {0, pi/4, pi/2, 3pi/4}, are bisected in parallel
(log-bisection on eps in [1e-3, 2], 9 iterations).

Prediction (subcritical Neimark-Sacker): an unstable invariant circle surrounds the orbit and
shrinks onto it as F -> F_c^-, so r(F) ~ (F_c - F)^(1/2) (log-log slope 1/2) in every direction.
Supercritical prediction: no shrinking boundary (r does not tend to 0).
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

from fputv.floquet import multipliers, newton_orbit, period_map  # noqa: E402
from fputv.integrate import batch  # noqa: E402
from fputv.io import Timer, save  # noqa: E402
from fputv.model import FPUT  # noqa: E402

FC = 0.004693158232
STEPS = 200
FS = [0.0044, 0.0045, 0.0046, 0.00465, 0.00468]
PHIS = [0.0, np.pi / 4, np.pi / 2, 3 * np.pi / 4]


def canonical(v):
    v = v / np.linalg.norm(v)
    # phase maximising |Re(e^{i a} v)|: a = -arg(v.v)/2
    a = -0.5 * np.angle(np.sum(v * v))
    w = np.exp(1j * a) * v
    return w if np.linalg.norm(w.real) >= np.linalg.norm(w.imag) else 1j * w


def classify(s, W, y, eps):
    E1 = s.energies(W)[:, 0]
    d = float(np.max(np.abs(W[-1] - y)))
    if np.ptp(E1) < 1e-3 and d < 1e-3 * eps:
        return "returns"
    if np.ptp(E1) > 5e-2 or d > eps:
        return "leaves"
    return "undecided"


def main():
    tm = Timer()
    s0 = FPUT(0.0)
    y = np.zeros(16)
    for F in np.arange(0, FS[0], 2e-4):
        y, _, _ = newton_orbit(s0.with_F(F), y, STEPS)
    rows = []
    for F in FS:
        s = s0.with_F(F)
        y, M, info = newton_orbit(s, y, STEPS)
        w, V = np.linalg.eig(M)
        i = int(np.argmax(np.abs(w)))
        v = canonical(V[:, i])
        dirs = np.array([np.real(np.exp(1j * p) * v) for p in PHIS])
        dirs /= np.linalg.norm(dirs, axis=1)[:, None]
        periods = int(min(40000, max(8000, 15 / (1 - abs(w[i])))))
        lo = np.full(4, 1e-3); hi = np.full(4, 2.0)
        status = ["ok"] * 4
        for e0, tag in ((lo, "lo"), (hi, "hi")):
            labs = [classify(s, Wk, y, e) for Wk, e in zip(batch(s, y + e0[:, None] * dirs, periods, STEPS, 1000), e0)]
            for k, l in enumerate(labs):
                if (tag == "lo" and l != "returns") or (tag == "hi" and l != "leaves"):
                    status[k] = f"bracket_{tag}_{l}"
        hist = []
        for it in range(9):
            mid = np.sqrt(lo * hi)
            labs = [classify(s, Wk, y, e) for Wk, e in zip(batch(s, y + mid[:, None] * dirs, periods, STEPS, 1000), mid)]
            for k, l in enumerate(labs):
                if l == "returns":
                    lo[k] = mid[k]
                elif l == "leaves":
                    hi[k] = mid[k]
                else:
                    status[k] = "undecided_at_" + f"{mid[k]:.4g}"
            hist.append(labs)
        r = np.sqrt(lo * hi)
        rows.append({"F": F, "F_c_minus_F": FC - F, "max_abs_mu": float(abs(w[i])), "periods": periods,
                     "radius_by_direction": r, "bracket_lo": lo, "bracket_hi": hi, "status": status,
                     "radius_min": float(r.min()), "radius_mean": float(r.mean())})
        print(F, np.round(r, 4), status, flush=True)
        tm.mark(f"F{F}")

    x = np.log([row["F_c_minus_F"] for row in rows])
    fits = {}
    for key in ("radius_min", "radius_mean"):
        yv = np.log([row[key] for row in rows])
        fits[key] = {"slope_all": float(np.polyfit(x, yv, 1)[0]),
                     "slope_three_closest": float(np.polyfit(x[-3:], yv[-3:], 1)[0]),
                     "local_slopes": list(np.diff(yv) / np.diff(x))}
    per_dir = [float(np.polyfit(x[-3:], np.log([row["radius_by_direction"][k] for row in rows[-3:]]), 1)[0]) for k in range(4)]
    fits["slope_three_closest_per_direction"] = per_dir

    # Direct dynamical check of the high-amplitude locked orbit (Exp 3A 'stable_0') at F = 0.0045.
    s = FPUT(0.0045)
    import json as _j
    cat = _j.loads((ROOT / "results/exp3_multistability.json").read_text())["results"]["full"]["A_catalogue_F0.0045"]["orbits"]
    high = next(o for o in cat if o["name"].startswith("stable"))
    yh, Mh, ih = newton_orbit(s, np.array(high["y"]), STEPS)
    _, Mhd = period_map(s, yh, method="DOP853")
    rng = np.random.default_rng(20261014)
    pert = rng.standard_normal((8, 16)); pert /= np.linalg.norm(pert, axis=1)[:, None]
    amps = np.r_[np.full(4, 1e-3), np.full(4, 3e-2)]
    W = batch(s, yh + amps[:, None] * pert, 8000, STEPS, 1000)
    high_check = {"E1": float(s.energies(yh)[0]), "max_abs_mu_rk4_200": float(abs(multipliers(Mh)[0])),
                  "max_abs_mu_dop853_monodromy": float(abs(multipliers(Mhd)[0])),
                  "perturbation_amplitudes": amps, "final_supdist": [float(np.max(np.abs(Wk[-1] - yh))) for Wk in W],
                  "final_E1_range": [float(np.ptp(s.energies(Wk)[:, 0])) for Wk in W]}
    print("high orbit", high_check, flush=True)
    save("exp3b_subcritical_scaling", {"config": {"F_c": FC, "rk4_steps": STEPS, "F_values": FS, "phases": PHIS,
                                                  "bisection_iterations": 9, "eps_bracket": [1e-3, 2.0],
                                                  "classification": "returns: E1 range < 1e-3 and final distance < 1e-3 eps; leaves: E1 range > 0.05 or final distance > eps"},
                                       "rows": rows, "fits": fits, "high_amplitude_orbit_check": high_check}, tm)
    print(json.dumps(fits, indent=1))


if __name__ == "__main__":
    main()
