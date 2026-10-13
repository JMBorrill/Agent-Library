#!/usr/bin/env python3
"""Check a NIST SSDF (SP 800-218 v1.1) practice -> evidence map and report coverage per group.

CSV columns: practice_id, task_id (optional), evidence_ref, evidence_date (YYYY-MM-DD), owner,
status (planned|implemented|verified|not_applicable), justification.
IDs may be version-qualified (SSDF-v1.1-PO.1 / SSDF-v1.1-PO.1.1) or bare (PO.1 / PO.1.1).

Checks: practice and task IDs exist in the bundled v1.1 practice list (there is no PW.3), task
belongs to its practice, implemented/verified rows have evidence and a date, not_applicable rows
have a justification, evidence freshness against --as-of, and practice/task coverage per group.

Usage:
  ssdf_evidence_check.py evidence.csv [--as-of YYYY-MM-DD] [--max-age-days 365] [--require-all] [--json]
Exit codes: 0 no errors, 1 errors, 2 unreadable input / bad arguments.

Scope: bookkeeping over the evidence map. It does not judge whether evidence is adequate and is
not an attestation of conformance to the SSDF.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

DEFAULT_PRACTICES = Path(__file__).resolve().parents[1] / "assets" / "data" / "nist-ssdf-practices.json"
VERSION = "1.1"
COLUMNS = ["practice_id", "task_id", "evidence_ref", "evidence_date", "owner", "status", "justification"]
STATUSES = {"planned", "implemented", "verified", "not_applicable"}
DONE = {"implemented", "verified"}
ID_RX = re.compile(r"^(?:SSDF-v(\d+(?:\.\d+)*)-)?((PO|PS|PW|RV)\.\d+(?:\.\d+)?)$")


def _finding(fid: str, severity: str, rule: str, message: str) -> dict:
    return {"id": fid, "severity": severity, "rule": rule, "message": message}


def load_practices(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {p["id"]: {"title": p["title"], "group": p["group"], "group_title": p["group_title"],
                      "tasks": list(p["task_ids"])} for p in data["practices"]}


def parse_id(raw: str) -> tuple[str | None, str | None, bool]:
    """Return (bare id, version or None, ok)."""
    m = ID_RX.match(raw.strip())
    if not m:
        return None, None, False
    return m.group(2), m.group(1), True


def check(columns: list[str], rows: list[dict], practices: dict, as_of: date | None = None,
          max_age_days: int = 365, require_all: bool = False) -> dict:
    findings: list[dict] = []
    missing = [c for c in ("practice_id", "evidence_ref", "status") if c not in columns]
    if missing:
        findings.append(_finding("-", "error", "missing-columns", f"missing columns: {', '.join(missing)}"))
        return {"findings": findings, "summary": {"errors": 1, "warnings": 0, "info": 0}}
    all_tasks = {t: pid for pid, p in practices.items() for t in p["tasks"]}
    covered_practices: set[str] = set()
    covered_tasks: set[str] = set()
    unqualified = 0
    for n, r in enumerate(rows, start=2):
        raw_p = r.get("practice_id", "")
        fid = raw_p or f"row{n}"
        pid, ver, ok = parse_id(raw_p)
        if not ok or pid is None or pid.count(".") != 1:
            findings.append(_finding(fid, "error", "bad-practice-id",
                                     "practice_id must look like SSDF-v1.1-PO.1 or PO.1 (practice level)"))
            continue
        if ver is not None and ver != VERSION:
            findings.append(_finding(fid, "error", "version-mismatch", f"evidence map is for SSDF v{VERSION}, not v{ver}"))
            continue
        unqualified += ver is None
        if pid not in practices:
            hint = (" (SSDF v1.1 has no PW.3; former task PW.3.1 is now PO.1.3)" if pid == "PW.3" else "")
            findings.append(_finding(fid, "error", "unknown-practice", f"{pid} is not an SSDF v{VERSION} practice{hint}"))
            continue
        task_raw = r.get("task_id", "")
        task = None
        if task_raw:
            tid, tver, tok = parse_id(task_raw)
            if not tok or tid is None or tid.count(".") != 2:
                findings.append(_finding(fid, "error", "bad-task-id", f"task_id '{task_raw}' must look like PO.1.1"))
                continue
            if tid not in all_tasks:
                findings.append(_finding(fid, "error", "unknown-task", f"{tid} is not an SSDF v{VERSION} task"))
                continue
            if all_tasks[tid] != pid:
                findings.append(_finding(fid, "error", "task-practice-mismatch", f"{tid} belongs to {all_tasks[tid]}, not {pid}"))
                continue
            task = tid
        status = r.get("status", "").lower()
        if status not in STATUSES:
            findings.append(_finding(fid, "error", "status-value", f"status '{r.get('status')}' not in {sorted(STATUSES)}"))
            continue
        label = task or pid
        if not r.get("owner"):
            findings.append(_finding(label, "warning", "no-owner", "no accountable owner recorded"))
        if status == "not_applicable":
            if len(r.get("justification", "").strip()) < 10:
                findings.append(_finding(label, "error", "na-without-justification", "not_applicable needs a justification"))
                continue
        elif status in DONE:
            if not r.get("evidence_ref"):
                findings.append(_finding(label, "error", "no-evidence", f"status {status} without evidence_ref"))
                continue
            raw_date = r.get("evidence_date", "")
            try:
                ev_date = date.fromisoformat(raw_date)
            except ValueError:
                findings.append(_finding(label, "error", "bad-evidence-date",
                                         f"evidence_date '{raw_date}' is not YYYY-MM-DD"))
                continue
            if as_of is not None:
                age = (as_of - ev_date).days
                if age < 0:
                    findings.append(_finding(label, "error", "future-evidence-date", f"evidence dated after --as-of ({raw_date})"))
                    continue
                if age > max_age_days:
                    findings.append(_finding(label, "warning", "stale-evidence",
                                             f"evidence is {age} days old (> {max_age_days}); refresh"))
        else:  # planned
            continue
        covered_practices.add(pid)
        if task:
            covered_tasks.add(task)
        elif status in DONE or status == "not_applicable":
            pass
    if unqualified:
        findings.append(_finding("-", "info", "unqualified-id",
                                 f"{unqualified} row(s) use bare IDs; prefer SSDF-v{VERSION}-<id> in shared reports"))
    if as_of is None:
        findings.append(_finding("-", "info", "freshness-not-checked", "pass --as-of YYYY-MM-DD to check evidence age"))
    groups: dict[str, dict] = {}
    for pid, p in practices.items():
        g = groups.setdefault(p["group"], {"title": p["group_title"], "practices": 0, "covered": 0,
                                           "tasks": 0, "tasks_with_evidence": 0, "missing": []})
        g["practices"] += 1
        g["tasks"] += len(p["tasks"])
        g["tasks_with_evidence"] += sum(1 for t in p["tasks"] if t in covered_tasks)
        if pid in covered_practices:
            g["covered"] += 1
        else:
            g["missing"].append(pid)
    for gid, g in groups.items():
        g["coverage_pct"] = round(100 * g["covered"] / g["practices"], 1)
        for pid in g["missing"]:
            findings.append(_finding(pid, "error" if require_all else "warning", "practice-not-covered",
                                     f"no implemented/verified (or justified N/A) evidence for {pid} "
                                     f"{practices[pid]['title']}"))
    sev = Counter(f["severity"] for f in findings)
    summary = {"ssdf_version": VERSION, "practices": len(practices), "practices_covered": len(covered_practices),
               "tasks": len(all_tasks), "tasks_with_evidence": len(covered_tasks), "groups": groups,
               "as_of": as_of.isoformat() if as_of else None,
               "errors": sev.get("error", 0), "warnings": sev.get("warning", 0), "info": sev.get("info", 0)}
    return {"findings": findings, "summary": summary}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Check an SSDF v1.1 practice evidence map.")
    ap.add_argument("csv", type=Path)
    ap.add_argument("--practices", type=Path, default=DEFAULT_PRACTICES)
    ap.add_argument("--as-of", help="YYYY-MM-DD reference date for evidence freshness")
    ap.add_argument("--max-age-days", type=int, default=365)
    ap.add_argument("--require-all", action="store_true", help="uncovered practices are errors")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        as_of = date.fromisoformat(args.as_of) if args.as_of else None
        practices = load_practices(args.practices)
        with args.csv.open(newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            rows = [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in reader]
            cols = [c.strip() for c in reader.fieldnames or []]
    except (OSError, UnicodeDecodeError, csv.Error, ValueError, KeyError) as exc:
        print(f"cannot run: {exc}", file=sys.stderr)
        return 2
    result = check(cols, rows, practices, as_of, args.max_age_days, args.require_all)
    s = result["summary"]
    failed = s["errors"] > 0
    result["passed"] = not failed
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for gid, g in s.get("groups", {}).items():
            print(f"  {gid} {g['title']:<35} practices {g['covered']}/{g['practices']} ({g['coverage_pct']}%)  "
                  f"tasks with evidence {g['tasks_with_evidence']}/{g['tasks']}")
        for f in result["findings"]:
            print(f"{f['severity'].upper():8} {f['id']:<18} {f['rule']:<24} {f['message']}")
        print(f"\n{'FAIL' if failed else 'PASS'}: {s.get('practices_covered')}/{s.get('practices')} practices covered; "
              f"{s['errors']} errors, {s['warnings']} warnings")
        print("Scope: evidence bookkeeping only; not an SSDF attestation or conformance statement.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
