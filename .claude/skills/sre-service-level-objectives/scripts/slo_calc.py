#!/usr/bin/env python3
"""SLO calculator: SLI, error budget, burn rate, multi-window multi-burn-rate alerts, SLO spec checks.

Subcommands:
  sli       --good N --total N [--target T]
  budget    --target T --window-days D [--total-events N] [--bad-events N] [--bad-minutes M] [--elapsed-days E]
  alerts    --policy policy.json --observations obs.json
  validate  spec.json
Targets may be given as a fraction (0.999) or a percentage (99.9).

Maths (generic): error budget = 1 - target; allowed bad minutes = (1 - target) x window minutes;
burn rate = observed error rate / (1 - target); an alert fires when the burn rate over BOTH its long
and short windows is >= its threshold; budget spent before it fires = threshold x long / SLO window.

Exit codes: 0 ok (no alert firing / spec valid), 1 alert firing or spec errors, 2 invalid input.
Add --json for machine-readable output.

Scope: arithmetic and structure only. Choosing SLIs, targets and alert thresholds that reflect user
happiness is a product and engineering decision.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DURATION = re.compile(r"^(\d+(?:\.\d+)?)\s*([smhdw])$")
UNIT_MIN = {"s": 1 / 60, "m": 1, "h": 60, "d": 1440, "w": 10080}
WINDOW = re.compile(r"^(\d+)\s*([dw])(\s+(rolling|calendar))?$", re.I)


class InputError(ValueError):
    pass


def _finding(fid: str, severity: str, rule: str, message: str) -> dict:
    return {"id": fid, "severity": severity, "rule": rule, "message": message}


def norm_target(t: float) -> float:
    t = float(t)
    if t > 1:
        t = t / 100.0
    if not 0 < t < 1:
        raise InputError("target must be between 0 and 1 (or 0-100 %), exclusive; 100% leaves no error budget")
    return round(t, 12)


def minutes(duration: str) -> float:
    m = DURATION.match(str(duration).strip())
    if not m:
        raise InputError(f"bad duration '{duration}' (use e.g. 5m, 1h, 3d)")
    return float(m.group(1)) * UNIT_MIN[m.group(2)]


def sli(good: float, total: float) -> float:
    if total <= 0:
        raise InputError("total events must be > 0")
    if good < 0 or good > total:
        raise InputError("good events must be between 0 and total")
    return good / total


def budget(target: float, window_days: float, total_events: float | None = None, bad_events: float | None = None,
           bad_minutes: float | None = None, elapsed_days: float | None = None) -> dict:
    t = norm_target(target)
    if window_days <= 0:
        raise InputError("window must be > 0 days")
    frac = 1 - t
    win_min = window_days * 1440
    out: dict = {"target": t, "window_days": window_days, "error_budget_fraction": round(frac, 10),
                 "allowed_bad_minutes": round(frac * win_min, 6)}
    consumed = None
    if total_events is not None:
        if total_events < 0:
            raise InputError("total events must be >= 0")
        out["allowed_bad_events"] = round(frac * total_events, 6)
        if bad_events is not None:
            if bad_events < 0 or bad_events > total_events:
                raise InputError("bad events must be between 0 and total events")
            consumed = bad_events / (frac * total_events) if total_events else 0.0
            out["bad_events"] = bad_events
            out["remaining_bad_events"] = round(frac * total_events - bad_events, 6)
    elif bad_events is not None:
        raise InputError("--bad-events needs --total-events")
    if bad_minutes is not None and bad_events is not None:
        raise InputError("give either bad events or bad minutes, not both (they measure the budget differently)")
    if bad_minutes is not None:
        if bad_minutes < 0:
            raise InputError("bad minutes must be >= 0")
        consumed = bad_minutes / (frac * win_min)
        out["bad_minutes"] = bad_minutes
        out["remaining_bad_minutes"] = round(frac * win_min - bad_minutes, 6)
    if consumed is not None:
        out["budget_consumed"] = round(consumed, 6)
        out["budget_remaining"] = round(1 - consumed, 6)
        out["budget_exhausted"] = round(consumed, 9) >= 1
        if elapsed_days is not None:
            if not 0 < elapsed_days <= window_days:
                raise InputError("elapsed days must be in (0, window]")
            out["average_burn_rate"] = round(consumed / (elapsed_days / window_days), 6)
    return out


def burn_rate(error_rate: float, target: float) -> float:
    return error_rate / (1 - norm_target(target))


def _error_rate(obs: dict) -> float:
    if "error_rate" in obs:
        er = float(obs["error_rate"])
        if not 0 <= er <= 1:
            raise InputError("error_rate must be within [0, 1]")
        return er
    good, total = obs.get("good"), obs.get("total")
    if total is None or good is None:
        raise InputError("observation needs error_rate or good+total")
    return 1 - sli(float(good), float(total))


def evaluate_alerts(policy: dict, observations: dict) -> dict:
    t = norm_target(policy["target"])
    period = float(policy.get("slo_window_days", 30)) * 1440
    results = []
    for a in policy.get("alerts", []):
        long_w, short_w, thr = a["long_window"], a["short_window"], float(a["burn_rate"])
        if thr <= 0:
            raise InputError(f"alert {a.get('name')}: burn_rate must be > 0")
        if minutes(short_w) >= minutes(long_w):
            raise InputError(f"alert {a.get('name')}: short window must be shorter than long window")
        for w in (long_w, short_w):
            if w not in observations:
                raise InputError(f"no observation for window '{w}' (alert {a.get('name')})")
        bl = burn_rate(_error_rate(observations[long_w]), t)
        bs = burn_rate(_error_rate(observations[short_w]), t)
        results.append({"name": a.get("name"), "severity": a.get("severity", "page"), "long_window": long_w,
                        "short_window": short_w, "threshold": thr, "burn_long": round(bl, 4),
                        "burn_short": round(bs, 4), "firing": bl >= thr - EPS and bs >= thr - EPS,
                        "budget_spent_at_detection": round(thr * minutes(long_w) / period, 6)})
    return {"target": t, "alerts": results, "firing": [r["name"] for r in results if r["firing"]]}


EPS = 1e-9  # tolerance so a burn rate exactly at the threshold fires despite float rounding


def validate_spec(spec: dict) -> dict:
    findings: list[dict] = []
    add = lambda *a: findings.append(_finding(*a))  # noqa: E731
    sid = str(spec.get("name") or spec.get("service") or "-")
    for key in ("service", "user_journey", "sli", "target", "window", "owner", "exclusion_policy", "alerting_policy"):
        if spec.get(key) in (None, "", {}, []):
            add(sid, "error", "missing-field", f"'{key}' missing or empty")
    sli_def = spec.get("sli") or {}
    if isinstance(sli_def, dict) and sli_def:
        for k in ("good_events", "valid_events", "measurement"):
            if not sli_def.get(k):
                add(sid, "error", "sli-incomplete", f"sli.{k} missing: define good and valid events and where measured")
    t = None
    if spec.get("target") not in (None, ""):
        try:
            t = norm_target(spec["target"])
        except (InputError, TypeError, ValueError):
            add(sid, "error", "target-range", f"target {spec.get('target')} must be < 100% and > 0")
        if t is not None and t < 0.9:
            add(sid, "warning", "low-target", f"target {t} is below 90%; confirm it reflects user expectations")
    wdays = None
    if spec.get("window"):
        m = WINDOW.match(str(spec["window"]).strip())
        if not m:
            add(sid, "error", "window-format", "window must look like '28d rolling', '30d', '4w calendar'")
        else:
            wdays = int(m.group(1)) * (7 if m.group(2).lower() == "w" else 1)
            if not m.group(3):
                add(sid, "info", "window-type", "say whether the window is rolling or calendar")
    ap = spec.get("alerting_policy")
    if isinstance(ap, dict):
        alerts = ap.get("alerts") or []
        if not alerts and not ap.get("ref"):
            add(sid, "error", "alerting-empty", "alerting_policy needs alerts or a ref to the alert config")
        if alerts and not any(a.get("severity") == "page" for a in alerts):
            add(sid, "warning", "no-paging-alert", "no page-severity alert: fast budget burn may go unnoticed")
        for a in alerts:
            name = str(a.get("name", "?"))
            try:
                lm, sm, thr = minutes(a["long_window"]), minutes(a["short_window"]), float(a["burn_rate"])
            except (KeyError, InputError, TypeError, ValueError) as exc:
                add(name, "error", "alert-definition", f"alert needs long_window, short_window, burn_rate ({exc})")
                continue
            if sm >= lm:
                add(name, "error", "alert-windows", "short window must be shorter than long window")
            if thr <= 0:
                add(name, "error", "alert-threshold", "burn_rate must be > 0")
            elif wdays and thr * lm / (wdays * 1440) > 1:
                add(name, "warning", "alert-after-exhaustion",
                    "threshold x long window exceeds the whole budget: alert fires only after exhaustion")
    if not spec.get("error_budget_policy"):
        add(sid, "warning", "no-error-budget-policy", "state what happens when the budget is exhausted")
    sev = {s: sum(1 for f in findings if f["severity"] == s) for s in ("error", "warning", "info")}
    summary = {"service": spec.get("service"), "target": t, "window_days": wdays,
               "allowed_bad_minutes": round((1 - t) * wdays * 1440, 4) if t and wdays else None,
               "errors": sev["error"], "warnings": sev["warning"], "info": sev["info"]}
    return {"findings": findings, "summary": summary}


def _load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise InputError(f"{path} must contain a JSON object")
    return data


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="SLO / error budget / burn-rate calculator.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("sli")
    p.add_argument("--good", type=float, required=True)
    p.add_argument("--total", type=float, required=True)
    p.add_argument("--target", type=float)
    p = sub.add_parser("budget")
    p.add_argument("--target", type=float, required=True)
    p.add_argument("--window-days", type=float, required=True)
    p.add_argument("--total-events", type=float)
    p.add_argument("--bad-events", type=float)
    p.add_argument("--bad-minutes", type=float)
    p.add_argument("--elapsed-days", type=float)
    p = sub.add_parser("alerts")
    p.add_argument("--policy", type=Path, required=True)
    p.add_argument("--observations", type=Path, required=True)
    p = sub.add_parser("validate")
    p.add_argument("spec", type=Path)
    for sp in sub.choices.values():
        sp.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    code = 0
    try:
        if args.cmd == "sli":
            val = sli(args.good, args.total)
            out = {"sli": round(val, 10), "good": args.good, "total": args.total}
            if args.target is not None:
                t = norm_target(args.target)
                out.update(target=t, meets_target=val >= t, burn_rate=round((1 - val) / (1 - t), 6))
        elif args.cmd == "budget":
            out = budget(args.target, args.window_days, args.total_events, args.bad_events, args.bad_minutes,
                         args.elapsed_days)
        elif args.cmd == "alerts":
            out = evaluate_alerts(_load(args.policy), _load(args.observations))
            code = 1 if out["firing"] else 0
        else:
            out = validate_spec(_load(args.spec))
            out["passed"] = out["summary"]["errors"] == 0
            code = 0 if out["passed"] else 1
    except (InputError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"invalid input: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        if args.cmd == "validate":
            for f in out["findings"]:
                print(f"{f['severity'].upper():8} {f['id']:<22} {f['rule']:<26} {f['message']}")
            print(f"\n{'PASS' if code == 0 else 'FAIL'}: {out['summary']}")
        elif args.cmd == "alerts":
            for r in out["alerts"]:
                state = "FIRING" if r["firing"] else "ok"
                print(f"{state:7} {r['name']:<24} {r['severity']:<7} burn {r['burn_long']}x/{r['long_window']} "
                      f"{r['burn_short']}x/{r['short_window']} (threshold {r['threshold']}x)")
        else:
            for k, v in out.items():
                print(f"{k}: {v}")
        print("Scope: SLO arithmetic/structure only; targets and thresholds are product and engineering decisions.")
    return code


if __name__ == "__main__":
    sys.exit(main())
