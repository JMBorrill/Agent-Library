#!/usr/bin/env python3
"""Lint a requirements register (CSV) for identifier, quality and traceability defects.

Checks: required columns, ID format/uniqueness, statement quality (shall, ambiguity, atomicity,
escape clauses, TBD/TBR), approval completeness, verification method, parent links, cycles and
orphans. Optionally prints the parent->child tree.

Usage:
  req_lint.py requirements.csv [--id-pattern REGEX] [--strict] [--tree] [--json]
Exit codes: 0 no errors (warnings allowed unless --strict), 1 errors, 2 unreadable input.

Scope: a structural/linguistic check. It cannot judge whether a requirement is technically
correct, complete, feasible or safe — that needs an accountable engineer.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

DEFAULT_ID_PATTERN = r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-[0-9]{3,}$"
REQUIRED_COLUMNS = ["id", "statement", "rationale", "source", "owner", "status",
                    "verification_method", "acceptance_criteria"]
OPTIONAL_COLUMNS = ["parent", "level", "verification_id", "priority", "notes"]
STATUSES = {"proposed", "approved", "retired"}
METHODS = {"test", "analysis", "inspection", "demonstration"}
TOP_LEVELS = {"mission", "stakeholder", "business", "need"}

AMBIGUOUS = [
    "adequate", "appropriate", "as appropriate", "sufficient", "user-friendly", "user friendly",
    "easy", "easily", "simple", "fast", "quick", "quickly", "rapid", "efficient", "efficiently",
    "flexible", "robust", "reliable", "reliably", "safe", "secure", "seamless", "intuitive",
    "minimal", "minimize", "minimise", "maximize", "maximise", "optimal", "optimize", "optimise",
    "approximately", "about", "several", "some", "many", "few", "large", "small", "high", "low",
    "state-of-the-art", "best practice", "modern", "normal", "typical", "significant",
    "reasonable", "timely", "real-time", "real time", "as needed", "user-centric",
]
ESCAPE_CLAUSES = ["if possible", "where possible", "where practical", "if practical",
                  "as required", "as necessary", "to the extent", "if feasible", "where feasible",
                  "unless otherwise", "as far as possible"]
OPEN_ENDED = ["etc", "and so on", "including but not limited to", "such as", "and/or"]
WEAK_MODALS = re.compile(r"\b(should|may|might|could|will|must|can)\b", re.I)
SHALL = re.compile(r"\bshall\b", re.I)
TBX = re.compile(r"\bTB[DRC]\b")
NUMBER = re.compile(r"\d")


def _finding(rid: str, severity: str, rule: str, message: str) -> dict:
    return {"id": rid, "severity": severity, "rule": rule, "message": message}


def _contains_term(text: str, term: str) -> bool:
    return re.search(rf"(?<![\w-]){re.escape(term)}(?![\w-])", text, re.I) is not None


def read_rows(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        rows = [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in reader]
        return [c.strip() for c in (reader.fieldnames or [])], rows


def parents_of(row: dict) -> list[str]:
    return [p.strip() for p in re.split(r"[;,]", row.get("parent", "")) if p.strip()]


def lint(columns: list[str], rows: list[dict], id_pattern: str = DEFAULT_ID_PATTERN) -> dict:
    findings: list[dict] = []
    missing = [c for c in REQUIRED_COLUMNS if c not in columns]
    if missing:
        findings.append(_finding("-", "error", "missing-columns", f"missing columns: {', '.join(missing)}"))
        return {"findings": findings, "summary": {"requirements": len(rows)}}
    if "evidence" in columns or "result" in columns:
        findings.append(_finding("-", "info", "results-in-register",
                                 "evidence/result columns belong in the verification matrix; "
                                 "they are ignored here"))
    id_re = re.compile(id_pattern)
    ids = [r["id"] for r in rows]
    counts = Counter(ids)
    known = set(ids)
    status_of = {r["id"]: r["status"].lower() for r in rows}

    for r in rows:
        rid = r["id"] or "<blank>"
        status = r["status"].lower()
        stmt = r["statement"]
        acc = r["acceptance_criteria"]
        if not r["id"]:
            findings.append(_finding(rid, "error", "blank-id", "requirement has no identifier"))
        elif not id_re.fullmatch(r["id"]):
            findings.append(_finding(rid, "error", "id-format", f"identifier does not match {id_pattern}"))
        if counts[r["id"]] > 1 and r["id"]:
            findings.append(_finding(rid, "error", "duplicate-id", f"identifier used {counts[r['id']]} times"))
        if status not in STATUSES:
            findings.append(_finding(rid, "error", "status", f"status '{r['status']}' not in {sorted(STATUSES)}"))
        if status == "retired":
            continue
        if not stmt:
            findings.append(_finding(rid, "error", "empty-statement", "statement is empty"))
            continue
        # --- statement quality
        n_shall = len(SHALL.findall(stmt))
        is_need = r.get("level", "").lower() in TOP_LEVELS
        if n_shall == 0 and is_need:
            findings.append(_finding(rid, "info", "need-statement", "stakeholder/mission need (no 'shall' expected)"))
        elif n_shall == 0:
            weak = WEAK_MODALS.search(stmt)
            msg = f"uses '{weak.group(1)}' instead of 'shall'" if weak else "no 'shall' — not a binding requirement"
            findings.append(_finding(rid, "warning", "no-shall", msg))
        elif n_shall > 1:
            findings.append(_finding(rid, "warning", "not-atomic", f"{n_shall} 'shall' clauses — split into separate requirements"))
        if re.search(r"\bshall\b[^.;]*\b(and|or)\b[^.;]*\b(shall|provide|support|allow|enable|perform)\b", stmt, re.I):
            findings.append(_finding(rid, "warning", "possible-compound", "conjunction may join two obligations; check atomicity"))
        amb = [t for t in AMBIGUOUS if _contains_term(stmt, t)]
        if amb:
            findings.append(_finding(rid, "warning", "ambiguous-term",
                                     f"ambiguous terms {amb}: define measurably or move to acceptance criteria"))
        esc = [t for t in ESCAPE_CLAUSES if _contains_term(stmt, t)]
        if esc:
            findings.append(_finding(rid, "warning", "escape-clause", f"escape clause {esc} makes the requirement unverifiable"))
        opn = [t for t in OPEN_ENDED if _contains_term(stmt, t)]
        if opn:
            findings.append(_finding(rid, "warning", "open-ended", f"open-ended wording {opn}"))
        if re.search(r"\bshall not\b", stmt, re.I):
            findings.append(_finding(rid, "info", "negative-requirement", "negative requirement: confirm it is verifiable within a bounded set of conditions"))
        # --- TBD/TBR handling
        has_tbx = bool(TBX.search(stmt) or TBX.search(acc))
        if has_tbx and status == "approved":
            findings.append(_finding(rid, "error", "tbd-in-approved", "approved requirement still contains TBD/TBR/TBC"))
        elif has_tbx:
            findings.append(_finding(rid, "warning", "tbd-open", "contains TBD/TBR/TBC — track closure owner and date"))
        # --- verification method and acceptance
        methods = {m.strip().lower() for m in re.split(r"[;,/]", r["verification_method"]) if m.strip()}
        bad = methods - METHODS
        if bad:
            findings.append(_finding(rid, "error", "verification-method", f"unknown method(s) {sorted(bad)}; use {sorted(METHODS)}"))
        if not methods:
            sev = "error" if status == "approved" else "warning"
            findings.append(_finding(rid, sev, "no-verification-method", "no verification method assigned"))
        if not acc:
            sev = "error" if status == "approved" else "warning"
            findings.append(_finding(rid, sev, "no-acceptance-criteria", "acceptance criteria missing"))
        elif methods & {"test", "analysis"} and not NUMBER.search(acc) and not TBX.search(acc):
            findings.append(_finding(rid, "warning", "unmeasurable-acceptance",
                                     "test/analysis acceptance criteria contain no quantitative threshold"))
        # --- approval completeness
        if status == "approved":
            for col in ("owner", "rationale", "source"):
                if not r[col] or r[col].upper() in {"TBD", "N/A", "-"}:
                    findings.append(_finding(rid, "error", f"approved-missing-{col}", f"approved requirement has no {col}"))
        else:
            for col in ("rationale", "source"):
                if not r[col]:
                    findings.append(_finding(rid, "warning", f"missing-{col}", f"no {col} recorded"))
        # --- traceability
        parents = parents_of(r)
        level = r.get("level", "").lower()
        for p in parents:
            if p == r["id"]:
                findings.append(_finding(rid, "error", "self-parent", "requirement lists itself as parent"))
            elif p not in known:
                findings.append(_finding(rid, "error", "unknown-parent", f"parent '{p}' not in register"))
            elif status_of.get(p) == "retired":
                findings.append(_finding(rid, "error", "retired-parent", f"parent '{p}' is retired"))
            elif status == "approved" and status_of.get(p) == "proposed":
                findings.append(_finding(rid, "warning", "approved-under-proposed",
                                         f"approved child of proposed parent '{p}'"))
        if not parents and level and level not in TOP_LEVELS:
            findings.append(_finding(rid, "warning", "orphan", f"level '{level}' requirement has no parent trace"))

    # cycles
    graph = {r["id"]: parents_of(r) for r in rows if r["id"]}
    state: dict[str, int] = {}

    def visit(n: str, stack: list[str]) -> None:
        state[n] = 1
        for p in graph.get(n, []):
            if p not in graph:
                continue
            if state.get(p) == 1:
                cyc = stack[stack.index(p):] + [p] if p in stack else [n, p]
                findings.append(_finding(n, "error", "trace-cycle", "parent cycle: " + " -> ".join(cyc)))
            elif state.get(p) is None:
                visit(p, stack + [p])
        state[n] = 2

    for n in graph:
        if state.get(n) is None:
            visit(n, [n])

    sev = Counter(f["severity"] for f in findings)
    summary = {
        "requirements": len(rows),
        "by_status": dict(Counter(r["status"].lower() for r in rows)),
        "errors": sev.get("error", 0),
        "warnings": sev.get("warning", 0),
        "info": sev.get("info", 0),
        "tbd_count": sum(1 for r in rows if TBX.search(r.get("statement", "") + " " + r.get("acceptance_criteria", ""))),
    }
    return {"findings": findings, "summary": summary}


def tree(rows: list[dict]) -> str:
    children: dict[str, list[str]] = {}
    roots = []
    known = {r["id"] for r in rows}
    for r in rows:
        ps = [p for p in parents_of(r) if p in known]
        if not ps:
            roots.append(r["id"])
        for p in ps:
            children.setdefault(p, []).append(r["id"])
    lines: list[str] = []

    def walk(n: str, depth: int, seen: set[str]) -> None:
        lines.append("  " * depth + "- " + n)
        if n in seen:
            return
        for c in children.get(n, []):
            walk(c, depth + 1, seen | {n})

    for root in roots:
        walk(root, 0, set())
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Lint a requirements register CSV.")
    ap.add_argument("csv", type=Path)
    ap.add_argument("--id-pattern", default=DEFAULT_ID_PATTERN)
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    ap.add_argument("--tree", action="store_true", help="print parent->child tree")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        columns, rows = read_rows(args.csv)
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        print(f"cannot read {args.csv}: {exc}", file=sys.stderr)
        return 2
    result = lint(columns, rows, args.id_pattern)
    s = result["summary"]
    failed = s.get("errors", 1) > 0 or (args.strict and s.get("warnings", 0) > 0)
    result["passed"] = not failed
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for f in result["findings"]:
            print(f"{f['severity'].upper():8} {f['id']:<18} {f['rule']:<26} {f['message']}")
        if args.tree:
            print("\nTrace tree:\n" + tree(rows))
        print(f"\n{'FAIL' if failed else 'PASS'}: {s}")
        print("Scope: structural/linguistic lint only; technical adequacy needs an accountable engineer.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
