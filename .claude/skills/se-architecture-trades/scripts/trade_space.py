#!/usr/bin/env python3
"""Enumerate a morphological trade space and screen it with compatibility rules.

Input JSON: functions[] each with options[] (id, name, trl), incompatible pairs, requires pairs
(option A requires option B). Output: feasible concept combinations, immature-option flags
(TRL below threshold), and optionally a decision.json skeleton for se-decision-analysis.

Usage: trade_space.py trade.json [--max 50] [--export-decision out.json --criteria criteria.json] [--json]
Exit: 0 valid trade space with >=1 feasible concept, 1 input errors or no feasible concept, 2 unreadable.
Scope: generates and screens candidates; it does not evaluate them (use se-decision-analysis).
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from collections import Counter
from pathlib import Path


def _f(rid, sev, rule, msg):
    return {"id": rid, "severity": sev, "rule": rule, "message": msg}


def analyse(d: dict, max_out: int = 50) -> dict:
    f = []
    funcs = d.get("functions", [])
    if not funcs:
        return {"findings": [_f("-", "error", "no-functions", "no functions defined")], "concepts": [], "summary": {"errors": 1}}
    fc = Counter(x.get("id") for x in funcs)
    for k, n in fc.items():
        if n > 1:
            f.append(_f(str(k), "error", "duplicate-function", "function listed twice"))
    opts = {}
    for fn in funcs:
        if not fn.get("options"):
            f.append(_f(fn.get("id", "?"), "error", "no-options", "function has no options"))
        for o in fn.get("options", []):
            if o["id"] in opts:
                f.append(_f(o["id"], "error", "duplicate-option", "option id used in more than one place"))
            opts[o["id"]] = {**o, "function": fn.get("id")}
            trl = o.get("trl")
            if trl is not None and not (isinstance(trl, int) and 1 <= trl <= 9):
                f.append(_f(o["id"], "error", "trl-range", "TRL must be an integer 1-9"))
    for kind in ("incompatible", "requires"):
        for pair in d.get(kind, []):
            if len(pair) != 2 or pair[0] == pair[1]:
                f.append(_f(str(pair), "error", f"bad-{kind}", "rule must name two different options"))
                continue
            for p in pair:
                if p not in opts:
                    f.append(_f(p, "error", "unknown-option", f"{kind} rule references unknown option"))
    if any(x["severity"] == "error" for x in f):
        return {"findings": f, "concepts": [], "summary": {"errors": sum(x["severity"] == "error" for x in f)}}
    inc = {frozenset(p) for p in d.get("incompatible", [])}
    req = [tuple(p) for p in d.get("requires", [])]
    threshold = d.get("trl_threshold", 0)
    total, feasible = 0, []
    for combo in itertools.product(*[[o["id"] for o in fn["options"]] for fn in funcs]):
        total += 1
        s = set(combo)
        if any(frozenset(pair) <= s for pair in inc):
            continue
        if any(a in s and b not in s for a, b in req):
            continue
        trls = [opts[c].get("trl") for c in combo if opts[c].get("trl") is not None]
        feasible.append({"concept": "+".join(combo), "options": list(combo),
                         "min_trl": min(trls) if trls else None,
                         "immature": [c for c in combo if (opts[c].get("trl") or 9) < threshold]})
    if not feasible:
        f.append(_f(d.get("trade_id", "-"), "error", "no-feasible-concept", "compatibility rules eliminate every combination"))
    for o, info in opts.items():
        if not any(o in c["options"] for c in feasible):
            f.append(_f(o, "info", "option-never-feasible", "option appears in no feasible concept — check rules"))
    if len(feasible) > max_out:
        f.append(_f(d.get("trade_id", "-"), "warning", "large-trade-space",
                    f"{len(feasible)} feasible concepts — prune with musts before scoring"))
    sev = Counter(x["severity"] for x in f)
    feasible.sort(key=lambda c: (-(c["min_trl"] or 0), c["concept"]))
    return {"findings": f, "concepts": feasible[:max_out],
            "summary": {"combinations": total, "feasible": len(feasible), "errors": sev.get("error", 0),
                        "with_immature_options": sum(1 for c in feasible if c["immature"])}}


def decision_skeleton(d: dict, concepts: list[dict], criteria: list[dict]) -> dict:
    return {"decision_id": d.get("trade_id", "") + "-DEC", "question": "Select concept for preliminary design",
            "decision_owner": "", "criteria": criteria,
            "alternatives": [{"id": c["concept"], "name": c["concept"],
                              "scores": {cr["id"]: {"value": None, "basis": "", "source": ""} for cr in criteria}}
                             for c in concepts]}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Enumerate and screen a morphological trade space.")
    ap.add_argument("json_file", type=Path)
    ap.add_argument("--max", type=int, default=50)
    ap.add_argument("--export-decision", type=Path)
    ap.add_argument("--criteria", type=Path, help="criteria list JSON for the exported skeleton")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        d = json.loads(a.json_file.read_text(encoding="utf-8"))
        criteria = json.loads(a.criteria.read_text(encoding="utf-8")) if a.criteria else []
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 2
    res = analyse(d, a.max)
    res["passed"] = res["summary"].get("errors", 1) == 0
    if a.export_decision and res["passed"]:
        a.export_decision.write_text(json.dumps(decision_skeleton(d, res["concepts"], criteria), indent=2), encoding="utf-8")
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        for c in res["concepts"]:
            print(f"{c['concept']:<32} min TRL {c['min_trl']}" + (f"  immature: {c['immature']}" if c["immature"] else ""))
        for x in res["findings"]:
            print(f"{x['severity'].upper():8} {x['id']:<16} {x['rule']:<24} {x['message']}")
        print(f"\n{'PASS' if res['passed'] else 'FAIL'}: {res['summary']}")
        print("Scope: candidate generation/screening only; evaluate with se-decision-analysis.")
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
