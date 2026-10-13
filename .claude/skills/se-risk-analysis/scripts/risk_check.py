#!/usr/bin/env python3
"""Check a technical risk register: scoring, ownership, handling approach, residual risk, review age.

Usage:
  risk_check.py risks.csv [--policy risk-matrix-policy.json] [--as-of YYYY-MM-DD]
                [--known-ids requirements.csv ...] [--json]
Exit: 0 no errors, 1 errors, 2 unreadable input/policy.

Scores are ordinal (likelihood x consequence on the policy scale), NOT calibrated probabilities.
Scope: register integrity and policy conformance only; risk identification and acceptance are
human responsibilities.
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

DEFAULT_POLICY = {
    "scale": 5,
    "levels": {"high": 15, "medium": 6},
    "high_cells": [[4, 4], [3, 5], [5, 3]],
    "max_review_age_days": {"high": 30, "medium": 90, "low": 180},
}
APPROACHES = {"mitigate", "watch", "research", "accept", "transfer", "close"}
REQUIRED = ["risk_id", "title", "statement", "likelihood", "consequence", "approach", "owner", "status"]
RISK_ID = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-RSK-[0-9]{3,}$")
STATEMENT = re.compile(r"\b(given|if|because)\b.+\b(possibility|may|might|could|chance)\b.+\b(resulting in|leading to|then|causing)\b", re.I | re.S)


def _f(rid, sev, rule, msg):
    return {"id": rid, "severity": sev, "rule": rule, "message": msg}


def level(lik: int, con: int, policy: dict) -> str:
    score = lik * con
    if score >= policy["levels"]["high"] or [lik, con] in policy.get("high_cells", []):
        return "high"
    if score >= policy["levels"]["medium"]:
        return "medium"
    return "low"


def _int(v: str, scale: int) -> int | None:
    try:
        n = int(v)
    except (TypeError, ValueError):
        return None
    return n if 1 <= n <= scale else None


def check(cols: list[str], rows: list[dict], policy: dict, as_of: date | None = None,
          known_ids: set[str] | None = None) -> dict:
    findings: list[dict] = []
    missing = [c for c in REQUIRED if c not in cols]
    if missing:
        return {"findings": [_f("-", "error", "missing-columns", ", ".join(missing))], "summary": {}, "risks": []}
    scale = policy["scale"]
    counts = Counter(r["risk_id"] for r in rows)
    out_rows = []
    for r in rows:
        rid = r["risk_id"] or "<blank>"
        if not RISK_ID.fullmatch(r["risk_id"]):
            findings.append(_f(rid, "error", "id-format", "risk id must look like <PROJECT>-RSK-NNN"))
        if counts[r["risk_id"]] > 1:
            findings.append(_f(rid, "error", "duplicate-id", "risk id used more than once"))
        status = r["status"].lower()
        lik, con = _int(r["likelihood"], scale), _int(r["consequence"], scale)
        if lik is None or con is None:
            findings.append(_f(rid, "error", "score-range", f"likelihood/consequence must be integers 1..{scale}"))
            continue
        lvl = level(lik, con, policy)
        approach = r["approach"].lower()
        if approach not in APPROACHES:
            findings.append(_f(rid, "error", "approach", f"approach '{r['approach']}' not in {sorted(APPROACHES)}"))
        if not STATEMENT.search(r["statement"]):
            findings.append(_f(rid, "warning", "statement-form",
                               "write as condition -> possible event -> consequence "
                               "('Given ..., there is a possibility ..., resulting in ...')"))
        if status == "open" and not r["owner"]:
            findings.append(_f(rid, "error", "no-owner", "open risk has no owner"))
        if status == "open" and lvl in {"high", "medium"} and approach in {"mitigate", "research"}:
            if not r.get("mitigation"):
                findings.append(_f(rid, "error", "no-mitigation", f"{lvl} risk with approach '{approach}' has no mitigation/research plan"))
            if not r.get("trigger"):
                findings.append(_f(rid, "error" if lvl == "high" else "warning", "no-trigger",
                                   "no trigger/threshold defined for re-evaluation"))
        if status == "open" and approach == "accept" and lvl == "high" and not r.get("accepted_by"):
            findings.append(_f(rid, "error", "unauthorised-acceptance", "high risk accepted without a named human acceptor (accepted_by)"))
        if status == "open" and approach == "watch" and lvl == "high":
            findings.append(_f(rid, "warning", "watch-high", "high risk only watched — confirm this is a deliberate, owner-approved decision"))
        # residual
        rl, rc = r.get("residual_likelihood", ""), r.get("residual_consequence", "")
        res_lvl = None
        if rl or rc:
            rli, rci = _int(rl, scale), _int(rc, scale)
            if rli is None or rci is None:
                findings.append(_f(rid, "error", "residual-range", "residual likelihood/consequence invalid"))
            else:
                res_lvl = level(rli, rci, policy)
                if rli * rci > lik * con:
                    findings.append(_f(rid, "error", "residual-exceeds-inherent", "residual score greater than current score"))
                if rci < con and approach == "mitigate":
                    findings.append(_f(rid, "info", "consequence-reduced",
                                       "mitigation claims to reduce consequence — ensure it changes the outcome, not just likelihood"))
                if res_lvl == "high" and status == "open" and not r.get("accepted_by"):
                    findings.append(_f(rid, "warning", "residual-high-unaccepted",
                                       "residual risk remains high and nobody has accepted it"))
        elif status == "open" and approach == "mitigate":
            findings.append(_f(rid, "warning", "no-residual", "mitigated risk has no residual assessment"))
        if r.get("category", "").lower() == "safety" and con >= scale - 1 and status == "open":
            findings.append(_f(rid, "warning", "safety-escalation",
                               "safety risk with severe consequence — requires review by a qualified safety authority"))
        # review age
        rd = r.get("review_date", "")
        if status == "open":
            if not rd:
                findings.append(_f(rid, "warning", "no-review-date", "open risk has no review date"))
            elif not re.fullmatch(r"\d{4}-\d{2}-\d{2}", rd):
                findings.append(_f(rid, "error", "date-format", "review_date must be YYYY-MM-DD"))
            elif as_of:
                age = (as_of - date.fromisoformat(rd)).days
                limit = policy.get("max_review_age_days", {}).get(lvl)
                if limit is not None and age > limit:
                    findings.append(_f(rid, "warning", "stale-review", f"{lvl} risk last reviewed {age} days ago (limit {limit})"))
        if known_ids is not None:
            for x in [v.strip() for v in re.split(r"[;,]", r.get("related_ids", "")) if v.strip()]:
                if x not in known_ids:
                    findings.append(_f(rid, "error", "unknown-related-id", f"related id '{x}' not found"))
        out_rows.append({"risk_id": rid, "score": lik * con, "level": lvl, "residual_level": res_lvl, "status": status})
    sev = Counter(f["severity"] for f in findings)
    open_rows = [x for x in out_rows if x["status"] == "open"]
    summary = {
        "risks": len(rows), "open": len(open_rows),
        "open_by_level": dict(Counter(x["level"] for x in open_rows)),
        "errors": sev.get("error", 0), "warnings": sev.get("warning", 0),
        "top_risks": [x["risk_id"] for x in sorted(open_rows, key=lambda x: -x["score"])[:5]],
    }
    return {"findings": findings, "summary": summary, "risks": out_rows}


def load_ids(paths: list[Path]) -> set[str]:
    ids: set[str] = set()
    for p in paths:
        with p.open(newline="", encoding="utf-8-sig") as fh:
            rd = csv.DictReader(fh)
            for r in rd:
                for key in ("id", "activity_id", "interface_id", "risk_id"):
                    if r.get(key):
                        ids.add(r[key].strip())
    return ids


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Check a technical risk register.")
    ap.add_argument("csv", type=Path)
    ap.add_argument("--policy", type=Path)
    ap.add_argument("--as-of", help="evaluation date YYYY-MM-DD for review-age checks")
    ap.add_argument("--known-ids", type=Path, nargs="*", default=None,
                    help="CSV files whose id/activity_id/interface_id columns define valid related_ids")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        policy = dict(DEFAULT_POLICY)
        if args.policy:
            policy.update(json.loads(args.policy.read_text(encoding="utf-8")))
        with args.csv.open(newline="", encoding="utf-8-sig") as fh:
            rd = csv.DictReader(fh)
            rows = [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in rd]
            cols = [c.strip() for c in rd.fieldnames or []]
        as_of = date.fromisoformat(args.as_of) if args.as_of else None
        known = load_ids(args.known_ids) if args.known_ids else None
    except (OSError, ValueError, csv.Error) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 2
    res = check(cols, rows, policy, as_of, known)
    res["passed"] = res["summary"].get("errors", 1) == 0
    if args.json:
        print(json.dumps(res, indent=2))
    else:
        for f in res["findings"]:
            print(f"{f['severity'].upper():8} {f['id']:<16} {f['rule']:<28} {f['message']}")
        print(f"\n{'PASS' if res['passed'] else 'FAIL'}: {res['summary']}")
        print("Scope: ordinal scores, register integrity only; identification and acceptance of risk are human decisions.")
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
