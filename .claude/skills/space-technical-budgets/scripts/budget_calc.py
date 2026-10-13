#!/usr/bin/env python3
"""Roll up engineering budgets (mass, power, energy, data, ...) with maturity-based contingency and
check system margin against a user/project-supplied margin policy. Optional TPM trend analysis over
several dated snapshots of the same budget.

Usage:
  budget_calc.py budget.csv --policy policy.json [--json]
  budget_calc.py --policy policy.json --snapshot 2026-03-01=a.csv --snapshot 2026-06-01=b.csv
                 [--project-to 2027-01-15 | --horizon-days 180] [--json]

Budget CSV columns: item_id, parent, budget, unit, cbe, maturity, quantity, mode, notes.
Rows that are referenced as a parent are header (group) rows: their own cbe is ignored.
Leaf rows contribute quantity * cbe; contingency = that * contingency_percent[maturity] / 100.
Predicted value = CBE + contingency. Margin = allocation - predicted, expressed as a percentage of
the allocation (margin_basis "allocation", default) or of the predicted value ("predicted").

Exit codes: 0 no blocking findings, 1 blocking findings, 2 unreadable input or invalid policy.

Scope: arithmetic and consistency check of the numbers supplied. The margin policy is the
programme's own; nothing here is taken from ECSS or NASA. Results are analysis aids, not a sign-off.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

REQUIRED_COLUMNS = ["item_id", "parent", "budget", "unit", "cbe", "maturity", "quantity", "mode", "notes"]
ALL_MODES = {"", "all", "*"}

# Unit conversion factors to a dimension's base unit. Data uses decimal prefixes (1 kbit = 1000 bit).
UNIT_TABLE: dict[str, dict[str, float]] = {
    "mass": {"kg": 1.0, "g": 1e-3, "mg": 1e-6},
    "power": {"W": 1.0, "mW": 1e-3, "kW": 1e3},
    "energy": {"Wh": 1.0, "kWh": 1e3, "mWh": 1e-3, "J": 1 / 3600, "kJ": 1 / 3.6},
    "data": {"bit": 1.0, "kbit": 1e3, "Mbit": 1e6, "Gbit": 1e9, "Tbit": 1e12,
             "B": 8.0, "kB": 8e3, "MB": 8e6, "GB": 8e9, "TB": 8e12},
    "rate": {"bps": 1.0, "kbps": 1e3, "Mbps": 1e6, "Gbps": 1e9},
    "time": {"s": 1.0, "ms": 1e-3, "us": 1e-6, "min": 60.0, "h": 3600.0},
    "angle": {"rad": 1.0, "mrad": 1e-3, "urad": 1e-6, "deg": math.pi / 180,
              "arcmin": math.pi / 10800, "arcsec": math.pi / 648000},
}
SCOPE = ("Scope: arithmetic/consistency check against the supplied margin policy only; margins are "
         "proposals until the programme signs them off; not an engineering sign-off.")


class PolicyError(ValueError):
    """Invalid margin policy (exit 2)."""


def _finding(fid: str, severity: str, rule: str, message: str) -> dict:
    return {"id": fid, "severity": severity, "rule": rule, "message": message}


def unit_factor(src: str, dst: str) -> float | None:
    """Factor converting a value in `src` to `dst`, or None if not convertible."""
    if src == dst:
        return 1.0
    for table in UNIT_TABLE.values():
        if src in table and dst in table:
            return table[src] / table[dst]
    return None


# ----------------------------------------------------------------------------- policy
def validate_policy(policy: dict) -> dict:
    if not isinstance(policy, dict):
        raise PolicyError("policy must be a JSON object")
    cont = policy.get("contingency_percent")
    if not isinstance(cont, dict) or not cont:
        raise PolicyError("policy.contingency_percent must map maturity -> percent")
    for k, v in cont.items():
        if not isinstance(v, (int, float)) or isinstance(v, bool) or v < 0 or not math.isfinite(v):
            raise PolicyError(f"contingency_percent[{k}] must be a non-negative number")
    budgets = policy.get("budgets")
    if not isinstance(budgets, dict) or not budgets:
        raise PolicyError("policy.budgets must map budget name -> settings")
    basis = policy.get("margin_basis", "allocation")
    if basis not in ("allocation", "predicted"):
        raise PolicyError("margin_basis must be 'allocation' or 'predicted'")
    for name, b in budgets.items():
        if not isinstance(b, dict) or not isinstance(b.get("unit"), str) or not b["unit"]:
            raise PolicyError(f"budgets.{name}.unit is required")
        req = b.get("required_system_margin_percent", policy.get("required_system_margin_percent"))
        if not isinstance(req, (int, float)) or isinstance(req, bool) or req < 0:
            raise PolicyError(f"budgets.{name}: required_system_margin_percent must be a non-negative number")
        if b.get("combine", "sum") not in ("sum", "rss"):
            raise PolicyError(f"budgets.{name}.combine must be 'sum' or 'rss'")
        allocs = []
        if "allocation" in b:
            allocs.append(b["allocation"])
        if "allocation_by_mode" in b:
            if not isinstance(b["allocation_by_mode"], dict) or not b["allocation_by_mode"]:
                raise PolicyError(f"budgets.{name}.allocation_by_mode must be a non-empty object")
            allocs.extend(b["allocation_by_mode"].values())
        for a in allocs:
            if not isinstance(a, (int, float)) or isinstance(a, bool) or a <= 0 or not math.isfinite(a):
                raise PolicyError(f"budgets.{name}: allocations must be positive numbers")
        for k, v in (b.get("contingency_percent") or {}).items():
            if not isinstance(v, (int, float)) or isinstance(v, bool) or v < 0:
                raise PolicyError(f"budgets.{name}.contingency_percent[{k}] must be non-negative")
    return policy


# ----------------------------------------------------------------------------- reading
def read_rows(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        rows = [{(k or "").strip(): (v or "").strip() for k, v in r.items() if k is not None}
                for r in reader]
        return [c.strip() for c in (reader.fieldnames or [])], rows


def _num(text: str) -> float | None:
    try:
        v = float(text)
    except ValueError:
        return None
    return v if math.isfinite(v) else None


# ----------------------------------------------------------------------------- core
def evaluate(columns: list[str], rows: list[dict], policy: dict) -> dict:
    """Evaluate one budget snapshot. Pure function; policy must already be validated."""
    findings: list[dict] = []
    missing = [c for c in REQUIRED_COLUMNS if c not in columns]
    if missing:
        findings.append(_finding("-", "error", "missing-columns", f"missing columns: {', '.join(missing)}"))
        return _result(findings, [], [], policy, len(rows))
    if not rows:
        findings.append(_finding("-", "error", "empty-budget", "budget file has no rows"))
        return _result(findings, [], [], policy, 0)

    budgets_cfg: dict = policy["budgets"]
    basis = policy.get("margin_basis", "allocation")
    ids = [r["item_id"] for r in rows]
    counts = Counter(ids)
    by_id = {r["item_id"]: r for r in rows if r["item_id"]}
    children: dict[str, list[str]] = defaultdict(list)
    for r in rows:
        if r["parent"]:
            children[r["parent"]].append(r["item_id"])

    for r in rows:
        rid = r["item_id"] or "<blank>"
        if not r["item_id"]:
            findings.append(_finding(rid, "error", "blank-id", "row has no item_id"))
        elif counts[r["item_id"]] > 1:
            findings.append(_finding(rid, "error", "duplicate-id", f"item_id used {counts[r['item_id']]} times"))
        if r["parent"] and r["parent"] not in by_id:
            findings.append(_finding(rid, "error", "unknown-parent", f"parent '{r['parent']}' is not an item_id"))
        if r["parent"] and r["parent"] == r["item_id"]:
            findings.append(_finding(rid, "error", "self-parent", "item lists itself as parent"))

    # cycle detection on parent links
    def ancestors(iid: str) -> list[str] | None:
        out, seen, cur = [], {iid}, by_id.get(iid, {}).get("parent", "")
        while cur and cur in by_id:
            if cur in seen:
                return None
            out.append(cur)
            seen.add(cur)
            cur = by_id[cur]["parent"]
        return out

    leaves: list[dict] = []
    for r in rows:
        rid = r["item_id"] or "<blank>"
        if not r["item_id"] or counts[r["item_id"]] > 1:
            continue
        anc = ancestors(r["item_id"])
        if anc is None:
            findings.append(_finding(rid, "error", "trace-cycle", "parent chain contains a cycle"))
            continue
        if r["item_id"] in children:  # header row
            if r["cbe"]:
                findings.append(_finding(rid, "warning", "header-cbe-ignored",
                                         "row has children; its own cbe is ignored to avoid double counting"))
            if r["quantity"] and _num(r["quantity"]) != 1:
                findings.append(_finding(rid, "warning", "header-quantity-ignored",
                                         "quantity on a header row is not applied to its children"))
            continue
        budget = r["budget"]
        if not budget:
            findings.append(_finding(rid, "error", "missing-budget", "leaf item has no budget name"))
            continue
        if budget not in budgets_cfg:
            findings.append(_finding(rid, "error", "budget-not-in-policy",
                                     f"budget '{budget}' has no entry in the margin policy"))
            continue
        cfg = budgets_cfg[budget]
        for a in anc:
            ab = by_id[a]["budget"]
            if ab and ab != budget:
                findings.append(_finding(rid, "error", "parent-budget-mismatch",
                                         f"ancestor '{a}' is budget '{ab}', item is '{budget}'"))
        cbe = _num(r["cbe"])
        if r["cbe"] == "":
            findings.append(_finding(rid, "error", "missing-cbe", "leaf item has no current best estimate"))
            continue
        if cbe is None:
            findings.append(_finding(rid, "error", "bad-number", f"cbe '{r['cbe']}' is not a number"))
            continue
        if cbe < 0:
            findings.append(_finding(rid, "error", "negative-cbe",
                                     "negative cbe; model credits (e.g. generation) as allocations, not items"))
            continue
        if not r["quantity"]:
            findings.append(_finding(rid, "warning", "missing-quantity", "no quantity; assumed 1 — confirm"))
            qty = 1.0
        else:
            qty = _num(r["quantity"])
            if qty is None or qty < 0:
                findings.append(_finding(rid, "error", "bad-quantity", f"quantity '{r['quantity']}' invalid"))
                continue
            if qty == 0:
                findings.append(_finding(rid, "info", "zero-quantity", "quantity is 0; item contributes nothing"))
        unit = r["unit"]
        factor = unit_factor(unit, cfg["unit"]) if unit else None
        if not unit:
            findings.append(_finding(rid, "error", "missing-unit", "item has no unit"))
            continue
        if factor is None:
            findings.append(_finding(rid, "error", "unit-mismatch",
                                     f"unit '{unit}' cannot be converted to budget unit '{cfg['unit']}'"))
            continue
        if factor != 1.0:
            findings.append(_finding(rid, "info", "unit-converted", f"{unit} converted to {cfg['unit']}"))
        maturity = r["maturity"].lower()
        cont_table = {**policy["contingency_percent"], **(cfg.get("contingency_percent") or {})}
        if not maturity:
            findings.append(_finding(rid, "error", "missing-maturity",
                                     "no maturity; contingency cannot be assigned"))
            continue
        if maturity not in cont_table:
            findings.append(_finding(rid, "error", "unknown-maturity",
                                     f"maturity '{maturity}' not in policy {sorted(cont_table)}"))
            continue
        value = cbe * qty * factor
        pct = float(cont_table[maturity])
        leaves.append({"item_id": r["item_id"], "budget": budget, "mode": r["mode"].strip(),
                       "cbe": value, "contingency": value * pct / 100.0, "contingency_percent": pct,
                       "ancestors": anc})

    # ---- roll-ups per node (header rows) per budget/mode
    def combine(vals: list[float], how: str) -> float:
        return math.sqrt(sum(v * v for v in vals)) if how == "rss" else sum(vals)

    node_acc: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for lf in leaves:
        for a in lf["ancestors"]:
            node_acc[(a, lf["budget"], lf["mode"] or "all")].append(lf)
    rollup = []
    for (node, budget, mode), items in sorted(node_acc.items()):
        how = budgets_cfg[budget].get("combine", "sum")
        cbe_t = combine([i["cbe"] for i in items], how)
        pred_t = combine([i["cbe"] + i["contingency"] for i in items], how)
        rollup.append({"node": node, "budget": budget, "mode": mode, "unit": budgets_cfg[budget]["unit"],
                       "cbe": _r(cbe_t), "contingency": _r(pred_t - cbe_t), "predicted": _r(pred_t),
                       "items": len(items)})

    # ---- budget-level totals vs allocation
    totals = []
    for budget, cfg in budgets_cfg.items():
        mine = [lf for lf in leaves if lf["budget"] == budget]
        how = cfg.get("combine", "sum")
        req = float(cfg.get("required_system_margin_percent", policy.get("required_system_margin_percent", 0)))
        by_mode = cfg.get("allocation_by_mode")
        named = sorted({lf["mode"] for lf in mine if lf["mode"].lower() not in ALL_MODES})
        if by_mode:
            modes = list(by_mode)
            for m in named:
                if m not in by_mode:
                    findings.append(_finding(budget, "error", "unknown-mode",
                                             f"mode '{m}' used by items but has no allocation"))
        else:
            modes = named or ["all"]
        if not mine:
            findings.append(_finding(budget, "info", "budget-empty", "policy budget has no items"))
            continue
        for mode in modes:
            items = [lf for lf in mine if lf["mode"] == mode or lf["mode"].lower() in ALL_MODES]
            cbe_t = combine([i["cbe"] for i in items], how)
            pred_t = combine([i["cbe"] + i["contingency"] for i in items], how)
            alloc = (by_mode or {}).get(mode, cfg.get("allocation"))
            entry = {"budget": budget, "mode": mode, "unit": cfg["unit"], "combine": how,
                     "items": len(items), "cbe": _r(cbe_t), "contingency": _r(pred_t - cbe_t),
                     "predicted": _r(pred_t), "allocation": alloc, "margin": None,
                     "margin_percent": None, "margin_basis": basis,
                     "required_margin_percent": req, "status": "no-allocation"}
            tag = f"{budget}/{mode}"
            if alloc is None:
                findings.append(_finding(tag, "warning", "no-allocation",
                                         "no allocation/limit in policy; margin not computed"))
            else:
                margin = alloc - pred_t
                denom = alloc if basis == "allocation" else pred_t
                mpct = (margin / denom * 100.0) if denom > 0 else None
                entry.update(margin=_r(margin), margin_percent=_r(mpct) if mpct is not None else None)
                if margin < 0:
                    entry["status"] = "negative-margin"
                    findings.append(_finding(tag, "error", "negative-margin",
                                             f"predicted {_r(pred_t)} {cfg['unit']} exceeds allocation {alloc}"))
                elif mpct is not None and mpct < req:
                    entry["status"] = "below-policy"
                    findings.append(_finding(tag, "error", "margin-below-policy",
                                             f"margin {_r(mpct)}% < policy {req}% ({basis} basis)"))
                else:
                    entry["status"] = "within-policy"
            totals.append(entry)
    return _result(findings, totals, rollup, policy, len(rows))


def _r(x: float | None, nd: int = 6) -> float | None:
    return None if x is None else round(x, nd)


def _result(findings, totals, rollup, policy, n_rows) -> dict:
    sev = Counter(f["severity"] for f in findings)
    if policy.get("is_example"):
        findings.append(_finding("policy", "warning", "example-policy-in-use",
                                 "policy is marked as example values; replace with your programme's policy"))
        sev["warning"] += 1
    return {"policy_label": policy.get("label", ""), "totals": totals, "rollup": rollup,
            "findings": findings,
            "summary": {"rows": n_rows, "errors": sev.get("error", 0), "warnings": sev.get("warning", 0),
                        "info": sev.get("info", 0)}}


# ----------------------------------------------------------------------------- TPM trend
def linear_fit(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """Least-squares slope and intercept. Requires >= 2 distinct x."""
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        raise ValueError("snapshots need at least two distinct dates")
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    return slope, my - slope * mx


def trend(snapshots: list[tuple[date, dict]], project_to: date) -> tuple[list[dict], list[dict]]:
    """Project predicted totals per budget/mode to `project_to` from dated snapshot results."""
    series: dict[tuple[str, str], list[tuple[date, dict]]] = defaultdict(list)
    for d, res in snapshots:
        for t in res["totals"]:
            series[(t["budget"], t["mode"])].append((d, t))
    out, findings = [], []
    d0 = min(d for d, _ in snapshots)
    for (budget, mode), pts in sorted(series.items()):
        if len({d for d, _ in pts}) < 2:
            continue
        xs = [(d - d0).days for d, _ in pts]
        ys = [t["predicted"] for _, t in pts]
        slope, icpt = linear_fit(xs, ys)
        last = pts[-1][1]
        xp = (project_to - d0).days
        proj = slope * xp + icpt
        entry = {"budget": budget, "mode": mode, "unit": last["unit"],
                 "points": [{"date": d.isoformat(), "predicted": t["predicted"]} for d, t in pts],
                 "slope_per_day": _r(slope, 9), "project_to": project_to.isoformat(),
                 "projected_predicted": _r(proj), "allocation": last["allocation"],
                 "projected_breach_date": None}
        alloc = last["allocation"]
        tag = f"{budget}/{mode}"
        if alloc is not None:
            req = last["required_margin_percent"]
            limit = alloc * (1 - req / 100.0) if last["margin_basis"] == "allocation" else alloc / (1 + req / 100.0)
            entry["policy_limit"] = _r(limit)
            if slope > 0:
                x_breach = (alloc - icpt) / slope
                entry["projected_breach_date"] = (d0 + timedelta(days=math.ceil(x_breach))).isoformat()
            if proj > alloc:
                findings.append(_finding(tag, "warning", "trend-projects-breach",
                                         f"trend projects {_r(proj)} {last['unit']} > allocation {alloc} "
                                         f"by {project_to.isoformat()}"))
            elif proj > limit:
                findings.append(_finding(tag, "warning", "trend-projects-margin-shortfall",
                                         f"trend projects margin below policy by {project_to.isoformat()}"))
        out.append(entry)
    return out, findings


# ----------------------------------------------------------------------------- CLI
def _parse_date(text: str) -> date:
    return date.fromisoformat(text)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Engineering budget roll-up with contingency and margin policy.")
    ap.add_argument("csv", nargs="?", type=Path, help="budget CSV (single snapshot)")
    ap.add_argument("--policy", type=Path, required=True, help="margin policy JSON (programme-supplied)")
    ap.add_argument("--snapshot", action="append", default=[], metavar="YYYY-MM-DD=CSV",
                    help="dated snapshot for TPM trend (repeat; latest is evaluated in full)")
    ap.add_argument("--project-to", help="date to project the TPM trend to (default: last snapshot + horizon)")
    ap.add_argument("--horizon-days", type=int, default=180)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if not args.csv and not args.snapshot:
        print("give a budget CSV or at least one --snapshot", file=sys.stderr)
        return 2
    if args.csv and args.snapshot:
        print("give either a budget CSV or --snapshot entries, not both", file=sys.stderr)
        return 2
    try:
        policy = validate_policy(json.loads(args.policy.read_text(encoding="utf-8")))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, PolicyError) as exc:
        print(f"invalid policy {args.policy}: {exc}", file=sys.stderr)
        return 2
    snaps: list[tuple[date, Path]] = []
    try:
        for s in args.snapshot:
            d, _, p = s.partition("=")
            if not p:
                raise ValueError(f"snapshot '{s}' must be YYYY-MM-DD=path")
            snaps.append((_parse_date(d), Path(p)))
        project_to = _parse_date(args.project_to) if args.project_to else None
    except ValueError as exc:
        print(f"bad argument: {exc}", file=sys.stderr)
        return 2
    if args.csv:
        snaps = [(date.min, args.csv)]
    snaps.sort(key=lambda t: t[0])
    results: list[tuple[date, dict]] = []
    for d, p in snaps:
        try:
            cols, rows = read_rows(p)
        except (OSError, UnicodeDecodeError, csv.Error) as exc:
            print(f"cannot read {p}: {exc}", file=sys.stderr)
            return 2
        results.append((d, evaluate(cols, rows, policy)))
    latest = results[-1][1]
    if len(results) > 1:
        if project_to is None:
            project_to = results[-1][0] + timedelta(days=args.horizon_days)
        try:
            tr, tf = trend(results, project_to)
        except ValueError as exc:
            print(f"trend: {exc}", file=sys.stderr)
            return 2
        latest["trend"] = tr
        latest["findings"].extend(tf)
        latest["summary"]["warnings"] += sum(1 for f in tf if f["severity"] == "warning")
        latest["summary"]["snapshots"] = len(results)
        latest["summary"]["evaluated_snapshot"] = results[-1][0].isoformat()
    failed = latest["summary"]["errors"] > 0
    latest["passed"] = not failed
    latest["scope"] = SCOPE
    if args.json:
        print(json.dumps(latest, indent=2))
    else:
        if latest["policy_label"]:
            print(f"Policy: {latest['policy_label']}")
        for t in latest["totals"]:
            mp = "n/a" if t["margin_percent"] is None else f"{t['margin_percent']:.2f}%"
            print(f"{t['budget']:<8} {t['mode']:<12} CBE {t['cbe']:.4g} + cont {t['contingency']:.4g} = "
                  f"{t['predicted']:.4g} {t['unit']} | alloc {t['allocation']} | margin {mp} "
                  f"(req {t['required_margin_percent']}%) {t['status']}")
        for t in latest.get("trend", []):
            print(f"TREND {t['budget']}/{t['mode']}: slope {t['slope_per_day']}/day -> "
                  f"{t['projected_predicted']} {t['unit']} at {t['project_to']}; breach {t['projected_breach_date']}")
        for f in latest["findings"]:
            print(f"{f['severity'].upper():8} {f['id']:<18} {f['rule']:<30} {f['message']}")
        print(f"\n{'FAIL' if failed else 'PASS'}: {latest['summary']}")
        print(SCOPE)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
