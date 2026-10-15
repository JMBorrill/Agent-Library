"""Edge tracking (bisection along a line between two basins, then forward tracking of the boundary
trajectory) for maps given as batch-advance functions.

The basin boundary between two attractors is the stable manifold of an invariant set with one
unstable direction (an "edge state"). Bisection places a trajectory on the boundary to precision
`tol`; it then stays near the edge state for ~ln(delta/tol)/sigma_u iterations, after which the
bracketing pair is re-bisected. The midpoint history converges to the edge state.
"""
from __future__ import annotations

import numpy as np


def bisect_edge(a, b, decide, tol, k=4, max_rounds=80):
    """a decides 'A', b decides 'B'. decide(X) -> list of labels in {'A','B','U'} for rows of X."""
    rounds = 0
    nundec = 0
    while np.max(np.abs(a - b)) > tol and rounds < max_rounds:
        fr = np.arange(1, k + 1) / (k + 1)
        pts = a[None, :] + fr[:, None] * (b - a)[None, :]
        labs = decide(pts)
        nundec += sum(1 for l in labs if l == "U")
        seq = ["A"] + list(labs) + ["B"]
        pos = [a] + list(pts) + [b]
        iB = next(i for i, l in enumerate(seq) if l == "B")
        iA = max(i for i in range(iB) if seq[i] == "A")
        a, b = pos[iA].copy(), pos[iB].copy()
        rounds += 1
    return a, b, {"rounds": rounds, "undecided": nundec, "final_gap": float(np.max(np.abs(a - b)))}


def track_edge(a, b, decide, advance1, tol=1e-11, delta=1e-5, total=6000, max_refinements=40):
    """Return midpoint history (total x dim), separation-growth samples and bisection stats."""
    hist, seps, stats = [], [], []
    for _ in range(max_refinements):
        a, b, st = bisect_edge(a, b, decide, tol)
        stats.append(st)
        seg = []
        while np.max(np.abs(a - b)) < delta and len(hist) < total:
            X = advance1(np.array([a, b]))
            a, b = X[0], X[1]
            hist.append(0.5 * (a + b))
            seg.append(np.max(np.abs(a - b)))
        seps.append(seg)
        if len(hist) >= total:
            break
    return np.array(hist), seps, stats


def separation_rate(seps):
    """Median exponential growth rate per iteration of |a-b| over tracking segments."""
    rates = []
    for s in seps:
        s = np.asarray(s)
        if len(s) > 50:
            n = np.arange(len(s))
            sel = s > 10 * s[0]
            if sel.sum() > 20:
                rates.append(np.polyfit(n[sel], np.log(s[sel]), 1)[0])
    return float(np.median(rates)) if rates else None, rates
