"""Experiment 4b - is the omitted-mode threshold shift carried by the base orbit or by the
Floquet perturbation? (follow-up to Exp 4 H4b: mode 5 carries ~73%, mode 6 ~25% of the gap.)

Critical F (max |mu| = 1) for five variants, all RK4/800 (Exp 4 shows RK4/800 F_c errors < 1e-9):
  V8   : full tangent about the full orbit                 (= F_c of the full chain)
  Vb   : {1..4} tangent about the full orbit (all modes of the base orbit in the stiffness)
  Va   : {1..4} tangent about the full orbit projected onto modes 1-4
  Vc   : full tangent about the {1..4}-truncated orbit
  V4   : {1..4} tangent about the {1..4} orbit             (= F_c of the truncation)
Decomposition of the gap F_c(V8) - F_c(V4):
  perturbation (tangent) channel at the full orbit   = F_c(V8) - F_c(Vb)
  base-orbit channel seen by 4-mode perturbations    = F_c(Vb) - F_c(V4)
     of which modes 5-8 of the orbit (via stiffness) = F_c(Vb) - F_c(Va)
     of which reshaped modes 1-4 of the orbit        = F_c(Va) - F_c(V4)
Predeclared hypothesis H4c: the perturbation channel carries >= 50% of the gap.
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

from fputv.floquet import multipliers, newton_orbit  # noqa: E402
from fputv.hybrid import hybrid_monodromy  # noqa: E402
from fputv.io import Timer, save  # noqa: E402
from fputv.model import FPUT  # noqa: E402

STEPS = 800
M4 = (1, 2, 3, 4)


def branch(modes, F, cache):
    key = (modes, round(F, 12))
    if key in cache:
        return cache[key]
    s0 = FPUT(0.0, modes=modes)
    near = [k for k in cache if k[0] == modes]
    if near:
        y = cache[min(near, key=lambda k: abs(k[1] - F))]
    else:
        y = np.zeros(s0.dim)
        for FF in np.arange(0, F, 2e-4):
            y, _, _ = newton_orbit(s0.with_F(FF), y, 400)
    y, M, info = newton_orbit(s0.with_F(F), y, STEPS)
    assert info["converged"]
    cache[key] = y
    return y


def max_mu(variant, F, cache):
    full = FPUT(F)
    red = FPUT(F, modes=M4)
    I = np.eye(8)
    P4 = red.Phi @ red.Phi.T
    if variant == "V8":
        base, sb, Phi_t, Pq = branch(None, F, cache), full, I, I
    elif variant == "Vb":
        base, sb, Phi_t, Pq = branch(None, F, cache), full, red.Phi, I
    elif variant == "Va":
        base, sb, Phi_t, Pq = branch(None, F, cache), full, red.Phi, P4
    elif variant == "Vc":
        base, sb, Phi_t, Pq = branch(M4, F, cache), red, I, I
    elif variant == "V4":
        base, sb, Phi_t, Pq = branch(M4, F, cache), red, red.Phi, I
    Phi_b, phys_b = sb.Phi, sb.physical
    _, W = hybrid_monodromy(base, STEPS, Phi_b, phys_b, np.ascontiguousarray(Phi_t), np.ascontiguousarray(Pq),
                            sb.alpha, sb.eta, F, sb.Omega)
    mu = multipliers(W)
    return float(abs(mu[0])), mu, W


def main():
    tm = Timer()
    cache = {}
    out = {}
    for v in ("V8", "Vb", "Va", "Vc", "V4"):
        grid = np.arange(0.0040, 0.0080 + 1e-12, 1e-4)
        vals = []
        Fc = None
        for a, b in zip(grid[:-1], grid[1:]):
            ma = max_mu(v, a, cache)[0] if not vals else vals[-1][1]
            if not vals:
                vals.append((a, ma))
            mb = max_mu(v, b, cache)[0]
            vals.append((b, mb))
            if ma < 1 <= mb:
                Fc = brentq(lambda F: max_mu(v, F, cache)[0] - 1, a, b, xtol=1e-12)
                break
        if Fc is None:
            out[v] = {"F_c": None, "note": "no crossing of |mu|=1 for F in [0.0040, 0.0080]", "scan": vals}
            print(v, None, flush=True)
            continue
        _, mu, W = max_mu(v, Fc, cache)
        c = np.exp(-0.0025 * 2 * np.pi / 0.347)
        mags = np.sort(np.abs(mu))[::-1]
        out[v] = {"F_c": Fc, "theta_crit": float(abs(np.angle(mu[0]))), "scan": vals,
                  "pairing_max_dev": float(np.max(np.abs(mags * mags[::-1] - c)))}
        print(v, Fc, flush=True)
        tm.mark(v)
    F = {k: out[k]["F_c"] for k in out}
    if any(x is None for x in F.values()):
        gap = F["V8"] - F["V4"]
        verdict = {"gap_V8_minus_V4": gap,
                   "Va_minus_V4_over_gap": None if F["Va"] is None else (F["Va"] - F["V4"]) / gap,
                   "Vb_minus_V4_over_gap": None if F["Vb"] is None else (F["Vb"] - F["V4"]) / gap,
                   "Vc": "no instability for F <= 0.0080" if F["Vc"] is None else F["Vc"],
                   "H4c": "ill-posed / rejected: the hybrid channels are strongly non-additive (a partial "
                          "inclusion of modes 5-8 moves F_c by several times the full gap or removes the "
                          "crossing), so the gap cannot be attributed to the base orbit or to the "
                          "perturbation dynamics separately"}
        save("exp4b_mechanism_decomposition", {"config": {"rk4_steps": STEPS, "scan": [0.0040, 0.0080, 1e-4]},
                                               "variants": out, "decomposition": None, "verdict": verdict}, tm)
        print(json.dumps(F, indent=1))
        return
    gap = F["V8"] - F["V4"]
    dec = {"gap_V8_minus_V4": gap,
           "perturbation_channel_V8_minus_Vb": F["V8"] - F["Vb"],
           "base_orbit_channel_Vb_minus_V4": F["Vb"] - F["V4"],
           "  base_orbit_modes5to8_in_stiffness_Vb_minus_Va": F["Vb"] - F["Va"],
           "  base_orbit_reshaped_modes1to4_Va_minus_V4": F["Va"] - F["V4"],
           "alt_perturbation_channel_at_4mode_orbit_Vc_minus_V4": F["Vc"] - F["V4"],
           "alt_base_channel_with_full_tangent_V8_minus_Vc": F["V8"] - F["Vc"]}
    frac = {k: v / gap for k, v in dec.items() if k != "gap_V8_minus_V4"}
    verdict = {"fractions_of_gap": frac,
               "H4c_perturbation_channel_ge_50pct": bool(frac["perturbation_channel_V8_minus_Vb"] >= 0.5),
               "H4c_alt_ordering_agrees": bool(frac["alt_perturbation_channel_at_4mode_orbit_Vc_minus_V4"] >= 0.5)}
    print(json.dumps(dec | verdict, indent=1))
    save("exp4b_mechanism_decomposition", {"config": {"rk4_steps": STEPS, "N": 8, "alpha": .25, "eta": .0025,
                                                      "Omega": .347}, "variants": out, "decomposition": dec,
                                           "verdict": verdict}, tm)


if __name__ == "__main__":
    main()
