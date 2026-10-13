#!/usr/bin/env python3
"""Validate an OWASP ASVS 5.0.0 control verification map (CSV) and compute verification coverage.

CSV columns: asvs_id, level, applicable (yes|no|na), justification, implementation_ref,
verification_method, evidence_ref, status (not_verified|pass|fail).

Checks: version-qualified IDs (v5.0.0-x.y.z) that exist in the bundled index, level matches the
index, N/A or "no" rows carry a justification, "pass" rows carry evidence, failed controls, rows
outside the chosen scope, and in-scope requirements missing from the map. Coverage is reported
per chapter for the chosen level (cumulative: L2 includes L1, L3 includes all).

Usage:
  asvs_coverage.py map.csv --level 2 [--chapters V1,V6,V8] [--require-complete] [--strict] [--json]
  asvs_coverage.py --generate-template --level 1 [--chapters V8] [--out map.csv]
Exit codes: 0 no errors, 1 errors, 2 unreadable input / usage error.

Scope: bookkeeping over the map as written. It cannot judge whether evidence really demonstrates a
requirement; OWASP does not certify, and this output is not a compliance statement.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from collections import Counter
from pathlib import Path

DEFAULT_INDEX = Path(__file__).resolve().parents[1] / "assets" / "data" / "asvs-5.0.0-index.json"
VERSION = "5.0.0"
COLUMNS = ["asvs_id", "level", "applicable", "justification", "implementation_ref",
           "verification_method", "evidence_ref", "status"]
APPLICABLE = {"yes", "no", "na"}
STATUSES = {"not_verified", "pass", "fail"}
METHODS = {"automated-test", "manual-test", "code-review", "config-review", "documentation-review",
           "pen-test", "tool-scan", "interview"}
ASVS_ID = re.compile(r"^(?:ASVS-)?v(\d+\.\d+\.\d+)-(\d+)\.(\d+)\.(\d+)$")
BARE = re.compile(r"^V?\d+\.\d+\.\d+$")


def _finding(fid: str, severity: str, rule: str, message: str) -> dict:
    return {"id": fid, "severity": severity, "rule": rule, "message": message}


def load_index(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != VERSION:
        raise ValueError(f"index version {data.get('version')} != {VERSION}")
    return {r["id"]: {"level": int(r["level"]), "chapter": r["chapter"], "section": r["section"]}
            for r in data["requirements"]}


def parse_chapters(raw: str | None, index: dict) -> set[str]:
    known = {v["chapter"] for v in index.values()}
    if not raw:
        return known
    chosen = {("V" + c.strip().upper().lstrip("V")) for c in raw.split(",") if c.strip()}
    unknown = chosen - known
    if unknown:
        raise ValueError(f"unknown chapter(s) {sorted(unknown)}; valid: V1..V17")
    return chosen


def in_scope(index: dict, level: int, chapters: set[str]) -> dict:
    return {rid: v for rid, v in index.items() if v["level"] <= level and v["chapter"] in chapters}


def _key(rid: str) -> tuple:
    return tuple(int(x) for x in rid.split("."))


def check(columns: list[str], rows: list[dict], index: dict, level: int, chapters: set[str],
          require_complete: bool = False) -> dict:
    findings: list[dict] = []
    missing_cols = [c for c in COLUMNS if c not in columns]
    if missing_cols:
        findings.append(_finding("-", "error", "missing-columns", f"missing columns: {', '.join(missing_cols)}"))
        return {"findings": findings, "summary": {"errors": 1, "warnings": 0, "info": 0}}
    scope = in_scope(index, level, chapters)
    seen: Counter = Counter()
    mapped: dict[str, dict] = {}
    for n, r in enumerate(rows, start=2):
        raw = r["asvs_id"]
        fid = raw or f"row{n}"
        m = ASVS_ID.match(raw)
        if not m:
            rule = "asvs-unversioned" if BARE.match(raw) else "asvs-bad-format"
            findings.append(_finding(fid, "error", rule, f"use v{VERSION}-<chapter>.<section>.<req>"))
            continue
        if m.group(1) != VERSION:
            findings.append(_finding(fid, "error", "asvs-version-mismatch", f"map must use ASVS {VERSION} IDs"))
            continue
        rid = f"{m.group(2)}.{m.group(3)}.{m.group(4)}"
        if rid not in index:
            findings.append(_finding(fid, "error", "asvs-unknown-id", f"{rid} is not in ASVS {VERSION}"))
            continue
        seen[rid] += 1
        if seen[rid] == 2:
            findings.append(_finding(fid, "error", "duplicate-row", "requirement listed more than once"))
        if seen[rid] > 1:
            continue
        ref = index[rid]
        lvl = r["level"].upper().lstrip("L")
        if lvl and lvl != str(ref["level"]):
            findings.append(_finding(fid, "error", "level-mismatch",
                                     f"level {r['level']} but ASVS {VERSION} lists L{ref['level']}"))
        if rid not in scope:
            why = f"above target L{level}" if ref["level"] > level else f"chapter {ref['chapter']} not selected"
            findings.append(_finding(fid, "info", "out-of-scope-row", f"row outside chosen scope ({why})"))
            continue
        app = r["applicable"].lower()
        status = r["status"].lower() or "not_verified"
        if app not in APPLICABLE:
            findings.append(_finding(fid, "error", "applicable-value", f"applicable '{r['applicable']}' not yes|no|na"))
            continue
        if status not in STATUSES:
            findings.append(_finding(fid, "error", "status-value", f"status '{r['status']}' not in {sorted(STATUSES)}"))
            continue
        if app in {"no", "na"}:
            if len(r["justification"].strip()) < 10:
                findings.append(_finding(fid, "error", "na-without-justification",
                                         "not-applicable requirement needs a written justification"))
            if status in {"pass", "fail"}:
                findings.append(_finding(fid, "warning", "status-on-not-applicable",
                                         f"status '{status}' on a requirement marked {app}"))
        else:
            if not r["implementation_ref"]:
                findings.append(_finding(fid, "warning", "no-implementation-ref",
                                         "applicable requirement has no implementation reference"))
            if status == "pass" and not r["evidence_ref"]:
                findings.append(_finding(fid, "error", "pass-without-evidence", "status pass with no evidence_ref"))
            if status == "pass" and not r["verification_method"]:
                findings.append(_finding(fid, "warning", "pass-without-method", "status pass with no verification_method"))
            if status == "fail":
                findings.append(_finding(fid, "error", "control-failed", "verification failed: remediate or record risk decision"))
        method = r["verification_method"].lower()
        if method and method not in METHODS:
            findings.append(_finding(fid, "warning", "verification-method",
                                     f"method '{r['verification_method']}' not in {sorted(METHODS)}"))
        mapped[rid] = {"applicable": app, "status": status}
    per_chapter: dict[str, dict] = {}
    for rid, ref in sorted(scope.items(), key=lambda kv: _key(kv[0])):
        c = per_chapter.setdefault(ref["chapter"], {"in_scope": 0, "mapped": 0, "applicable": 0, "not_applicable": 0,
                                                    "pass": 0, "fail": 0, "not_verified": 0, "missing": []})
        c["in_scope"] += 1
        row = mapped.get(rid)
        if not row:
            c["missing"].append(rid)
            continue
        c["mapped"] += 1
        if row["applicable"] == "yes":
            c["applicable"] += 1
            c[row["status"]] += 1
        else:
            c["not_applicable"] += 1
    for ch, c in sorted(per_chapter.items(), key=lambda kv: int(kv[0][1:])):
        c["mapped_pct"] = round(100 * c["mapped"] / c["in_scope"], 1)
        c["pass_pct_of_applicable"] = round(100 * c["pass"] / c["applicable"], 1) if c["applicable"] else None
        if c["missing"]:
            sev = "error" if require_complete else "warning"
            findings.append(_finding(ch, sev, "missing-requirements",
                                     f"{len(c['missing'])} of {c['in_scope']} in-scope requirements not in map: "
                                     + ", ".join(f"v{VERSION}-{x}" for x in c["missing"][:8])
                                     + (" ..." if len(c["missing"]) > 8 else "")))
    tot = {k: sum(c[k] for c in per_chapter.values()) for k in
           ("in_scope", "mapped", "applicable", "not_applicable", "pass", "fail", "not_verified")}
    sev = Counter(f["severity"] for f in findings)
    summary = {"asvs_version": VERSION, "target_level": level, "chapters": sorted(chapters, key=lambda c: int(c[1:])),
               **tot, "mapped_pct": round(100 * tot["mapped"] / tot["in_scope"], 1) if tot["in_scope"] else None,
               "pass_pct_of_applicable": round(100 * tot["pass"] / tot["applicable"], 1) if tot["applicable"] else None,
               "per_chapter": per_chapter, "errors": sev.get("error", 0), "warnings": sev.get("warning", 0),
               "info": sev.get("info", 0)}
    return {"findings": findings, "summary": summary}


def template(index: dict, level: int, chapters: set[str]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(COLUMNS)
    for rid, ref in sorted(in_scope(index, level, chapters).items(), key=lambda kv: _key(kv[0])):
        w.writerow([f"v{VERSION}-{rid}", f"L{ref['level']}", "yes", "", "", "", "", "not_verified"])
    return buf.getvalue()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate an ASVS 5.0.0 verification map and compute coverage.")
    ap.add_argument("map", type=Path, nargs="?")
    ap.add_argument("--level", type=int, choices=[1, 2, 3], required=True)
    ap.add_argument("--chapters", help="comma-separated, e.g. V1,V6,V8 (default: all 17)")
    ap.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    ap.add_argument("--require-complete", action="store_true", help="missing in-scope requirements are errors")
    ap.add_argument("--generate-template", action="store_true")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        index = load_index(args.index)
        chapters = parse_chapters(args.chapters, index)
        if args.generate_template:
            text = template(index, args.level, chapters)
            if args.out and str(args.out) != "-":
                args.out.write_text(text, encoding="utf-8")
            else:
                sys.stdout.write(text)
            return 0
        if args.map is None:
            raise ValueError("map CSV required (or --generate-template)")
        with args.map.open(newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            rows = [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in reader]
            cols = [c.strip() for c in reader.fieldnames or []]
    except (OSError, UnicodeDecodeError, csv.Error, ValueError, KeyError) as exc:
        print(f"cannot run: {exc}", file=sys.stderr)
        return 2
    result = check(cols, rows, index, args.level, chapters, args.require_complete)
    s = result["summary"]
    failed = s["errors"] > 0 or (args.strict and s["warnings"] > 0)
    result["passed"] = not failed
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"ASVS {VERSION} target L{args.level}; chapters {','.join(s.get('chapters', []))}")
        for ch, c in s.get("per_chapter", {}).items():
            print(f"  {ch:<4} in-scope {c['in_scope']:>3}  mapped {c['mapped_pct']:>5}%  applicable {c['applicable']:>3}  "
                  f"pass {c['pass']:>3}  fail {c['fail']:>3}  not_verified {c['not_verified']:>3}  n/a {c['not_applicable']:>3}")
        for f in result["findings"]:
            print(f"{f['severity'].upper():8} {f['id']:<16} {f['rule']:<26} {f['message']}")
        print(f"\n{'FAIL' if failed else 'PASS'}: mapped {s.get('mapped_pct')}% of in-scope; "
              f"pass {s.get('pass_pct_of_applicable')}% of applicable; {s['errors']} errors, {s['warnings']} warnings")
        print("Scope: verification bookkeeping only; not a compliance statement or certification (OWASP does not certify).")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
