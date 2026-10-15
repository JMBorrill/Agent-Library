"""Experiment 8 (Priority 3b) - is there an unstable invariant circle connecting the subcritical NS
point to the lower edge of the hysteresis loop (fold of invariant circles)?  Full chain, RK4/200.

A. Stable torus by quasi-static continuation from rest at F = 0.0045 (up to 0.00465, down to 0.0043),
   4096 stroboscopic samples per F (reference set for basin decisions).
B. Lower edge F_low of the torus: downward continuation in 2e-5 steps below 0.0043, then
   bisection in F (each trial started from the torus at the last persisting F; up to 60 000 periods).
C. Ghost transit times tau(F) for F = F_low - {1, 3, 10, 30} x 1e-6 (fold prediction tau ~ dF^-1/2).
D. Leading transverse Lyapunov exponent lambda_2 of the stable torus versus F towards F_low
   (fold prediction: lambda_2 -> 0, ~ (F - F_low)^1/2; at F = 0.0045 lambda_2 = -eta/2).
E. Edge tracking between the locked orbit (A) and the torus (B), started along the critical
   direction, at F in {0.00465, 0.0046, 0.0045, 0.0044, 0.0043} and close to F_low; at F = 0.0045
   also started along the locked->torus segment (edge-state uniqueness check). Edge state
   diagnostics: fixed point (saddle orbit) vs circle, size, rotation number, instability rate,
   distance to the stable torus. Normal-form predictions (Exp 7) are compared near F_c.
Falsifiers of the fold-of-circles connection: edge state is a fixed point/chaotic; edge circle does
not approach the torus at F_low; lambda_2 stays at -eta/2 up to F_low; tau exponent far from -1/2.
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
from scipy.spatial import cKDTree  # noqa: E402

from fputv import diagnostics as D  # noqa: E402
from fputv.edge import separation_rate, track_edge  # noqa: E402
from fputv.floquet import multipliers, newton_orbit  # noqa: E402
from fputv.integrate import batch, lyapunov_qr, strobe  # noqa: E402
from fputv.io import Timer, save, save_npz  # noqa: E402
from fputv.model import FPUT  # noqa: E402
from fputv.normal_form import critical_vectors  # noqa: E402

STEPS = 200
FC200 = None  # filled in main (F_c of the RK4/200 discrete map)


def locked(F, y0):
    s = FPUT(F)
    y, M, info = newton_orbit(s, y0, STEPS)
    assert info["converged"]
    return y, M


def settle_torus(F, y0, periods=6000, keep=4096):
    s = FPUT(F)
    Y = strobe(s, y0, periods + keep, STEPS)
    W = Y[-keep:]
    return W, float(np.ptp(s.energies(W)[:, 0]))


def persists(F, y0, y_lock, maxp=60000, chunk=2000):
    """Run from y0 at F; return ('torus'|'locked'|'undecided', periods, final state, E1-range history)."""
    s = FPUT(F)
    y = y0.copy()
    hist = []
    p = 0
    while p < maxp:
        Y = strobe(s, y, chunk, STEPS)
        p += chunk
        y = Y[-1]
        r = float(np.ptp(s.energies(Y[-1000:])[:, 0]))
        hist.append(r)
        if np.max(np.abs(y - y_lock)) < 1e-6:
            return "locked", p, y, hist
        if len(hist) >= 6 and min(hist[-6:]) > 0.2 and np.ptp(hist[-6:]) < 1e-4:
            return "torus", p, y, hist
    return "undecided", p, y, hist


def transit_time(F, y0, y_lock, maxp=200000):
    """Periods until the trajectory leaves the torus region (E1 range in a 200-period window < 0.1)."""
    s = FPUT(F)
    y = y0.copy()
    p = 0
    while p < maxp:
        Y = strobe(s, y, 200, STEPS)
        p += 200
        y = Y[-1]
        if np.ptp(s.energies(Y)[:, 0]) < 0.1:
            return p
    return None


def make_decider(F, y_lock, torus, r_in, r_out):
    s = FPUT(F)
    tree = cKDTree(torus)

    def decide(X, chunk=1000, maxp=120000):
        X = np.array(X, float)
        lab = ["U"] * len(X)
        todo = list(range(len(X)))
        p = 0
        while todo and p < maxp:
            W = batch(s, X[todo], chunk, STEPS, 1)
            p += chunk
            for k, i in enumerate(list(todo)):
                x = W[k, -1]
                X[i] = x
                dl = np.max(np.abs(x - y_lock))
                if dl < r_in:
                    lab[i] = "A"
                elif tree.query(x)[0] < 2e-3:
                    lab[i] = "B"
            todo = [i for i in todo if lab[i] == "U"]
        return lab

    def advance1(X):
        return batch(s, X, 1, STEPS, 1)[:, -1]

    return decide, advance1


def edge_state(F, y_lock, M, torus, start_dir=None, total=6000):
    s = FPUT(F)
    mu, q, p = critical_vectors(M)
    if start_dir is None:
        d = np.real(q); d /= np.linalg.norm(d)
        a, b = y_lock + 0.01 * d, y_lock + 2.5 * d
    else:
        a, b = y_lock + 0.01 * start_dir, y_lock + start_dir
    r_in = 1e-3
    decide, adv = make_decider(F, y_lock, torus, r_in, None)
    la, lb = decide(np.array([a, b]))
    start_used = "critical direction" if start_dir is None else "given direction"
    if (la != "A" or lb != "B") and start_dir is None:
        seg = torus[0] - y_lock
        a, b = y_lock + 0.01 * seg / np.linalg.norm(seg), torus[0].copy()
        la, lb = decide(np.array([a, b]))
        start_used = "locked->torus segment (fallback)"
    if la != "A" or lb != "B":
        return {"F": F, "error": f"bad initial bracket {la},{lb}"}, None
    H, seps, stats = track_edge(a, b, decide, adv, tol=1e-11, delta=1e-5, total=total)
    burn = min(len(H) // 3, 2000)
    E = H[burn:]
    z = (E - y_lock) @ np.conj(p)
    ang = np.unwrap(np.angle(z))
    rot_z = float(np.mean(np.diff(ang)) / (2 * np.pi))
    steps = np.max(np.abs(np.diff(E, axis=0)), axis=1)
    dist_lock = np.max(np.abs(E - y_lock), axis=1)
    tr = cKDTree(torus)
    dist_torus = tr.query(E)[0]
    sig, rates = separation_rate(seps)
    out = {"F": F, "start": start_used, "abs_mu": float(abs(mu)), "theta_over_2pi": float(abs(np.angle(mu)) / (2 * np.pi)),
           "tracked_periods": len(H), "burn_in": burn, "bisection_stats": stats[:3] + stats[-2:],
           "is_fixed_point": bool(np.median(steps) < 1e-6),
           "median_step_between_iterates": float(np.median(steps)),
           "abs_z_mean": float(np.mean(np.abs(z))), "abs_z_rel_spread": float(np.ptp(np.abs(z)) / np.mean(np.abs(z))),
           "rotation_number_critical_plane": rot_z,
           "supdist_to_locked_min_max": [float(dist_lock.min()), float(dist_lock.max())],
           "distance_to_stable_torus_min_median": [float(dist_torus.min()), float(np.median(dist_torus))],
           "E1_range": float(np.ptp(s.energies(E)[:, 0])), "E1_mean": float(s.energies(E)[:, 0].mean()),
           "instability_rate_per_period": sig, "n_rate_segments": len(rates)}
    if len(E) > 500 and not out["is_fixed_point"]:
        out["circle_fit"] = D.invariant_circle_fit(E, (10, 20, 40))["relative_rms_residual_by_harmonics"]
        P, _ = D.pca_plane(E)
        out["abs_rho_naff"] = abs(D.refined_frequency(P[:, 0] + 1j * P[:, 1]))
    return out, H


def lyap_top(F, y0, periods=16000, nvec=4):
    s = FPUT(F)
    y, cum = lyapunov_qr(y0, periods, STEPS, nvec, *s.args)
    h = periods // 2
    lam = (cum[-1] - cum[h - 1]) / ((periods - h) * s.T)
    q = periods // 4
    l3 = (cum[3 * q - 1] - cum[h - 1]) / (q * s.T)
    l4 = (cum[-1] - cum[3 * q - 1]) / ((periods - 3 * q) * s.T)
    return {"lambda": lam, "third_quarter": l3, "fourth_quarter": l4}, y


def main():
    tm = Timer()
    out = {}
    # locked orbits along F (continuation, RK4/200 map)
    y = np.zeros(16)
    s0 = FPUT(0.0)
    for F in np.arange(0, 0.0042, 2e-4):
        y, _, _ = newton_orbit(s0.with_F(F), y, STEPS)
    lock = {}

    def get_lock(F):
        key = round(F, 9)
        if key not in lock:
            near = min(lock, key=lambda k: abs(k - F)) if lock else None
            lock[key] = locked(F, lock[near][0] if near is not None else y)
        return lock[key]

    for F in np.round(np.arange(0.0042, 0.00466, 2e-5), 7):
        get_lock(F)
    # A: torus continuation
    tor = {}
    W, r = settle_torus(0.0045, np.zeros(16))
    tor[0.0045] = W
    yt = W[-1]
    for F in (0.0046, 0.00465):
        W, r = settle_torus(F, yt); tor[F] = W; yt = W[-1]
    yt = tor[0.0045][-1]
    for F in (0.0044, 0.0043):
        W, r = settle_torus(F, yt); tor[F] = W; yt = W[-1]
    out["A_torus_E1_range"] = {str(F): float(np.ptp(FPUT(F).energies(W)[:, 0])) for F, W in tor.items()}
    tm.mark("A_torus")

    # B: lower edge
    F_last, y_last = 0.0043, tor[0.0043][-1]
    steps_log = []
    F = 0.0043
    while F > 0.0040:
        Fn = round(F - 2e-5, 7)
        lab, p, yend, hist = persists(Fn, y_last, get_lock(Fn)[0])
        steps_log.append({"F": Fn, "outcome": lab, "periods": p})
        print("B step", Fn, lab, p, flush=True)
        if lab != "torus":
            F_lost = Fn
            break
        F, F_last, y_last = Fn, Fn, yend
    lo, hi, ylo = F_lost, F_last, y_last
    for _ in range(6):
        mid = 0.5 * (lo + hi)
        lab, p, yend, hist = persists(mid, ylo, get_lock(mid)[0])
        steps_log.append({"F": mid, "outcome": lab, "periods": p})
        print("B bisect", mid, lab, p, flush=True)
        if lab == "torus":
            hi, ylo = mid, yend
        else:
            lo = mid
    F_low = 0.5 * (lo + hi)
    out["B_lower_edge"] = {"log": steps_log, "bracket": [lo, hi], "F_low_estimate": F_low}
    tor[hi] = settle_torus(hi, ylo, periods=4000)[0]
    tm.mark("B_lower_edge")

    # C: ghost transit times below F_low (start from torus at F = hi)
    ghost = []
    for dF in (1e-6, 3e-6, 1e-5, 3e-5):
        F = lo - dF
        tau = transit_time(F, tor[hi][-1], get_lock(F)[0])
        ghost.append({"F": F, "dF_below_lo": dF, "transit_periods": tau})
        print("C ghost", F, tau, flush=True)
    pts = [(g["dF_below_lo"], g["transit_periods"]) for g in ghost if g["transit_periods"]]
    out["C_ghost"] = {"rows": ghost, "loglog_slope": float(np.polyfit(np.log([a for a, _ in pts]), np.log([b for _, b in pts]), 1)[0]) if len(pts) >= 3 else None,
                      "fold_prediction": -0.5, "note": "dF measured from the lower bracket end lo (F_low uncertainty <= hi - lo)"}
    tm.mark("C_ghost")

    # D: lambda_2 of the stable torus towards F_low
    lyap = []
    yv = tor[0.0045][-1]
    Fs_l = [0.0045, 0.0044, 0.0043, round(hi + 3e-5, 8), round(hi + 1e-5, 8), hi]
    for F in Fs_l:
        start = tor[min(tor, key=lambda k: abs(k - F))][-1]
        W, _ = settle_torus(F, start, periods=4000, keep=10)
        L, _ = lyap_top(F, W[-1])
        lyap.append({"F": F, "F_minus_F_low": F - F_low, **L})
        print("D lyap", F, np.round(L["lambda"], 7), flush=True)
    out["D_lyapunov_vs_F"] = lyap
    tm.mark("D_lyapunov")

    # E: edge states
    edges = []
    Hs = {}
    Fe = [0.00465, 0.0046, 0.0045, 0.0044, 0.0043, hi]
    for F in Fe:
        yl, M = get_lock(F)
        T = tor[min(tor, key=lambda k: abs(k - F))] if F not in tor else tor[F]
        if F not in tor:
            T = settle_torus(F, T[-1])[0]
            tor[F] = T
        e, H = edge_state(F, yl, M, T)
        edges.append(e)
        Hs[f"edge_F{F}"] = H if H is not None else np.zeros((0, 16))
        print("E edge", json.dumps({k: e.get(k) for k in ("F", "is_fixed_point", "abs_z_mean", "rotation_number_critical_plane",
                                                          "abs_rho_naff", "distance_to_stable_torus_min_median",
                                                          "instability_rate_per_period", "error")}, default=str), flush=True)
        tm.mark(f"E_edge_{F}")
    yl, M = get_lock(0.0045)
    seg = tor[0.0045][0] - yl
    e2, H2 = edge_state(0.0045, yl, M, tor[0.0045], start_dir=seg)
    e2["start"] = "locked->torus segment"
    Hs["edge_F0.0045_segment_start"] = H2 if H2 is not None else np.zeros((0, 16))
    tm.mark("E_edge_uniqueness")
    out["E_edge_states"] = edges
    out["E_edge_uniqueness_F0.0045"] = e2
    # compare with saddle orbit of the catalogue (Exp 3)
    cat = json.loads((ROOT / "results/exp3_multistability.json").read_text())["results"]["full"]["A_catalogue_F0.0045"]["orbits"]
    sad = np.array(next(o for o in cat if o["name"].startswith("saddle"))["y"])
    out["saddle_orbit_distance_to_edge_history_F0.0045"] = float(np.min(np.max(np.abs(Hs["edge_F0.0045"] - sad), axis=1))) if len(Hs["edge_F0.0045"]) else None
    save("exp8_edge_and_fold", {"config": {"rk4_steps": STEPS, "edge_tol": 1e-11, "edge_delta": 1e-5,
                                           "decision": "A: sup-dist to locked < 1e-3; B: within 2e-3 of the torus sample set"},
                                "results": out}, tm)
    save_npz("exp8_edge_histories", **Hs, **{f"torus_F{F}": W for F, W in tor.items()})
    print(json.dumps({k: out[k] for k in ("B_lower_edge", "C_ghost")}, indent=1, default=str))


if __name__ == "__main__":
    main()
