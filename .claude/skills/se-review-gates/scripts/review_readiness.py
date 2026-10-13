#!/usr/bin/env python3
"""Compute a review-gate readiness recommendation from evidence, check results and actions.

Rules (per criterion from the criteria file):
  met      -> needs evidence_ref, otherwise treated as not met ("claimed-without-evidence")
  partial  -> condition
  not_met  -> blocking criterion => NO_GO; non-blocking => condition
  na       -> needs a justification
  missing  -> treated as not_met
Additionally: failed automated checks block; open major actions block; open minor actions are
conditions; actions need owner + due date; at least one independent reviewer who is not an author.

Recommendation: NO_GO | GO_WITH_CONDITIONS | GO — always a recommendation to the gate authority.

Usage: review_readiness.py review.json [--criteria criteria.json] [--json]
Exit: 0 GO or GO_WITH_CONDITIONS, 1 NO_GO or input errors, 2 unreadable.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

DEFAULT_CRITERIA = Path(__file__).resolve().parents[1] / "assets" / "data" / "review-criteria.json"
STATUSES = {"met", "partial", "not_met", "na"}


def _f(rid, sev, rule, msg):
    return {"id": rid, "severity": sev, "rule": rule, "message": msg}


def evaluate(review: dict, criteria_doc: dict) -> dict:
    findings, blocking, conditions = [], [], []
    rtype = review.get("review", "")
    spec = criteria_doc.get("reviews", {}).get(rtype)
    if not spec:
        return {"findings": [_f(rtype or "-", "error", "unknown-review",
                                f"review type '{rtype}' not in criteria file ({sorted(criteria_doc.get('reviews', {}))})")],
                "recommendation": "NO_GO", "summary": {"errors": 1}}
    crit = {c["id"]: c for c in spec["criteria"]}
    ev = {}
    for e in review.get("evidence", []):
        cid = e.get("criterion_id", "")
        if cid not in crit:
            findings.append(_f(cid, "warning", "unknown-criterion", f"evidence for criterion not in {rtype} set"))
            continue
        ev[cid] = e
    for cid, c in crit.items():
        e = ev.get(cid)
        st = (e or {}).get("status", "missing")
        if st not in STATUSES | {"missing"}:
            findings.append(_f(cid, "error", "status", f"status '{st}' not in {sorted(STATUSES)}"))
            st = "not_met"
        if st == "met" and not e.get("evidence_ref"):
            findings.append(_f(cid, "error", "claimed-without-evidence", "criterion marked met with no evidence reference"))
            st = "not_met"
        if st == "na" and not e.get("justification"):
            findings.append(_f(cid, "error", "na-without-justification", "not-applicable needs a justification"))
            st = "not_met"
        if st == "missing":
            findings.append(_f(cid, "warning", "no-evidence", f"no evidence supplied: {c['text']}"))
            st = "not_met"
        if st == "not_met":
            (blocking if c.get("blocking") else conditions).append(cid)
        elif st == "partial":
            conditions.append(cid)
    for chk in review.get("checks", []):
        if chk.get("exit_code") not in (0, None):
            findings.append(_f(chk.get("name", "check"), "error", "check-failed",
                               f"automated check failed (exit {chk.get('exit_code')}); see {chk.get('report', '-')}"))
            blocking.append(chk.get("name", "check"))
    for a in review.get("actions", []):
        aid = a.get("id", "?")
        if a.get("status", "open") == "closed":
            if not a.get("closure_evidence"):
                findings.append(_f(aid, "error", "closed-without-evidence", "action closed without closure evidence"))
            continue
        if not a.get("owner") or not a.get("due"):
            findings.append(_f(aid, "error", "action-incomplete", "open action needs owner and due date"))
        if a.get("severity") == "major":
            blocking.append(aid)
        else:
            conditions.append(aid)
    authors = set(review.get("authors", []))
    reviewers = set(review.get("independent_reviewers", []))
    independent = reviewers - authors
    if not independent:
        findings.append(_f("-", "error", "no-independent-review", "no reviewer independent of the authors"))
        blocking.append("independence")
    if not review.get("gate_authority"):
        findings.append(_f("-", "warning", "no-gate-authority", "name the human gate authority who will decide"))
    rec = "NO_GO" if blocking else "GO_WITH_CONDITIONS" if conditions else "GO"
    sev = Counter(f["severity"] for f in findings)
    return {"review": rtype, "recommendation": rec, "blocking": sorted(set(blocking)), "conditions": sorted(set(conditions)),
            "decision": f"pending — only {review.get('gate_authority') or 'the named gate authority'} can record the gate decision",
            "criteria_provenance": criteria_doc.get("_provenance", "programme-supplied"),
            "findings": findings,
            "summary": {"criteria": len(crit), "errors": sev.get("error", 0), "warnings": sev.get("warning", 0)}}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Review-gate readiness recommendation.")
    ap.add_argument("review_json", type=Path)
    ap.add_argument("--criteria", type=Path, default=DEFAULT_CRITERIA)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        review = json.loads(a.review_json.read_text(encoding="utf-8"))
        crit = json.loads(a.criteria.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 2
    res = evaluate(review, crit)
    res["passed"] = res["recommendation"] != "NO_GO"
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        for f in res["findings"]:
            print(f"{f['severity'].upper():8} {f['id']:<14} {f['rule']:<26} {f['message']}")
        print(f"\nRecommendation ({res.get('review')}): {res['recommendation']}")
        print(f"Blocking: {res.get('blocking')}  Conditions: {res.get('conditions')}")
        print(f"Decision: {res.get('decision', '')}")
        print("Scope: readiness of recorded evidence only; not a technical judgement of the design.")
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
