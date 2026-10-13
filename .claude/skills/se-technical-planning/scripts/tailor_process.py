#!/usr/bin/env python3
"""Tailor the 17 systems-engineering processes to a project's risk profile.

Base rigour from risk_class (low -> light, moderate -> standard, high -> rigorous), raised to
'rigorous' for specific processes when the project is safety-critical, regulated or uses novel
technology. Outputs per-process rigour and artifacts, recommended reviews, and required human
authorities. Flags inconsistent profiles (e.g. low risk but safety-critical).

Usage: tailor_process.py profile.json [--data tailoring.json] [--markdown] [--json]
Exit: 0 profile valid, 1 profile errors, 2 unreadable.
Scope: a proportionality heuristic proposed by this library; the decision owner approves the tailoring.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DEFAULT_DATA = Path(__file__).resolve().parents[1] / "assets" / "data" / "tailoring.json"
BASE = {"low": "light", "moderate": "standard", "high": "rigorous"}
ORDER = ["light", "standard", "rigorous"]


def _f(rid, sev, rule, msg):
    return {"id": rid, "severity": sev, "rule": rule, "message": msg}


def tailor(profile: dict, data: dict) -> dict:
    f = []
    rc = profile.get("risk_class")
    if rc not in BASE:
        f.append(_f("risk_class", "error", "risk-class", f"risk_class must be one of {sorted(BASE)}"))
    for k in ("safety_critical", "regulated", "novel_technology", "hardware", "software"):
        if k not in profile:
            f.append(_f(k, "warning", "missing-flag", f"'{k}' not stated — assumed false"))
        elif not isinstance(profile[k], bool):
            f.append(_f(k, "error", "flag-type", f"'{k}' must be true/false"))
    if not profile.get("decision_owner"):
        f.append(_f("decision_owner", "error", "no-decision-owner", "name the human decision owner"))
    ts = profile.get("team_size")
    if ts is not None and (not isinstance(ts, int) or ts < 1):
        f.append(_f("team_size", "error", "team-size", "team_size must be a positive integer"))
    if any(x["severity"] == "error" for x in f):
        return {"findings": f, "processes": [], "reviews": [], "authorities": []}
    if profile.get("safety_critical") and rc == "low":
        f.append(_f("risk_class", "warning", "risk-understated", "safety-critical project classed as low risk — confirm with the safety authority"))
    if profile.get("safety_critical") and not profile.get("safety_authority"):
        f.append(_f("safety_authority", "error", "no-safety-authority", "safety-critical work needs a named safety authority"))
    base = BASE[rc]
    raised = set()
    if profile.get("safety_critical"):
        raised |= set(data["safety_rigorous"])
    if profile.get("regulated"):
        raised |= set(data["regulated_rigorous"])
    if profile.get("novel_technology"):
        raised |= set(data["novel_rigorous"])
    procs = []
    for p in data["processes"]:
        lvl = "rigorous" if p["id"] in raised else base
        if not profile.get("hardware") and p["id"] in ("SE-05", "SE-06") and lvl != "rigorous":
            lvl = ORDER[max(0, ORDER.index(lvl) - 1)]
            note = "software-only: integration via CI pipeline"
        else:
            note = ""
        procs.append({"id": p["id"], "process": p["name"], "skill": p["skill"], "rigour": lvl,
                      "artifacts": p["artifacts"][lvl], "note": note})
    level_for_reviews = "rigorous" if rc == "high" else base
    reviews = list(data["reviews"][level_for_reviews])
    if profile.get("safety_critical") and not any(r.startswith("TRR") for r in reviews):
        reviews.append("TRR")
    auth = [{"role": "decision owner", "name": profile["decision_owner"], "approves": "baselines, gate decisions, tailoring"}]
    if profile.get("safety_critical"):
        auth.append({"role": "safety authority", "name": profile.get("safety_authority", "TBD"),
                     "approves": "hazard analysis, physical test authorisation, residual safety risk"})
    if profile.get("regulated"):
        auth.append({"role": "compliance / legal", "name": profile.get("compliance_authority", "TBD"),
                     "approves": "regulatory applicability and obligations"})
    return {"findings": f, "processes": procs, "reviews": reviews, "authorities": auth,
            "provenance": data.get("_provenance", "")}


def markdown(res: dict, profile: dict) -> str:
    lines = [f"# Process tailoring — {profile.get('project', '')}", "",
             "| ID | Process | Rigour | Skill | Artifacts |", "|---|---|---|---|---|"]
    for p in res["processes"]:
        lines.append(f"| {p['id']} | {p['process']} | {p['rigour']} | `{p['skill']}` | {p['artifacts']}{' — ' + p['note'] if p['note'] else ''} |")
    lines += ["", "Reviews: " + ", ".join(res["reviews"]), "", "Authorities:"]
    lines += [f"- {a['role']}: {a['name']} — approves {a['approves']}" for a in res["authorities"]]
    lines += ["", "_Proposed by tailor_process.py; requires approval by the decision owner._"]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Tailor SE processes to a project profile.")
    ap.add_argument("profile", type=Path)
    ap.add_argument("--data", type=Path, default=DEFAULT_DATA)
    ap.add_argument("--markdown", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        profile = json.loads(a.profile.read_text(encoding="utf-8"))
        data = json.loads(a.data.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 2
    res = tailor(profile, data)
    res["passed"] = not any(x["severity"] == "error" for x in res["findings"])
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        if res["processes"] and a.markdown:
            print(markdown(res, profile))
        elif res["processes"]:
            for p in res["processes"]:
                print(f"{p['id']} {p['process']:<38} {p['rigour']:<9} {p['artifacts']}")
            print("Reviews: " + ", ".join(res["reviews"]))
        for x in res["findings"]:
            print(f"{x['severity'].upper():8} {x['id']:<16} {x['rule']:<22} {x['message']}")
        print("Scope: library heuristic; the decision owner approves the tailoring.")
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
