#!/usr/bin/env python3
"""Track technical performance measures (TPMs): margin to limit, alert bands and trend projection.

For each TPM the latest value is compared with its limit:
  margin % (upper_limit) = (limit - value) / limit * 100
  margin % (lower_limit) = (value - limit) / limit * 100
status: breach (< 0), alert (< alert_margin_pct), ok. A least-squares line through the last
three points projects the value at --milestone (YYYY-MM-DD) and flags a projected breach.

Usage: tpm_track.py tpm.csv [--milestone YYYY-MM-DD] [--json]
Exit: 0 no errors and no breaches, 1 errors or breaches, 2 unreadable.
Scope: arithmetic on supplied values; the quality of each estimate/measurement is not assessed.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

DIRECTIONS = {"upper_limit", "lower_limit"}
BASES = {"estimate", "analysis", "measured", "allocation"}


def _f(rid, sev, rule, msg):
    return {"id": rid, "severity": sev, "rule": rule, "message": msg}


def margin_pct(value: float, limit: float, direction: str) -> float:
    if limit == 0:
        raise ZeroDivisionError("limit is zero; express margin in absolute terms")
    return ((limit - value) if direction == "upper_limit" else (value - limit)) / abs(limit) * 100.0


def fit(points: list[tuple[int, float]]) -> tuple[float, float] | None:
    if len(points) < 2:
        return None
    n = len(points)
    mx = sum(x for x, _ in points) / n
    my = sum(y for _, y in points) / n
    sxx = sum((x - mx) ** 2 for x, _ in points)
    if sxx == 0:
        return None
    slope = sum((x - mx) * (y - my) for x, y in points) / sxx
    return slope, my - slope * mx


def assess(cols, rows, milestone: date | None = None) -> dict:
    findings, results = [], []
    need = ["tpm_id", "unit", "direction", "limit", "date", "value"]
    missing = [c for c in need if c not in cols]
    if missing:
        return {"findings": [_f("-", "error", "missing-columns", ", ".join(missing))], "tpms": [], "summary": {}}
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        groups[r["tpm_id"]].append(r)
    for tid, rs in groups.items():
        units = {r["unit"] for r in rs}
        limits = {r["limit"] for r in rs}
        dirs = {r["direction"] for r in rs}
        if len(units) > 1:
            findings.append(_f(tid, "error", "inconsistent-units", f"units {sorted(units)} mixed within one TPM — convert to one unit"))
            continue
        if len(dirs) > 1 or not dirs <= DIRECTIONS:
            findings.append(_f(tid, "error", "direction", f"direction must be one of {sorted(DIRECTIONS)} and constant"))
            continue
        if len(limits) > 1:
            findings.append(_f(tid, "warning", "limit-changed", f"limit changed over time {sorted(limits)} — confirm a CR exists; latest used"))
        pts = []
        bad = False
        for r in rs:
            try:
                d = date.fromisoformat(r["date"])
                v = float(r["value"])
                lim = float(r["limit"])
            except ValueError:
                findings.append(_f(tid, "error", "non-numeric", f"bad date/value/limit in row dated '{r['date']}'"))
                bad = True
                continue
            if r.get("basis") and r["basis"] not in BASES:
                findings.append(_f(tid, "warning", "basis", f"unknown basis '{r['basis']}'"))
            pts.append((d, v, lim, r.get("basis", ""), r))
        if bad or not pts:
            continue
        pts.sort(key=lambda p: p[0])
        if len({p[0] for p in pts}) != len(pts):
            findings.append(_f(tid, "error", "duplicate-date", "two values on the same date"))
            continue
        d, v, lim, basis, r = pts[-1]
        direction = r["direction"]
        try:
            m = margin_pct(v, lim, direction)
        except ZeroDivisionError as exc:
            findings.append(_f(tid, "error", "zero-limit", str(exc)))
            continue
        alert = float(r.get("alert_margin_pct") or 0)
        status = "breach" if m < 0 else "alert" if m < alert else "ok"
        if status == "breach":
            findings.append(_f(tid, "error", "breach", f"latest {v} {r['unit']} violates limit {lim} ({m:.1f}% margin)"))
        elif status == "alert":
            findings.append(_f(tid, "warning", "alert", f"margin {m:.1f}% below alert threshold {alert}%"))
        if basis in ("estimate", "allocation") and status != "ok":
            findings.append(_f(tid, "info", "estimate-basis", "latest value is an estimate — obtain analysis/measurement"))
        projection = None
        line = fit([(p[0].toordinal(), p[1]) for p in pts[-3:]])
        if milestone and line:
            projection = line[0] * milestone.toordinal() + line[1]
            pm = margin_pct(projection, lim, direction)
            if pm < 0 <= m:
                findings.append(_f(tid, "warning", "projected-breach",
                                   f"trend projects {projection:.2f} {r['unit']} at {milestone} (margin {pm:.1f}%)"))
        results.append({"tpm_id": tid, "latest_date": d.isoformat(), "latest_value": v, "limit": lim,
                        "unit": r["unit"], "margin_pct": round(m, 2), "status": status, "basis": basis,
                        "projection": None if projection is None else round(projection, 3),
                        "requirement_id": r.get("requirement_id", "")})
    sev = Counter(f["severity"] for f in findings)
    return {"findings": findings, "tpms": results,
            "summary": {"tpms": len(groups), "by_status": dict(Counter(x["status"] for x in results)),
                        "errors": sev.get("error", 0), "warnings": sev.get("warning", 0)}}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Track TPM margins and trends.")
    ap.add_argument("csv", type=Path)
    ap.add_argument("--milestone", help="YYYY-MM-DD date to project trends to")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        with a.csv.open(newline="", encoding="utf-8-sig") as fh:
            rd = csv.DictReader(fh)
            rows = [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in rd]
            cols = [c.strip() for c in rd.fieldnames or []]
        ms = date.fromisoformat(a.milestone) if a.milestone else None
    except (OSError, ValueError, csv.Error) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 2
    res = assess(cols, rows, ms)
    res["passed"] = res["summary"].get("errors", 1) == 0
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        for t in res["tpms"]:
            print(f"{t['tpm_id']:<10} {t['latest_value']:>10} {t['unit']:<4} limit {t['limit']:<8} "
                  f"margin {t['margin_pct']:>7}%  {t['status']:<6} ({t['basis']})"
                  + (f"  projected {t['projection']}" if t["projection"] is not None else ""))
        for f in res["findings"]:
            print(f"{f['severity'].upper():8} {f['id']:<10} {f['rule']:<18} {f['message']}")
        print(f"\n{'PASS' if res['passed'] else 'FAIL'}: {res['summary']}")
        print("Scope: arithmetic on supplied values; estimate quality is not assessed.")
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
