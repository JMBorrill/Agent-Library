#!/usr/bin/env python3
"""Scan a unified diff for review risk signals before (not instead of) human code review.

Checks on added lines only: change size against small/large heuristics, source changes with no
test changes, TODO/FIXME without an issue reference, debug output (print/console.log/debugger),
broad exception swallowing (except: pass, empty catch), hard-coded secret patterns, blocks of
commented-out code and very long functions added in one go.

Usage:
  diff_risk_scan.py change.diff [--small-lines 100] [--large-lines 1000] [--max-files 25]
                    [--max-function-lines 60] [--strict] [--json]
Exit codes: 0 no errors (warnings allowed unless --strict), 1 errors, 2 unreadable input.

Scope: pattern heuristics over the diff text. It cannot judge design, correctness or whether the
change improves code health; that is the reviewer's job.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Size heuristics paraphrased from Google eng-practices review/developer/small-cls.md
# ("~100 lines usually reasonable, ~1000 usually too large"). Heuristics, not hard rules.
DEFAULT_SMALL_LINES = 100
DEFAULT_LARGE_LINES = 1000
DEFAULT_MAX_FILES = 25          # library default (file spread also matters per the source)
DEFAULT_MAX_FUNCTION_LINES = 60  # library default

SOURCE_EXT = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".go", ".java", ".kt", ".rb",
              ".cs", ".rs", ".php", ".scala", ".swift", ".c", ".cc", ".cpp", ".h", ".hpp", ".sql"}
TEST_PATH = re.compile(r"(^|/)(tests?|__tests__|spec|specs)/|(^|/)test_[^/]+\.py$|_test\.(py|go)$|"
                       r"\.(test|spec)\.(js|jsx|ts|tsx|mjs|cjs)$|Test\.(java|kt|cs)$")
ISSUE_REF = re.compile(r"(#\d+|\b[A-Z][A-Z0-9]+-\d+\b|https?://|\bb/\d+|\bissue\b|\bticket\b)", re.I)
TODO = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b")
DEBUG = [
    (re.compile(r"\bconsole\.(log|debug|trace)\s*\("), "console output"),
    (re.compile(r"(^|[^\w.])debugger\s*;?\s*$"), "debugger statement"),
    (re.compile(r"\b(pdb|ipdb)\.set_trace\s*\("), "debugger breakpoint"),
    (re.compile(r"(^|[^\w.])breakpoint\s*\(\s*\)"), "debugger breakpoint"),
    (re.compile(r"(^|[^\w.])print\s*\("), "print() call"),
]
SECRETS = [
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS access key id pattern"),
    (re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"), "private key block"),
    (re.compile(r"\bsk-[A-Za-z0-9-]{8,}"), "API secret key pattern (sk-...)"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"), "GitHub token pattern"),
    (re.compile(r"\bxox[abpr]-[A-Za-z0-9-]{10,}"), "Slack token pattern"),
    (re.compile(r"""(?i)\b(password|passwd|pwd|secret|api[_-]?key|access[_-]?token|auth[_-]?token|"""
                r"""client[_-]?secret)\b\s*[:=]\s*["'][^"'\s]{6,}["']"""), "credential assigned a literal"),
]
PLACEHOLDER = re.compile(r"(?i)(example|changeme|placeholder|<[^>]+>|\$\{|os\.environ|process\.env|getenv)")
COMMENT_LINE = re.compile(r"^\s*(#|//)\s?(.*)$")
CODE_LIKE = re.compile(r"(;\s*$|\)\s*$|\{\s*$|^\s*\}|=\s*\S|\breturn\b|^\s*(def|class|import|from|if|for|while|"
                       r"const|let|var|function|await|elif|else)\b)")
PY_EXCEPT = re.compile(r"^\s*except\s*(?:(?:Exception|BaseException)(?:\s+as\s+\w+)?)?\s*:\s*(pass\b.*)?$")
JS_EMPTY_CATCH = re.compile(r"\bcatch\s*(\([^)]*\))?\s*\{\s*\}")
JS_CATCH_OPEN = re.compile(r"\bcatch\s*(\([^)]*\))?\s*\{\s*$")
PY_DEF = re.compile(r"^(\s*)(async\s+)?def\s+(\w+)")
JS_FUNC = re.compile(r"(\bfunction\s+(\w+)\s*\(|\b(\w+)\s*=\s*(async\s*)?\([^)]*\)\s*=>\s*\{|"
                     r"^\s*(async\s+)?(\w+)\s*\([^)]*\)\s*\{\s*$)")


def _finding(fid: str, severity: str, rule: str, message: str, **extra) -> dict:
    out = {"id": fid, "severity": severity, "rule": rule, "message": message}
    out.update(extra)
    return out


def parse_diff(text: str) -> list[dict]:
    """Return files: {path, added: [(new_lineno, text)], deleted: int, hunks: [[(lineno, text)]]}."""
    files: list[dict] = []
    cur: dict | None = None
    new_line = 0
    hunk: list | None = None
    for raw in text.splitlines():
        if raw.startswith("diff --git "):
            cur = {"path": None, "added": [], "deleted": 0, "hunks": [], "is_new": False, "is_deleted": False}
            files.append(cur)
            m = re.match(r"diff --git a/(\S+) b/(\S+)", raw)
            if m:
                cur["path"] = m.group(2)
            hunk = None
            continue
        if raw.startswith("--- "):
            if cur is None:  # plain unified diff without git header
                cur = {"path": None, "added": [], "deleted": 0, "hunks": [], "is_new": False, "is_deleted": False}
                files.append(cur)
            if raw.strip() == "--- /dev/null":
                cur["is_new"] = True
            continue
        if raw.startswith("+++ ") and cur is not None:
            target = raw[4:].strip().split("\t")[0]
            if target == "/dev/null":
                cur["is_deleted"] = True
            else:
                cur["path"] = target[2:] if target.startswith("b/") else target
            continue
        if raw.startswith("@@") and cur is not None:
            m = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", raw)
            if not m:
                raise ValueError(f"malformed hunk header: {raw!r}")
            new_line = int(m.group(1))
            hunk = []
            cur["hunks"].append(hunk)
            continue
        if cur is None or hunk is None:
            continue
        if raw.startswith("+"):
            cur["added"].append((new_line, raw[1:]))
            hunk.append((new_line, raw[1:]))
            new_line += 1
        elif raw.startswith("-"):
            cur["deleted"] += 1
        elif raw.startswith("\\"):
            continue
        else:
            new_line += 1
            hunk.append(None)  # context line breaks runs of added lines
    return [f for f in files if f["path"]]


def classify(path: str) -> str:
    if TEST_PATH.search(path):
        return "test"
    return "source" if Path(path).suffix.lower() in SOURCE_EXT else "other"


def _runs(hunk: list) -> list[list[tuple[int, str]]]:
    runs, cur = [], []
    for item in hunk:
        if item is None:
            if cur:
                runs.append(cur)
            cur = []
        else:
            cur.append(item)
    if cur:
        runs.append(cur)
    return runs


def _long_functions(path: str, hunk: list, limit: int) -> list[tuple[int, str, int]]:
    out = []
    for run in _runs(hunk):
        i = 0
        while i < len(run):
            ln, txt = run[i]
            if path.endswith(".py"):
                m = PY_DEF.match(txt)
                if m:
                    indent = len(m.group(1))
                    j = i + 1
                    while j < len(run):
                        t = run[j][1]
                        if t.strip() and len(t) - len(t.lstrip()) <= indent:
                            break
                        j += 1
                    body = sum(1 for _, t in run[i:j] if t.strip())
                    if body > limit:
                        out.append((ln, m.group(3), body))
                    i = j
                    continue
            elif Path(path).suffix in {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".java", ".go", ".cs"}:
                m = JS_FUNC.search(txt)
                if m and "{" in txt:
                    name = next((g for g in (m.group(2), m.group(3), m.group(6)) if g), "<anonymous>")
                    depth, j = 0, i
                    while j < len(run):
                        t = run[j][1]
                        depth += t.count("{") - t.count("}")
                        j += 1
                        if depth <= 0:
                            break
                    body = sum(1 for _, t in run[i:j] if t.strip())
                    if body > limit:
                        out.append((ln, name, body))
                    i = j
                    continue
            i += 1
    return out


def scan(text: str, small: int = DEFAULT_SMALL_LINES, large: int = DEFAULT_LARGE_LINES,
         max_files: int = DEFAULT_MAX_FILES, max_func: int = DEFAULT_MAX_FUNCTION_LINES) -> dict:
    files = parse_diff(text)
    findings: list[dict] = []
    if not files:
        findings.append(_finding("-", "error", "empty-diff", "no file changes found in the diff"))
        return {"findings": findings, "summary": {"files_changed": 0}}
    added = sum(len(f["added"]) for f in files)
    deleted = sum(f["deleted"] for f in files)
    changed = added + deleted
    kinds = {f["path"]: classify(f["path"]) for f in files}
    src = [p for p, k in kinds.items() if k == "source" and not next(f for f in files if f["path"] == p)["is_deleted"]]
    tests = [p for p, k in kinds.items() if k == "test"]
    band = "small" if changed <= small else ("large" if changed > large else "medium")
    if changed > large:
        findings.append(_finding("-", "error", "cl-too-large",
                                 f"{changed} changed lines exceeds {large}: ask for the change to be split "
                                 "(stacked, by files, horizontally or vertically)"))
    elif changed > small:
        findings.append(_finding("-", "info", "cl-size-medium",
                                 f"{changed} changed lines (> {small}): check it is one self-contained change"))
    if len(files) > max_files:
        findings.append(_finding("-", "warning", "many-files", f"{len(files)} files changed (> {max_files})"))
    if src and not tests:
        findings.append(_finding("-", "warning", "no-test-changes",
                                 f"{len(src)} source file(s) changed with no test changes: "
                                 + ", ".join(sorted(src)[:5])))

    for f in files:
        path, kind = f["path"], kinds[f["path"]]
        lines = f["added"]
        for idx, (ln, txt) in enumerate(lines):
            loc = f"{path}:{ln}"
            if TODO.search(txt) and not ISSUE_REF.search(txt):
                findings.append(_finding(loc, "warning", "todo-without-issue",
                                         "TODO/FIXME added without an issue reference", file=path, line=ln))
            if kind != "test" and kind != "other":
                for rx, label in DEBUG:
                    if rx.search(txt) and not COMMENT_LINE.match(txt):
                        if label == "print() call" and not path.endswith(".py"):
                            continue
                        findings.append(_finding(loc, "warning", "debug-output", f"{label} added in non-test code",
                                                 file=path, line=ln))
                        break
            if PY_EXCEPT.match(txt) and path.endswith(".py"):
                swallowed = bool(PY_EXCEPT.match(txt).group(1))
                if not swallowed and idx + 1 < len(lines) and lines[idx + 1][0] == ln + 1:
                    swallowed = lines[idx + 1][1].strip() in {"pass", "...", "continue"}
                if swallowed:
                    findings.append(_finding(loc, "error", "swallowed-exception",
                                             "broad exception caught and silently ignored", file=path, line=ln))
            if JS_EMPTY_CATCH.search(txt) or (JS_CATCH_OPEN.search(txt) and idx + 1 < len(lines)
                                              and lines[idx + 1][0] == ln + 1
                                              and lines[idx + 1][1].strip().startswith("}")):
                findings.append(_finding(loc, "error", "swallowed-exception", "empty catch block swallows errors",
                                         file=path, line=ln))
            for rx, label in SECRETS:
                m = rx.search(txt)
                if m and not PLACEHOLDER.search(txt):
                    findings.append(_finding(loc, "error", "hardcoded-secret",
                                             f"possible hard-coded secret ({label}); value masked — rotate if real",
                                             file=path, line=ln))
                    break
        # commented-out code: >= 3 consecutive added comment lines that look like code
        for hunk in f["hunks"]:
            for run in _runs(hunk):
                streak: list[int] = []
                for ln, txt in run + [(None, "")]:
                    m = COMMENT_LINE.match(txt) if ln is not None else None
                    if m and CODE_LIKE.search(m.group(2)) and not TODO.search(m.group(2)):
                        streak.append(ln)
                        continue
                    if len(streak) >= 3:
                        findings.append(_finding(f"{path}:{streak[0]}", "warning", "commented-out-code",
                                                 f"{len(streak)} consecutive lines of commented-out code; delete it "
                                                 "(version control keeps history)", file=path, line=streak[0]))
                    streak = []
            if kind == "source":
                for ln, name, body in _long_functions(path, hunk, max_func):
                    findings.append(_finding(f"{path}:{ln}", "warning", "long-function",
                                             f"function '{name}' added with {body} non-blank lines (> {max_func})",
                                             file=path, line=ln))

    sev = {s: sum(1 for x in findings if x["severity"] == s) for s in ("error", "warning", "info")}
    summary = {"files_changed": len(files), "source_files": len(src), "test_files": len(tests),
               "lines_added": added, "lines_deleted": deleted, "lines_changed": changed, "size_band": band,
               "errors": sev["error"], "warnings": sev["warning"], "info": sev["info"]}
    return {"findings": findings, "summary": summary}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Scan a unified diff for code review risk signals.")
    ap.add_argument("diff", type=Path)
    ap.add_argument("--small-lines", type=int, default=DEFAULT_SMALL_LINES)
    ap.add_argument("--large-lines", type=int, default=DEFAULT_LARGE_LINES)
    ap.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES)
    ap.add_argument("--max-function-lines", type=int, default=DEFAULT_MAX_FUNCTION_LINES)
    ap.add_argument("--strict", action="store_true", help="treat warnings as blocking")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        text = args.diff.read_text(encoding="utf-8")
        result = scan(text, args.small_lines, args.large_lines, args.max_files, args.max_function_lines)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"cannot read {args.diff}: {exc}", file=sys.stderr)
        return 2
    s = result["summary"]
    failed = s.get("errors", 1) > 0 or (args.strict and s.get("warnings", 0) > 0)
    result["passed"] = not failed
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for f in result["findings"]:
            print(f"{f['severity'].upper():8} {f['id']:<34} {f['rule']:<20} {f['message']}")
        print(f"\n{'FAIL' if failed else 'PASS'}: {s}")
        print("Scope: diff heuristics only; design, correctness and code-health judgement remain with the reviewer.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
