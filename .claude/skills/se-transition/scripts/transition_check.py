#!/usr/bin/env python3
"""Check a product transition package for readiness to hand over to the receiving organisation.

Rules: receiving organisation named; each deliverable has version, configuration ID, acceptance
reference and documentation; open verification results (fail/blocked/not_tested) each have an
approved waiver; limitations documented; training/support/handling addressed.
Readiness: NOT_READY | READY_FOR_ACCEPTANCE (the receiver's sign-off completes the transition).

Usage: transition_check.py transition.json [--json]
Exit: 0 READY_FOR_ACCEPTANCE, 1 NOT_READY, 2 unreadable.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


def _f(rid, sev, rule, msg):
    return {"id": rid, "severity": sev, "rule": rule, "message": msg}


def check(t: dict) -> dict:
    f = []
    if not t.get("receiving_organisation"):
        f.append(_f("-", "error", "no-receiver", "receiving organisation not named"))
    dels = t.get("deliverables", [])
    if not dels:
        f.append(_f("-", "error", "no-deliverables", "no deliverables listed"))
    for d in dels:
        did = d.get("id", "?")
        for k in ("version", "configuration_id", "acceptance_ref"):
            if not d.get(k):
                f.append(_f(did, "error", f"missing-{k.replace('_', '-')}", f"deliverable lacks {k}"))
        if not d.get("documentation"):
            f.append(_f(did, "error", "no-documentation", "deliverable has no user/maintenance documentation"))
        if "known_issues" not in d:
            f.append(_f(did, "warning", "known-issues-unstated", "state known issues explicitly (empty list if none)"))
    for v in t.get("open_verification", []):
        vid = v.get("activity_id", "?")
        if v.get("result") in ("fail", "blocked", "not_tested"):
            if not (v.get("waiver_ref") and v.get("waiver_approved_by")):
                f.append(_f(vid, "error", "open-verification-unwaived",
                            f"result '{v.get('result')}' with no approved waiver — transition would hide an open item"))
    if not t.get("limitations_documented"):
        f.append(_f("-", "error", "limitations-undocumented", "known limitations must be documented for the receiver"))
    tr = t.get("training", {})
    if tr.get("required") and not tr.get("completed"):
        f.append(_f("training", "warning", "training-incomplete", "required training not completed"))
    if not t.get("support_plan_ref"):
        f.append(_f("support", "warning", "no-support-plan", "no support/maintenance plan referenced"))
    if not t.get("handling_storage"):
        f.append(_f("handling", "warning", "no-handling", "handling, storage and transport conditions not stated"))
    so = t.get("receiver_signoff") or {}
    status = "NOT_READY" if any(x["severity"] == "error" for x in f) else "READY_FOR_ACCEPTANCE"
    if status == "READY_FOR_ACCEPTANCE" and not (so.get("name") and so.get("date")):
        f.append(_f("signoff", "info", "awaiting-receiver", "package ready; transition completes only on receiver sign-off"))
    sev = Counter(x["severity"] for x in f)
    return {"findings": f, "status": status, "summary": {"deliverables": len(dels), "errors": sev.get("error", 0),
                                                       "warnings": sev.get("warning", 0)}}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check a transition package.")
    ap.add_argument("json_file", type=Path)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        t = json.loads(a.json_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 2
    res = check(t)
    res["passed"] = res["status"] == "READY_FOR_ACCEPTANCE"
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        for x in res["findings"]:
            print(f"{x['severity'].upper():8} {x['id']:<14} {x['rule']:<30} {x['message']}")
        print(f"\nStatus: {res['status']}  {res['summary']}")
        print("Scope: package completeness only; the receiving organisation decides acceptance.")
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
