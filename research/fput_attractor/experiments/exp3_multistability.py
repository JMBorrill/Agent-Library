"""Experiment 3 - bounded multistability, hysteresis and bifurcation-type tests (predeclared).

All trajectories use RK4 with STEPS=200 per drive period, and every reference periodic orbit is
a fixed point of the SAME discrete map (Newton at STEPS), so "converged to orbit X" is decided at
round-off level rather than at the RK4 discretisation error (~1e-5 at 200 steps).

A. Catalogue of drive-locked periodic orbits at F = 0.0045 (multistart Newton: 40 seeded random
   states + 10 points on the modulated attractor + rest), full chain and {1,2,3,4} truncation.
A2. Natural-parameter continuation of every catalogued family over F in [0.0030, 0.0060] with
   step halving (to 1e-7) at failures or jumps: existence intervals (fold estimates) and stability.
B. Basin sample at F = 0.0045 (84 initial conditions, seed 20261014):
   R: 48 random physical states q_n, p_n ~ U(-s, s), s in {0.25, 0.5, 1.0} (16 each);
   L: 21 points on the segment y_branch + lam (y_mod - y_branch), lam in [0, 1];
   E: 13 perturbations y_branch + eps d, d = Re(critical Floquet eigenvector)/|.|, eps in [1e-3, 1];
   plus rest. 8000 periods, classification on the last 1000 periods.
C. Hysteresis: quasi-static continuation over F = 0.0043..0.0053 (dF = 1e-4), upward from the
   continued (low-amplitude) locked orbit and downward from the modulated state, full chain and
   {1,2,3,4} truncation. Each step re-uses the previous final state plus a seeded 1e-7
   perturbation. Downward runs continue below 0.0043 only until the modulated state is lost
   (floor 0.0030) to locate the lower edge of the loop.
D. Bifurcation type at F_c = 0.00469315823 (full chain):
   D1: basin radius of the continued orbit along d for F < F_c. Subcritical NS predicts an
       unstable invariant circle shrinking onto the orbit, r ~ (F_c - F)^(1/2).
   D2: F > F_c: start 1e-6 from the unstable orbit; supercritical predicts a small torus growing
       continuously from zero size; subcritical predicts a jump to a distant attractor.
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

from fputv import diagnostics as D  # noqa: E402
from fputv.floquet import multipliers, newton_orbit  # noqa: E402
from fputv.integrate import batch, strobe  # noqa: E402
from fputv.io import Timer, save, save_npz  # noqa: E402
from fputv.model import FPUT  # noqa: E402

SEED = 20261014
FC_FULL = 0.004693158232
STEPS = 200
LOCK_TOL = 1e-6


def newton(s, y0, maxit=40):
    try:
        y, M, info = newton_orbit(s, y0, STEPS, maxit=maxit)
    except np.linalg.LinAlgError:
        return None, None
    if not info["converged"] or not np.all(np.isfinite(y)):
        return None, None
    return y, M


def orbit_record(s, y, M, name):
    mu = multipliers(M)
    G = s.S @ strobe(s, y, 1, STEPS, half=True)[1][0]
    w, V = np.linalg.eig(M)
    i = int(np.argmax(np.abs(w)))
    d = V[:, i].real
    return {"name": name, "y": y, "abs_mu": np.abs(mu), "max_abs_mu": float(abs(mu[0])),
            "n_unstable": int(np.sum(np.abs(mu) > 1)), "E1": float(s.energies(y)[0]),
            "E_total_linear": float(s.energies(y).sum()),
            "z2_symmetric_residual": float(np.max(np.abs(G - y))), "d_crit": d / np.linalg.norm(d)}


def catalogue(s, rng, extra):
    """Multistart Newton. The orbit continued from F=0 is named 'branch'; others by stability."""
    yb = np.zeros(s.dim)
    for F in np.r_[np.arange(0, s.F, 2e-4), s.F]:
        yb, Mb = newton(s.with_F(F), yb)
    found = [orbit_record(s, yb, Mb, "branch") | {"hits": 0}]
    starts = [rng.uniform(-1, 1, s.dim) * sc for sc in (0.25, 0.5, 1.0, 1.5) for _ in range(10)]
    starts += list(extra) + [np.zeros(s.dim)]
    for y0 in starts:
        y, M = newton(s, y0, 60)
        if y is None:
            continue
        hit = next((f for f in found if np.max(np.abs(y - f["y"])) < 1e-6), None)
        if hit is not None:
            hit["hits"] += 1
            continue
        k = sum(1 for f in found if f["name"] != "branch")
        rec = orbit_record(s, y, M, "tmp")
        rec["name"] = ("stable" if rec["n_unstable"] == 0 else f"saddle{rec['n_unstable']}") + f"_{k}"
        found.append(rec | {"hits": 1})
    return {"n_starts": len(starts), "orbits": found}


def continue_family(s0, y0, Flo=0.0030, Fhi=0.0060, dF=1e-4, dFmin=1e-7):
    """Continue a locked orbit up and down in F; stop at Newton failure/jump after step halving."""
    rows = {round(s0.F, 9): (y0, None)}
    ends = {}
    for sgn in (+1, -1):
        F, y, yprev, h = s0.F, y0.copy(), None, dF
        while (sgn > 0 and F < Fhi - 1e-12) or (sgn < 0 and F > Flo + 1e-12):
            Fn = round(F + sgn * h, 10)
            pred = y if yprev is None else y + (y - yprev) * (h / hprev)
            yn, M = newton(s0.with_F(Fn), pred)
            ok = yn is not None and np.max(np.abs(yn - pred)) < max(0.02, 0.5 * np.max(np.abs(y - (y if yprev is None else yprev))))
            if not ok:
                if h / 2 < dFmin:
                    break
                h /= 2
                continue
            yprev, hprev, y, F = y, h, yn, Fn
            mu = multipliers(M)
            rows[round(F, 9)] = (y, mu)
            h = min(dF, h * 2)
        ends["upper" if sgn > 0 else "lower"] = float(F)
    table = [{"F": F, "max_abs_mu": None if mu is None else float(abs(mu[0])),
              "n_unstable": None if mu is None else int(np.sum(np.abs(mu) > 1)),
              "E1": float(s0.with_F(F).energies(y)[0])} for F, (y, mu) in sorted(rows.items())]
    return {"last_converged_F": ends, "table": table, "states": {F: y for F, (y, _) in rows.items()}}


def orbits_at(families, F):
    out = {}
    for name, fam in families.items():
        st = fam["states"]
        key = round(F, 9)
        if key in st:
            out[name] = st[key]
    return out


def describe(s, W, refs):
    """Label a trajectory window W (keep x dim) against reference orbits {name: y}."""
    if not np.all(np.isfinite(W)):
        return {"label": "escaped"}
    E1 = s.energies(W)[:, 0]
    rng = float(np.ptp(E1))
    out = {"E1_range": rng, "E1_mean": float(E1.mean())}
    dists = {k: float(np.max(np.abs(W[-1] - y))) for k, y in refs.items()}
    out["supdist_to_orbits"] = dists
    near = min(dists, key=dists.get) if dists else None
    if rng > 5e-2:
        P, _ = D.pca_plane(W)
        out["abs_rotation_frequency"] = abs(D.refined_frequency(P[:, 0] + 1j * P[:, 1]))
        out["label"] = "modulated"
    elif near is not None and dists[near] < LOCK_TOL:
        out["label"] = f"locked:{near}"
    elif float(np.max(np.abs(W[-1] - W[-2]))) < 1e-9:
        out["label"] = "other_fixed_point"
    else:
        out["label"] = "undecided"
    return out


def part_b(s, refs, d, y_mod, rng):
    y_b = refs["branch"]
    ics, fam = [], []
    for sc in (0.25, 0.5, 1.0):
        for _ in range(16):
            ics.append(rng.uniform(-sc, sc, s.dim)); fam.append(f"R{sc}")
    for lam in np.linspace(0, 1, 21):
        ics.append(y_b + lam * (y_mod - y_b)); fam.append(f"L{lam:.2f}")
    for eps in np.logspace(-3, 0, 13):
        ics.append(y_b + eps * d); fam.append(f"E{eps:.4g}")
    ics.append(np.zeros(s.dim)); fam.append("rest")
    W = batch(s, np.array(ics), 8000, STEPS, 1000)
    return [{"family": f, "y0": y0, **describe(s, w, refs)} for f, y0, w in zip(fam, ics, W)]


def settle(s, y0, refs, maxp=30000, chunk=2000):
    y = np.array(y0, float)
    prev = None
    p = 0
    while p < maxp:
        Y = strobe(s, y, chunk, STEPS)
        p += chunk
        y = Y[-1]
        r = describe(s, Y[-1000:], refs)
        if r["label"] == "escaped" or r["label"].startswith("locked"):
            return r | {"periods": p}, y
        if r["label"] == "modulated" and prev is not None and abs(r["E1_range"] - prev) < 1e-4:
            return r | {"periods": p}, y
        prev = r["E1_range"]
    if r["label"] == "undecided":
        dmin = min(r["supdist_to_orbits"].values(), default=np.inf)
        r["label"] = "near_locked_unresolved" if dmin < 1e-2 else "undecided"
    return r | {"periods": p}, y


def hysteresis(modes, families, rng, Fgrid, floor=0.0030):
    s0 = FPUT(Fgrid[0], modes=modes)
    up, down = [], []
    y = orbits_at(families, Fgrid[0])["branch"].copy()
    for F in Fgrid:
        s = s0.with_F(F)
        r, y = settle(s, y + 1e-7 * rng.standard_normal(s.dim), orbits_at(families, F))
        up.append({"F": F, **r})
        print("up", modes, F, r["label"], round(r.get("E1_range", -1), 6), flush=True)
    y = strobe(s0.with_F(Fgrid[-1]), np.zeros(s0.dim), 6000, STEPS)[-1]
    F = Fgrid[-1]
    while F >= floor - 1e-12:
        s = s0.with_F(F)
        r, y = settle(s, y + 1e-7 * rng.standard_normal(s.dim), orbits_at(families, F))
        down.append({"F": F, **r})
        print("down", modes, F, r["label"], round(r.get("E1_range", -1), 6), flush=True)
        if F < Fgrid[0] - 1e-12 and r["label"] != "modulated":
            break
        F = round(F - 1e-4, 7)
    return {"up": up, "down": down}


def part_d1(Fs, families):
    out = []
    for F in Fs:
        s = FPUT(F)
        y_b, M = newton(s, orbits_at(families, round(round(F / 1e-4) * 1e-4, 7))["branch"])
        rec0 = orbit_record(s, y_b, M, "branch")
        mu, d = rec0["max_abs_mu"], rec0["d_crit"]
        periods = int(min(40000, max(8000, 15 / (1 - mu))))

        def labels(eps):
            W = batch(s, y_b + eps[:, None] * d, periods, STEPS, 1000)
            res = []
            for e, w in zip(eps, W):
                r = describe(s, w, {"branch": y_b})
                dist = r.get("supdist_to_orbits", {}).get("branch", np.inf)
                if r["label"] == "locked:branch" or (r["label"] != "modulated" and dist < 1e-3 * e and r["E1_range"] < 1e-3):
                    res.append("returns")
                elif r["label"] == "modulated" or (r["label"] == "other_fixed_point" and dist > 1e-2):
                    res.append("leaves:" + ("modulated" if r["label"] == "modulated" else "other_locked"))
                else:
                    res.append("undecided")
            return res

        eps = np.logspace(-3, 0.3, 20)
        lab = labels(eps)
        pts = sorted(zip(eps.tolist(), lab))
        lo = max([e for e, l in pts if l == "returns"], default=None)
        hi = min([e for e, l in pts if l.startswith("leaves") and (lo is None or e > lo)], default=None)
        rec = {"F": F, "max_abs_mu": mu, "periods": periods, "coarse": pts}
        if lo is not None and hi is not None:
            eps2 = np.geomspace(lo, hi, 10)[1:-1]
            pts = sorted(pts + list(zip(eps2.tolist(), labels(eps2))))
            lo = max(e for e, l in pts if l == "returns" and e < hi)
            hi = min(e for e, l in pts if l.startswith("leaves") and e > lo)
            rec["fine"] = pts
        rec["radius_bracket"] = [lo, hi]
        rec["radius_estimate"] = float(np.sqrt(lo * hi)) if (lo and hi) else None
        out.append(rec)
        print("D1", F, mu, rec["radius_bracket"], flush=True)
    return out


def part_d2(Fs, families, ref_down):
    out = []
    for F in Fs:
        s = FPUT(F)
        refs = orbits_at(families, F)
        rec0 = orbit_record(s, refs["branch"], newton(s, refs["branch"])[1], "branch")
        Y = strobe(s, refs["branch"] + 1e-6 * rec0["d_crit"], 30000, STEPS)
        E1 = s.energies(Y)[:, 0]
        blocks = [float(np.ptp(E1[i:i + 500])) for i in range(0, 30000, 500)]
        r = describe(s, Y[-1000:], refs)
        ref = next((x for x in ref_down if abs(x["F"] - F) < 1e-9), None)
        out.append({"F": F, "branch_max_abs_mu": rec0["max_abs_mu"], "E1_range_per_500_block": blocks, **r,
                    "downward_continuation_state_at_same_F": ref})
        print("D2", F, r["label"], r["E1_range"], flush=True)
    return out


def strip(cat):
    return {"n_starts": cat["n_starts"], "orbits": [{k: v for k, v in o.items() if k != "d_crit"} for o in cat["orbits"]]}


def main():
    tm = Timer()
    rng = np.random.default_rng(SEED)
    out = {}
    fams = {}
    for label, modes in (("full", None), ("modes1234", (1, 2, 3, 4))):
        s = FPUT(0.0045, modes=modes)
        Ymod = strobe(s, np.zeros(s.dim), 6000, STEPS)
        extra = [Ymod[i] for i in np.linspace(4000, 5999, 10).astype(int)]
        cat = catalogue(s, rng, extra)
        fams[label] = {o["name"]: continue_family(s, o["y"]) for o in cat["orbits"]}
        out[label] = {"A_catalogue_F0.0045": strip(cat),
                      "A2_families": {k: {"last_converged_F": v["last_converged_F"], "table": v["table"]}
                                      for k, v in fams[label].items()},
                      "rest_state_F0.0045": describe(s, Ymod[-1000:], {o["name"]: o["y"] for o in cat["orbits"]})}
        print("A", label, [(o["name"], o["hits"], o["n_unstable"], round(o["E1"], 4), fams[label][o["name"]]["last_converged_F"])
                           for o in cat["orbits"]], flush=True)
        if label == "full":
            refs = {o["name"]: o["y"] for o in cat["orbits"]}
            d_crit = cat["orbits"][0]["d_crit"]
            y_mod = Ymod[-1]
    tm.mark("A_catalogue_and_families")

    s = FPUT(0.0045)
    B = part_b(s, refs, d_crit, y_mod, rng)
    counts = {}
    for r in B:
        key = f"{r['family'][0]}|{r['label']}"
        counts[key] = counts.get(key, 0) + 1
    out["full"]["B_basin_sample"] = B
    out["full"]["B_counts"] = counts
    print("B", counts, flush=True)
    tm.mark("B_basin_sample")

    Fgrid = [round(x, 7) for x in np.arange(0.0043, 0.0053 + 1e-12, 1e-4)]
    for label, modes in (("full", None), ("modes1234", (1, 2, 3, 4))):
        out[label]["C_hysteresis"] = hysteresis(modes, fams[label], rng, Fgrid)
        tm.mark(f"C_hysteresis_{label}")

    D1 = part_d1([0.0042, 0.0043, 0.0044, 0.0045, 0.0046, 0.00465, 0.00468], fams["full"])
    tm.mark("D1_basin_radius")
    D2 = part_d2([0.0048, 0.0050, 0.0052], fams["full"], out["full"]["C_hysteresis"]["down"])
    tm.mark("D2_above_Fc")
    pts = [(r["F"], r["radius_estimate"]) for r in D1 if r["radius_estimate"]]
    fit = None
    if len(pts) >= 3:
        x = np.log([FC_FULL - F for F, _ in pts]); yv = np.log([r for _, r in pts])
        near = [(F, r) for F, r in pts if F >= 0.0045]
        fit = {"points": pts, "loglog_slope_all": float(np.polyfit(x, yv, 1)[0]),
               "loglog_slope_F_ge_0.0045": float(np.polyfit(np.log([FC_FULL - F for F, _ in near]),
                                                            np.log([r for _, r in near]), 1)[0]) if len(near) >= 3 else None,
               "subcritical_prediction": 0.5}
    out["full"]["D1_basin_radius_vs_F"] = D1
    out["full"]["D1_scaling_fit"] = fit
    out["full"]["D2_above_Fc"] = D2
    payload = {"config": {"F_basin": 0.0045, "seed": SEED, "rk4_steps": STEPS, "F_c_full": FC_FULL,
                          "lock_tolerance": LOCK_TOL,
                          "classification": "modulated: E1 range > 0.05 over last 1000 periods; locked:X: sup-distance "
                                            "< 1e-6 to the discrete-map fixed point X; D1 'returns' also accepts "
                                            "distance < 1e-3 eps with E1 range < 1e-3"},
               "results": out}
    save("exp3_multistability", payload, tm)
    save_npz("exp3_basin_ics", ics=np.array([r["y0"] for r in B]), families=np.array([r["family"] for r in B]))
    print(json.dumps(fit, indent=1))


if __name__ == "__main__":
    main()
