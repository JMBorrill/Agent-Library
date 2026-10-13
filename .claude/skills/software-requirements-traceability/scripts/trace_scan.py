#!/usr/bin/env python3
"""Build a requirement -> code -> test traceability matrix from tags in source and test files.

Tags are requirement IDs found inside comments, docstrings, test names / test titles, or explicit
`@req ID` markers. Optionally attaches JUnit XML results so each requirement gets a status
(pass / fail / blocked / not_tested). A pass is never inferred from a missing result.

Usage:
  trace_scan.py requirements.csv --src DIR [--src DIR] --tests DIR [--tests DIR]
                [--junit results.xml] [--id-pattern REGEX] [--matrix-csv out.csv] [--strict] [--json]
Exit codes: 0 no errors, 1 errors (gaps), 2 unreadable input / usage error.

Scope: finds declared trace links only. A tag does not prove that code implements, or a test
verifies, the requirement; a reviewer must confirm each link.
"""
from __future__ import annotations

import argparse
import ast
import csv
import io
import json
import re
import sys
import tokenize
import xml.etree.ElementTree as ET
from pathlib import Path

DEFAULT_ID_PATTERN = r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-[0-9]{3,}"
TEXT_EXT = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".java", ".kt", ".go", ".cs", ".rb",
            ".rs", ".c", ".cc", ".cpp", ".h", ".hpp", ".swift", ".scala", ".php", ".sql", ".sh"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
REQ_MARKER = r"@req\s+({pat})"
JS_TEST = re.compile(r"\b(?:it|test)\s*\(\s*(['\"`])((?:(?!\1).)*)\1")
STATUSES = {"proposed", "approved", "retired"}
TOP_LEVELS = {"mission", "stakeholder", "business", "need"}  # validated with users, not unit-tested


def _finding(fid: str, severity: str, rule: str, message: str) -> dict:
    return {"id": fid, "severity": severity, "rule": rule, "message": message}


def iter_files(dirs: list[Path]) -> list[Path]:
    out = []
    for d in dirs:
        if d.is_file():
            out.append(d)
            continue
        for p in sorted(d.rglob("*")):
            if p.is_file() and p.suffix in TEXT_EXT and not (set(p.parts) & SKIP_DIRS):
                out.append(p)
    return out


def _ids(text: str, rx: re.Pattern) -> list[str]:
    return rx.findall(text)


def python_tags(text: str, rx: re.Pattern) -> list[tuple[int, str]]:
    """IDs inside comments and docstrings (string statements) of a Python file."""
    tags: list[tuple[int, str]] = []
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return [(i, x) for i, line in enumerate(text.splitlines(), 1) if "#" in line
                for x in _ids(line.split("#", 1)[1], rx)]
    prev = tokenize.NEWLINE
    for tok in toks:
        if tok.type == tokenize.COMMENT:
            tags += [(tok.start[0], x) for x in _ids(tok.string, rx)]
        elif tok.type == tokenize.STRING and prev in (tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT,
                                                      tokenize.NL, tokenize.ENCODING):
            tags += [(tok.start[0], x) for x in _ids(tok.string, rx)]
        if tok.type not in (tokenize.COMMENT, tokenize.NL):
            prev = tok.type
    return tags


def c_like_tags(text: str, rx: re.Pattern) -> list[tuple[int, str]]:
    """IDs inside // and /* */ comments (and # comments for sh/sql-ish files)."""
    tags = []
    for m in re.finditer(r"//[^\n]*|/\*.*?\*/|--[^\n]*|^\s*#[^\n]*", text, re.S | re.M):
        line = text.count("\n", 0, m.start()) + 1
        for sub in re.finditer(rx, m.group(0)):
            tags.append((line + m.group(0).count("\n", 0, sub.start()), sub.group(0)))
    return tags


def scan_code(path: Path, rx: re.Pattern, marker: re.Pattern) -> list[tuple[int, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    tags = python_tags(text, rx) if path.suffix == ".py" else c_like_tags(text, rx)
    for i, line in enumerate(text.splitlines(), 1):
        tags += [(i, m) for m in marker.findall(line)]
    return sorted(set(tags))


def scan_tests(path: Path, rx: re.Pattern, marker: re.Pattern) -> list[dict]:
    """Return tests: {name, file, line, ids}. File-level tags apply to every test in the file."""
    text = path.read_text(encoding="utf-8", errors="replace")
    tags = scan_code(path, rx, marker)
    tests: list[dict] = []
    used_lines: set[int] = set()
    if path.suffix == ".py":
        try:
            tree = ast.parse(text)
        except SyntaxError:
            tree = None
        for node in ast.walk(tree) if tree is not None else []:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
                end = getattr(node, "end_lineno", node.lineno)
                start = min([node.lineno] + [d.lineno for d in node.decorator_list]) - 1  # comment above
                span = set(range(start, end + 1))
                ids = set(_ids(node.name.replace("_", "-"), rx)) | {t for ln, t in tags if ln in span}
                used_lines |= span
                tests.append({"name": node.name, "file": path.as_posix(), "line": node.lineno, "ids": ids})
    else:
        lines = text.splitlines()
        for m in JS_TEST.finditer(text):
            ln = text.count("\n", 0, m.start()) + 1
            ids = set(_ids(m.group(2), rx))
            span = {ln}
            j = ln - 2  # comment lines immediately above the test
            while j >= 0 and lines[j].strip().startswith(("//", "*", "/*")):
                span.add(j + 1)
                j -= 1
            ids |= {t for l2, t in tags if l2 in span}
            used_lines |= span
            tests.append({"name": m.group(2), "file": path.as_posix(), "line": ln, "ids": ids})
    file_level = {t for ln, t in tags if ln not in used_lines}
    for t in tests:
        t["ids"] |= file_level
    if not tests and tags:
        tests.append({"name": f"<file:{path.name}>", "file": path.as_posix(), "line": tags[0][0],
                      "ids": {t for _, t in tags}})
    return tests


def parse_junit(path: Path) -> dict[str, str]:
    """Map test name -> pass|fail|blocked from a JUnit XML file."""
    root = ET.parse(path).getroot()
    results: dict[str, str] = {}
    for case in root.iter("testcase"):
        name = case.get("name", "")
        if case.find("failure") is not None or case.find("error") is not None:
            res = "fail"
        elif case.find("skipped") is not None:
            res = "blocked"
        else:
            res = "pass"
        for key in {name, name.split("[")[0], f"{case.get('classname', '')}.{name}"}:
            prev = results.get(key)
            results[key] = "fail" if "fail" in (prev, res) else res
    return results


def read_requirements(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        cols = [c.strip() for c in (reader.fieldnames or [])]
        if "id" not in cols or "status" not in cols:
            raise ValueError("requirements CSV needs at least 'id' and 'status' columns")
        return [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in reader]


def build(reqs: list[dict], code_tags: dict[str, list[tuple[int, str]]], tests: list[dict],
          junit: dict[str, str] | None) -> dict:
    findings: list[dict] = []
    status = {r["id"]: r["status"].lower() for r in reqs if r.get("id")}
    for r in reqs:
        if r.get("status", "").lower() not in STATUSES:
            findings.append(_finding(r.get("id") or "<blank>", "error", "bad-status",
                                     f"status '{r.get('status')}' not in {sorted(STATUSES)}"))
    code_refs: dict[str, list[str]] = {}
    for f, tags in code_tags.items():
        for ln, rid in tags:
            code_refs.setdefault(rid, []).append(f"{f}:{ln}")
    test_refs: dict[str, list[dict]] = {}
    for t in tests:
        for rid in sorted(t["ids"]):
            test_refs.setdefault(rid, []).append(t)
    # references to unknown / retired IDs
    for rid, refs in sorted(code_refs.items()):
        if rid not in status:
            findings.append(_finding(rid, "warning", "code-unknown-requirement", f"code tags unknown ID at {refs[0]}"))
        elif status[rid] == "retired":
            findings.append(_finding(rid, "warning", "code-retired-requirement", f"code tags retired ID at {refs[0]}"))
    for rid, ts in sorted(test_refs.items()):
        where = f"{ts[0]['file']}::{ts[0]['name']}"
        if rid not in status:
            findings.append(_finding(rid, "error", "test-unknown-requirement", f"test references unknown ID ({where})"))
        elif status[rid] == "retired":
            findings.append(_finding(rid, "error", "test-retired-requirement", f"test references retired ID ({where})"))
    matrix = []
    for r in reqs:
        rid = r.get("id")
        if not rid:
            continue
        st = status[rid]
        ts = test_refs.get(rid, [])
        result = "not_tested"
        missing = []
        if junit is not None and ts:
            res = []
            for t in ts:
                got = junit.get(t["name"]) or junit.get(t["name"].split("[")[0])
                res.append(got)
                if got is None:
                    missing.append(t["name"])
            if "fail" in res:
                result = "fail"
            elif res and all(x == "pass" for x in res):
                result = "pass"
            elif "blocked" in res:
                result = "blocked"
        row = {"id": rid, "status": st, "code_refs": code_refs.get(rid, []),
               "tests": [f"{t['file']}::{t['name']}" for t in ts], "result": result}
        if missing:
            row["tests_without_result"] = missing
        matrix.append(row)
        if st == "retired":
            continue
        if r.get("level", "").lower() in TOP_LEVELS:
            row["note"] = "need-level: validated with stakeholders, not expected in code tests"
            continue
        if st == "approved" and not ts:
            findings.append(_finding(rid, "error", "approved-untested", "approved requirement has no linked test"))
        elif st == "proposed" and not ts and code_refs.get(rid):
            findings.append(_finding(rid, "warning", "code-untested", "requirement tagged in code but no test"))
        if st == "approved" and ts and not code_refs.get(rid):
            findings.append(_finding(rid, "info", "no-code-trace", "tested but no code location tagged"))
        if result == "fail":
            findings.append(_finding(rid, "error", "test-failed", "at least one linked test failed or errored"))
        if missing and result != "fail":
            findings.append(_finding(rid, "warning", "missing-result",
                                     f"no JUnit result for {missing}; status left as {result}"))
    if junit is None:
        findings.append(_finding("-", "info", "no-results", "no JUnit file given: every result is not_tested"))
    sev = {s: sum(1 for x in findings if x["severity"] == s) for s in ("error", "warning", "info")}
    active = [m for m in matrix if m["status"] == "approved" and "note" not in m]
    summary = {"requirements": len(matrix), "approved_code_level": len(active),
               "approved_with_tests": sum(1 for m in active if m["tests"]),
               "approved_passing": sum(1 for m in active if m["result"] == "pass"),
               "tests_found": len(tests), "code_tags": sum(len(v) for v in code_refs.values()),
               "errors": sev["error"], "warnings": sev["warning"], "info": sev["info"]}
    return {"findings": findings, "summary": summary, "matrix": matrix}


def run(req_csv: Path, src: list[Path], test_dirs: list[Path], junit: Path | None,
        id_pattern: str = DEFAULT_ID_PATTERN, base: Path | None = None) -> dict:
    rx = re.compile(id_pattern)
    marker = re.compile(REQ_MARKER.format(pat=id_pattern))
    reqs = read_requirements(req_csv)
    test_files = iter_files(test_dirs)
    test_set = {p.resolve() for p in test_files}

    def rel(p: Path) -> str:
        try:
            return p.resolve().relative_to((base or Path.cwd()).resolve()).as_posix()
        except ValueError:
            return p.as_posix()

    code_tags = {rel(p): scan_code(p, rx, marker) for p in iter_files(src) if p.resolve() not in test_set}
    tests = []
    for p in test_files:
        for t in scan_tests(p, rx, marker):
            t["file"] = rel(p)
            tests.append(t)
    results = parse_junit(junit) if junit else None
    return build(reqs, code_tags, tests, results)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Requirement -> code -> test traceability scan.")
    ap.add_argument("requirements", type=Path)
    ap.add_argument("--src", type=Path, action="append", default=[])
    ap.add_argument("--tests", type=Path, action="append", default=[])
    ap.add_argument("--junit", type=Path)
    ap.add_argument("--id-pattern", default=DEFAULT_ID_PATTERN)
    ap.add_argument("--base", type=Path, help="paths in output are relative to this directory")
    ap.add_argument("--matrix-csv", type=Path)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if not args.tests:
        print("at least one --tests directory is required", file=sys.stderr)
        return 2
    try:
        re.compile(args.id_pattern)
        for d in args.src + args.tests:
            if not d.exists():
                raise OSError(f"{d} does not exist")
        result = run(args.requirements, args.src, args.tests, args.junit, args.id_pattern, args.base)
    except (OSError, UnicodeDecodeError, csv.Error, ValueError, ET.ParseError, re.error) as exc:
        print(f"cannot run trace scan: {exc}", file=sys.stderr)
        return 2
    s = result["summary"]
    failed = s["errors"] > 0 or (args.strict and s["warnings"] > 0)
    result["passed"] = not failed
    if args.matrix_csv:
        with args.matrix_csv.open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["id", "status", "code_refs", "tests", "result"])
            for m in result["matrix"]:
                w.writerow([m["id"], m["status"], ";".join(m["code_refs"]), ";".join(m["tests"]), m["result"]])
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"{'ID':<16} {'STATUS':<9} {'CODE':>4} {'TESTS':>5} RESULT")
        for m in result["matrix"]:
            print(f"{m['id']:<16} {m['status']:<9} {len(m['code_refs']):>4} {len(m['tests']):>5} {m['result']}")
        print()
        for f in result["findings"]:
            print(f"{f['severity'].upper():8} {f['id']:<16} {f['rule']:<26} {f['message']}")
        print(f"\n{'FAIL' if failed else 'PASS'}: {s}")
        print("Scope: declared trace links only; a reviewer must confirm each link is genuine.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
