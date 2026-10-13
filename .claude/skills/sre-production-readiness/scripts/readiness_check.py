#!/usr/bin/env python3
"""Evaluate a production readiness checklist (JSON) and recommend GO / GO_WITH_CONDITIONS / NO_GO.

Areas: slo, monitoring, alerting, capacity, dependencies, rollback, runbooks, oncall, security,
backup_restore, feature_flags. Blocking items (identified by `key`) must be status "done" with an
evidence reference: slo_defined, rollback_tested, oncall_staffed, restore_tested (restore_tested may
be "na" only with a justification, e.g. a stateless service). Any blocking gap -> NO_GO. Open
non-blocking items, missing evidence, unjustified N/A or uncovered areas -> GO_WITH_CONDITIONS.

Usage:
  readiness_check.py checklist.json [--json]
Exit codes: 0 GO or GO_WITH_CONDITIONS, 1 NO_GO, 2 unreadable input.

Scope: the output is a recommendation from the checklist as written; the launch decision requires
named human sign-off.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

AREAS = ["slo", "monitoring", "alerting", "capacity", "dependencies", "rollback", "runbooks", "oncall",
         "security", "backup_restore", "feature_flags"]
BLOCKING = {"slo_defined": "slo", "rollback_tested": "rollback", "oncall_staffed": "oncall",
            "restore_tested": "backup_restore"}
NA_ALLOWED_BLOCKING = {"restore_tested"}
STATUSES = {"done", "partial", "not_done", "na"}


def _finding(fid: str, severity: str, rule: str, message: str) -> dict:
    return {"id": fid, "severity": severity, "rule": rule, "message": message}


def evaluate(doc: dict) -> dict:
    findings: list[dict] = []
    add = lambda *a: findings.append(_finding(*a))  # noqa: E731
    blocking_failures: list[str] = []
    conditions: list[dict] = []
    if not doc.get("service"):
        add("-", "error", "missing-field", "service name missing")
    if not doc.get("reviewers"):
        add("-", "warning", "no-reviewers", "no reviewers recorded; readiness review needs named participants")
    items = doc.get("items")
    if not isinstance(items, list) or not items:
        add("-", "error", "no-items", "checklist has no items")
        items = []
    ids = Counter(str(i.get("id")) for i in items if isinstance(i, dict))
    for d, n in ids.items():
        if n > 1:
            add(d, "error", "duplicate-id", f"item id used {n} times")
    by_key: dict[str, dict] = {}
    covered: set[str] = set()
    for it in items:
        if not isinstance(it, dict):
            add("-", "error", "bad-item", "item is not an object")
            continue
        iid = str(it.get("id") or it.get("key") or "<no id>")
        area, status = it.get("area"), str(it.get("status", "")).lower()
        if area not in AREAS:
            add(iid, "error", "unknown-area", f"area '{area}' not in {AREAS}")
            continue
        if status not in STATUSES:
            add(iid, "error", "status-value", f"status '{it.get('status')}' not in {sorted(STATUSES)}")
            continue
        covered.add(area)
        key = it.get("key")
        if key:
            by_key[key] = it
        evidence = str(it.get("evidence_ref") or "").strip()
        if key in BLOCKING:
            if status == "na" and key in NA_ALLOWED_BLOCKING and len(str(it.get("justification") or "")) >= 10:
                add(iid, "info", "restore-not-applicable", f"restore marked N/A: {it.get('justification')}")
            elif status != "done":
                blocking_failures.append(key)
                add(iid, "error", "blocking-item-not-done", f"blocking item '{key}' is {status}")
            elif not evidence:
                blocking_failures.append(key)
                add(iid, "error", "blocking-no-evidence", f"blocking item '{key}' marked done without evidence")
            continue
        if status in {"partial", "not_done"}:
            cond = {"id": iid, "title": it.get("title", ""), "owner": it.get("owner"), "due": it.get("due")}
            conditions.append(cond)
            due_ok = True
            try:
                date.fromisoformat(str(it.get("due")))
            except ValueError:
                due_ok = False
            if not it.get("owner") or not due_ok:
                add(iid, "warning", "condition-no-owner", "open item needs an owner and a due date (YYYY-MM-DD)")
            else:
                add(iid, "warning", "open-item", f"open ({status}): owner {it.get('owner')}, due {it.get('due')}")
        elif status == "done" and not evidence:
            conditions.append({"id": iid, "title": it.get("title", ""), "owner": it.get("owner"), "due": it.get("due")})
            add(iid, "warning", "no-evidence", "marked done without an evidence reference")
        elif status == "na" and len(str(it.get("justification") or "")) < 10:
            conditions.append({"id": iid, "title": it.get("title", ""), "owner": it.get("owner"), "due": it.get("due")})
            add(iid, "warning", "na-without-justification", "N/A needs a justification")
    for key, area in BLOCKING.items():
        if key not in by_key:
            blocking_failures.append(key)
            add(key, "error", "blocking-item-missing", f"no checklist item with key '{key}' (area {area})")
    for area in AREAS:
        if area not in covered:
            conditions.append({"id": area, "title": f"area {area} not reviewed", "owner": None, "due": None})
            add(area, "warning", "area-not-covered", f"no checklist item for area '{area}'")
    sev = Counter(f["severity"] for f in findings)
    if blocking_failures or sev.get("error", 0):
        rec = "NO_GO"
    elif conditions:
        rec = "GO_WITH_CONDITIONS"
    else:
        rec = "GO"
    summary = {"service": doc.get("service"), "recommendation": rec, "requires_human_signoff": True,
               "blocking_failures": sorted(set(blocking_failures)), "conditions": conditions,
               "areas_covered": sorted(covered), "items": len(items),
               "errors": sev.get("error", 0), "warnings": sev.get("warning", 0), "info": sev.get("info", 0)}
    return {"findings": findings, "summary": summary}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Production readiness recommendation from a checklist.")
    ap.add_argument("checklist", type=Path)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        doc = json.loads(args.checklist.read_text(encoding="utf-8"))
        if not isinstance(doc, dict):
            raise ValueError("checklist must be a JSON object")
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"cannot read: {exc}", file=sys.stderr)
        return 2
    result = evaluate(doc)
    s = result["summary"]
    result["passed"] = s["recommendation"] != "NO_GO"
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for f in result["findings"]:
            print(f"{f['severity'].upper():8} {f['id']:<18} {f['rule']:<26} {f['message']}")
        print(f"\nRECOMMENDATION: {s['recommendation']} (requires human sign-off)")
        if s["blocking_failures"]:
            print(f"Blocking: {', '.join(s['blocking_failures'])}")
        for c in s["conditions"]:
            print(f"Condition: {c['id']} {c['title']} owner={c['owner']} due={c['due']}")
        print("Scope: recommendation from the checklist as written; the launch decision needs named human sign-off.")
    return 1 if s["recommendation"] == "NO_GO" else 0


if __name__ == "__main__":
    sys.exit(main())
