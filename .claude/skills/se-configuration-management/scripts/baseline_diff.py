#!/usr/bin/env python3
"""Compare two baselines of a controlled register and audit changes against the change log.

Works on any CSV register with a key column (auto-detected: id, interface_id, risk_id, ci_id,
activity_id). Reports added / removed / modified items (field-level) and flags:
  uncontrolled-change   controlled item modified without an approved CR naming it
  deleted-not-retired   controlled item removed instead of being retired
  retired-id-reused     a retired ID re-appears with new content or status
  approval-without-cr   status changed to approved/baselined without an approved CR (warning)
  cr-not-implemented    approved CR whose items show no change (warning)
  rejected-cr-applied   change applied although its CR was rejected

Usage: baseline_diff.py OLD.csv NEW.csv [--changes change-log.csv] [--key COLUMN] [--json]
Exit: 0 no errors, 1 errors, 2 unreadable input / no key column.
Scope: detects differences between files; whether a change is technically sound is a human decision.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

KEYS = ("id", "interface_id", "risk_id", "ci_id", "activity_id")
CONTROLLED = {"approved", "baselined", "agreed", "released"}


def read(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        rd = csv.DictReader(fh)
        rows = [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in rd]
        return [c.strip() for c in rd.fieldnames or []], rows


def _f(rid, sev, rule, msg):
    return {"id": rid, "severity": sev, "rule": rule, "message": msg}


def diff(old_rows, new_rows, key, changes=None) -> dict:
    findings = []
    old = {r[key]: r for r in old_rows if r.get(key)}
    new = {r[key]: r for r in new_rows if r.get(key)}
    approved_crs: dict[str, list[str]] = {}
    rejected_crs: dict[str, list[str]] = {}
    for c in changes or []:
        targets = [x.strip() for x in re.split(r"[;,]", c.get("changed_ids", "")) if x.strip()]
        st = c.get("status", "").lower()
        for t in targets:
            if st == "approved":
                if not c.get("approved_by"):
                    findings.append(_f(c.get("cr_id", "?"), "error", "cr-without-approver", "approved CR has no approved_by"))
                approved_crs.setdefault(t, []).append(c.get("cr_id", "?"))
            elif st == "rejected":
                rejected_crs.setdefault(t, []).append(c.get("cr_id", "?"))
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    modified = {}
    for k in sorted(set(old) & set(new)):
        fields = {f: {"old": old[k].get(f, ""), "new": new[k].get(f, "")}
                  for f in sorted(set(old[k]) | set(new[k])) if old[k].get(f, "") != new[k].get(f, "")}
        if fields:
            modified[k] = fields
    for k in removed:
        if old[k].get("status", "").lower() in CONTROLLED:
            findings.append(_f(k, "error", "deleted-not-retired", "controlled item removed — retire it (status=retired) instead"))
    for k, fields in modified.items():
        ost = old[k].get("status", "").lower()
        nst = new[k].get("status", "").lower()
        if ost == "retired":
            findings.append(_f(k, "error", "retired-id-reused", "retired identifier re-used with new content; allocate a new ID"))
            continue
        if k in rejected_crs and k not in approved_crs:
            findings.append(_f(k, "error", "rejected-cr-applied", f"changed although CR {rejected_crs[k]} was rejected"))
        if ost in CONTROLLED and k not in approved_crs:
            findings.append(_f(k, "error", "uncontrolled-change",
                               f"controlled item modified ({', '.join(fields)}) without an approved CR"))
        if nst in CONTROLLED and ost not in CONTROLLED and k not in approved_crs:
            findings.append(_f(k, "warning", "approval-without-cr",
                               f"status {ost or '-'} -> {nst} without an approved CR/baseline record"))
    for k, crs in approved_crs.items():
        if k in old and k not in modified and k not in removed:
            findings.append(_f(k, "warning", "cr-not-implemented", f"approved CR {crs} but no change found in new baseline"))
        if k not in old and k not in new:
            findings.append(_f(k, "warning", "cr-unknown-item", f"CR {crs} names an item absent from both baselines"))
    sev = Counter(f["severity"] for f in findings)
    return {"added": added, "removed": removed, "modified": modified, "findings": findings,
            "summary": {"added": len(added), "removed": len(removed), "modified": len(modified),
                        "errors": sev.get("error", 0), "warnings": sev.get("warning", 0)}}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Diff two baselines and audit against the change log.")
    ap.add_argument("old", type=Path)
    ap.add_argument("new", type=Path)
    ap.add_argument("--changes", type=Path)
    ap.add_argument("--key")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        oc, old_rows = read(a.old)
        nc, new_rows = read(a.new)
        changes = read(a.changes)[1] if a.changes else None
    except (OSError, csv.Error) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 2
    key = a.key or next((k for k in KEYS if k in oc and k in nc), None)
    if not key:
        print("no key column found; pass --key", file=sys.stderr)
        return 2
    res = diff(old_rows, new_rows, key, changes)
    res["key"] = key
    res["passed"] = res["summary"]["errors"] == 0
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        print(f"added: {res['added']}\nremoved: {res['removed']}")
        for k, f in res["modified"].items():
            print(f"modified {k}: " + "; ".join(f"{n}: '{v['old']}' -> '{v['new']}'" for n, v in f.items()))
        for f in res["findings"]:
            print(f"{f['severity'].upper():8} {f['id']:<14} {f['rule']:<22} {f['message']}")
        print(f"\n{'PASS' if res['passed'] else 'FAIL'}: {res['summary']}")
        print("Scope: file differences vs change log only; technical soundness of changes needs human review.")
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
