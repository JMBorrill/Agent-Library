#!/usr/bin/env python3
"""Lint a product requirements brief (PRD, Markdown) and its job-story CSV; optionally flow
verifiable candidate requirements down into the se-requirements register format.

PRD checks: required sections present and not placeholders (outcomes and metrics, users, job
stories, non-goals, assumptions, risks, accessibility, privacy and security, release slices);
measurable outcomes; explicit non-goals; assumptions linked to evidence IDs; evidence IDs exist
in a discovery evidence log when one is given; job-story bullets use the
"When <situation>, I want to <motivation>, so I can <outcome>" form.
Story CSV checks (id, job_story, acceptance_criteria, priority, evidence_ids, requirement_ids):
unique well-formed IDs, job-story form, MoSCoW priority, every "must" story has at least one
Given/When/Then scenario, evidence links resolve, solution language in stories.
--flow-down PATH writes one stakeholder-level row per must/should story plus one software-level
"shall" row per Given/When/Then scenario, status=proposed, verification_method=test, in the CSV
columns used by se-requirements (req_lint.py).

Usage:
  prd_check.py PRD.md [--stories stories.csv] [--evidence evidence.csv]
               [--flow-down OUT.csv|-] [--prefix DWS-SW] [--owner NAME] [--strict] [--json]
Exit codes: 0 no errors, 1 errors (or warnings with --strict), 2 unreadable input.

Scope: a structural and wording check. It cannot judge whether outcomes are the right ones, the
stories reflect real user needs, or the flowed-down requirements are complete; candidate
requirements are proposals for a requirements owner to rewrite and approve.
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

SECTIONS = {
    "outcomes": ["outcomes and metrics", "outcomes & metrics", "outcomes", "success metrics", "goals and metrics"],
    "users": ["users", "target users", "users and needs"],
    "job_stories": ["job stories"],
    "non_goals": ["non-goals", "non goals", "out of scope"],
    "assumptions": ["assumptions", "assumptions and evidence"],
    "risks": ["risks"],
    "accessibility": ["accessibility"],
    "privacy_security": ["privacy and security", "security and privacy", "privacy, security", "privacy"],
    "release_slices": ["release slices", "release plan", "releases"],
}
TITLES = {k: v[0].capitalize() for k, v in SECTIONS.items()}
STORY_COLUMNS = ["id", "job_story", "acceptance_criteria", "priority", "evidence_ids", "requirement_ids"]
PRIORITIES = {"must", "should", "could", "wont"}
ID_RE = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-[0-9]{3,}$")
EVIDENCE_ID = re.compile(r"\b[A-Z][A-Z0-9]*-EV-\d{3,}\b")
JOB_STORY = re.compile(r"^when\s+(?P<situation>.+?),\s*i want to\s+(?P<motivation>.+?),\s*so (?:that\s+)?i can\s+(?P<outcome>.+?)\.?$",
                       re.I | re.S)
GWT = re.compile(r"\bGiven\b(?P<given>.+?)\bWhen\b(?P<when>.+?)\bThen\b(?P<then>.+?)(?=\bGiven\b|$)", re.S)
PLACEHOLDER = re.compile(r"^\W*(tbd|tbc|todo|n/?a|none|-|to be (decided|confirmed))\W*$", re.I)
SOLUTION_WORDS = ["click", "tap", "button", "dropdown", "drop-down", "checkbox", "modal", "popup",
                  "pop-up", "screen", "page", "toggle", "database", "api"]
AMBIGUOUS = ["fast", "quickly", "easy", "easily", "user-friendly", "intuitive", "seamless", "simple",
             "appropriate", "sufficient", "as needed", "etc"]
BULLET = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.*\S)\s*$")
OUT_COLUMNS = ["id", "parent", "level", "statement", "rationale", "source", "owner", "status",
               "verification_method", "acceptance_criteria", "verification_id"]


def _f(rid: str, severity: str, rule: str, message: str) -> dict:
    return {"id": rid, "severity": severity, "rule": rule, "message": message}


def _term(text: str, term: str) -> bool:
    return re.search(rf"(?<![\w-]){re.escape(term)}(?![\w-])", text, re.I) is not None


def split_ids(value: str) -> list[str]:
    return [x.strip() for x in re.split(r"[;,\s]+", value or "") if x.strip()]


def parse_sections(text: str) -> dict[str, str]:
    found: dict[str, str] = {}
    current, buf, in_code = None, [], False
    for line in text.splitlines() + ["## __end__"]:
        if line.startswith("```"):
            in_code = not in_code
        m = None if in_code else re.match(r"^#{2,3}\s+(.+?)\s*#*\s*$", line)
        if m:
            if current is not None:
                found[current] = (found.get(current, "") + "\n" + "\n".join(buf)).strip()
            buf, current = [], None
            title = re.sub(r"^\d+[.)]\s*", "", m.group(1)).strip().lower()
            for key, names in SECTIONS.items():
                if any(title == n or title.startswith(n) for n in names):
                    current = key
                    break
            continue
        if current is not None:
            buf.append(line)
    return found


def bullets(body: str) -> list[str]:
    return [m.group(1) for line in body.splitlines() if (m := BULLET.match(line))]


def scenarios(ac: str) -> list[dict]:
    return [{k: " ".join(v.strip(" ,;.\n").split()) for k, v in m.groupdict().items()} for m in GWT.finditer(ac or "")]


def strip_story_id(text: str) -> str:
    return re.sub(r"^\**[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d{3,}\**\s*[:.\-—]\s*", "", text.strip())


def load_evidence(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames or "id" not in [c.strip() for c in reader.fieldnames]:
            raise csv.Error("evidence log has no 'id' column")
        out = {}
        for r in reader:
            r = {(k or "").strip(): (v or "").strip() for k, v in r.items()}
            out[r["id"]] = r.get("type", "").lower()
        return out


def read_stories(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        rows = []
        for r in reader:
            if None in r:
                raise csv.Error(f"row {reader.line_num} has more cells than the header")
            rows.append({(k or "").strip(): (v or "").strip() for k, v in r.items()})
        return [c.strip() for c in (reader.fieldnames or [])], rows


def check_prd(text: str, evidence: dict[str, str] | None = None, has_stories: bool = False) -> list[dict]:
    findings: list[dict] = []
    if not text.strip():
        return [_f("prd", "error", "empty-document", "PRD is empty")]
    sec = parse_sections(text)
    for key in SECTIONS:
        if key not in sec:
            findings.append(_f(key, "error", "missing-section", f"no '{TITLES[key]}' section"))
        elif not sec[key].strip() or PLACEHOLDER.fullmatch(sec[key].strip()):
            findings.append(_f(key, "error", "placeholder-section", f"'{TITLES[key]}' is empty or a placeholder"))
    out = sec.get("outcomes", "")
    if out.strip() and not PLACEHOLDER.fullmatch(out.strip()):
        if re.search(r"\bTB[DC]\b", out):
            findings.append(_f("outcomes", "warning", "outcome-target-tbd", "an outcome target is still TBD"))
        elif not re.search(r"\d", out):
            findings.append(_f("outcomes", "error", "outcome-unmeasurable",
                               "outcomes contain no measurable target (baseline -> target, by when)"))
    ng = sec.get("non_goals", "")
    if ng.strip() and not bullets(ng):
        findings.append(_f("non_goals", "error", "non-goals-empty", "list explicit non-goals as bullets"))
    asm = sec.get("assumptions", "")
    if asm.strip() and not EVIDENCE_ID.search(asm):
        findings.append(_f("assumptions", "warning", "assumptions-unlinked",
                           "assumptions cite no evidence IDs from the discovery evidence log"))
    a11y = sec.get("accessibility", "")
    if a11y.strip() and not re.search(r"WCAG|\d", a11y):
        findings.append(_f("accessibility", "warning", "accessibility-unspecific",
                           "name a conformance target (e.g. WCAG 2.2 AA) and the specific needs considered"))
    rel = sec.get("release_slices", "")
    if rel.strip() and not bullets(rel):
        findings.append(_f("release_slices", "warning", "release-slices-not-listed", "list release slices as bullets"))
    for i, item in enumerate(bullets(sec.get("job_stories", "")), 1):
        story = strip_story_id(item)
        if story.lower().startswith("when") and not JOB_STORY.match(story):
            findings.append(_f(f"job_stories[{i}]", "error", "job-story-format",
                               "use 'When <situation>, I want to <motivation>, so I can <outcome>'"))
    if not has_stories and not GWT.search(text):
        findings.append(_f("prd", "warning", "no-acceptance-criteria",
                           "no Given/When/Then acceptance criteria in the PRD and no stories CSV given"))
    if evidence is not None:
        for eid in sorted(set(EVIDENCE_ID.findall(text))):
            if eid not in evidence:
                findings.append(_f(eid, "error", "unknown-evidence-id", "PRD cites evidence not in the evidence log"))
    return findings


def check_stories(columns: list[str], rows: list[dict], evidence: dict[str, str] | None = None) -> list[dict]:
    findings: list[dict] = []
    missing = [c for c in STORY_COLUMNS if c not in columns]
    if missing:
        return [_f("-", "error", "missing-columns", f"stories CSV missing columns: {', '.join(missing)}")]
    if not rows:
        return [_f("-", "error", "no-stories", "stories CSV has no rows")]
    counts = Counter(r["id"] for r in rows)
    req_owner: dict[str, str] = {}
    for r in rows:
        sid = r["id"] or "<blank>"
        pr = r["priority"].lower()
        if not r["id"]:
            findings.append(_f(sid, "error", "blank-id", "story has no identifier"))
        elif not ID_RE.fullmatch(r["id"]):
            findings.append(_f(sid, "error", "id-format", "story ID must look like DWS-STY-001"))
        if r["id"] and counts[r["id"]] > 1:
            findings.append(_f(sid, "error", "duplicate-id", f"story ID used {counts[r['id']]} times"))
        m = JOB_STORY.match(r["job_story"])
        if not m:
            findings.append(_f(sid, "error", "job-story-format",
                               "use 'When <situation>, I want to <motivation>, so I can <outcome>'"))
        else:
            sol = [w for w in SOLUTION_WORDS if _term(m.group("motivation"), w)]
            if sol:
                findings.append(_f(sid, "warning", "solution-in-story",
                                   f"motivation names UI/implementation {sol}; describe the need, put design in AC"))
        if pr not in PRIORITIES:
            findings.append(_f(sid, "error", "priority", f"priority '{r['priority']}' not in {sorted(PRIORITIES)}"))
        sc = scenarios(r["acceptance_criteria"])
        if pr == "must" and not sc:
            findings.append(_f(sid, "error", "must-without-gwt", "must story has no Given/When/Then scenario"))
        elif pr in ("should", "could") and not sc:
            findings.append(_f(sid, "warning", "story-without-gwt", "no Given/When/Then scenario yet"))
        amb = sorted({t for t in AMBIGUOUS if _term(r["acceptance_criteria"], t)})
        if amb:
            findings.append(_f(sid, "warning", "ambiguous-acceptance", f"ambiguous words in acceptance criteria {amb}"))
        eids = split_ids(r["evidence_ids"])
        if pr == "must" and not eids:
            findings.append(_f(sid, "warning", "must-without-evidence", "must story cites no discovery evidence"))
        if evidence is not None:
            for eid in eids:
                if eid not in evidence:
                    findings.append(_f(sid, "error", "unknown-evidence-id", f"evidence '{eid}' not in evidence log"))
                elif evidence[eid] in ("hypothesis", "assumption"):
                    findings.append(_f(sid, "warning", "non-evidence-cited", f"'{eid}' is a {evidence[eid]}, not evidence"))
        for rid in split_ids(r["requirement_ids"]):
            if not ID_RE.fullmatch(rid):
                findings.append(_f(sid, "error", "requirement-id-format", f"requirement ID '{rid}' malformed"))
            elif rid in req_owner and req_owner[rid] != r["id"]:
                findings.append(_f(sid, "error", "requirement-id-reused",
                                   f"requirement ID '{rid}' already used by story {req_owner[rid]}"))
            else:
                req_owner[rid] = r["id"]
    return findings


def flow_down(rows: list[dict], prefix: str | None = None, owner: str = "product-lead (to confirm)",
              prd_name: str = "PRD") -> tuple[list[dict], list[dict]]:
    """Build se-requirements rows from must/should stories. Returns (rows, info findings)."""
    out: list[dict] = []
    info: list[dict] = []
    used = {rid for r in rows for rid in split_ids(r.get("requirement_ids", ""))} | {r.get("id", "") for r in rows}
    counter = 0
    ver_counter = 0
    seen_story: set[str] = set()

    def next_id(pfx: str) -> str:
        nonlocal counter
        while True:
            counter += 1
            cand = f"{pfx}-{counter:03d}"
            if cand not in used:
                used.add(cand)
                return cand

    for r in rows:
        sid, pr = r.get("id", ""), r.get("priority", "").lower()
        m = JOB_STORY.match(r.get("job_story", ""))
        sc = scenarios(r.get("acceptance_criteria", ""))
        if pr not in ("must", "should"):
            continue
        if not ID_RE.fullmatch(sid or "") or sid in seen_story or not m or not sc:
            info.append(_f(sid or "<blank>", "info", "flow-down-skipped",
                           "story not flowed down (fix ID, job-story form or Given/When/Then first)"))
            continue
        seen_story.add(sid)
        pfx = prefix or (sid.split("-")[0] + "-SW")
        ev = ";".join(split_ids(r.get("evidence_ids", "")))
        source = f"{prd_name} story {sid}" + (f"; evidence {ev}" if ev else "")
        ver_pfx = sid.split("-")[0] + "-VAL"
        ver_counter += 1
        out.append({
            "id": sid, "parent": "", "level": "stakeholder",
            "statement": " ".join(r["job_story"].split()),
            "rationale": f"User need captured as a job story (priority {pr})",
            "source": source, "owner": owner, "status": "proposed",
            "verification_method": "demonstration",
            "acceptance_criteria": f"Target users achieve the outcome '{m.group('outcome').strip()}' in a usability session",
            "verification_id": f"{ver_pfx}-{ver_counter:03d}",
        })
        given_ids = split_ids(r.get("requirement_ids", ""))
        for i, s in enumerate(sc):
            rid = given_ids[i] if i < len(given_ids) else next_id(pfx)
            used.add(rid)
            stmt = f"When {s['when']}, the system shall ensure that {s['then']}"
            if s["given"]:
                stmt += f" (precondition: {s['given']})"
            out.append({
                "id": rid, "parent": sid, "level": "software", "statement": stmt + ".",
                "rationale": f"Derived from acceptance scenario {i + 1} of {sid} (priority {pr})",
                "source": source, "owner": owner, "status": "proposed", "verification_method": "test",
                "acceptance_criteria": f"Given {s['given']} When {s['when']} Then {s['then']}",
                "verification_id": f"{rid.split('-')[0]}-VER-{len([x for x in out if x['level'] == 'software']) + 1:03d}",
            })
    return out, info


def to_csv(rows: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=OUT_COLUMNS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Lint a PRD and job stories; optionally flow down requirements.")
    ap.add_argument("prd", type=Path)
    ap.add_argument("--stories", type=Path)
    ap.add_argument("--evidence", type=Path, help="discovery evidence log CSV (product-discovery format)")
    ap.add_argument("--flow-down", dest="flow_down", help="write candidate requirements CSV here ('-' = stdout)")
    ap.add_argument("--prefix", help="ID prefix for generated requirements, e.g. DWS-SW")
    ap.add_argument("--owner", default="product-lead (to confirm)")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if args.flow_down and not args.stories:
        print("--flow-down needs --stories", file=sys.stderr)
        return 2
    if args.prefix and not re.fullmatch(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*", args.prefix):
        print("--prefix must look like DWS-SW", file=sys.stderr)
        return 2
    try:
        text = args.prd.read_text(encoding="utf-8")
        evidence = load_evidence(args.evidence) if args.evidence else None
        cols, rows = read_stories(args.stories) if args.stories else ([], [])
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 2
    findings = check_prd(text, evidence, has_stories=bool(args.stories))
    if args.stories:
        findings += check_stories(cols, rows, evidence)
    flowed: list[dict] = []
    if args.flow_down and not any(f["rule"] == "missing-columns" for f in findings):
        flowed, info = flow_down(rows, args.prefix, args.owner, args.prd.name)
        findings += info
        csv_text = to_csv(flowed)
        if args.flow_down == "-":
            sys.stdout.write(csv_text)
        else:
            try:
                Path(args.flow_down).write_text(csv_text, encoding="utf-8")
            except OSError as exc:
                print(f"cannot write {args.flow_down}: {exc}", file=sys.stderr)
                return 2
    sev = Counter(f["severity"] for f in findings)
    summary = {"stories": len(rows), "by_priority": dict(Counter(r.get("priority", "").lower() for r in rows)),
               "flowed_down_rows": len(flowed),
               "errors": sev.get("error", 0), "warnings": sev.get("warning", 0), "info": sev.get("info", 0)}
    failed = summary["errors"] > 0 or (args.strict and summary["warnings"] > 0)
    result = {"findings": findings, "summary": summary, "passed": not failed}
    report_stream = sys.stderr if args.flow_down == "-" else sys.stdout
    if args.json:
        print(json.dumps(result, indent=2), file=report_stream)
    else:
        for f in findings:
            print(f"{f['severity'].upper():8} {f['id']:<18} {f['rule']:<26} {f['message']}", file=report_stream)
        print(f"\n{'FAIL' if failed else 'PASS'}: {summary}", file=report_stream)
        print("Scope: structure/wording lint only; flowed-down requirements are proposals needing owner approval.",
              file=report_stream)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
