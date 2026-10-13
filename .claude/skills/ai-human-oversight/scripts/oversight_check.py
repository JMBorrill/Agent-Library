#!/usr/bin/env python3
"""Validate a human-oversight matrix (CSV) for AI decision support.

Columns: decision_type, impact (low|medium|high|critical), ai_role (inform|recommend|draft|act),
human_role, approver_role, override_logged (yes/no), explanation_provided (yes/no),
appeal_route, monitoring_metric, rollback_trigger; optional about_individuals (yes/no),
kill_switch_owner, notes.

Rules (error unless noted):
  OV-ACT-WITHOUT-APPROVAL   high/critical decision about individuals with ai_role=act and no approver
  OV-CRITICAL-ACT           critical decision with ai_role=act even with an approver (warning)
  OV-EXPLANATION-REQUIRED   credit/eligibility-type decision without explanation_provided=yes
  OV-APPEAL-REQUIRED        credit/eligibility-type decision without an appeal route
  OV-ACT-NO-ROLLBACK        ai_role=act without a rollback trigger
  OV-NO-MONITORING          no monitoring metric
  OV-OVERRIDE-NOT-LOGGED    overrides not logged (error for high/critical, warning otherwise)
  OV-NO-HUMAN-ROLE          no accountable human role
  OV-APPROVER-NOT-HUMAN     approver or human role names an AI/system
  OV-AUTOMATION-BIAS        recommend/draft at high/critical impact with no explanation (warning)
  OV-SELF-APPROVAL          critical decision where the operator also approves (warning)
  OV-NO-KILL-SWITCH         ai_role=act rows but no kill_switch_owner (warning)
  OV-DUPLICATE-DECISION     decision_type repeated (warning)
  OV-ENUM / OV-MISSING-COLUMNS / OV-EMPTY                                   input defects

Usage:
  oversight_check.py matrix.csv [--strict] [--json]
Exit codes: 0 no errors, 1 errors (or warnings with --strict), 2 unreadable input.

Scope: checks the oversight design is complete and internally consistent. It cannot tell whether
the people named have the time, competence or authority to oversee effectively.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

REQUIRED = ["decision_type", "impact", "ai_role", "human_role", "approver_role", "override_logged",
            "explanation_provided", "appeal_route", "monitoring_metric", "rollback_trigger"]
OPTIONAL = ["about_individuals", "kill_switch_owner", "notes"]
IMPACTS = ["low", "medium", "high", "critical"]
ROLES = ["inform", "recommend", "draft", "act"]
YESNO = {"yes", "no"}
NONE_WORDS = {"", "none", "n/a", "na", "-", "tbd", "no"}
NON_HUMAN = re.compile(r"\b(ai|model|system|agent|bot|llm|automated|automation|algorithm)\b", re.I)
CREDIT_LIKE = re.compile(
    r"\b(credit|loan|lending|mortgage|affordab\w*|eligib\w*|underwrit\w*|decline|approv\w*|limit|"
    r"insurance|claim|benefit|hiring|recruit\w*|tenancy|pricing)\b", re.I)
INDIVIDUAL_HINT = re.compile(r"\b(applicant|customer|individual|person|borrower|claimant|candidate|tenant|consumer)s?\b", re.I)


def _f(rid: str, severity: str, rule: str, message: str) -> dict:
    return {"id": rid, "severity": severity, "rule": rule, "message": message}


def blank(v: str) -> bool:
    return (v or "").strip().lower() in NONE_WORDS


def read_rows(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        rows = [{(k or "").strip(): (v or "").strip() for k, v in r.items() if k is not None} for r in reader]
        return [c.strip() for c in (reader.fieldnames or [])], rows


def is_credit_like(row: dict) -> bool:
    return bool(CREDIT_LIKE.search(row.get("decision_type", "")))


def about_individuals(row: dict) -> bool:
    flag = row.get("about_individuals", "").lower()
    if flag in YESNO:
        return flag == "yes"
    return is_credit_like(row) or bool(INDIVIDUAL_HINT.search(row.get("decision_type", "")))


def check(columns: list[str], rows: list[dict]) -> dict:
    findings: list[dict] = []
    missing = [c for c in REQUIRED if c not in columns]
    if missing:
        findings.append(_f("-", "error", "ov-missing-columns", f"missing columns: {', '.join(missing)}"))
        return {"findings": findings, "summary": {"decisions": len(rows), "errors": 1, "warnings": 0, "info": 0}}
    if not rows:
        findings.append(_f("-", "error", "ov-empty", "matrix has no decision rows"))
    counts = Counter(r["decision_type"].lower() for r in rows)
    has_ks_col = "kill_switch_owner" in columns
    for i, r in enumerate(rows, 1):
        rid = r["decision_type"] or f"row-{i}"
        impact, role = r["impact"].lower(), r["ai_role"].lower()
        bad = False
        if impact not in IMPACTS:
            findings.append(_f(rid, "error", "ov-enum", f"impact '{r['impact']}' not in {IMPACTS}"))
            bad = True
        if role not in ROLES:
            findings.append(_f(rid, "error", "ov-enum", f"ai_role '{r['ai_role']}' not in {ROLES}"))
            bad = True
        for col in ("override_logged", "explanation_provided"):
            if r[col].lower() not in YESNO:
                findings.append(_f(rid, "error", "ov-enum", f"{col} '{r[col]}' must be yes/no"))
        if not r["decision_type"]:
            findings.append(_f(rid, "error", "ov-enum", "decision_type is empty"))
        elif counts[r["decision_type"].lower()] > 1:
            findings.append(_f(rid, "warning", "ov-duplicate-decision", "decision_type appears more than once"))
        if blank(r["human_role"]):
            findings.append(_f(rid, "error", "ov-no-human-role", "no accountable human role"))
        for col in ("human_role", "approver_role"):
            if not blank(r[col]) and NON_HUMAN.search(r[col]):
                findings.append(_f(rid, "error", "ov-approver-not-human", f"{col} '{r[col]}' names an AI/system, not a person"))
        if blank(r["monitoring_metric"]):
            findings.append(_f(rid, "error", "ov-no-monitoring", "no monitoring metric"))
        if bad:
            continue
        high = impact in ("high", "critical")
        indiv = about_individuals(r)
        no_approver = blank(r["approver_role"]) or bool(NON_HUMAN.search(r["approver_role"]))
        if role == "act" and high and indiv and no_approver:
            findings.append(_f(rid, "error", "ov-act-without-approval",
                               f"{impact}-impact decision about individuals executed by AI without human approval"))
        if role == "act" and impact == "critical" and not no_approver:
            findings.append(_f(rid, "warning", "ov-critical-act",
                               "critical decision with ai_role=act; prefer recommend/draft with human decision"))
        if role == "act" and blank(r["rollback_trigger"]):
            findings.append(_f(rid, "error", "ov-act-no-rollback", "AI acts but no rollback trigger is defined"))
        if is_credit_like(r) and indiv:
            if r["explanation_provided"].lower() != "yes":
                findings.append(_f(rid, "error", "ov-explanation-required",
                                   "credit/eligibility-type decision must give the individual an explanation"))
            if blank(r["appeal_route"]):
                findings.append(_f(rid, "error", "ov-appeal-required",
                                   "credit/eligibility-type decision needs an appeal / human review route"))
        if role != "inform" and r["override_logged"].lower() == "no":
            findings.append(_f(rid, "error" if high else "warning", "ov-override-not-logged",
                               "human overrides of AI output are not logged"))
        if role in ("recommend", "draft") and high and r["explanation_provided"].lower() == "no":
            findings.append(_f(rid, "warning", "ov-automation-bias",
                               "high-impact recommendation without rationale invites rubber-stamping"))
        if impact == "critical" and not blank(r["approver_role"]) and \
                r["approver_role"].strip().lower() == r["human_role"].strip().lower():
            findings.append(_f(rid, "warning", "ov-self-approval", "operator and approver are the same role"))
    act_rows = [r for r in rows if r["ai_role"].lower() == "act"]
    if act_rows and (not has_ks_col or all(blank(r.get("kill_switch_owner", "")) for r in act_rows)):
        findings.append(_f("-", "warning", "ov-no-kill-switch", "AI acts autonomously but no kill_switch_owner is named"))
    sev = Counter(f["severity"] for f in findings)
    summary = {"decisions": len(rows),
               "by_ai_role": dict(Counter(r["ai_role"].lower() for r in rows)),
               "by_impact": dict(Counter(r["impact"].lower() for r in rows)),
               "errors": sev.get("error", 0), "warnings": sev.get("warning", 0), "info": sev.get("info", 0)}
    return {"findings": findings, "summary": summary}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate a human-oversight matrix CSV.")
    ap.add_argument("csv", type=Path)
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        columns, rows = read_rows(args.csv)
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        print(f"cannot read {args.csv}: {exc}", file=sys.stderr)
        return 2
    result = check(columns, rows)
    s = result["summary"]
    failed = s["errors"] > 0 or (args.strict and s["warnings"] > 0)
    result["passed"] = not failed
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for f in result["findings"]:
            print(f"{f['severity'].upper():8} {f['rule']:<26} {f['id']}: {f['message']}")
        print(f"\n{'FAIL' if failed else 'PASS'}: {s}")
        print("Scope: oversight design completeness only; effectiveness of the humans involved needs review.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
