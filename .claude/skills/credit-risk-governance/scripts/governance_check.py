#!/usr/bin/env python3
"""Gap-check a credit risk controls register against Basel-style coverage areas.

Register CSV columns (required): control_id, area, description, owner, frequency, evidence_ref,
last_tested, status, independent_of_origination. Optional: topic, control_type, model_risk,
last_validated.

Areas (the four areas of the Basel credit risk principles as reported by secondary sources -
unverified against the 2025 text):
  credit_risk_environment | credit_granting | administration_measurement_monitoring | controls

Checks: coverage of every area (and of default topics when a `topic` column is used), owners,
descriptions, status vocabulary, evidence for tested controls, testing age against --as-of,
independence of approval/review/validation controls from origination, and validation of
model-risk items.

Usage: governance_check.py register.csv [--as-of YYYY-MM-DD] [--max-test-age-days 365]
                           [--model-max-age-days 365] [--coverage coverage.json] [--strict] [--json]
Exit: 0 no error findings, 1 error findings (gaps), 2 unreadable input.

Scope: a gap report for human review. It never approves a credit risk framework and is not a
supervisory or audit opinion.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

SCOPE = "Scope: gap report for human review only; not an approval, audit opinion or supervisory assessment."
REQUIRED_COLUMNS = ["control_id", "area", "description", "owner", "frequency", "evidence_ref",
                    "last_tested", "status", "independent_of_origination"]
AREAS = {
    "credit_risk_environment": {"credit_risk_environment", "environment", "governance", "strategy",
                                "governance_and_strategy"},
    "credit_granting": {"credit_granting", "granting", "credit_granting_process"},
    "administration_measurement_monitoring": {"administration_measurement_monitoring", "administration",
                                              "measurement", "monitoring", "administration_monitoring"},
    "controls": {"controls", "controls_over_credit_risk", "independent_review"},
}
DEFAULT_TOPICS = {
    "credit_risk_environment": ["risk-appetite-strategy", "credit-policy", "new-product-approval"],
    "credit_granting": ["granting-criteria", "credit-limits", "approval-authority", "exceptions-overrides"],
    "administration_measurement_monitoring": ["credit-administration", "individual-credit-monitoring",
                                              "internal-rating", "portfolio-reporting", "stress-testing",
                                              "problem-credit-management"],
    "controls": ["independent-credit-review", "limit-breach-escalation", "internal-audit"],
}
STATUSES = {"designed", "operating", "tested_effective", "tested_deficient", "not_implemented", "retired"}
FREQUENCIES = {"continuous", "daily", "weekly", "monthly", "quarterly", "semi-annual", "annual",
               "event-driven", "per-application"}
INDEPENDENT_TYPES = {"approval", "credit-review", "model-validation", "limit-monitoring",
                     "override-approval", "collateral-valuation", "independent-review"}
MODEL_TYPES = {"model", "model-validation", "scorecard"}
YES, NO = {"yes", "y", "true"}, {"no", "n", "false"}


class InputError(ValueError):
    pass


def _f(fid: str, severity: str, rule: str, message: str) -> dict:
    return {"id": fid, "severity": severity, "rule": rule, "message": message}


def normalise_area(raw: str) -> str | None:
    key = raw.strip().lower().replace(" ", "_").replace("-", "_").replace("&", "and")
    for canon, aliases in AREAS.items():
        if key in aliases:
            return canon
    return None


def _date(raw: str, cid: str, col: str, findings: list[dict]) -> date | None:
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        findings.append(_f(cid, "error", "bad-date", f"{col} '{raw}' is not YYYY-MM-DD"))
        return None


def check(columns: list[str], rows: list[dict], as_of: date | None = None, max_test_age: int = 365,
          model_max_age: int = 365, topics: dict | None = None) -> dict:
    findings: list[dict] = []
    missing = [c for c in REQUIRED_COLUMNS if c not in columns]
    if missing:
        findings.append(_f("-", "error", "missing-columns", f"missing columns: {', '.join(missing)}"))
        return {"findings": findings, "summary": {"controls": len(rows), "errors": 1, "warnings": 0, "info": 0}}
    topics = DEFAULT_TOPICS if topics is None else topics
    use_topics = "topic" in columns
    if as_of is None:
        findings.append(_f("-", "info", "age-check-skipped", "no --as-of date: testing/validation age not checked"))
    counts = Counter(r["control_id"] for r in rows)
    coverage = {a: 0 for a in AREAS}
    topic_hits: dict[str, set] = {a: set() for a in AREAS}
    for r in rows:
        cid = r["control_id"] or "<blank>"
        if not r["control_id"]:
            findings.append(_f(cid, "error", "blank-id", "control has no identifier"))
        elif counts[r["control_id"]] > 1:
            findings.append(_f(cid, "error", "duplicate-control-id", f"control_id used {counts[cid]} times"))
        status = r["status"].lower()
        if status not in STATUSES:
            findings.append(_f(cid, "error", "bad-status", f"status '{r['status']}' not in {sorted(STATUSES)}"))
        if status == "retired":
            continue
        area = normalise_area(r["area"])
        if area is None:
            findings.append(_f(cid, "warning", "unknown-area",
                               f"area '{r['area']}' does not map to {sorted(AREAS)}; not counted for coverage"))
        elif status != "not_implemented":
            coverage[area] += 1
            if use_topics and r.get("topic"):
                topic_hits[area].add(r["topic"].strip().lower())
        if not r["description"]:
            findings.append(_f(cid, "error", "missing-description", "control has no description"))
        if not r["owner"] or r["owner"].upper() in {"TBD", "N/A", "-"}:
            findings.append(_f(cid, "error", "missing-owner", "control has no accountable owner"))
        if r["frequency"].lower() not in FREQUENCIES:
            findings.append(_f(cid, "warning", "unknown-frequency",
                               f"frequency '{r['frequency']}' not in {sorted(FREQUENCIES)}"))
        if status == "not_implemented":
            findings.append(_f(cid, "warning", "control-not-implemented", "control recorded but not implemented"))
        if status == "tested_deficient":
            findings.append(_f(cid, "warning", "control-deficient", "last test found the control deficient; track remediation"))
        if status.startswith("tested") and not r["evidence_ref"]:
            findings.append(_f(cid, "error", "tested-without-evidence", "status says tested but no evidence_ref"))
        tested = _date(r["last_tested"], cid, "last_tested", findings)
        if status in ("operating", "tested_effective", "tested_deficient") and not r["last_tested"]:
            findings.append(_f(cid, "error", "never-tested", "operating control has never been tested"))
        if tested and as_of:
            age = (as_of - tested).days
            if age < 0:
                findings.append(_f(cid, "error", "future-date", f"last_tested {tested} is after as-of {as_of}"))
            elif age > max_test_age:
                findings.append(_f(cid, "error", "test-overdue",
                                   f"last tested {age} days before {as_of} (limit {max_test_age})"))
        ind = r["independent_of_origination"].strip().lower()
        ctype = (r.get("control_type") or "").strip().lower()
        if ind not in YES | NO:
            findings.append(_f(cid, "error", "independence-unknown",
                               "independent_of_origination must be yes or no"))
        elif ind in NO and (ctype in INDEPENDENT_TYPES or area == "controls"):
            findings.append(_f(cid, "error", "independence-lacking",
                               f"{ctype or area} control is performed by, or reports to, origination"))
        is_model = (r.get("model_risk") or "").strip().lower() in YES or ctype in MODEL_TYPES
        if is_model:
            validated = _date((r.get("last_validated") or "").strip(), cid, "last_validated", findings)
            if not (r.get("last_validated") or "").strip():
                findings.append(_f(cid, "error", "model-not-validated",
                                   "model-risk item has no independent validation date"))
            elif validated and as_of and (as_of - validated).days > model_max_age:
                findings.append(_f(cid, "warning", "model-validation-overdue",
                                   f"model last validated {(as_of - validated).days} days ago (limit {model_max_age})"))
    for area, n in coverage.items():
        if n == 0:
            findings.append(_f(area, "error", "area-not-covered", f"no implemented control covers '{area}'"))
        elif use_topics:
            gaps = [t for t in topics.get(area, []) if t not in topic_hits[area]]
            if gaps:
                findings.append(_f(area, "warning", "topic-not-covered", f"topics without a control: {gaps}"))
    sev = Counter(f["severity"] for f in findings)
    return {"findings": findings,
            "summary": {"controls": len(rows), "coverage_by_area": coverage,
                        "errors": sev.get("error", 0), "warnings": sev.get("warning", 0), "info": sev.get("info", 0)}}


def read_rows(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        cols = [c.strip() for c in (reader.fieldnames or [])]
        rows = []
        for r in reader:
            if None in r:
                raise InputError(f"row {reader.line_num} has more fields than the header")
            rows.append({(k or "").strip(): (v or "").strip() for k, v in r.items()})
        return cols, rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Credit risk controls register gap check.")
    ap.add_argument("csv", type=Path)
    ap.add_argument("--as-of", help="assessment date YYYY-MM-DD (enables age checks)")
    ap.add_argument("--max-test-age-days", type=int, default=365)
    ap.add_argument("--model-max-age-days", type=int, default=365)
    ap.add_argument("--coverage", type=Path, help="JSON {area: [topics]} overriding default topics")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        as_of = date.fromisoformat(args.as_of) if args.as_of else None
        topics = None
        if args.coverage:
            topics = json.loads(args.coverage.read_text(encoding="utf-8")).get("topics")
        cols, rows = read_rows(args.csv)
    except (OSError, UnicodeDecodeError, csv.Error, json.JSONDecodeError, ValueError) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 2
    res = check(cols, rows, as_of, args.max_test_age_days, args.model_max_age_days, topics)
    s = res["summary"]
    failed = s["errors"] > 0 or (args.strict and s["warnings"] > 0)
    res["passed"] = not failed
    res["report_type"] = "gap-report"
    res["as_of"] = args.as_of
    res["scope"] = SCOPE
    if args.json:
        print(json.dumps(res, indent=2))
    else:
        for f in res["findings"]:
            print(f"{f['severity'].upper():8} {f['id']:<40} {f['rule']:<26} {f['message']}")
        print(f"\nCoverage by area: {s.get('coverage_by_area')}")
        print(f"{'GAPS FOUND' if failed else 'NO BLOCKING GAPS'}: {s}")
        print(SCOPE)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
