#!/usr/bin/env python3
"""Validate a model / AI system card (JSON) against the bundled schema plus semantic rules.

Schema layer: a small built-in JSON Schema subset validator (type, required, properties,
items, enum, pattern, minLength, minItems, minimum, format=date) applied to
assets/schemas/system-card.schema.json.
Semantic layer: evaluation results consistent with their thresholds, evaluation dates and
dataset versions present and not stale (with --as-of), duplicate eval IDs, a GO
recommendation alongside failing evals, sign-off completeness, rollback plan tested,
personal data without a recorded lawful basis, unsupported assurance language.

Usage:
  system_card_check.py card.json [--as-of YYYY-MM-DD] [--max-eval-age-days 180]
                       [--schema system-card.schema.json] [--strict] [--json]
Exit codes: 0 no errors, 1 errors (or warnings with --strict), 2 unreadable input.

Scope: completeness and consistency of the card only. It cannot tell whether the evaluations
were well designed or the system is fit for use; a GO recommendation still needs human sign-off.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from collections import Counter
from pathlib import Path

DEFAULT_SCHEMA = Path(__file__).resolve().parent.parent / "assets" / "schemas" / "system-card.schema.json"
# A name is non-human if it IS a system label ("the model", "AI agent", "GPT-4o") or contains an
# unambiguous product/bot token. Human role titles such as "Head of Model Risk" are allowed.
NON_HUMAN_FULL = re.compile(r"^\s*(the\s+)?(ai|ai\s+system|agent|ai\s+agent|bot|chatbot|model|the\s+model|llm|system|"
                            r"assistant|ai\s+assistant|copilot|automated\s+\w+)\s*$", re.I)
NON_HUMAN_TOKEN = re.compile(r"\b(llm|gpt[\w.-]*|claude[\w.-]*|chatbot|bot)\b", re.I)


class _NonHuman:
    @staticmethod
    def search(text: str):
        return NON_HUMAN_FULL.search(text) or NON_HUMAN_TOKEN.search(text)


NON_HUMAN = _NonHuman()
ASSURANCE = re.compile(r"\b(compliant|certified|approved|guaranteed|fully safe|risk[- ]free)\b", re.I)
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
TYPES = {"object": dict, "array": list, "string": str, "boolean": bool, "null": type(None)}


def _f(where: str, severity: str, rule: str, message: str) -> dict:
    return {"id": where, "severity": severity, "rule": rule, "message": message}


def _is_type(value, name: str) -> bool:
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, TYPES[name])


def parse_date(text) -> dt.date | None:
    if not isinstance(text, str):
        return None
    try:
        return dt.date.fromisoformat(text) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text) else None
    except ValueError:
        return None


def validate_schema(instance, schema: dict, path: str = "$") -> list[dict]:
    """Validate against the supported JSON Schema subset; return findings."""
    out: list[dict] = []
    t = schema.get("type")
    if t:
        names = t if isinstance(t, list) else [t]
        if not any(_is_type(instance, n) for n in names):
            return [_f(path, "error", "schema-type", f"expected {t}, got {type(instance).__name__}")]
    if "enum" in schema and instance not in schema["enum"]:
        out.append(_f(path, "error", "schema-enum", f"{instance!r} not in {schema['enum']}"))
    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            out.append(_f(path, "error", "schema-min-length", f"shorter than {schema['minLength']} characters"))
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            out.append(_f(path, "error", "schema-pattern", f"{instance!r} does not match {schema['pattern']}"))
        if schema.get("format") == "date" and parse_date(instance) is None:
            out.append(_f(path, "error", "schema-format", f"{instance!r} is not a YYYY-MM-DD date"))
    if _is_type(instance, "number") and "minimum" in schema and instance < schema["minimum"]:
        out.append(_f(path, "error", "schema-minimum", f"{instance} < {schema['minimum']}"))
    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                out.append(_f(path, "error", "schema-required", f"missing required property '{key}'"))
        for key, sub in schema.get("properties", {}).items():
            if key in instance:
                out.extend(validate_schema(instance[key], sub, f"{path}.{key}"))
    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            out.append(_f(path, "error", "schema-min-items", f"needs at least {schema['minItems']} item(s)"))
        if "items" in schema:
            for i, item in enumerate(instance):
                out.extend(validate_schema(item, schema["items"], f"{path}[{i}]"))
    return out


def _meets(value: float, comparator: str, threshold: float) -> bool:
    return {">=": value >= threshold, "<=": value <= threshold, "==": value == threshold,
            ">": value > threshold, "<": value < threshold}[comparator]


def _strings(obj, path: str = "$"):
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from _strings(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _strings(v, f"{path}[{i}]")


def semantic_checks(card: dict, as_of: dt.date | None, max_age: int) -> list[dict]:
    out: list[dict] = []
    evals = card.get("evaluations") if isinstance(card.get("evaluations"), list) else []
    ids = Counter(e.get("eval_id") for e in evals if isinstance(e, dict))
    card_date = parse_date(card.get("card_date"))
    failing = []
    for i, e in enumerate(evals):
        if not isinstance(e, dict):
            continue
        where = f"$.evaluations[{i}]({e.get('eval_id', '?')})"
        if e.get("eval_id") and ids[e["eval_id"]] > 1:
            out.append(_f(where, "error", "duplicate-eval-id", "eval_id appears more than once"))
        val, thr, cmp_, res = e.get("value"), e.get("threshold"), e.get("comparator"), e.get("result")
        if all(_is_type(x, "number") for x in (val, thr)) and cmp_ in (">=", "<=", "==", ">", "<"):
            meets = _meets(val, cmp_, thr)
            if res == "pass" and not meets:
                out.append(_f(where, "error", "eval-result-inconsistent",
                              f"result 'pass' but {val} {cmp_} {thr} is false"))
            if res == "fail" and meets:
                out.append(_f(where, "error", "eval-result-inconsistent",
                              f"result 'fail' but {val} {cmp_} {thr} is true"))
        if res == "fail":
            failing.append(e.get("eval_id", "?"))
        if res == "not_tested":
            out.append(_f(where, "warning", "eval-not-tested", "evaluation listed but not run"))
        d = parse_date(e.get("date"))
        if d and as_of:
            if d > as_of:
                out.append(_f(where, "error", "eval-date-future", f"eval date {d} after --as-of {as_of}"))
            elif (as_of - d).days > max_age:
                out.append(_f(where, "warning", "eval-stale",
                              f"eval is {(as_of - d).days} days old (> {max_age}); re-run before relying on it"))
        if d and card_date and d > card_date:
            out.append(_f(where, "warning", "eval-after-card-date", "eval dated after the card; update card_date"))
    rec = card.get("recommendation")
    if rec == "GO" and failing:
        out.append(_f("$.recommendation", "error", "go-with-failing-eval",
                      f"GO recommended while evals fail: {failing}"))
    if rec == "GO_WITH_CONDITIONS" and failing and not card.get("conditions"):
        out.append(_f("$.recommendation", "error", "conditions-missing",
                      f"GO_WITH_CONDITIONS with failing evals {failing} but no conditions listed"))
    sign = card.get("sign_off") if isinstance(card.get("sign_off"), dict) else {}
    if sign.get("status") == "signed":
        for k in ("name", "role", "date"):
            if not sign.get(k):
                out.append(_f("$.sign_off", "error", "sign-off-incomplete", f"signed but no {k} recorded"))
        if NON_HUMAN.search(str(sign.get("name", ""))):
            out.append(_f("$.sign_off", "error", "sign-off-non-human", "sign-off must be by a named human"))
    elif rec:
        out.append(_f("$.sign_off", "info", "recommendation-awaiting-sign-off",
                      f"recommendation {rec} is advisory until a named human signs off"))
    for i, d in enumerate(card.get("data_lineage") or []):
        if isinstance(d, dict) and d.get("contains_personal_data") is True and not d.get("lawful_basis_ref"):
            out.append(_f(f"$.data_lineage[{i}]", "warning", "personal-data-no-basis",
                          "personal data with no lawful_basis_ref / DPIA pointer"))
    rb = card.get("rollback_plan") if isinstance(card.get("rollback_plan"), dict) else {}
    if rb and not rb.get("last_tested"):
        out.append(_f("$.rollback_plan", "warning", "rollback-untested", "no record that rollback was exercised"))
    mon = card.get("monitoring") if isinstance(card.get("monitoring"), dict) else {}
    for where, owner in (("$.monitoring.alert_owner", mon.get("alert_owner")), ("$.rollback_plan.owner", rb.get("owner"))):
        if owner and NON_HUMAN.search(str(owner)):
            out.append(_f(where, "error", "owner-non-human", f"'{owner}' must be a named human role"))
    contacts = [c for c in card.get("contacts") or [] if isinstance(c, dict)]
    if contacts and all(NON_HUMAN.search(str(c.get("name", ""))) for c in contacts):
        out.append(_f("$.contacts", "error", "no-human-contact", "no named human contact"))
    for i, c in enumerate(contacts):
        if c.get("email") and not EMAIL.fullmatch(c["email"]):
            out.append(_f(f"$.contacts[{i}]", "warning", "contact-email-format", f"'{c['email']}' is not an email"))
    if sign.get("status") != "signed":
        for path, text in _strings(card):
            m = ASSURANCE.search(text)
            if m and not path.startswith("$.sign_off"):
                out.append(_f(path, "warning", "assurance-language",
                              f"'{m.group(0)}' claimed without recorded human sign-off"))
    return out


def check_card(card, schema: dict, as_of: dt.date | None = None, max_age: int = 180) -> dict:
    findings = validate_schema(card, schema)
    if isinstance(card, dict):
        findings.extend(semantic_checks(card, as_of, max_age))
    sev = Counter(f["severity"] for f in findings)
    evals = card.get("evaluations", []) if isinstance(card, dict) else []
    summary = {
        "system": card.get("system_name") if isinstance(card, dict) else None,
        "evaluations": len(evals) if isinstance(evals, list) else 0,
        "recommendation": card.get("recommendation") if isinstance(card, dict) else None,
        "errors": sev.get("error", 0), "warnings": sev.get("warning", 0), "info": sev.get("info", 0),
        "as_of": as_of.isoformat() if as_of else None,
    }
    return {"findings": findings, "summary": summary}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate a model/system card JSON.")
    ap.add_argument("card", type=Path)
    ap.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    ap.add_argument("--as-of", help="YYYY-MM-DD for eval staleness checks")
    ap.add_argument("--max-eval-age-days", type=int, default=180)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    as_of = parse_date(args.as_of) if args.as_of else None
    if args.as_of and as_of is None:
        print(f"--as-of must be YYYY-MM-DD, got {args.as_of!r}", file=sys.stderr)
        return 2
    if args.max_eval_age_days < 0:
        print("--max-eval-age-days must be >= 0", file=sys.stderr)
        return 2
    try:
        schema = json.loads(args.schema.read_text(encoding="utf-8"))
        card = json.loads(args.card.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 2
    result = check_card(card, schema, as_of, args.max_eval_age_days)
    s = result["summary"]
    failed = s["errors"] > 0 or (args.strict and s["warnings"] > 0)
    result["passed"] = not failed
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for f in result["findings"]:
            print(f"{f['severity'].upper():8} {f['rule']:<32} {f['id']}: {f['message']}")
        print(f"\n{'FAIL' if failed else 'PASS'}: {s}")
        print("Scope: card completeness/consistency only; fitness for use and go/no-go need human sign-off.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
