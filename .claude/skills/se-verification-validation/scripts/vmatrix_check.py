#!/usr/bin/env python3
"""Check a verification & validation matrix against a requirements register.

Finds: approved requirements with no verification activity, activities pointing at unknown
requirements/needs, validation used in place of verification, invalid methods/results, results
claimed without evidence, run date or configuration identification, author self-review, and
stakeholder needs with no validation. Reports coverage percentages.

Usage:
  vmatrix_check.py --requirements requirements.csv matrix.csv [--include-proposed] [--json]
Exit codes: 0 no errors, 1 errors, 2 unreadable input.

Scope: checks the *completeness and integrity of the plan and records*. It cannot confirm a test
was adequate, that evidence is genuine, or that the product meets its needs.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

METHODS = {"test", "analysis", "inspection", "demonstration"}
RESULTS = {"not_tested", "pass", "fail", "blocked"}
TYPES = {"verification", "validation"}
TOP_LEVELS = {"mission", "stakeholder", "business", "need"}
REQUIRED = ["activity_id", "type", "requirement_id", "method", "acceptance_criteria", "result"]
ACT_ID = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-(VER|VAL)-[0-9]{3,}$")


def read_csv(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        rd = csv.DictReader(fh)
        rows = [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in rd]
        return [c.strip() for c in rd.fieldnames or []], rows


def _f(rid, sev, rule, msg):
    return {"id": rid, "severity": sev, "rule": rule, "message": msg}


def split_ids(value: str) -> list[str]:
    return [v.strip() for v in re.split(r"[;,]", value or "") if v.strip()]


def check(req_rows: list[dict], cols: list[str], rows: list[dict], include_proposed: bool = False) -> dict:
    findings: list[dict] = []
    missing = [c for c in REQUIRED if c not in cols]
    if missing:
        findings.append(_f("-", "error", "missing-columns", f"matrix missing columns: {', '.join(missing)}"))
        return {"findings": findings, "summary": {}}
    reqs = {r["id"]: r for r in req_rows if r.get("id")}
    needs = {i for i, r in reqs.items() if r.get("level", "").lower() in TOP_LEVELS}
    in_scope = {i for i, r in reqs.items()
                if i not in needs and r.get("status", "").lower() in ({"approved", "proposed"} if include_proposed else {"approved"})}
    verified_by: dict[str, list[dict]] = {}
    validated_by: dict[str, list[dict]] = {}

    for r in rows:
        aid = r["activity_id"] or "<blank>"
        typ = r["type"].lower()
        method = r["method"].lower()
        result = r["result"].lower()
        if not ACT_ID.fullmatch(r["activity_id"]):
            findings.append(_f(aid, "warning", "activity-id-format", "activity id should look like <PROJECT>-VER-NNN or -VAL-NNN"))
        if typ not in TYPES:
            findings.append(_f(aid, "error", "type", f"type '{r['type']}' must be verification or validation"))
        if method not in METHODS:
            findings.append(_f(aid, "error", "method", f"method '{r['method']}' not in {sorted(METHODS)} "
                                                      "(simulation/modelling is a form of analysis)"))
        if result not in RESULTS:
            findings.append(_f(aid, "error", "result", f"result '{r['result']}' not in {sorted(RESULTS)}"))
        if not r["acceptance_criteria"]:
            findings.append(_f(aid, "error", "no-acceptance-criteria", "activity has no acceptance criteria"))
        req_ids = split_ids(r["requirement_id"])
        need_ids = split_ids(r.get("need_id", ""))
        if typ == "verification":
            if not req_ids:
                findings.append(_f(aid, "error", "verification-without-requirement", "verification activity traces to no requirement"))
            for q in req_ids:
                if q not in reqs:
                    findings.append(_f(aid, "error", "unknown-requirement", f"requirement '{q}' not in register"))
                    continue
                if reqs[q].get("status", "").lower() == "retired":
                    findings.append(_f(aid, "warning", "retired-requirement", f"verifies retired requirement '{q}'"))
                if q in needs:
                    findings.append(_f(aid, "warning", "verifying-a-need", f"'{q}' is a stakeholder need — needs are validated, not verified"))
                planned = {m.strip().lower() for m in re.split(r"[;,/]", reqs[q].get("verification_method", "")) if m.strip()}
                if planned and method in METHODS and method not in planned:
                    findings.append(_f(aid, "warning", "method-mismatch",
                                       f"method '{method}' differs from register method {sorted(planned)} for '{q}'"))
                verified_by.setdefault(q, []).append(r)
        elif typ == "validation":
            targets = need_ids or req_ids
            if not targets:
                findings.append(_f(aid, "error", "validation-without-need", "validation activity traces to no stakeholder need"))
            for q in targets:
                if q not in reqs:
                    findings.append(_f(aid, "error", "unknown-need", f"need '{q}' not in register"))
                elif q not in needs:
                    findings.append(_f(aid, "error", "validation-used-as-verification",
                                       f"validation traces to '{q}', a {reqs[q].get('level') or 'non-need'} requirement; "
                                       "validation answers 'right system?' against stakeholder needs — "
                                       "add a verification activity for the requirement"))
                else:
                    validated_by.setdefault(q, []).append(r)
        # evidence integrity
        if result in {"pass", "fail"}:
            if not r.get("evidence_ref"):
                findings.append(_f(aid, "error", "result-without-evidence", f"result '{result}' recorded with no evidence_ref"))
            if not r.get("run_date"):
                findings.append(_f(aid, "error", "result-without-date", "result recorded without run_date"))
            elif not re.fullmatch(r"\d{4}-\d{2}-\d{2}", r["run_date"]):
                findings.append(_f(aid, "error", "date-format", "run_date must be YYYY-MM-DD"))
            if not r.get("configuration"):
                findings.append(_f(aid, "error", "no-configuration",
                                   "result recorded without configuration identification (hardware/software version)"))
            if r.get("performed_by") and r.get("reviewer") and r["performed_by"] == r["reviewer"]:
                findings.append(_f(aid, "warning", "self-review", "performer and reviewer are the same person"))
            if not r.get("reviewer"):
                findings.append(_f(aid, "warning", "no-reviewer", "result has no independent reviewer recorded"))
        if result == "blocked" and not r.get("notes"):
            findings.append(_f(aid, "warning", "blocked-without-reason", "blocked result needs a reason in notes"))

    for q in sorted(in_scope):
        if q not in verified_by:
            findings.append(_f(q, "error", "unverified-requirement", "approved requirement has no verification activity"))
    for n in sorted(needs):
        if reqs[n].get("status", "").lower() != "retired" and n not in validated_by:
            findings.append(_f(n, "warning", "unvalidated-need", "stakeholder need has no validation activity"))

    def req_state(q: str) -> str:
        res = [a["result"].lower() for a in verified_by.get(q, [])]
        if not res:
            return "no_plan"
        if "fail" in res:
            return "fail"
        if "blocked" in res:
            return "blocked"
        if all(x == "pass" for x in res):
            return "pass"
        return "not_tested"

    states = Counter(req_state(q) for q in in_scope)
    n = len(in_scope) or 1
    sev = Counter(f["severity"] for f in findings)
    summary = {
        "requirements_in_scope": len(in_scope),
        "planned_coverage_pct": round(100 * (len(in_scope) - states.get("no_plan", 0)) / n, 1),
        "passed_pct": round(100 * states.get("pass", 0) / n, 1),
        "requirement_states": dict(states),
        "needs": len(needs),
        "needs_with_validation": sum(1 for x in needs if x in validated_by),
        "activities_by_result": dict(Counter(r["result"].lower() for r in rows)),
        "errors": sev.get("error", 0), "warnings": sev.get("warning", 0),
        "failed_or_blocked": sorted(q for q in in_scope if req_state(q) in {"fail", "blocked"}),
    }
    return {"findings": findings, "summary": summary}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Check a V&V matrix against a requirements register.")
    ap.add_argument("matrix", type=Path)
    ap.add_argument("--requirements", type=Path, required=True)
    ap.add_argument("--include-proposed", action="store_true", help="also require plans for proposed requirements")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        _, req_rows = read_csv(args.requirements)
        cols, rows = read_csv(args.matrix)
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 2
    res = check(req_rows, cols, rows, args.include_proposed)
    res["passed"] = res["summary"].get("errors", 1) == 0
    if args.json:
        print(json.dumps(res, indent=2))
    else:
        for f in res["findings"]:
            print(f"{f['severity'].upper():8} {f['id']:<16} {f['rule']:<32} {f['message']}")
        print(f"\n{'PASS' if res['passed'] else 'FAIL'}: {res['summary']}")
        print("Scope: plan/record integrity only — not evidence that tests were adequate or that the product is fit for use.")
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
