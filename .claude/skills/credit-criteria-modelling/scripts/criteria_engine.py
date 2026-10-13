#!/usr/bin/env python3
"""Versioned lender-criteria rules: validate a criteria file and evaluate a synthetic case.

Criteria JSON (assets/schemas/criteria.schema.json): {"dataset", "rules": [ {rule_id, lender,
product, criterion, operator, value, unit, effective_from, effective_to, source_document,
last_verified} ]}.

Validation findings: missing fields, unknown operators, bad value shapes, effective_to before
effective_from, overlapping effective periods for the same lender/product/criterion, missing
source_document, last_verified older than --max-age-days at --as-of (stale).

Evaluation (with --case): for each lender/product, rules in effect on the case date are applied.
Per rule: pass | fail | refer. Missing case data -> refer (never pass). Unit mismatch -> refer.
Product outcome: any fail -> ineligible_indicative; else any refer, stale rule or no rules in
effect -> refer; else eligible_indicative. The engine never outputs an approval or a credit decision.

Usage: criteria_engine.py criteria.json [--case case.json] [--as-of YYYY-MM-DD]
                          [--max-age-days 90] [--strict] [--json]
Exit: 0 criteria valid (and case evaluated), 1 validation errors (case not evaluated),
      2 unreadable input.

Scope: indicative criteria matching for decision support. Lender underwriting makes every decision.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

SCOPE = ("Scope: indicative criteria matching only; not a lending decision, offer or advice. "
         "The lender's own underwriting decides.")
REQUIRED = ["rule_id", "lender", "product", "criterion", "operator", "value", "unit",
            "effective_from", "source_document", "last_verified"]
OPERATORS = {"lt", "lte", "gt", "gte", "eq", "neq", "in", "not_in", "between", "is_true", "is_false"}
OUTCOMES = ("eligible_indicative", "ineligible_indicative", "refer")


class InputError(ValueError):
    pass


def _f(fid: str, severity: str, rule: str, message: str) -> dict:
    return {"id": fid, "severity": severity, "rule": rule, "message": message}


def _d(raw) -> date | None:
    if raw in (None, ""):
        return None
    return date.fromisoformat(str(raw))


# ----------------------------------------------------------------------------- validation
def validate(rules: list[dict], as_of: date | None = None, max_age_days: int = 90) -> list[dict]:
    findings: list[dict] = []
    ids = Counter(r.get("rule_id") for r in rules)
    windows: dict[tuple, list[tuple]] = defaultdict(list)
    for r in rules:
        rid = str(r.get("rule_id") or "<blank>")
        if ids[r.get("rule_id")] > 1:
            findings.append(_f(rid, "error", "duplicate-rule-id", "rule_id used more than once"))
        miss = [k for k in REQUIRED if r.get(k) in (None, "") and k not in ("value", "source_document")]
        if "value" not in r and r.get("operator") not in ("is_true", "is_false"):
            miss.append("value")
        if miss:
            findings.append(_f(rid, "error", "missing-field", f"missing: {miss}"))
        if not r.get("source_document"):
            findings.append(_f(rid, "error", "missing-source", "no source_document: provenance required"))
        op = r.get("operator")
        val = r.get("value")
        if op not in OPERATORS:
            findings.append(_f(rid, "error", "unknown-operator", f"operator '{op}' not in {sorted(OPERATORS)}"))
        elif op == "between" and not (isinstance(val, list) and len(val) == 2
                                      and all(isinstance(v, (int, float)) for v in val) and val[0] <= val[1]):
            findings.append(_f(rid, "error", "bad-value", "between needs [low, high] numbers with low <= high"))
        elif op in ("in", "not_in") and not isinstance(val, list):
            findings.append(_f(rid, "error", "bad-value", f"{op} needs a list value"))
        elif op in ("lt", "lte", "gt", "gte") and (isinstance(val, bool) or not isinstance(val, (int, float))):
            findings.append(_f(rid, "error", "bad-value", f"{op} needs a numeric value"))
        try:
            start, end = _d(r.get("effective_from")), _d(r.get("effective_to"))
            verified = _d(r.get("last_verified"))
        except ValueError:
            findings.append(_f(rid, "error", "bad-date", "dates must be YYYY-MM-DD"))
            continue
        if start and end and end < start:
            findings.append(_f(rid, "error", "bad-effective-period", "effective_to is before effective_from"))
            continue
        if start:
            windows[(r.get("lender"), r.get("product"), r.get("criterion"))].append((start, end, rid))
        if verified and as_of and not (end and end < as_of):  # superseded rules are not re-verified
            age = (as_of - verified).days
            if age > max_age_days:
                findings.append(_f(rid, "warning", "stale-criterion",
                                   f"last verified {age} days before {as_of} (limit {max_age_days}); outcomes using it are referred"))
            elif age < 0:
                findings.append(_f(rid, "error", "future-verification", "last_verified is after the as-of date"))
    for key, wins in windows.items():
        wins.sort(key=lambda w: w[0])
        for (s1, e1, r1), (s2, e2, r2) in zip(wins, wins[1:]):
            if e1 is None or s2 <= e1:
                findings.append(_f(r2, "error", "overlapping-effective-dates",
                                   f"{r1} and {r2} both in effect for {key[0]} / {key[1]} / {key[2]}"))
    return findings


# ----------------------------------------------------------------------------- evaluation
def apply_operator(op: str, actual, value) -> bool:
    if op in ("is_true", "is_false"):
        if not isinstance(actual, bool):
            raise TypeError("expected true/false")
        return actual if op == "is_true" else not actual
    if op in ("lt", "lte", "gt", "gte", "between"):
        if isinstance(actual, bool) or not isinstance(actual, (int, float)):
            raise TypeError("expected a number")
    if op == "lt":
        return actual < value
    if op == "lte":
        return actual <= value
    if op == "gt":
        return actual > value
    if op == "gte":
        return actual >= value
    if op == "eq":
        return actual == value
    if op == "neq":
        return actual != value
    if op == "in":
        return actual in value
    if op == "not_in":
        return actual not in value
    if op == "between":
        return value[0] <= actual <= value[1]
    raise ValueError(op)


def in_effect(rule: dict, on: date) -> bool:
    start, end = _d(rule["effective_from"]), _d(rule.get("effective_to"))
    return start <= on and (end is None or on <= end)


def evaluate(rules: list[dict], case: dict, stale_ids: set[str] | None = None) -> list[dict]:
    stale_ids = stale_ids or set()
    if not isinstance(case, dict) or not isinstance(case.get("facts"), dict):
        raise InputError("case must be an object with a 'facts' object")
    try:
        on = _d(case.get("application_date"))
    except ValueError:
        raise InputError("application_date must be YYYY-MM-DD") from None
    if on is None:
        raise InputError("case needs application_date (YYYY-MM-DD) to select criteria in effect")
    facts, units = case["facts"], case.get("units", {}) or {}
    products: dict[tuple, list[dict]] = defaultdict(list)
    for r in rules:
        products[(r["lender"], r["product"])]
    for r in rules:
        if in_effect(r, on):
            products[(r["lender"], r["product"])].append(r)
    results = []
    for (lender, product), active in sorted(products.items()):
        reasons = []
        for r in active:
            base = {"rule_id": r["rule_id"], "criterion": r["criterion"], "operator": r["operator"],
                    "value": r.get("value"), "unit": r["unit"], "source_document": r["source_document"],
                    "last_verified": r["last_verified"]}
            crit = r["criterion"]
            if crit not in facts or facts[crit] is None:
                reasons.append({**base, "actual": None, "result": "refer",
                                "reason": f"missing case data for '{crit}' - cannot assume it passes"})
                continue
            if crit in units and units[crit] != r["unit"]:
                reasons.append({**base, "actual": facts[crit], "result": "refer",
                                "reason": f"unit mismatch: case '{units[crit]}' vs rule '{r['unit']}'"})
                continue
            try:
                ok = apply_operator(r["operator"], facts[crit], r.get("value"))
            except TypeError as exc:
                reasons.append({**base, "actual": facts[crit], "result": "refer", "reason": f"type mismatch: {exc}"})
                continue
            res = "pass" if ok else "fail"
            if ok and r["rule_id"] in stale_ids:
                res, why = "refer", "criterion passes but its source is stale; re-verify with the lender"
            else:
                why = "meets criterion" if ok else "does not meet criterion"
            reasons.append({**base, "actual": facts[crit], "result": res, "reason": why})
        if not active:
            outcome, note = "refer", "no criteria in effect on the application date"
        elif any(x["result"] == "fail" for x in reasons):
            outcome, note = "ineligible_indicative", "at least one criterion not met"
        elif any(x["result"] == "refer" for x in reasons):
            outcome, note = "refer", "missing, mismatched or stale information - human review needed"
        else:
            outcome, note = "eligible_indicative", ("all criteria in effect met on the data supplied; excludes affordability "
                                                    "assessment, credit search, valuation and underwriting - not an offer or decision")
        results.append({"lender": lender, "product": product, "outcome": outcome, "note": note,
                        "rules_evaluated": len(reasons), "reasons": reasons})
    return results


def load_rules(doc) -> list[dict]:
    if not isinstance(doc, dict) or not isinstance(doc.get("rules"), list):
        raise InputError("criteria file must be an object with a 'rules' list")
    for i, r in enumerate(doc["rules"]):
        if not isinstance(r, dict):
            raise InputError(f"rules[{i}] must be an object")
    return doc["rules"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate lender criteria and evaluate a synthetic case.")
    ap.add_argument("criteria", type=Path)
    ap.add_argument("--case", type=Path)
    ap.add_argument("--as-of", help="date for staleness check (default: case application_date)")
    ap.add_argument("--max-age-days", type=int, default=90)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        doc = json.loads(args.criteria.read_text(encoding="utf-8"))
        rules = load_rules(doc)
        case = json.loads(args.case.read_text(encoding="utf-8")) if args.case else None
        as_of = _d(args.as_of) if args.as_of else (_d(case.get("application_date")) if isinstance(case, dict) else None)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 2
    findings = validate(rules, as_of, args.max_age_days)
    if as_of is None:
        findings.append(_f("-", "info", "staleness-not-checked", "no --as-of or case date: last_verified age not checked"))
    sev = Counter(f["severity"] for f in findings)
    out: dict = {"dataset": doc.get("dataset", ""), "as_of": as_of.isoformat() if as_of else None,
                 "findings": findings,
                 "summary": {"rules": len(rules), "errors": sev.get("error", 0),
                             "warnings": sev.get("warning", 0), "info": sev.get("info", 0)}}
    failed = out["summary"]["errors"] > 0 or (args.strict and out["summary"]["warnings"] > 0)
    if case is not None and not failed:
        stale = {f["id"] for f in findings if f["rule"] == "stale-criterion"}
        try:
            out["case_id"] = case.get("case_id", "")
            out["results"] = evaluate(rules, case, stale)
        except InputError as exc:
            print(f"invalid case: {exc}", file=sys.stderr)
            return 2
        out["summary"]["outcomes"] = dict(Counter(r["outcome"] for r in out["results"]))
    elif case is not None:
        out["results"] = []
        out["summary"]["note"] = "case not evaluated: fix criteria validation errors first"
    out["passed"] = not failed
    out["scope"] = SCOPE
    if args.json:
        print(json.dumps(out, indent=2, default=str))
    else:
        for f in findings:
            print(f"{f['severity'].upper():8} {f['id']:<16} {f['rule']:<28} {f['message']}")
        for r in out.get("results", []):
            print(f"\n{r['lender']} - {r['product']}: {r['outcome'].upper()} ({r['note']})")
            for x in r["reasons"]:
                print(f"    [{x['result']:5}] {x['rule_id']:<14} {x['criterion']} {x['operator']} {x['value']} "
                      f"{x['unit']} (case: {x['actual']}) - {x['reason']}; source {x['source_document']}")
        print(f"\n{'FAIL' if failed else 'PASS'}: {out['summary']}")
        print(SCOPE)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
