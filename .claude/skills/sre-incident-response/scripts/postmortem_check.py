#!/usr/bin/env python3
"""Check a blameless postmortem (Markdown or JSON) for completeness, a coherent timeline and owned actions.

Required content: summary; impact with numbers; timeline with timestamps in order; root cause(s)
and contributing factors; detection; response; what went well; what went badly; action items each
with owner, priority, due date (YYYY-MM-DD) and tracking ID. Also flags blame-oriented language
(heuristic) and, with --as-of, overdue open action items.

Markdown: sections are headings (#, ##, ###) whose text contains e.g. "Summary", "Impact",
"Timeline", "Root cause", "Contributing factors", "Detection", "Response", "What went well",
"What went badly"/"What went wrong", "Action items"; action items are a table with columns
including Owner, Priority, Due, Tracking (or Ticket/ID). Put "Severity: SEVn" near the top.

Usage:
  postmortem_check.py postmortem.md|postmortem.json [--as-of YYYY-MM-DD] [--strict] [--json]
Exit codes: 0 no errors, 1 errors, 2 unreadable input.

Scope: completeness and consistency of the write-up. It cannot tell whether the analysis found the
real causes or whether the actions will prevent recurrence.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

SECTIONS = {
    "summary": ("summary", "overview"),
    "impact": ("impact",),
    "timeline": ("timeline",),
    "root_cause": ("root cause",),
    "contributing": ("contributing",),
    "detection": ("detection", "how we detected", "how was it detected"),
    "response": ("response", "mitigation", "resolution", "recovery"),
    "went_well": ("went well",),
    "went_badly": ("went badly", "went wrong", "didn't go well", "did not go well", "could have gone better"),
    "action_items": ("action item", "follow-up", "follow up", "corrective action"),
}
REQUIRED = ["summary", "impact", "timeline", "root_cause", "detection", "response", "went_well",
            "went_badly", "action_items"]
TS = re.compile(r"(?P<date>\d{4}-\d{2}-\d{2})?[T ]?(?P<time>(?<!\d)\d{1,2}:\d{2}(?::\d{2})?)\s*"
                r"(?P<tz>Z|UTC|GMT|[+-]\d{2}:?\d{2})?")
PRIORITY = re.compile(r"^(P[0-4]|critical|high|medium|low)$", re.I)
TRACKING = re.compile(r"^([A-Z][A-Z0-9]+-\d+|#\d+)$")
BLAME = [
    re.compile(r"(?i)\b(human|operator|user|engineer|developer|admin) error\b"),
    re.compile(r"(?i)\b(should|ought to) have (known|noticed|checked|caught|realised|realized)\b"),
    re.compile(r"(?i)\b(careless(ly)?|negligen(t|ce)|incompetent|sloppy|lazy|reckless)\b"),
    re.compile(r"(?i)\b(at fault|to blame|blamed|(his|her|their) fault)\b"),
    re.compile(r"\b(?!The\b|This\b|That\b|It\b|We\b|Our\b|An?\b|Monitoring\b|Alerting\b|Deploy\b|Deployment\b|"
               r"Pipeline\b|Service\b|System\b|Job\b|Worker\b|Script\b|Check\b|Tests?\b|Config\b|Rollout\b|Alert\b)"
               r"[A-Z][a-z]+ (forgot|neglected|ignored|messed up|didn't bother|failed to)\b"),
]
DONE = {"done", "closed", "complete", "completed", "fixed", "resolved"}


def _finding(fid: str, severity: str, rule: str, message: str) -> dict:
    return {"id": fid, "severity": severity, "rule": rule, "message": message}


def _key(heading: str) -> list[str]:
    h = heading.lower()
    keys = [k for k, words in SECTIONS.items() if any(w in h for w in words)]
    if "went_well" in keys or "went_badly" in keys:
        keys = [k for k in keys if k not in ("response",)]
    return keys


def _table(lines: list[tuple[int, str]]) -> tuple[list[str], list[tuple[int, dict]]]:
    header: list[str] = []
    rows: list[tuple[int, dict]] = []
    for n, line in lines:
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", c) for c in cells if c):
            continue
        if not header:
            header = [c.lower() for c in cells]
            continue
        rows.append((n, dict(zip(header, cells + [""] * (len(header) - len(cells))))))
    return header, rows


def parse_markdown(text: str) -> dict:
    lines = text.splitlines()
    sections: dict[str, list[tuple[int, str]]] = {}
    current: list[str] = []
    meta_sev = None
    for n, line in enumerate(lines, 1):
        m = re.match(r"^#{1,4}\s+(.*)$", line)
        if m:
            current = _key(m.group(1))
            for k in current:
                sections.setdefault(k, [])
            continue
        sv = re.search(r"(?i)\bseverity\b\**\s*[:|]\s*\**\s*(SEV-?\s?\d|S\d|P\d|critical|major|minor)", line)
        if sv and meta_sev is None:
            meta_sev = sv.group(1)
        for k in current:
            sections[k].append((n, line))
    header, rows = _table(sections.get("action_items", []))
    actions = []
    for n, r in rows:
        def col(*names):
            for h, v in r.items():
                if any(x in h for x in names):
                    return v
            return None
        actions.append({"line": n, "owner": col("owner"), "priority": col("priority", "prio"),
                        "due": col("due", "deadline"), "tracking_id": col("tracking", "ticket", "issue", "id"),
                        "status": col("status") or ""})
    timeline = [(n, l) for n, l in sections.get("timeline", []) if l.strip()]
    return {"sections": {k: "\n".join(l for _, l in v) for k, v in sections.items()}, "timeline": timeline,
            "actions": actions, "action_header": header, "severity": meta_sev, "lines": list(enumerate(lines, 1))}


def parse_json(data: dict) -> dict:
    def text(v):
        return "\n".join(map(str, v)) if isinstance(v, list) else str(v or "")
    sections = {k: text(data.get(src)) for k, src in (
        ("summary", "summary"), ("impact", "impact"), ("root_cause", "root_causes"),
        ("contributing", "contributing_factors"), ("detection", "detection"), ("response", "response"),
        ("went_well", "went_well"), ("went_badly", "went_badly"))}
    sections = {k: v for k, v in sections.items() if v.strip()}
    tl = data.get("timeline") or []
    timeline = [(i, f"{e.get('time', '')} {e.get('event', '')}") for i, e in enumerate(tl, 1)] if isinstance(tl, list) else []
    if timeline:
        sections["timeline"] = "\n".join(t for _, t in timeline)
    acts = data.get("action_items")
    actions = []
    if isinstance(acts, list):
        sections["action_items"] = "present"
        for i, a in enumerate(acts, 1):
            actions.append({"line": i, "owner": a.get("owner"), "priority": a.get("priority"), "due": a.get("due"),
                            "tracking_id": a.get("tracking_id"), "status": a.get("status", "")})
    lines = list(enumerate(json.dumps(data, indent=1).splitlines(), 1))
    return {"sections": sections, "timeline": timeline, "actions": actions,
            "action_header": ["owner", "priority", "due", "tracking"] if actions else [],
            "severity": data.get("severity"), "lines": lines}


def check(doc: dict, as_of: date | None = None) -> dict:
    findings: list[dict] = []
    add = lambda *a: findings.append(_finding(*a))  # noqa: E731
    secs = doc["sections"]
    for k in REQUIRED:
        if k not in secs or not secs[k].strip():
            add(k, "error", "missing-section", f"required section '{k.replace('_', ' ')}' missing or empty")
    if "root_cause" in secs and "contributing" not in secs and "contributing" not in secs.get("root_cause", "").lower():
        add("root_cause", "warning", "no-contributing-factors", "list contributing factors, not just one root cause")
    if secs.get("impact", "").strip() and not re.search(r"\d", secs["impact"]):
        add("impact", "error", "impact-not-quantified", "impact has no numbers (users, tenants, requests, minutes, money)")
    if not doc.get("severity"):
        add("-", "warning", "no-severity", "state the incident severity (e.g. 'Severity: SEV2')")
    # timeline
    tl_text = secs.get("timeline", "")
    tz_declared = bool(re.search(r"(?i)\b(all times|times are|timezone|time zone)\b.*\b(UTC|GMT|[A-Z]{3,4}|[+-]\d{2})", tl_text))
    stamps: list[tuple[int, datetime]] = []
    cur_date: date | None = None
    naive = 0
    for n, line in doc["timeline"]:
        m = TS.search(line)
        if not m or re.match(r"^\s*\|?\s*:?-{3,}", line):
            continue
        if m.group("date"):
            try:
                cur_date = date.fromisoformat(m.group("date"))
            except ValueError:
                add(f"line {n}", "error", "timeline-bad-timestamp", f"invalid date '{m.group('date')}'")
                continue
        if cur_date is None:
            add(f"line {n}", "warning", "timeline-no-date", "time without a date; give the date on the first entry")
            continue
        parts = [int(x) for x in m.group("time").split(":")]
        if parts[0] > 23 or parts[1] > 59:
            add(f"line {n}", "error", "timeline-bad-timestamp", f"invalid time '{m.group('time')}'")
            continue
        tz = m.group("tz")
        if not tz:
            naive += 1
        offset = timezone.utc
        if tz and tz[0] in "+-":
            hh, mm = int(tz[1:3]), int(tz[-2:])
            offset = timezone((1 if tz[0] == "+" else -1) * timedelta(hours=hh, minutes=mm))
        stamps.append((n, datetime(cur_date.year, cur_date.month, cur_date.day, parts[0], parts[1],
                                   parts[2] if len(parts) > 2 else 0, tzinfo=offset)))
    if "timeline" in secs and len(stamps) < 2:
        add("timeline", "error", "timeline-missing-timestamps", "timeline needs at least two timestamped entries")
    for (n1, t1), (n2, t2) in zip(stamps, stamps[1:]):
        if t2 < t1:
            add(f"line {n2}", "error", "timeline-out-of-order", f"entry at line {n2} is earlier than line {n1}")
    if naive and not tz_declared:
        add("timeline", "warning", "timeline-timezone", f"{naive} timestamp(s) without a time zone and no 'All times UTC' note")
    # action items
    if "action_items" in secs:
        hdr = " ".join(doc.get("action_header") or [])
        for col, words in (("owner", ("owner",)), ("priority", ("priority", "prio")), ("due date", ("due", "deadline")),
                           ("tracking ID", ("tracking", "ticket", "issue", "id"))):
            if doc["actions"] and not any(w in hdr for w in words):
                add("action_items", "error", "action-items-columns", f"action items table has no {col} column")
        if not doc["actions"]:
            add("action_items", "error", "no-action-items", "no action items table rows found")
    for a in doc["actions"]:
        aid = f"action line {a['line']}"
        owner = (a.get("owner") or "").strip()
        if not owner or owner.upper() in {"TBD", "TBC", "?", "-", "N/A"}:
            add(aid, "error", "action-no-owner", "action item has no named owner")
        pr = (a.get("priority") or "").strip()
        if not PRIORITY.match(pr):
            add(aid, "error", "action-bad-priority", f"priority '{pr}' not P0-P4 or critical/high/medium/low")
        due_raw = (a.get("due") or "").strip()
        try:
            due = date.fromisoformat(due_raw)
        except ValueError:
            add(aid, "error", "action-bad-due-date", f"due date '{due_raw}' is not YYYY-MM-DD")
            due = None
        tid = (a.get("tracking_id") or "").strip().strip("`")
        if not TRACKING.match(tid):
            add(aid, "error", "action-no-tracking-id", f"tracking ID '{tid}' not like ABC-123 or #123")
        if as_of and due and due < as_of and (a.get("status") or "").strip().lower() not in DONE:
            add(aid, "warning", "action-overdue", f"due {due_raw} has passed and the item is not done")
    # blame language
    for n, line in doc["lines"]:
        if line.lstrip().startswith((">", "```")):
            continue
        for rx in BLAME:
            m = rx.search(line)
            if m:
                add(f"line {n}", "warning", "blame-language",
                    f"'{m.group(0)}' reads as blame; describe the system conditions and decisions instead")
                break
    sev = Counter(f["severity"] for f in findings)
    duration = None
    if len(stamps) >= 2:
        duration = round((max(t for _, t in stamps) - min(t for _, t in stamps)).total_seconds() / 60, 1)
    summary = {"severity": doc.get("severity"), "sections_found": sorted(k for k in secs if k in SECTIONS),
               "timeline_entries": len(stamps), "timeline_span_minutes": duration,
               "action_items": len(doc["actions"]), "errors": sev.get("error", 0),
               "warnings": sev.get("warning", 0), "info": sev.get("info", 0)}
    return {"findings": findings, "summary": summary}


def load(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("JSON postmortem must be an object")
        return parse_json(data)
    return parse_markdown(text)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Check a blameless postmortem.")
    ap.add_argument("postmortem", type=Path)
    ap.add_argument("--as-of", help="YYYY-MM-DD; flag overdue open action items")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        as_of = date.fromisoformat(args.as_of) if args.as_of else None
        doc = load(args.postmortem)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"cannot read: {exc}", file=sys.stderr)
        return 2
    result = check(doc, as_of)
    s = result["summary"]
    failed = s["errors"] > 0 or (args.strict and s["warnings"] > 0)
    result["passed"] = not failed
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for f in result["findings"]:
            print(f"{f['severity'].upper():8} {f['id']:<16} {f['rule']:<28} {f['message']}")
        print(f"\n{'FAIL' if failed else 'PASS'}: {s}")
        print("Scope: write-up completeness and consistency only; not a judgement of the analysis or the fixes.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
