#!/usr/bin/env python3
"""Check a technical data register: ownership, classification, access, retention, single source of truth.

Rules: duplicate IDs; missing owner/classification/retention/location; restricted or confidential data
without access roles; credentials embedded in locations (error, value redacted in output); multiple
source-of-truth entries for one title; personal data without lawful basis; export-controlled data
flagged for human review; stale entries (--as-of, --max-age-days).

Usage: data_register_check.py register.csv [--as-of YYYY-MM-DD] [--max-age-days 365] [--json]
Exit: 0 no errors, 1 errors, 2 unreadable.
Scope: register hygiene only; legal classification and data-protection compliance need qualified review.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

CLASSES = {"public", "internal", "confidential", "restricted", "export_controlled"}
CRED = re.compile(r"://[^/\s:@]+:[^/\s@]+@|(?:password|passwd|pwd|token|secret|api[_-]?key)=", re.I)


def _f(rid, sev, rule, msg):
    return {"id": rid, "severity": sev, "rule": rule, "message": msg}


def check(rows: list[dict], as_of: date | None = None, max_age: int = 365) -> dict:
    f = []
    ids = Counter(r.get("data_id") for r in rows)
    sot: dict[str, list[str]] = {}
    for r in rows:
        did = r.get("data_id") or "<blank>"
        if ids[r.get("data_id")] > 1:
            f.append(_f(did, "error", "duplicate-id", "data id used more than once"))
        for k in ("owner", "classification", "location", "retention"):
            if not r.get(k):
                f.append(_f(did, "error", f"missing-{k}", f"no {k}"))
        cls = r.get("classification", "").lower()
        if cls and cls not in CLASSES:
            f.append(_f(did, "error", "classification", f"classification '{r['classification']}' not in {sorted(CLASSES)}"))
        if cls in {"confidential", "restricted", "export_controlled"} and not r.get("access_roles"):
            f.append(_f(did, "error", "no-access-control", f"{cls} data has no access roles"))
        if cls == "export_controlled":
            f.append(_f(did, "warning", "export-control-review", "export-controlled data — confirm handling with a qualified export-control officer"))
        if CRED.search(r.get("location", "")):
            f.append(_f(did, "error", "credential-in-location", "location contains embedded credentials (value redacted) — remove and rotate"))
        if r.get("retention", "").lower() in {"forever", "indefinite", "permanent"}:
            f.append(_f(did, "warning", "unbounded-retention", "indefinite retention — justify or bound it"))
        if r.get("contains_personal_data", "").lower() in {"yes", "true", "y"} and not r.get("lawful_basis"):
            f.append(_f(did, "error", "personal-data-no-basis", "personal data without a recorded lawful basis (needs data-protection review)"))
        if r.get("source_of_truth", "").lower() in {"yes", "true", "y"}:
            sot.setdefault(re.sub(r"\s*copy$", "", r.get("title", "").strip().lower()), []).append(did)
        if as_of and r.get("last_updated"):
            try:
                age = (as_of - date.fromisoformat(r["last_updated"])).days
                if age > max_age:
                    f.append(_f(did, "warning", "stale", f"last updated {age} days ago"))
            except ValueError:
                f.append(_f(did, "error", "date-format", "last_updated must be YYYY-MM-DD"))
    for title, dids in sot.items():
        if len(dids) > 1:
            f.append(_f(";".join(dids), "error", "multiple-sources-of-truth", f"'{title}' has {len(dids)} sources of truth"))
    sev = Counter(x["severity"] for x in f)
    return {"findings": f, "summary": {"entries": len(rows), "errors": sev.get("error", 0), "warnings": sev.get("warning", 0)}}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check a technical data register.")
    ap.add_argument("csv", type=Path)
    ap.add_argument("--as-of")
    ap.add_argument("--max-age-days", type=int, default=365)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        with a.csv.open(newline="", encoding="utf-8-sig") as fh:
            rows = [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(fh)]
        as_of = date.fromisoformat(a.as_of) if a.as_of else None
    except (OSError, ValueError, csv.Error) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 2
    res = check(rows, as_of, a.max_age_days)
    res["passed"] = res["summary"]["errors"] == 0
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        for x in res["findings"]:
            print(f"{x['severity'].upper():8} {x['id']:<26} {x['rule']:<26} {x['message']}")
        print(f"\n{'PASS' if res['passed'] else 'FAIL'}: {res['summary']}")
        print("Scope: register hygiene; classification and data-protection decisions need qualified review.")
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
