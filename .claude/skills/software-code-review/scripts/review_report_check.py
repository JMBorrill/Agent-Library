#!/usr/bin/env python3
"""Check that a code review findings report is complete enough to act on.

Accepts JSON (schema assets/schemas/review-report.schema.json) or Markdown containing a findings
table (columns: Severity | Aspect | Location | Comment) and a line "Decision: <value>".

Checks: explicit decision from the allowed vocabulary; every finding has a severity label
(required / nit / optional / consider / fyi), a file:line location, a known review aspect and a
comment; decision consistent with open required findings; comments aimed at people, not code.

Usage:
  review_report_check.py review.json|review.md [--strict] [--json]
Exit codes: 0 no errors, 1 errors, 2 unreadable input.

Scope: checks the form of the review record, not whether the review was thorough or right.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DECISIONS = {"lgtm", "lgtm-with-comments", "request-changes", "escalate"}
SEVERITIES = {"required", "nit", "optional", "consider", "fyi"}
# The 12 aspects of review/reviewer/looking-for.md (Google eng-practices), normalised.
ASPECTS = {"design", "functionality", "complexity", "tests", "naming", "comments", "style",
           "consistency", "documentation", "every-line", "context", "good-things", "security"}
LOCATION = re.compile(r"^[^\s:]+(?::\d+(?:-\d+)?)$")
PERSONAL = re.compile(r"(?i)\b(you always|you never|lazy|sloppy|careless|stupid|obviously wrong|"
                      r"why would you|what were you thinking|incompetent)\b")


def _finding(fid: str, severity: str, rule: str, message: str) -> dict:
    return {"id": fid, "severity": severity, "rule": rule, "message": message}


def _norm(value: str) -> str:
    return re.sub(r"[\s_]+", "-", (value or "").strip().strip("*").strip().lower()).rstrip(":")


def parse_markdown(text: str) -> dict:
    decision = None
    m = re.search(r"(?im)^\s*\**decision\**\s*:\s*\**\s*([A-Za-z _-]+?)\s*\**\s*$", text)
    if m:
        decision = m.group(1)
    findings, header = [], None
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            header = None if not s else header
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", c) for c in cells if c):
            continue
        lowered = [c.lower() for c in cells]
        if "severity" in lowered and ("location" in lowered or "comment" in lowered):
            header = lowered
            continue
        if header:
            row = dict(zip(header, cells + [""] * (len(header) - len(cells))))
            findings.append({"severity": row.get("severity", ""), "aspect": row.get("aspect", ""),
                             "location": row.get("location", ""), "comment": row.get("comment", ""),
                             "status": row.get("status", "")})
    return {"decision": decision, "findings": findings, "_tables": header is not None or bool(findings)}


def check(report: dict) -> dict:
    findings: list[dict] = []
    decision = _norm(report.get("decision") or "")
    if not decision:
        findings.append(_finding("-", "error", "missing-decision",
                                 f"no explicit decision; use one of {sorted(DECISIONS)}"))
    elif decision not in DECISIONS:
        findings.append(_finding("-", "error", "unknown-decision",
                                 f"decision '{report.get('decision')}' not in {sorted(DECISIONS)}"))
    items = report.get("findings")
    if not isinstance(items, list):
        findings.append(_finding("-", "error", "no-findings-table", "no findings list/table found"))
        items = []
    open_required = 0
    counts: dict[str, int] = {}
    for i, f in enumerate(items, 1):
        fid = f"F{i}"
        sev = _norm(f.get("severity", ""))
        if sev not in SEVERITIES:
            findings.append(_finding(fid, "error", "missing-severity-label",
                                     f"severity '{f.get('severity', '')}' is not one of {sorted(SEVERITIES)}"))
        else:
            counts[sev] = counts.get(sev, 0) + 1
        loc = (f.get("location") or "").strip().strip("`")
        if not loc:
            findings.append(_finding(fid, "error", "missing-location", "no file:line reference"))
        elif not LOCATION.match(loc):
            findings.append(_finding(fid, "error", "bad-location", f"location '{loc}' is not file:line[-line]"))
        aspect = _norm(f.get("aspect", ""))
        if not aspect:
            findings.append(_finding(fid, "warning", "missing-aspect", "no review aspect recorded"))
        elif aspect not in ASPECTS:
            findings.append(_finding(fid, "warning", "unknown-aspect", f"aspect '{f.get('aspect')}' not recognised"))
        comment = (f.get("comment") or "").strip()
        if not comment:
            findings.append(_finding(fid, "error", "empty-comment", "finding has no comment"))
        elif PERSONAL.search(comment):
            findings.append(_finding(fid, "warning", "comment-targets-person",
                                     "comment wording is about the author, not the code; rephrase courteously"))
        elif sev == "required" and len(comment.split()) < 6:
            findings.append(_finding(fid, "warning", "unexplained-required",
                                     "required change has a very short comment; explain why"))
        if sev == "required" and _norm(f.get("status", "")) not in {"resolved", "fixed", "done"}:
            open_required += 1
    if decision == "lgtm" and open_required:
        findings.append(_finding("-", "error", "decision-inconsistent",
                                 f"decision is LGTM but {open_required} required finding(s) remain open"))
    if decision == "lgtm-with-comments" and open_required:
        findings.append(_finding("-", "warning", "lgtm-with-open-required",
                                 "LGTM with comments while required findings are open: confirm the author is "
                                 "trusted to address them and no further review is needed"))
    if decision == "request-changes" and not open_required:
        findings.append(_finding("-", "warning", "request-changes-without-required",
                                 "changes requested but no open 'required' finding explains which"))
    if items and not any(_norm(f.get("aspect", "")) == "good-things" for f in items):
        findings.append(_finding("-", "info", "no-positive-feedback", "consider noting what was done well"))
    sev_count = {s: sum(1 for x in findings if x["severity"] == s) for s in ("error", "warning", "info")}
    summary = {"decision": decision or None, "review_findings": len(items), "by_label": counts,
               "open_required": open_required, "errors": sev_count["error"], "warnings": sev_count["warning"],
               "info": sev_count["info"]}
    return {"findings": findings, "summary": summary}


def load(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("JSON report must be an object")
        return data
    return parse_markdown(text)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Check a code review findings report.")
    ap.add_argument("report", type=Path)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        report = load(args.report)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"cannot read {args.report}: {exc}", file=sys.stderr)
        return 2
    result = check(report)
    s = result["summary"]
    failed = s["errors"] > 0 or (args.strict and s["warnings"] > 0)
    result["passed"] = not failed
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for f in result["findings"]:
            print(f"{f['severity'].upper():8} {f['id']:<5} {f['rule']:<34} {f['message']}")
        print(f"\n{'FAIL' if failed else 'PASS'}: {s}")
        print("Scope: form of the review record only; not evidence that the review was thorough or correct.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
