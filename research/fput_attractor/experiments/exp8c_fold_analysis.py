"""Experiment 8c - post-processing of Exp 8/8b (no new integration).

Saddle-node of invariant circles, leading order: the stable circle's slow normal rate and the
unstable circle's instability rate are equal in magnitude, both ~ (F - F_low)^(1/2); next-order
terms make them asymmetric. Tests:
  (i)   ratio (-lambda_2 T)/sigma_u -> 1 as F -> F_low;
  (ii)  the mean normal rate scales with exponent 1/2;
  (iii) ghost exponent gamma: sensitivity to F_low over the bisection bracket and fold-side fits.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
from scipy.optimize import curve_fit  # noqa: E402

from fputv.io import Timer, save  # noqa: E402


def main():
    tm = Timer()
    b = json.loads((ROOT / "results/exp8b_fold_scaling.json").read_text())["results"]
    T = 2 * np.pi / 0.347
    rows = [r for r in b["fold_side"] if r["F"] - b["bisection_bracket_exp8"][1] <= 1.01e-5]
    F = np.array([r["F"] for r in rows])
    lam = np.array([-r["lambda2_per_time"] * T for r in rows])
    sig = np.array([r["edge"]["instability_rate_per_period"] for r in rows])
    dist = np.array([r["edge"]["distance_to_stable_torus_min_median"][1] for r in rows])
    Fl_dist = b["fits"]["edge_torus_distance_median_squared"]["F_low_from_zero_crossing"]
    lo, hi = b["bisection_bracket_exp8"]
    out = {"F": F.tolist(), "minus_lambda2_T": lam.tolist(), "sigma_u": sig.tolist(),
           "ratio_lambda2T_over_sigma_u": (lam / sig).tolist()}
    mean_rate = 0.5 * (lam + sig)
    exps = {}
    for name, Fl in (("F_low_dist_fit", Fl_dist), ("bracket_lo", lo), ("bracket_mid", 0.5 * (lo + hi)), ("bracket_hi_minus_1e-9", hi - 1e-9)):
        x = F - Fl
        if np.all(x > 0):
            exps[name] = {"F_low": Fl, "mean_rate_exponent": float(np.polyfit(np.log(x), np.log(mean_rate), 1)[0]),
                          "distance_exponent": float(np.polyfit(np.log(x), np.log(dist), 1)[0])}
    out["exponents_vs_F_low_choice"] = exps
    g = [(r["F"], r["transit_periods"]) for r in b["ghost"] if r["transit_periods"]]
    gs = {}
    for name, Fl in (("F_low_dist_fit", Fl_dist), ("bracket_lo", lo), ("bracket_mid", 0.5 * (lo + hi)), ("bracket_hi", hi),
                     ("fold_side_mean", b["F_low_estimate_from_fold_side_fits"])):
        x = np.array([Fl - f for f, _ in g]); yv = np.array([t for _, t in g], float)
        if np.all(x > 0):
            p, cov = curve_fit(lambda x, a, bb, gam: bb + a * x ** -gam, x, yv, p0=(5, 100, 0.5), maxfev=20000)
            gs[name] = {"F_low": Fl, "gamma": float(p[2]), "gamma_std": float(np.sqrt(cov[2, 2])), "offset_b": float(p[1])}
    out["ghost_gamma_vs_F_low_choice"] = gs
    tm.mark("fits")
    save("exp8c_fold_analysis", {"results": out}, tm)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
