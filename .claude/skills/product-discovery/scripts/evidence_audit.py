#!/usr/bin/env python3
"""Audit a discovery evidence log (and optional assumptions register) and recommend a phase gate.

Checks
  Evidence log: required columns, unique IDs, allowed type/method values, observations carry a
  source reference, a method, an ISO date and participants > 0, quotes are traceable to a
  research session, hypotheses/assumptions are never counted as evidence, strength summary.
  Assumptions: allowed category/risk/status values, evidence links resolve, every high/medium
  risk assumption has counted evidence or a planned experiment, claimed status is backed by
  evidence, high-risk untested assumptions block a "proceed" recommendation.

Usage
  evidence_audit.py evidence.csv [--assumptions assumptions.csv] [--target alpha|beta]
                    [--as-of YYYY-MM-DD] [--strong-min-participants 5] [--strict] [--json]
Exit codes: 0 no errors, 1 errors (or warnings with --strict), 2 unreadable input / bad arguments.

Scope: checks the structure and traceability of evidence. It cannot tell whether research was
done well, whether participants were representative or whether a claim is true. The phase-gate
output is a recommendation for the accountable product owner, never an approval.
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

EVIDENCE_COLUMNS = ["id", "claim", "type", "source_ref", "method", "date", "participants",
                    "segment", "confidence", "linked_assumption"]
ASSUMPTION_COLUMNS = ["id", "assumption", "category", "risk", "evidence_ids", "status"]
TYPES = {"observation", "hypothesis", "assumption", "desk_research"}
METHODS = {"interview", "usability_test", "analytics", "survey", "desk", "none"}
CONFIDENCE = {"high", "medium", "low"}
CATEGORIES = {"desirability", "viability", "feasibility", "usability", "ethics"}
RISKS = {"high", "medium", "low"}
STATUSES = {"untested", "experiment_planned", "testing", "supported", "refuted"}
PLANNED = {"experiment_planned", "testing"}
TESTED = {"supported", "refuted"}
NOT_EVIDENCE = {"hypothesis", "assumption"}

# Quoted text of 3+ words in straight or curly double quotes.
QUOTE_RE = re.compile(r"[\"“]([^\"”]*\s[^\"”]*\s[^\"”]*)[\"”]")
# A source reference that identifies a research session: e.g. INT-07, UT-03, session 4,
# transcript T12, call-2026-09-01, or a timestamp such as 14:32.
SESSION_RE = re.compile(
    r"(\b(INT|UT|SES|SESSION|CALL|REC|TRANSCRIPT|T)[-_ ]?\d+\b|\bsession\s*\d+|\binterview\s*\d+|\b\d{1,2}:\d{2}\b)",
    re.I)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

GATE_LABELS = {"PROCEED": "GO", "PROCEED_WITH_CONDITIONS": "GO_WITH_CONDITIONS", "DO_NOT_PROCEED": "NO_GO"}


def _f(rid: str, severity: str, rule: str, message: str) -> dict:
    return {"id": rid, "severity": severity, "rule": rule, "message": message}


def read_csv(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        rows = []
        for r in reader:
            if None in r:  # more cells than headers
                raise csv.Error(f"row {reader.line_num} has more cells than the header")
            rows.append({(k or "").strip(): (v or "").strip() for k, v in r.items()})
        return [c.strip() for c in (reader.fieldnames or [])], rows


def split_ids(value: str) -> list[str]:
    return [x.strip() for x in re.split(r"[;,\s]+", value or "") if x.strip()]


def _int(value: str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def classify_strength(row: dict, strong_min: int) -> str:
    """Strength of a *valid* evidence row: strong | moderate | weak."""
    if row["type"] == "desk_research":
        return "weak"
    n = _int(row["participants"]) or 0
    if row["method"] == "analytics" or n >= strong_min:
        return "strong"
    return "moderate"


def audit_evidence(columns: list[str], rows: list[dict], as_of: dt.date | None = None,
                   strong_min: int = 5) -> tuple[list[dict], dict[str, dict]]:
    """Return (findings, catalogue). catalogue[id] = {type, counted, strength}."""
    findings: list[dict] = []
    missing = [c for c in EVIDENCE_COLUMNS if c not in columns]
    if missing:
        findings.append(_f("-", "error", "missing-columns", f"evidence log missing columns: {', '.join(missing)}"))
        return findings, {}
    if not rows:
        findings.append(_f("-", "error", "empty-log", "evidence log has no rows"))
        return findings, {}
    counts = Counter(r["id"] for r in rows)
    catalogue: dict[str, dict] = {}
    for r in rows:
        rid = r["id"] or "<blank>"
        typ = r["type"].lower()
        method = r["method"].lower()
        r["type"], r["method"] = typ, method
        valid = True
        if not r["id"]:
            findings.append(_f(rid, "error", "blank-id", "evidence row has no identifier"))
            valid = False
        elif counts[r["id"]] > 1:
            findings.append(_f(rid, "error", "duplicate-id", f"identifier used {counts[r['id']]} times"))
            valid = False
        if typ not in TYPES:
            findings.append(_f(rid, "error", "invalid-type", f"type '{r['type']}' not in {sorted(TYPES)}"))
            valid = False
        if method and method not in METHODS:
            findings.append(_f(rid, "error", "invalid-method", f"method '{method}' not in {sorted(METHODS)}"))
            valid = False
        if r["confidence"] and r["confidence"].lower() not in CONFIDENCE:
            findings.append(_f(rid, "warning", "invalid-confidence",
                               f"confidence '{r['confidence']}' not in {sorted(CONFIDENCE)}"))
        if not r["claim"]:
            findings.append(_f(rid, "error", "empty-claim", "claim is empty"))
            valid = False
        if r["date"]:
            if not DATE_RE.fullmatch(r["date"]):
                findings.append(_f(rid, "error", "bad-date", f"date '{r['date']}' is not YYYY-MM-DD"))
                valid = False
            else:
                try:
                    d = dt.date.fromisoformat(r["date"])
                    if as_of and d > as_of:
                        findings.append(_f(rid, "error", "future-date", f"dated {d} after --as-of {as_of}"))
                        valid = False
                except ValueError:
                    findings.append(_f(rid, "error", "bad-date", f"date '{r['date']}' is not a real date"))
                    valid = False

        if typ == "observation":
            if not r["source_ref"]:
                findings.append(_f(rid, "error", "observation-no-source",
                                   "observation has no source_ref (session, recording, dataset)"))
                valid = False
            if method in ("", "none"):
                findings.append(_f(rid, "error", "observation-no-method", "observation has no research method"))
                valid = False
            elif method == "desk":
                findings.append(_f(rid, "warning", "observation-desk-method",
                                   "method 'desk' on an observation — record it as desk_research"))
            if not r["date"]:
                findings.append(_f(rid, "error", "observation-no-date", "observation has no date"))
                valid = False
            n = _int(r["participants"])
            if n is None or n <= 0:
                findings.append(_f(rid, "error", "observation-no-participants",
                                   f"participants must be an integer > 0 (got '{r['participants']}')"))
                valid = False
        elif typ == "desk_research":
            if not r["source_ref"]:
                findings.append(_f(rid, "error", "desk-no-source", "desk research has no source_ref"))
                valid = False
        elif typ in NOT_EVIDENCE:
            findings.append(_f(rid, "info", f"{typ}-not-evidence",
                               f"{typ} recorded for tracking; never counted as evidence"))
            if r["confidence"].lower() == "high":
                findings.append(_f(rid, "warning", "untested-high-confidence",
                                   f"{typ} marked high confidence without evidence"))

        quote = QUOTE_RE.search(r["claim"])
        if quote and not SESSION_RE.search(r["source_ref"]):
            findings.append(_f(rid, "error", "quote-without-session",
                               "quoted words with no traceable session reference in source_ref — "
                               "possible fabricated or composite quote"))
            valid = False
        if typ in NOT_EVIDENCE and quote:
            findings.append(_f(rid, "error", "quote-in-hypothesis",
                               "a hypothesis/assumption must not contain a user quote; imagined quotes are not evidence"))

        if r["id"]:
            counted = valid and typ in {"observation", "desk_research"}
            if r["id"] in catalogue:  # duplicates: keep first type, never count
                catalogue[r["id"]]["counted"] = False
                catalogue[r["id"]]["strength"] = None
                continue
            catalogue[r["id"]] = {
                "type": typ, "counted": counted,
                "strength": classify_strength(r, strong_min) if counted else None,
                "linked_assumption": r["linked_assumption"],
            }
    return findings, catalogue


def audit_assumptions(columns: list[str], rows: list[dict], catalogue: dict[str, dict],
                      target: str = "alpha") -> tuple[list[dict], dict]:
    findings: list[dict] = []
    missing = [c for c in ASSUMPTION_COLUMNS if c not in columns]
    if missing:
        findings.append(_f("-", "error", "missing-columns", f"assumptions missing columns: {', '.join(missing)}"))
        return findings, {"blockers": ["assumptions register unreadable"], "conditions": []}
    counts = Counter(r["id"] for r in rows)
    blockers: list[str] = []
    conditions: list[str] = []
    for r in rows:
        rid = r["id"] or "<blank>"
        cat, risk, status = r["category"].lower(), r["risk"].lower(), r["status"].lower()
        if not r["id"]:
            findings.append(_f(rid, "error", "blank-id", "assumption has no identifier"))
        elif counts[r["id"]] > 1:
            findings.append(_f(rid, "error", "duplicate-id", f"assumption identifier used {counts[r['id']]} times"))
        if cat not in CATEGORIES:
            findings.append(_f(rid, "error", "invalid-category", f"category '{r['category']}' not in {sorted(CATEGORIES)}"))
        if risk not in RISKS:
            findings.append(_f(rid, "error", "invalid-risk", f"risk '{r['risk']}' not in {sorted(RISKS)}"))
        if status not in STATUSES:
            findings.append(_f(rid, "error", "invalid-status", f"status '{r['status']}' not in {sorted(STATUSES)}"))
        counted = []
        for eid in split_ids(r["evidence_ids"]):
            entry = catalogue.get(eid)
            if entry is None:
                findings.append(_f(rid, "error", "unknown-evidence-id", f"evidence '{eid}' not in evidence log"))
            elif entry["type"] in NOT_EVIDENCE:
                findings.append(_f(rid, "warning", "non-evidence-cited",
                                   f"'{eid}' is a {entry['type']}; it does not count as evidence"))
            elif not entry["counted"]:
                findings.append(_f(rid, "warning", "invalid-evidence-cited",
                                   f"'{eid}' has blocking defects in the evidence log; not counted"))
            else:
                counted.append(eid)
        if status in TESTED and not counted:
            findings.append(_f(rid, "error", "status-without-evidence",
                               f"status '{status}' but no valid evidence linked"))
        has_plan = status in PLANNED
        if risk in ("high", "medium") and not counted and not has_plan:
            sev = "error" if risk == "high" else "warning"
            findings.append(_f(rid, sev, "assumption-uncovered",
                               f"{risk}-risk assumption has neither evidence nor a planned experiment"))
        if risk == "high":
            if status == "refuted":
                blockers.append(f"{rid}: high-risk assumption refuted — revisit the concept")
                findings.append(_f(rid, "error", "high-risk-refuted",
                                   "high-risk assumption refuted by evidence; re-shape before proceeding"))
            elif not (status == "supported" and counted):
                if has_plan and target == "alpha":
                    conditions.append(f"{rid}: run the planned experiment in alpha before any build commitment")
                    findings.append(_f(rid, "warning", "high-risk-untested",
                                       "high-risk assumption not yet tested; acceptable only as an alpha condition"))
                else:
                    blockers.append(f"{rid}: high-risk assumption untested")
                    findings.append(_f(rid, "error", "high-risk-untested",
                                       f"high-risk assumption untested — blocks a proceed-to-{target} recommendation"))
        elif risk == "medium" and not (status == "supported" and counted):
            conditions.append(f"{rid}: medium-risk assumption still open ({status or 'no status'})")
    return findings, {"blockers": blockers, "conditions": conditions}


def recommend(findings: list[dict], catalogue: dict[str, dict], gate: dict | None, target: str) -> dict:
    reasons: list[str] = []
    data_errors = [f for f in findings if f["severity"] == "error"
                   and f["rule"] not in ("high-risk-untested", "high-risk-refuted", "assumption-uncovered")]
    counted = sum(1 for e in catalogue.values() if e["counted"])
    blockers = list(gate["blockers"]) if gate else []
    conditions = list(gate["conditions"]) if gate else []
    if data_errors:
        blockers.append(f"{len(data_errors)} evidence/register integrity error(s) — fix before deciding")
    if counted == 0:
        blockers.append("no valid evidence recorded")
    if gate is None:
        conditions.append("no assumptions register supplied — risky assumptions not assessed")
    if blockers:
        rec, reasons = "DO_NOT_PROCEED", blockers
    elif conditions:
        rec, reasons = "PROCEED_WITH_CONDITIONS", conditions
    else:
        rec, reasons = "PROCEED", ["all high/medium-risk assumptions supported by valid evidence"]
    return {"recommendation": rec, "gate_equivalent": GATE_LABELS[rec], "target_phase": target,
            "reasons": reasons, "requires_human_decision": True}


def audit(ev_cols, ev_rows, as_cols=None, as_rows=None, target="alpha", as_of=None, strong_min=5) -> dict:
    findings, catalogue = audit_evidence(ev_cols, ev_rows, as_of, strong_min)
    gate = None
    if as_cols is not None:
        known_assumptions = {r.get("id", "") for r in (as_rows or [])}
        for r in ev_rows:
            la = r.get("linked_assumption", "")
            for aid in split_ids(la):
                if aid not in known_assumptions:
                    findings.append(_f(r.get("id") or "<blank>", "error", "unknown-assumption",
                                       f"linked_assumption '{aid}' not in assumptions register"))
        af, gate = audit_assumptions(as_cols, as_rows or [], catalogue, target)
        findings.extend(af)
    strength = Counter(e["strength"] for e in catalogue.values() if e["counted"])
    sev = Counter(f["severity"] for f in findings)
    summary = {
        "evidence_rows": len(ev_rows),
        "counted_evidence": sum(strength.values()),
        "by_strength": {k: strength.get(k, 0) for k in ("strong", "moderate", "weak")},
        "not_evidence": {t: sum(1 for e in catalogue.values() if e["type"] == t) for t in sorted(NOT_EVIDENCE)},
        "excluded_invalid": sum(1 for e in catalogue.values() if e["type"] in {"observation", "desk_research"} and not e["counted"]),
        "assumptions": len(as_rows or []),
        "assumptions_by_risk": dict(Counter(r.get("risk", "").lower() for r in (as_rows or []))),
        "errors": sev.get("error", 0), "warnings": sev.get("warning", 0), "info": sev.get("info", 0),
    }
    return {"findings": findings, "summary": summary, "gate": recommend(findings, catalogue, gate, target)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Audit a discovery evidence log and recommend a phase gate.")
    ap.add_argument("evidence", type=Path)
    ap.add_argument("--assumptions", type=Path)
    ap.add_argument("--target", choices=["alpha", "beta"], default="alpha",
                    help="phase the team wants to enter (beta = commit to building for real users)")
    ap.add_argument("--as-of", help="YYYY-MM-DD; evidence dated later is an error")
    ap.add_argument("--strong-min-participants", type=int, default=5)
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        as_of = dt.date.fromisoformat(args.as_of) if args.as_of else None
    except ValueError:
        print(f"--as-of must be YYYY-MM-DD, got {args.as_of}", file=sys.stderr)
        return 2
    if args.strong_min_participants < 1:
        print("--strong-min-participants must be >= 1", file=sys.stderr)
        return 2
    try:
        ev_cols, ev_rows = read_csv(args.evidence)
        as_cols = as_rows = None
        if args.assumptions:
            as_cols, as_rows = read_csv(args.assumptions)
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 2
    result = audit(ev_cols, ev_rows, as_cols, as_rows, args.target, as_of, args.strong_min_participants)
    s = result["summary"]
    failed = s["errors"] > 0 or (args.strict and s["warnings"] > 0)
    result["passed"] = not failed
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for f in result["findings"]:
            print(f"{f['severity'].upper():8} {f['id']:<12} {f['rule']:<28} {f['message']}")
        g = result["gate"]
        print(f"\nEvidence: {s['counted_evidence']} counted {s['by_strength']}; "
              f"not evidence {s['not_evidence']}; excluded {s['excluded_invalid']}")
        print(f"Gate recommendation (to {g['target_phase']}): {g['recommendation']} ({g['gate_equivalent']})")
        for reason in g["reasons"]:
            print(f"  - {reason}")
        print(f"\n{'FAIL' if failed else 'PASS'}: {s['errors']} errors, {s['warnings']} warnings")
        print("Scope: structure/traceability check only; a recommendation for the product owner, not an approval.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
