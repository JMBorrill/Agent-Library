#!/usr/bin/env python3
"""Audit source metadata freshness and access status; list sources needing manual re-check.

Flags: review_by date passed (error), last_checked older than --max-age-days (warning), access status
other than VERIFIED (re-attempt primary access), missing audit file, extracts whose 'retrieved' date is
older than --max-age-days. Link reachability is NOT checked (no network) and would not prove content is
unchanged anyway.

Usage: source_freshness.py [--as-of YYYY-MM-DD] [--max-age-days 180] [--json]
Exit: 0 nothing overdue, 1 at least one review_by date passed or audit missing.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def audit(as_of: date, max_age: int) -> dict:
    reg = json.loads((ROOT / "sources" / "registry.json").read_text(encoding="utf-8"))
    rows, errors = [], 0
    for r in reg:
        issues = []
        rb = date.fromisoformat(r["review_by"])
        lc = date.fromisoformat(r["last_checked"])
        if rb < as_of:
            issues.append(("error", f"review_by {rb} has passed"))
        if (as_of - lc).days > max_age:
            issues.append(("warning", f"last checked {(as_of - lc).days} days ago"))
        if r["access_status"] != "VERIFIED":
            issues.append(("info", f"access {r['access_status']} — re-attempt primary access and update audit"))
        if not (ROOT / r["audit"]).is_file():
            issues.append(("error", "audit file missing"))
        errors += sum(1 for s, _ in issues if s == "error")
        rows.append({"source_id": r["id"], "access_status": r["access_status"], "last_checked": r["last_checked"],
                     "review_by": r["review_by"], "issues": [{"severity": s, "message": m} for s, m in issues]})
    extracts = []
    for p in sorted((ROOT / "sources" / "extracts").glob("*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            ret = d.get("retrieved")
            age = (as_of - date.fromisoformat(ret)).days if ret else None
        except (ValueError, json.JSONDecodeError):
            age = None
        extracts.append({"file": p.name, "retrieved": d.get("retrieved") if isinstance(d, dict) else None,
                         "stale": age is not None and age > max_age})
    return {"as_of": as_of.isoformat(), "sources": rows, "extracts": extracts, "errors": errors}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--as-of", default=date.today().isoformat())
    ap.add_argument("--max-age-days", type=int, default=180)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    res = audit(date.fromisoformat(a.as_of), a.max_age_days)
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        print(f"Source freshness as of {res['as_of']}")
        for r in res["sources"]:
            flag = "OVERDUE" if any(i["severity"] == "error" for i in r["issues"]) else "ok"
            print(f"  {r['source_id']:<16} {r['access_status']:<19} review_by {r['review_by']}  {flag}")
            for i in r["issues"]:
                if i["severity"] != "info":
                    print(f"      {i['severity'].upper()}: {i['message']}")
        recheck = [r["source_id"] for r in res["sources"] if r["access_status"] != "VERIFIED"]
        print(f"\nRe-attempt primary access for {len(recheck)} sources: {', '.join(recheck)}")
        stale = [e["file"] for e in res["extracts"] if e["stale"]]
        print(f"Stale extracts: {stale or 'none'}")
        print("Note: reachability is not proof that content is unchanged; re-read the source when re-checking.")
    return 1 if res["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
