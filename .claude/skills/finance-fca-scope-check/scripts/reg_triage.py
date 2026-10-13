#!/usr/bin/env python3
"""UK regulatory applicability TRIAGE for credit / mortgage products (not legal advice).

Reads a product questionnaire JSON (assets/schemas/questionnaire.schema.json) and a rules table
(default: ../assets/rules/triage-rules.json) and lists candidate FCA Handbook sourcebooks/areas -
plus out-of-registry considerations such as UK GDPR and the Equality Act - each with why it was
triggered, confidence, provenance, verification status, verify_effective_version: true and a
mandatory human_signoff_required naming the role.

Status:
  escalate  - jurisdiction missing or not UK: stop, no candidates produced;
  refer     - required answers missing or unrecognised: partial candidates, human must complete;
  triage_complete_signoff_required - all answers present; candidates still need sign-off.

Usage: reg_triage.py questionnaire.json [--rules rules.json] [--json]
Exit: 0 triage complete, 1 refer or escalate, 2 unreadable input or invalid rules table.

Scope: triage of areas to examine only. Not legal advice and not a regulatory compliance
conclusion; every item requires review by the named role against the current Handbook.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCOPE = ("Scope: applicability triage only - not legal advice or a compliance conclusion. Every item "
         "needs sign-off by the named role against the point-in-time FCA Handbook.")
DEFAULT_RULES = Path(__file__).resolve().parent.parent / "assets" / "rules" / "triage-rules.json"
UK = {"uk", "gb", "united kingdom", "great britain", "england", "scotland", "wales", "northern ireland",
      "england and wales"}
REQUIRED = ["jurisdiction", "customer_types", "products", "service_model", "activities.arranges",
            "activities.advises", "activities.lends", "ai_in_decisions", "vulnerable_customers",
            "handles_complaints"]
PRODUCTS = {"first_charge_mortgage", "second_charge_mortgage", "buy_to_let_mortgage",
            "unsecured_consumer_credit", "bnpl", "business_lending", "other"}
CUSTOMER_TYPES = {"consumer", "business"}
SERVICE_MODELS = {"advice", "execution_only", "information_criteria_search", "lending_direct"}
CONFIDENCE = {"high", "medium", "low"}
RULE_FIELDS = ["rule_id", "area", "title", "condition", "why", "confidence", "in_fca_registry",
               "provenance", "verification", "signoff_role"]
_MISSING = object()


class InputError(ValueError):
    pass


def _f(fid: str, severity: str, rule: str, message: str) -> dict:
    return {"id": fid, "severity": severity, "rule": rule, "message": message}


def get(q: dict, path: str):
    cur = q
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return _MISSING
        cur = cur[part]
    return cur


def cond_true(cond: dict, q: dict) -> bool:
    """Evaluate the small condition language used in the rules table."""
    if cond.get("always"):
        return True
    if "all" in cond:
        return all(cond_true(c, q) for c in cond["all"])
    if "any" in cond:
        return any(cond_true(c, q) for c in cond["any"])
    val = get(q, cond["field"])
    if val is _MISSING:
        val = None
    if "equals" in cond:
        return val == cond["equals"]
    if "in" in cond:
        return val in cond["in"]
    if "contains" in cond:
        return isinstance(val, list) and cond["contains"] in val
    if "contains_any" in cond:
        return isinstance(val, list) and bool(set(val) & set(cond["contains_any"]))
    raise InputError(f"unsupported condition {cond}")


def validate_rules(doc) -> list[dict]:
    if not isinstance(doc, dict) or not isinstance(doc.get("rules"), list) or not doc["rules"]:
        raise InputError("rules table must be an object with a non-empty 'rules' list")
    seen = set()
    for r in doc["rules"]:
        missing = [k for k in RULE_FIELDS if k not in r or r[k] in ("", None)]
        if missing:
            raise InputError(f"rule {r.get('rule_id', '?')} missing {missing}")
        if r["rule_id"] in seen:
            raise InputError(f"duplicate rule_id {r['rule_id']}")
        seen.add(r["rule_id"])
        if r["confidence"] not in CONFIDENCE:
            raise InputError(f"rule {r['rule_id']} confidence must be one of {sorted(CONFIDENCE)}")
    return doc["rules"]


def triage(q: dict, rules: list[dict]) -> dict:
    if not isinstance(q, dict):
        raise InputError("questionnaire must be a JSON object")
    findings: list[dict] = []
    jur = get(q, "jurisdiction")
    if jur is _MISSING or not isinstance(jur, str) or not jur.strip():
        findings.append(_f("jurisdiction", "error", "jurisdiction-missing",
                           "jurisdiction not stated: stop and escalate to legal counsel"))
        return _result("escalate", findings, [], q)
    if jur.strip().lower() not in UK:
        findings.append(_f("jurisdiction", "error", "non-uk-jurisdiction",
                           f"jurisdiction '{jur}' is outside this UK FCA triage: stop and escalate to legal counsel "
                           "with local regulatory expertise"))
        return _result("escalate", findings, [], q)
    for path in REQUIRED:
        val = get(q, path)
        if val is _MISSING or val is None or val == [] or val == "":
            findings.append(_f(path, "error", "missing-answer", f"'{path}' not answered: triage incomplete"))
    for path, allowed in (("products", PRODUCTS), ("customer_types", CUSTOMER_TYPES)):
        val = get(q, path)
        if isinstance(val, list):
            unknown = [v for v in val if v not in allowed]
            if unknown:
                findings.append(_f(path, "error", "unrecognised-answer", f"{unknown} not in {sorted(allowed)}"))
        elif val is not _MISSING and val is not None:
            findings.append(_f(path, "error", "unrecognised-answer", f"'{path}' must be a list"))
    sm = get(q, "service_model")
    if isinstance(sm, str) and sm not in SERVICE_MODELS:
        findings.append(_f("service_model", "error", "unrecognised-answer", f"'{sm}' not in {sorted(SERVICE_MODELS)}"))
    for path in ("activities.arranges", "activities.advises", "activities.lends", "ai_in_decisions",
                 "vulnerable_customers", "handles_complaints"):
        val = get(q, path)
        if val is not _MISSING and val is not None and not isinstance(val, bool):
            findings.append(_f(path, "error", "unrecognised-answer", f"'{path}' must be true or false"))
    # Optional questions that drive candidate areas: an explicit null means "asked but not yet answered"
    # and must not be silently treated as false (raised by the mortgage demo review F-01).
    for path in ("activities.communicates_promotions",):
        if get(q, path) is None:
            findings.append(_f(path, "error", "missing-answer", f"'{path}' is null (unanswered): triage incomplete"))
    if get(q, "processes_personal_data") is _MISSING:
        findings.append(_f("processes_personal_data", "info", "assumed-personal-data",
                           "not answered; personal data processing assumed for data protection triage"))
    candidates = []
    for r in rules:
        if cond_true(r["condition"], q):
            candidates.append({
                "rule_id": r["rule_id"], "area": r["area"], "title": r["title"], "why": r["why"],
                "confidence": r["confidence"], "in_fca_registry": r["in_fca_registry"],
                "provenance": r["provenance"], "verification": r["verification"],
                "verify_effective_version": True,
                "human_signoff_required": {"required": True, "role": r["signoff_role"]},
            })
    status = "refer" if any(f["severity"] == "error" for f in findings) else "triage_complete_signoff_required"
    return _result(status, findings, candidates, q)


def _result(status: str, findings: list[dict], candidates: list[dict], q: dict) -> dict:
    sev = [f["severity"] for f in findings]
    return {"status": status, "product": q.get("product_name", "") if isinstance(q, dict) else "",
            "assessment_date": q.get("assessment_date") if isinstance(q, dict) else None,
            "candidates": candidates, "findings": findings,
            "summary": {"candidates": len(candidates),
                        "fca_areas": sorted({c["area"] for c in candidates if c["in_fca_registry"]}),
                        "out_of_registry": sorted({c["area"] for c in candidates if not c["in_fca_registry"]}),
                        "errors": sev.count("error"), "warnings": sev.count("warning"), "info": sev.count("info")}}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="UK FCA regulatory applicability triage (not legal advice).")
    ap.add_argument("questionnaire", type=Path)
    ap.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        rules = validate_rules(json.loads(args.rules.read_text(encoding="utf-8")))
        out = triage(json.loads(args.questionnaire.read_text(encoding="utf-8")), rules)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 2
    except InputError as exc:
        print(f"invalid input: {exc}", file=sys.stderr)
        return 2
    out["passed"] = out["status"] == "triage_complete_signoff_required"
    out["scope"] = SCOPE
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        print(f"Status: {out['status']}")
        for c in out["candidates"]:
            tag = "FCA" if c["in_fca_registry"] else "OUT-OF-REGISTRY"
            print(f"  [{c['confidence']:6}] {c['rule_id']:<14} {tag:<15} {c['area']}: {c['title']}")
            print(f"           why: {c['why']}")
            print(f"           provenance: {c['provenance']} ({c['verification']}); "
                  f"sign-off: {c['human_signoff_required']['role']}; verify effective version")
        for f in out["findings"]:
            print(f"{f['severity'].upper():8} {f['id']:<24} {f['rule']:<22} {f['message']}")
        print(f"\n{out['status'].upper()}: {out['summary']['candidates']} candidate areas; "
              f"errors={out['summary']['errors']}")
        print(SCOPE)
    return 0 if out["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
