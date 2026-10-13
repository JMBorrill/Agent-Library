#!/usr/bin/env python3
"""Compute DORA's five software delivery performance metrics from a deployments CSV.

Metrics (names as used by the DORA metrics guide): Change lead time, Deployment frequency,
Failed deployment recovery time, Change fail rate, Deployment rework rate. Operational
definitions used here are stated in the output because DORA does not prescribe formulas.

CSV columns: deploy_id, service, deployed_at, status (success|failed), and optionally
first_commit_at or commit_times (';'-separated), is_rework (yes|no), restored_at.
All timestamps must be ISO 8601 with a UTC offset (e.g. 2026-09-01T10:00:00Z).

Usage:
  dora_metrics.py deployments.csv [--service NAME] [--start ISO] [--end ISO] [--min-sample 10] [--json]
Exit codes: 0 no errors, 1 data errors found (rows excluded), 2 unreadable input / bad arguments.

Scope: descriptive statistics for one service's own improvement conversation. Not a target,
not a benchmark, and not a basis for comparing teams.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REQUIRED = ["deploy_id", "service", "deployed_at", "status"]
DEFINITIONS = {
    "Change lead time": "Per commit: deployed_at minus commit time, over successful deployments in the window "
                        "(commit_times, else first_commit_at). Hours; median and percentiles.",
    "Deployment frequency": "Number of production deployments (any status) with deployed_at in [start, end), "
                            "also per day/week and the median interval between consecutive deployments.",
    "Failed deployment recovery time": "Per failed deployment with restored_at: restored_at minus deployed_at. "
                                       "Hours; median and percentiles. Unrecovered failures are excluded and counted.",
    "Change fail rate": "Deployments with status=failed (needed immediate intervention such as rollback or hotfix) "
                        "divided by all deployments in the window.",
    "Deployment rework rate": "Deployments with is_rework=yes (unplanned, caused by a production incident) divided "
                              "by all deployments in the window.",
}
CATEGORIES = {"Change lead time": "throughput", "Deployment frequency": "throughput",
              "Failed deployment recovery time": "throughput", "Change fail rate": "instability",
              "Deployment rework rate": "instability"}
CAUTIONS = [
    "Do not set these metrics as goals or targets; doing so invites gaming (DORA pitfall: Setting metrics as a goal).",
    "Use all five together, not one in isolation (Having one metric to rule them all).",
    "Industry or regulation is not a reason to stop improving (Using industry as a shield against improving).",
    "Measure per application/service; do not compare dissimilar applications or teams (Making disparate comparisons).",
    "Share all metrics across development, operations and release (Having siloed ownership).",
    "Improve against your own baseline; do not rank or compete with other teams (Competing).",
    "Do not let measurement plumbing displace improvement work (Focusing on measurement at the expense of improvement).",
]


def _finding(fid: str, severity: str, rule: str, message: str) -> dict:
    return {"id": fid, "severity": severity, "rule": rule, "message": message}


def parse_ts(value: str) -> datetime:
    """Parse ISO 8601; raise ValueError if unparseable, TypeError if timezone-naive."""
    dt = datetime.fromisoformat(value.strip().replace("z", "Z"))
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise TypeError("timezone-naive timestamp")
    return dt.astimezone(timezone.utc)


def parse_bound(value: str) -> datetime:
    """Window bound: a date (taken as 00:00 UTC) or an offset-aware datetime."""
    v = value.strip()
    if len(v) == 10:
        return datetime.fromisoformat(v).replace(tzinfo=timezone.utc)
    return parse_ts(v)


def percentile(values: list[float], p: float) -> float | None:
    """Linear interpolation between closest ranks (inclusive method): rank = (n-1)*p/100."""
    if not values:
        return None
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    rank = (len(xs) - 1) * p / 100.0
    lo = int(rank)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (rank - lo)


def _dist(values: list[float]) -> dict:
    r = lambda v: None if v is None else round(v, 4)  # noqa: E731
    return {"n": len(values), "median": r(statistics.median(values)) if values else None,
            "p75": r(percentile(values, 75)), "p90": r(percentile(values, 90)),
            "min": r(min(values)) if values else None, "max": r(max(values)) if values else None}


def compute(columns: list[str], rows: list[dict], service: str | None = None,
            start: datetime | None = None, end: datetime | None = None, min_sample: int = 10) -> dict:
    findings: list[dict] = []
    missing = [c for c in REQUIRED if c not in columns]
    if missing:
        findings.append(_finding("-", "error", "missing-columns", f"missing columns: {', '.join(missing)}"))
        return {"findings": findings, "summary": {"errors": 1, "warnings": 0}, "metrics": {}}
    has_commits = "commit_times" in columns or "first_commit_at" in columns
    if not has_commits:
        findings.append(_finding("-", "warning", "no-commit-data", "no commit_times/first_commit_at column: "
                                 "Change lead time cannot be computed"))
    if "is_rework" not in columns:
        findings.append(_finding("-", "warning", "no-rework-data", "no is_rework column: "
                                 "Deployment rework rate cannot be computed"))
    deps: list[dict] = []
    seen: set[str] = set()
    for i, r in enumerate(rows, start=2):
        rid = r.get("deploy_id") or f"row{i}"
        if service and r.get("service") != service:
            continue
        if rid in seen:
            findings.append(_finding(rid, "error", "duplicate-deploy-id", "deploy_id appears more than once; row excluded"))
            continue
        seen.add(rid)
        try:
            dep = parse_ts(r["deployed_at"])
            status = r["status"].strip().lower()
            if status not in {"success", "failed"}:
                raise ValueError(f"status '{r['status']}' not success|failed")
            rework_raw = (r.get("is_rework") or "").strip().lower()
            if rework_raw not in {"", "yes", "no"}:
                raise ValueError(f"is_rework '{r.get('is_rework')}' not yes|no")
            raw_commits = (r.get("commit_times") or "").strip() or (r.get("first_commit_at") or "").strip()
            commits = [parse_ts(c) for c in raw_commits.split(";") if c.strip()]
            restored = parse_ts(r["restored_at"]) if (r.get("restored_at") or "").strip() else None
        except TypeError:
            findings.append(_finding(rid, "error", "naive-timestamp",
                                     "timestamp has no UTC offset; add Z or +HH:MM (row excluded)"))
            continue
        except (ValueError, KeyError) as exc:
            findings.append(_finding(rid, "error", "malformed-row", f"{exc} (row excluded)"))
            continue
        bad = [c for c in commits if c > dep]
        if bad or (restored and restored < dep):
            findings.append(_finding(rid, "error", "negative-duration",
                                     "commit after deployment or restore before deployment (row excluded)"))
            continue
        deps.append({"id": rid, "service": r.get("service", ""), "at": dep, "status": status,
                     "rework": rework_raw == "yes", "rework_known": rework_raw != "", "commits": commits,
                     "restored": restored})
    services = sorted({d["service"] for d in deps})
    if len(services) > 1 and not service:
        findings.append(_finding("-", "warning", "mixed-services",
                                 f"{len(services)} services blended ({', '.join(services)}): DORA metrics are best "
                                 "per application/service; use --service"))
    if deps and start is None:
        start = min(d["at"] for d in deps).replace(hour=0, minute=0, second=0, microsecond=0)
    if deps and end is None:
        end = max(d["at"] for d in deps).replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    if start is not None and end is not None and end <= start:
        raise ValueError("window end must be after start")
    win = sorted((d for d in deps if start <= d["at"] < end), key=lambda d: d["at"]) if deps else []
    days = (end - start).total_seconds() / 86400 if start and end else 0
    total = len(win)
    metrics: dict = {}
    if total == 0:
        findings.append(_finding("-", "warning", "no-deployments", "no deployments in the window; metrics undefined"))
    else:
        if total < min_sample:
            findings.append(_finding("-", "warning", "small-sample",
                                     f"only {total} deployments (< {min_sample}); treat metrics as indicative"))
        intervals = [(b["at"] - a["at"]).total_seconds() / 3600 for a, b in zip(win, win[1:])]
        metrics["Deployment frequency"] = {
            "count": total, "window_days": round(days, 4), "per_day": round(total / days, 4),
            "per_week": round(total / days * 7, 4),
            "median_interval_hours": round(statistics.median(intervals), 4) if intervals else None}
        lead = [(d["at"] - c).total_seconds() / 3600 for d in win if d["status"] == "success" for c in d["commits"]]
        if has_commits:
            metrics["Change lead time"] = {"unit": "hours", **_dist(lead)}
            if len(lead) < min_sample:
                findings.append(_finding("-", "warning", "small-sample",
                                         f"Change lead time has {len(lead)} samples (< {min_sample})"))
            no_commit = [d["id"] for d in win if d["status"] == "success" and not d["commits"]]
            if no_commit:
                findings.append(_finding(",".join(no_commit), "warning", "missing-commit-times",
                                         f"{len(no_commit)} successful deployment(s) without commit times excluded "
                                         "from Change lead time"))
        failed = [d for d in win if d["status"] == "failed"]
        metrics["Change fail rate"] = {"failed": len(failed), "deployments": total,
                                       "ratio": round(len(failed) / total, 4)}
        rec = [(d["restored"] - d["at"]).total_seconds() / 3600 for d in failed if d["restored"]]
        unrecovered = [d["id"] for d in failed if not d["restored"]]
        metrics["Failed deployment recovery time"] = {"unit": "hours", **_dist(rec), "unrecovered": len(unrecovered)}
        if unrecovered:
            findings.append(_finding(",".join(unrecovered), "warning", "unrecovered-failure",
                                     "failed deployment(s) without restored_at excluded from recovery time"))
        for d in win:
            if d["status"] == "success" and d["restored"]:
                findings.append(_finding(d["id"], "warning", "restored-on-success",
                                         "restored_at set on a successful deployment; check status"))
        if "is_rework" in columns:
            known = [d for d in win if d["rework_known"]]
            rw = sum(1 for d in known if d["rework"])
            metrics["Deployment rework rate"] = {"rework": rw, "deployments": len(known),
                                                 "ratio": round(rw / len(known), 4) if known else None}
            if len(known) < total:
                findings.append(_finding("-", "warning", "missing-rework-flag",
                                         f"{total - len(known)} deployment(s) with blank is_rework excluded"))
    sev = {s: sum(1 for f in findings if f["severity"] == s) for s in ("error", "warning", "info")}
    summary = {"service": service or (services[0] if len(services) == 1 else None), "services": services,
               "window_start": start.isoformat() if start else None, "window_end": end.isoformat() if end else None,
               "deployments_in_window": total, "errors": sev["error"], "warnings": sev["warning"], "info": sev["info"]}
    return {"findings": findings, "summary": summary, "metrics": metrics,
            "categories": CATEGORIES, "definitions": DEFINITIONS, "cautions": CAUTIONS}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Compute DORA's five delivery metrics from a deployments CSV.")
    ap.add_argument("csv", type=Path)
    ap.add_argument("--service")
    ap.add_argument("--start", help="window start (YYYY-MM-DD = 00:00 UTC, or offset-aware ISO datetime)")
    ap.add_argument("--end", help="window end, exclusive")
    ap.add_argument("--min-sample", type=int, default=10)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        start = parse_bound(args.start) if args.start else None
        end = parse_bound(args.end) if args.end else None
        with args.csv.open(newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            rows = [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in reader]
            cols = [c.strip() for c in reader.fieldnames or []]
        result = compute(cols, rows, args.service, start, end, args.min_sample)
    except (OSError, UnicodeDecodeError, csv.Error, ValueError, TypeError) as exc:
        print(f"cannot compute metrics: {exc}", file=sys.stderr)
        return 2
    failed = result["summary"]["errors"] > 0
    result["passed"] = not failed
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        s = result["summary"]
        print(f"Service: {s['service'] or ', '.join(s['services']) or '-'}  Window: {s['window_start']} .. {s['window_end']}")
        for name, val in result["metrics"].items():
            print(f"  {name} [{CATEGORIES[name]}]: {json.dumps(val)}")
        for f in result["findings"]:
            print(f"{f['severity'].upper():8} {f['id']:<14} {f['rule']:<22} {f['message']}")
        print("\nCautions (DORA common pitfalls):")
        for c in CAUTIONS:
            print(f"  - {c}")
        print(f"\n{'FAIL' if failed else 'PASS'}: {s['errors']} errors, {s['warnings']} warnings")
        print("Scope: descriptive metrics for one service's improvement; not targets, benchmarks or team comparisons.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
