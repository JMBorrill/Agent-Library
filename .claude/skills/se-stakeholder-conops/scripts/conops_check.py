#!/usr/bin/env python3
"""Check a ConOps document plus stakeholder and needs registers for completeness and honesty.

ConOps (Markdown): required sections, nominal AND off-nominal scenarios, solution language in the
mission need, stakeholder/customer claims or quotes without an [evidence: ...] tag.
Stakeholders CSV: role present, at least one decision owner, high-influence stakeholders have needs,
referenced needs exist. Needs CSV: unique IDs, each need has a stakeholder and a measurable MOE.

Usage: conops_check.py conops.md [--stakeholders S.csv] [--needs N.csv] [--json]
Exit: 0 no errors, 1 errors, 2 unreadable.
Scope: completeness and evidence hygiene only; whether the needs are the real needs is validated with people.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

SECTIONS = {
    "mission-need": ["mission need", "need statement", "problem statement", "mission"],
    "stakeholders": ["stakeholder"],
    "scenarios": ["operational scenario", "scenarios", "use case"],
    "modes": ["mode"],
    "environment": ["environment"],
    "constraints": ["constraint"],
    "moe": ["measures of effectiveness", "moe", "success criteria"],
    "assumptions": ["assumption"],
    "open-questions": ["open question", "open issue", "tbd"],
}
SOLUTION_WORDS = re.compile(r"\b(we will build|build a|using|with (a |an )?(reaction wheel|motor|app|platform|database)|"
                            r"implement|develop a|the robot|the app|the system will)\b", re.I)
CLAIM = re.compile(r"(customers?|users?|stakeholders?|operators?)\s+(told|said|say|want|love|asked|confirmed)|\"[^\"]{8,}\"", re.I)
EVIDENCE_TAG = re.compile(r"\[evidence:\s*[^\]]+\]", re.I)
MEASURABLE = re.compile(r"\d")


def _f(rid, sev, rule, msg):
    return {"id": rid, "severity": sev, "rule": rule, "message": msg}


def sections(md: str) -> dict[str, str]:
    out, cur = {}, None
    for line in md.splitlines():
        m = re.match(r"^#{2,3}\s+(.*)", line)
        if m:
            cur = m.group(1).strip().lower()
            out.setdefault(cur, "")
        elif cur:
            out[cur] += line + "\n"
    return out


def check_conops(md: str) -> list[dict]:
    f = []
    secs = sections(md)
    found = {}
    for key, pats in SECTIONS.items():
        hit = next((h for h in secs if any(p in h for p in pats)), None)
        found[key] = hit
        if not hit:
            f.append(_f(key, "error" if key in {"mission-need", "stakeholders", "scenarios", "moe"} else "warning",
                        "missing-section", f"ConOps has no '{key}' section"))
    text_lower = md.lower()
    if found["scenarios"]:
        scen = " ".join(v for h, v in secs.items() if "scenario" in h or "nominal" in h) + " ".join(secs)
        if "nominal" not in scen.lower():
            f.append(_f("scenarios", "warning", "no-nominal", "no nominal scenario identified"))
        if not re.search(r"off-nominal|contingency|failure|fault|abort|emergency", scen, re.I):
            f.append(_f("scenarios", "error", "no-off-nominal", "no off-nominal/contingency scenario — failures are where requirements hide"))
    if found["mission-need"]:
        need_text = secs[found["mission-need"]]
        if SOLUTION_WORDS.search(need_text):
            f.append(_f("mission-need", "warning", "solution-in-need",
                        "mission need contains solution language; state the problem, not the design"))
    for i, line in enumerate(md.splitlines(), 1):
        if CLAIM.search(line) and not EVIDENCE_TAG.search(line):
            f.append(_f(f"line {i}", "error", "unsupported-stakeholder-claim",
                        "stakeholder claim or quote without [evidence: ...] — never invent interviews or quotes"))
    if "none." in text_lower and found["assumptions"] and secs[found["assumptions"]].strip().lower() in {"none.", "none"}:
        f.append(_f("assumptions", "warning", "no-assumptions", "'None' assumptions is implausible at concept stage"))
    return f


def read_csv(p: Path) -> list[dict]:
    with p.open(newline="", encoding="utf-8-sig") as fh:
        return [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(fh)]


def check_registers(stk: list[dict] | None, needs: list[dict] | None) -> list[dict]:
    f = []
    need_ids = set()
    if needs is not None:
        c = Counter(n.get("need_id") for n in needs)
        for n in needs:
            nid = n.get("need_id") or "<blank>"
            need_ids.add(n.get("need_id"))
            if c[n.get("need_id")] > 1:
                f.append(_f(nid, "error", "duplicate-need", "need id repeated"))
            if not n.get("stakeholder"):
                f.append(_f(nid, "error", "need-without-stakeholder", "need not attributed to a stakeholder"))
            moe = n.get("moe", "")
            if not moe:
                f.append(_f(nid, "error", "need-without-moe", "need has no measure of effectiveness"))
            elif not MEASURABLE.search(moe):
                f.append(_f(nid, "warning", "moe-not-measurable", "MOE has no quantitative element"))
            if not n.get("evidence_ref"):
                f.append(_f(nid, "warning", "need-without-evidence", "need has no evidence reference (marked as hypothesis)"))
    if stk is not None:
        if not any(s.get("decision_rights") for s in stk):
            f.append(_f("stakeholders", "error", "no-decision-owner", "no stakeholder holds decision rights"))
        for s in stk:
            sid = s.get("stakeholder") or "<blank>"
            if not s.get("role"):
                f.append(_f(sid, "error", "no-role", "stakeholder has no role"))
            linked = [x.strip() for x in re.split(r"[;,]", s.get("needs", "")) if x.strip()]
            if s.get("influence", "").lower() == "high" and not linked:
                f.append(_f(sid, "warning", "high-influence-no-needs", "high-influence stakeholder with no recorded needs"))
            if needs is not None:
                for x in linked:
                    if x not in need_ids:
                        f.append(_f(sid, "error", "unknown-need", f"need '{x}' not in needs register"))
    return f


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check ConOps, stakeholders and needs.")
    ap.add_argument("conops", type=Path)
    ap.add_argument("--stakeholders", type=Path)
    ap.add_argument("--needs", type=Path)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        md = a.conops.read_text(encoding="utf-8")
        stk = read_csv(a.stakeholders) if a.stakeholders else None
        needs = read_csv(a.needs) if a.needs else None
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 2
    findings = check_conops(md) + check_registers(stk, needs)
    sev = Counter(x["severity"] for x in findings)
    res = {"findings": findings, "summary": {"errors": sev.get("error", 0), "warnings": sev.get("warning", 0)}}
    res["passed"] = res["summary"]["errors"] == 0
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        for x in findings:
            print(f"{x['severity'].upper():8} {x['id']:<22} {x['rule']:<30} {x['message']}")
        print(f"\n{'PASS' if res['passed'] else 'FAIL'}: {res['summary']}")
        print("Scope: completeness/evidence hygiene only; validate needs with the real stakeholders.")
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
