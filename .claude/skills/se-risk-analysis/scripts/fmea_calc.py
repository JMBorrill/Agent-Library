#!/usr/bin/env python3
"""Compute and check an FMEA worksheet (severity x occurrence x detection = RPN).

RPN is an ordinal product with known weaknesses (different S/O/D combinations give equal RPNs);
therefore high-severity modes are flagged regardless of RPN.

Usage: fmea_calc.py fmea.csv [--severity-review 9] [--rpn-action 100] [--json]
Exit: 0 no errors, 1 errors (e.g. missing action on a mode that needs one), 2 unreadable.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

REQUIRED = ["fmea_id", "item", "failure_mode", "effect", "cause", "severity", "occurrence", "detection"]


def _f(rid, sev, rule, msg):
    return {"id": rid, "severity": sev, "rule": rule, "message": msg}


def analyse(cols, rows, severity_review=9, rpn_action=100):
    findings, ranked = [], []
    missing = [c for c in REQUIRED if c not in cols]
    if missing:
        return {"findings": [_f("-", "error", "missing-columns", ", ".join(missing))], "ranked": [], "summary": {}}
    seen = Counter(r["fmea_id"] for r in rows)
    for r in rows:
        fid = r["fmea_id"] or "<blank>"
        if seen[r["fmea_id"]] > 1:
            findings.append(_f(fid, "error", "duplicate-id", "duplicate fmea_id"))
        try:
            s, o, d = (int(r[k]) for k in ("severity", "occurrence", "detection"))
        except ValueError:
            findings.append(_f(fid, "error", "non-integer", "S/O/D must be integers 1-10"))
            continue
        if not all(1 <= x <= 10 for x in (s, o, d)):
            findings.append(_f(fid, "error", "range", "S/O/D must be within 1-10"))
            continue
        rpn = s * o * d
        needs_action = s >= severity_review or rpn >= rpn_action
        if needs_action and not r.get("recommended_action"):
            findings.append(_f(fid, "error", "no-action", f"S={s}, RPN={rpn} requires a recommended action"))
        if needs_action and not r.get("owner"):
            findings.append(_f(fid, "error", "no-owner", "mode requiring action has no owner"))
        if s >= severity_review:
            findings.append(_f(fid, "warning", "high-severity", f"severity {s} — review regardless of RPN ({rpn}); escalate if safety-related"))
        if d >= 8:
            findings.append(_f(fid, "info", "poor-detection", f"detection {d}: failure unlikely to be caught before effect"))
        ranked.append({"fmea_id": fid, "rpn": rpn, "severity": s, "needs_action": needs_action})
    ranked.sort(key=lambda x: (0 if x["severity"] >= severity_review else 1, -x["rpn"]))
    sev = Counter(f["severity"] for f in findings)
    return {"findings": findings, "ranked": ranked,
            "summary": {"modes": len(rows), "needing_action": sum(x["needs_action"] for x in ranked),
                        "errors": sev.get("error", 0), "warnings": sev.get("warning", 0)}}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Compute and check an FMEA worksheet.")
    ap.add_argument("csv", type=Path)
    ap.add_argument("--severity-review", type=int, default=9)
    ap.add_argument("--rpn-action", type=int, default=100)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        with a.csv.open(newline="", encoding="utf-8-sig") as fh:
            rd = csv.DictReader(fh)
            rows = [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in rd]
            cols = [c.strip() for c in rd.fieldnames or []]
    except (OSError, csv.Error) as exc:
        print(f"cannot read {a.csv}: {exc}", file=sys.stderr)
        return 2
    res = analyse(cols, rows, a.severity_review, a.rpn_action)
    res["passed"] = res["summary"].get("errors", 1) == 0
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        for x in res["ranked"]:
            print(f"{x['fmea_id']:<10} S={x['severity']:<3} RPN={x['rpn']:<5} {'ACTION' if x['needs_action'] else ''}")
        for f in res["findings"]:
            print(f"{f['severity'].upper():8} {f['id']:<10} {f['rule']:<16} {f['message']}")
        print(f"\n{'PASS' if res['passed'] else 'FAIL'}: {res['summary']}")
        print("Scope: ordinal prioritisation aid; does not establish safety.")
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
