#!/usr/bin/env python3
"""Lint an AI risk register (CSV) against NIST AI RMF reference structure and scoring rules.

Checks: required columns, risk ID format/uniqueness, AI RMF reference format and
function/category numbering (against the bundled structure file), 1-5 likelihood/impact,
recomputed inherent and residual scores, high residual risk without a named human acceptor,
risks without evaluation evidence, missing owner/controls, status vocabulary and stale
reviews (with --as-of).

Usage:
  ai_risk_register_check.py register.csv [--as-of YYYY-MM-DD] [--high-threshold 15]
                            [--structure airmf-1.0-structure.json] [--strict] [--json]
Exit codes: 0 no errors, 1 errors (or warnings with --strict), 2 unreadable input.

Scope: structural and arithmetic check of the register. It does not judge whether the risks
identified are complete or the scores right, and it never accepts a risk - a named human does.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import sys
from collections import Counter
from pathlib import Path

DEFAULT_STRUCTURE = Path(__file__).resolve().parent.parent / "assets" / "data" / "airmf-1.0-structure.json"
REQUIRED_COLUMNS = ["risk_id", "description", "rmf_refs", "harm_category", "affected_party",
                    "likelihood", "impact", "inherent_score", "controls", "eval_ids", "owner",
                    "residual_likelihood", "residual_impact", "status", "review_date"]
OPTIONAL_COLUMNS = ["residual_score", "accepted_by", "trustworthiness", "notes"]
RISK_ID = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-RSK-[0-9]{3,}$")
REF_RE = re.compile(r"^AIRMF-(?P<ver>\d+\.\d+)-(?P<fn>[A-Z]+)-(?P<cat>\d+)(?:\.(?P<sub>\d+))?$")
STATUSES = {"open", "mitigating", "accepted", "transferred", "closed"}
LIVE = {"open", "mitigating", "accepted", "transferred"}
HARM_CATEGORIES = {"people", "organisation", "organization", "ecosystem"}
NON_HUMAN = re.compile(r"\b(ai|agent|bot|model|llm|gpt|claude|system|auto(mated)?)\b", re.I)
EVAL_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
TRUST_CHARS = {"valid-and-reliable", "safe", "secure-and-resilient", "accountable-and-transparent",
               "explainable-and-interpretable", "privacy-enhanced", "fair-with-harmful-bias-managed"}


def _f(rid: str, severity: str, rule: str, message: str) -> dict:
    return {"id": rid, "severity": severity, "rule": rule, "message": message}


def load_structure(path: Path = DEFAULT_STRUCTURE) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_rows(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        rows = [{(k or "").strip(): (v or "").strip() for k, v in r.items() if k is not None}
                for r in reader]
        return [c.strip() for c in (reader.fieldnames or [])], rows


def split_list(value: str) -> list[str]:
    return [v.strip() for v in re.split(r"[;,]", value or "") if v.strip()]


def check_ref(ref: str, structure: dict) -> tuple[str | None, str, str]:
    """Return (function or None, severity-or-'', message). Empty severity means valid."""
    m = REF_RE.fullmatch(ref)
    prefix_ver = structure.get("ref_prefix", "AIRMF-1.0").split("-", 1)[1]
    if not m:
        return None, "error", f"'{ref}' does not match AIRMF-<ver>-<FUNCTION>-<cat>[.<sub>]"
    if m["ver"] != prefix_ver:
        return None, "error", f"'{ref}' uses version {m['ver']}; structure file is {prefix_ver}"
    fns = structure["functions"]
    if m["fn"] not in fns:
        return None, "error", f"'{ref}' function {m['fn']} not in {sorted(fns)}"
    cats = fns[m["fn"]]["categories"]
    if m["cat"] not in cats:
        return m["fn"], "error", f"'{ref}' category {m['fn']} {m['cat']} not in 1-{len(cats)}"
    if m["sub"] is not None:
        known = cats[m["cat"]].get("subcategories") or []
        if known and f"{m['cat']}.{m['sub']}" not in known:
            return m["fn"], "error", f"'{ref}' subcategory not in bundled structure"
        if not known:
            return m["fn"], "info", f"'{ref}' subcategory checked for pattern only (list not verified)"
    return m["fn"], "", ""


def _int_1_5(row: dict, col: str, rid: str, findings: list[dict]) -> int | None:
    raw = row.get(col, "")
    try:
        val = int(raw)
    except ValueError:
        findings.append(_f(rid, "error", "score-not-integer", f"{col} '{raw}' is not an integer 1-5"))
        return None
    if not 1 <= val <= 5:
        findings.append(_f(rid, "error", "score-range", f"{col} {val} outside 1-5"))
        return None
    return val


def parse_date(text: str) -> dt.date | None:
    try:
        return dt.date.fromisoformat(text)
    except ValueError:
        return None


def lint(columns: list[str], rows: list[dict], structure: dict, as_of: dt.date | None = None,
         high: int = 15, medium: int = 8, known_evals: set[str] | None = None) -> dict:
    findings: list[dict] = []
    missing = [c for c in REQUIRED_COLUMNS if c not in columns]
    if missing:
        findings.append(_f("-", "error", "missing-columns", f"missing columns: {', '.join(missing)}"))
        return {"findings": findings, "summary": {"risks": len(rows), "errors": 1, "warnings": 0, "info": 0}}
    if not rows:
        findings.append(_f("-", "error", "empty-register", "register has no risks"))
    if as_of is None:
        findings.append(_f("-", "info", "stale-check-skipped", "no --as-of date given; review staleness not checked"))
    counts = Counter(r["risk_id"] for r in rows)
    functions_seen: Counter = Counter()
    bands: Counter = Counter()
    for r in rows:
        rid = r["risk_id"] or "<blank>"
        status = r["status"].lower()
        if not r["risk_id"]:
            findings.append(_f(rid, "error", "blank-id", "risk has no identifier"))
        elif not RISK_ID.fullmatch(r["risk_id"]):
            findings.append(_f(rid, "error", "risk-id-format", "risk ID must look like <PROJECT>-RSK-NNN"))
        if r["risk_id"] and counts[r["risk_id"]] > 1:
            findings.append(_f(rid, "error", "duplicate-id", f"risk ID used {counts[r['risk_id']]} times"))
        if status not in STATUSES:
            findings.append(_f(rid, "error", "status", f"status '{r['status']}' not in {sorted(STATUSES)}"))
        if not r["description"]:
            findings.append(_f(rid, "error", "empty-description", "risk has no description"))
        # --- RMF references
        refs = split_list(r["rmf_refs"])
        if not refs:
            findings.append(_f(rid, "warning", "no-rmf-refs", "no AI RMF reference recorded"))
        for ref in refs:
            fn, sev, msg = check_ref(ref, structure)
            if fn:
                functions_seen[fn] += 1
            if sev == "error":
                rule = "rmf-ref-format" if fn is None and "does not match" in msg else "rmf-ref-unknown"
                findings.append(_f(rid, "error", rule, msg))
            elif sev == "info":
                findings.append(_f(rid, "info", "rmf-subcategory-unverified", msg))
        # --- harm and affected party
        if r["harm_category"].lower() not in HARM_CATEGORIES:
            findings.append(_f(rid, "warning", "harm-category",
                               f"harm_category '{r['harm_category']}' not in {sorted(HARM_CATEGORIES - {'organization'})}"))
        if not r["affected_party"]:
            findings.append(_f(rid, "warning", "no-affected-party", "affected party not identified"))
        for tc in split_list(r.get("trustworthiness", "")):
            if tc.lower() not in TRUST_CHARS:
                findings.append(_f(rid, "warning", "trustworthiness-unknown",
                                   f"'{tc}' is not one of the seven characteristic keys"))
        # --- scoring
        li = _int_1_5(r, "likelihood", rid, findings)
        im = _int_1_5(r, "impact", rid, findings)
        inherent = li * im if li and im else None
        if inherent is not None and r["inherent_score"] != str(inherent):
            findings.append(_f(rid, "error", "inherent-score-mismatch",
                               f"inherent_score '{r['inherent_score']}' != {li}x{im} = {inherent}"))
        rli = _int_1_5(r, "residual_likelihood", rid, findings)
        rim = _int_1_5(r, "residual_impact", rid, findings)
        residual = rli * rim if rli and rim else None
        if residual is not None and r.get("residual_score") and r["residual_score"] != str(residual):
            findings.append(_f(rid, "error", "residual-score-mismatch",
                               f"residual_score '{r['residual_score']}' != {rli}x{rim} = {residual}"))
        if residual is not None and inherent is not None and residual > inherent:
            findings.append(_f(rid, "warning", "residual-exceeds-inherent",
                               f"residual {residual} > inherent {inherent}; controls should not raise risk"))
        if residual is not None:
            bands["high" if residual >= high else "medium" if residual >= medium else "low"] += 1
        # --- ownership, controls, evidence, acceptance
        if not r["owner"] or r["owner"].upper() in {"TBD", "N/A", "-"}:
            findings.append(_f(rid, "error", "no-owner", "risk has no named owner"))
        live = status in LIVE
        if live and not r["controls"] and inherent is not None and inherent >= medium:
            findings.append(_f(rid, "warning", "no-controls", f"inherent score {inherent} with no controls listed"))
        evals = split_list(r["eval_ids"])
        if live and not evals:
            sev = "error" if inherent is not None and inherent >= high else "warning"
            findings.append(_f(rid, sev, "no-eval-evidence",
                               "no evaluation linked; residual score is unmeasured judgement"))
        for e in evals:
            if not EVAL_ID.fullmatch(e):
                findings.append(_f(rid, "error", "eval-id-format", f"eval id '{e}' has invalid characters"))
            elif known_evals is not None and e not in known_evals:
                findings.append(_f(rid, "error", "unknown-eval", f"eval '{e}' not found in the supplied eval set(s)"))
        acceptor = r.get("accepted_by", "")
        if acceptor and NON_HUMAN.search(acceptor):
            findings.append(_f(rid, "error", "accepted-by-non-human",
                               f"accepted_by '{acceptor}' looks like a system or AI; acceptance needs a named human"))
            acceptor = ""
        elif status == "accepted" and not acceptor:
            findings.append(_f(rid, "error", "accepted-without-acceptor", "status accepted but accepted_by is empty"))
        if live and residual is not None and residual >= high and not acceptor:
            findings.append(_f(rid, "error", "high-residual-not-accepted",
                               f"residual {residual} >= {high} with no named human risk acceptor"))
        # --- review date
        rd = parse_date(r["review_date"])
        if not rd:
            sev = "error" if live else "warning"
            findings.append(_f(rid, sev, "review-date", f"review_date '{r['review_date']}' is not YYYY-MM-DD"))
        elif as_of and live and rd < as_of:
            findings.append(_f(rid, "error", "review-overdue", f"review date {rd} is before {as_of}"))
    for fn in structure["functions"]:
        if rows and fn not in functions_seen:
            findings.append(_f("-", "info", "function-not-referenced",
                               f"no risk references {fn}; confirm this is a proportionate omission"))
    sev = Counter(f["severity"] for f in findings)
    summary = {
        "risks": len(rows),
        "by_status": dict(Counter(r["status"].lower() for r in rows)),
        "residual_bands": dict(bands),
        "rmf_function_refs": dict(functions_seen),
        "errors": sev.get("error", 0), "warnings": sev.get("warning", 0), "info": sev.get("info", 0),
        "high_threshold": high, "as_of": as_of.isoformat() if as_of else None,
    }
    return {"findings": findings, "summary": summary}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Lint an AI risk register CSV (NIST AI RMF references).")
    ap.add_argument("csv", type=Path)
    ap.add_argument("--structure", type=Path, default=DEFAULT_STRUCTURE)
    ap.add_argument("--as-of", help="YYYY-MM-DD date for stale-review checks")
    ap.add_argument("--high-threshold", type=int, default=15, help="residual score treated as high (default 15)")
    ap.add_argument("--evals", type=Path, nargs="*", help="eval set JSONL file(s) or eval-config JSON; ids/names must match eval_ids")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    as_of = None
    if args.as_of:
        as_of = parse_date(args.as_of)
        if as_of is None:
            print(f"--as-of must be YYYY-MM-DD, got {args.as_of!r}", file=sys.stderr)
            return 2
    if not 1 <= args.high_threshold <= 25:
        print("--high-threshold must be between 1 and 25", file=sys.stderr)
        return 2
    try:
        structure = load_structure(args.structure)
        columns, rows = read_rows(args.csv)
        known_evals = None
        if args.evals:
            known_evals = set()
            for ep in args.evals:
                text = ep.read_text(encoding="utf-8")
                if ep.suffix == ".jsonl":
                    for line in text.splitlines():
                        if line.strip():
                            item = json.loads(line)
                            known_evals |= {str(item.get("id", ""))} | set(map(str, item.get("tags", [])))
                    known_evals.add(ep.stem)
                else:
                    cfg = json.loads(text)
                    known_evals |= {str(cfg.get("name", "")), str(cfg.get("id", "")), ep.stem}
            known_evals.discard("")
    except (OSError, UnicodeDecodeError, csv.Error, json.JSONDecodeError) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 2
    result = lint(columns, rows, structure, as_of, args.high_threshold, known_evals=known_evals)
    s = result["summary"]
    failed = s["errors"] > 0 or (args.strict and s["warnings"] > 0)
    result["passed"] = not failed
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for f in result["findings"]:
            print(f"{f['severity'].upper():8} {f['id']:<16} {f['rule']:<28} {f['message']}")
        print(f"\n{'FAIL' if failed else 'PASS'}: {s}")
        print("Scope: structural/arithmetic register check only; risk acceptance and go/no-go need a named human.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
