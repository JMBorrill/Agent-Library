#!/usr/bin/env python3
"""Weighted-criteria decision matrix with feasibility screen, sensitivity and evidence checks.

Steps: validate input -> screen alternatives against must-criteria thresholds -> min-max normalise
each criterion over feasible alternatives -> weighted sum -> rank -> weight sensitivity (+/- pct,
proportional renormalisation) -> switching weight per criterion -> evidence-basis audit.

Usage: decision_matrix.py decision.json [--json]
Exit: 0 analysis complete with no errors, 1 input errors (analysis not trustworthy), 2 unreadable.
Scope: an aid to a human decision owner; the ranking is only as good as the criteria, weights and
scores supplied. Output is a recommendation, never a decision.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

BASES = {"measured", "test", "analysis", "estimate", "judgement", "heritage", "vendor"}
WEAK_BASES = {"judgement", "estimate", "vendor"}


def _f(rid, sev, rule, msg):
    return {"id": rid, "severity": sev, "rule": rule, "message": msg}


def _score(alt: dict, cid: str):
    s = alt.get("scores", {}).get(cid)
    if isinstance(s, dict):
        return s.get("value"), s.get("basis", "")
    return s, ""


def normalise(values: dict[str, float], direction: str) -> dict[str, float]:
    lo, hi = min(values.values()), max(values.values())
    if hi == lo:
        return {k: 1.0 for k in values}
    if direction == "min":
        return {k: (hi - v) / (hi - lo) for k, v in values.items()}
    return {k: (v - lo) / (hi - lo) for k, v in values.items()}


def totals(norm: dict[str, dict[str, float]], weights: dict[str, float]) -> dict[str, float]:
    alts = next(iter(norm.values())).keys() if norm else []
    return {a: sum(weights[c] * norm[c][a] for c in norm) for a in alts}


def reweight(weights: dict[str, float], cid: str, new_w: float) -> dict[str, float]:
    """Set weight of cid to new_w and scale the others proportionally so the sum stays 1."""
    rest = 1.0 - weights[cid]
    out = {}
    for c, w in weights.items():
        if c == cid:
            out[c] = new_w
        else:
            out[c] = (w / rest) * (1.0 - new_w) if rest > 0 else (1.0 - new_w) / (len(weights) - 1)
    return out


def winner(t: dict[str, float]) -> str:
    return sorted(t.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]


def analyse(d: dict) -> dict:
    findings: list[dict] = []
    crit = d.get("criteria", [])
    alts = d.get("alternatives", [])
    settings = {"sensitivity_pct": 20, "close_margin": 0.05, **d.get("settings", {})}
    did = d.get("decision_id", "-")
    if not d.get("decision_owner"):
        findings.append(_f(did, "error", "no-decision-owner", "a named human decision owner is required"))
    if not d.get("question"):
        findings.append(_f(did, "warning", "no-question", "state the decision question"))
    if len(alts) < 2:
        findings.append(_f(did, "error", "too-few-alternatives", "need at least two alternatives (include do-nothing/baseline where meaningful)"))
    if not crit:
        findings.append(_f(did, "error", "no-criteria", "no criteria"))
    if any(f["severity"] == "error" for f in findings if f["rule"] in {"too-few-alternatives", "no-criteria"}):
        return {"findings": findings, "summary": {"errors": len([f for f in findings if f["severity"] == "error"])}}
    for i, c in enumerate(crit):
        if not isinstance(c, dict) or not c.get("id"):
            findings.append(_f(f"criteria[{i}]", "error", "criterion-id", "every criterion needs an id"))
    for i, a in enumerate(alts):
        if not isinstance(a, dict) or not a.get("id"):
            findings.append(_f(f"alternatives[{i}]", "error", "alternative-id", "every alternative needs an id"))
    if any(f["rule"] in {"criterion-id", "alternative-id"} for f in findings):
        return {"findings": findings, "summary": {"errors": sum(f["severity"] == "error" for f in findings)}}
    ids = Counter(c.get("id") for c in crit)
    for c, n in ids.items():
        if n > 1:
            findings.append(_f(str(c), "error", "duplicate-criterion", "criterion id repeated"))
    weights = {}
    for c in crit:
        w = c.get("weight")
        if not isinstance(w, (int, float)) or w < 0:
            findings.append(_f(c.get("id", "?"), "error", "weight", "weight must be a non-negative number"))
            continue
        if c.get("direction", "max") not in ("max", "min"):
            findings.append(_f(c["id"], "error", "direction", "direction must be max or min"))
        weights[c["id"]] = float(w)
    total_w = sum(weights.values())
    if total_w <= 0:
        findings.append(_f(did, "error", "weights-sum", "weights sum to zero"))
        return {"findings": findings, "summary": {"errors": 1}}
    if abs(total_w - 1.0) > 1e-6:
        findings.append(_f(did, "warning", "weights-normalised", f"weights summed to {total_w:g}; normalised to 1"))
        weights = {k: v / total_w for k, v in weights.items()}
    # scores present & numeric
    for a in alts:
        for c in crit:
            v, basis = _score(a, c["id"])
            if not isinstance(v, (int, float)):
                findings.append(_f(a.get("id", "?"), "error", "missing-score", f"no numeric score for criterion {c['id']}"))
            elif basis and basis not in BASES:
                findings.append(_f(a["id"], "warning", "basis", f"unknown basis '{basis}' for {c['id']}"))
            elif not basis:
                findings.append(_f(a["id"], "warning", "no-basis", f"score for {c['id']} has no evidence basis"))
    if any(f["rule"] in {"missing-score", "weight", "direction", "duplicate-criterion"} for f in findings):
        return {"findings": findings, "summary": {"errors": sum(f['severity'] == 'error' for f in findings)}}
    # feasibility screen
    feasible, screened = [], {}
    for a in alts:
        reasons = []
        for c in crit:
            v, _ = _score(a, c["id"])
            must = c.get("must") or {}
            if "min" in must and v < must["min"]:
                reasons.append(f"{c['id']}={v} < must-min {must['min']}")
            if "max" in must and v > must["max"]:
                reasons.append(f"{c['id']}={v} > must-max {must['max']}")
        if reasons:
            screened[a["id"]] = reasons
        else:
            feasible.append(a)
    for aid, reasons in screened.items():
        findings.append(_f(aid, "info", "screened-out", "; ".join(reasons)))
    if not feasible:
        findings.append(_f(did, "error", "no-feasible-alternative", "every alternative fails a must-criterion"))
        return {"findings": findings, "summary": {"errors": 1}, "screened": screened}
    norm = {}
    mode = settings.get("normalisation", "minmax")
    if mode not in ("minmax", "none"):
        findings.append(_f(did, "error", "normalisation", "settings.normalisation must be 'minmax' or 'none'"))
        return {"findings": findings, "summary": {"errors": 1}}
    if mode == "minmax" and len(feasible) < 3:
        findings.append(_f(did, "warning", "minmax-few-alternatives",
                           "min-max normalisation with fewer than 3 alternatives maps scores to 0/1 and exaggerates "
                           "differences; consider settings.normalisation='none' with scores on a common scale"))
    scale_max = float(settings.get("scale_max", 1.0))
    if mode == "none":
        if scale_max <= 0:
            findings.append(_f(did, "error", "scale-max", "scale_max must be > 0"))
            return {"findings": findings, "summary": {"errors": 1}}
        bad = [(a["id"], c["id"]) for a in feasible for c in crit
               if not 0 <= float(_score(a, c["id"])[0]) <= scale_max]
        for aid, cid in bad:
            findings.append(_f(aid, "error", "score-out-of-scale", f"score for {cid} outside 0..{scale_max:g}"))
        if bad:
            return {"findings": findings, "summary": {"errors": sum(f["severity"] == "error" for f in findings)}}
    for c in crit:
        vals = {a["id"]: float(_score(a, c["id"])[0]) for a in feasible}
        if mode == "none":
            if c.get("direction", "max") == "min":
                norm[c["id"]] = {k: (scale_max - v) / scale_max for k, v in vals.items()}
            else:
                norm[c["id"]] = {k: v / scale_max for k, v in vals.items()}
        else:
            norm[c["id"]] = normalise(vals, c.get("direction", "max"))
        if len(set(vals.values())) == 1 and len(vals) > 1:
            findings.append(_f(c["id"], "info", "non-discriminating", "all feasible alternatives score the same"))
    t = totals(norm, weights)
    ranking = sorted(t.items(), key=lambda kv: (-kv[1], kv[0]))
    best = ranking[0][0]
    margin = ranking[0][1] - ranking[1][1] if len(ranking) > 1 else None
    if margin is not None and margin < settings["close_margin"]:
        findings.append(_f(did, "warning", "too-close-to-call",
                           f"winner leads by {margin:.3f} (< {settings['close_margin']}) — treat as a tie; gather evidence"))
    # sensitivity
    sens = []
    pct = settings["sensitivity_pct"] / 100.0
    for c in crit:
        cid = c["id"]
        flips = []
        for factor in (1 - pct, 1 + pct):
            nw = min(1.0, max(0.0, weights[cid] * factor))
            w2 = reweight(weights, cid, nw)
            wn = winner(totals(norm, w2))
            if wn != best:
                flips.append({"weight": round(nw, 4), "winner": wn})
        switch = None
        if len(feasible) > 1:
            for step in range(0, 1001):
                nw = step / 1000
                wn = winner(totals(norm, reweight(weights, cid, nw)))
                if wn != best:
                    if switch is None or abs(nw - weights[cid]) < abs(switch["weight"] - weights[cid]):
                        switch = {"weight": nw, "winner": wn}
        sens.append({"criterion": cid, "weight": round(weights[cid], 4), "flips_within_pct": flips, "switching_weight": switch})
        if flips:
            findings.append(_f(cid, "warning", "rank-sensitive",
                               f"a ±{settings['sensitivity_pct']}% change in weight of {cid} changes the winner"))
    # evidence quality of winner
    wa = next(a for a in feasible if a["id"] == best)
    weak = sum(weights[c["id"]] * norm[c["id"]][best] for c in crit if _score(wa, c["id"])[1] in WEAK_BASES)
    share = weak / t[best] if t[best] > 0 else 0.0
    if share > 0.5:
        findings.append(_f(best, "warning", "weak-evidence",
                           f"{share:.0%} of the winner's score rests on judgement/estimate/vendor claims"))
    sev = Counter(f["severity"] for f in findings)
    return {
        "findings": findings,
        "weights": {k: round(v, 4) for k, v in weights.items()},
        "ranking": [{"alternative": a, "score": round(s, 4)} for a, s in ranking],
        "screened": screened,
        "sensitivity": sens,
        "recommendation": {"alternative": best, "margin": None if margin is None else round(margin, 4),
                           "status": "recommendation — requires approval by " + (d.get("decision_owner") or "a named owner")},
        "summary": {"errors": sev.get("error", 0), "warnings": sev.get("warning", 0),
                    "feasible": len(feasible), "screened": len(screened), "weak_evidence_share": round(share, 3)},
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Weighted decision matrix with sensitivity analysis.")
    ap.add_argument("json_file", type=Path)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        d = json.loads(a.json_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cannot read {a.json_file}: {exc}", file=sys.stderr)
        return 2
    res = analyse(d)
    res["passed"] = res["summary"].get("errors", 1) == 0
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        for r in res.get("ranking", []):
            print(f"{r['alternative']:<12} {r['score']:.4f}")
        for s in res.get("sensitivity", []):
            sw = s["switching_weight"]
            print(f"  {s['criterion']:<8} w={s['weight']:<7} switch at {sw['weight'] if sw else '—'}"
                  f"{' -> ' + sw['winner'] if sw else ''}")
        for f in res["findings"]:
            print(f"{f['severity'].upper():8} {f['id']:<14} {f['rule']:<24} {f['message']}")
        if "recommendation" in res:
            print(f"\nRecommendation: {res['recommendation']}")
        print("Scope: decision aid only; the decision owner decides.")
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
