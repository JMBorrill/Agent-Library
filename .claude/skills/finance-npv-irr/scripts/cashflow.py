#!/usr/bin/env python3
"""Discounted cash-flow toolkit: NPV, IRR, MIRR, payback, PI, CAPM, WACC, DCF EV, sensitivity.

Input: a JSON case file (see assets/schemas/cashflow-input.schema.json) or a CSV with columns
`period,cash_flow` (rate supplied with --rate).

Conventions (stated in every output):
  * convention "t0" (default): flows[0] occurs at time 0 and is NOT discounted;
    flows[k] is discounted by (1+r)^k.
  * convention "t1": flows[0] occurs at the end of period 1 (spreadsheet NPV() convention).
  * Rates are decimals per period (0.10 = 10%).

Usage:
  cashflow.py case.json [--json] [--strict]
  cashflow.py flows.csv --rate 0.10 [--convention t0|t1] [--json]
Exit codes: 0 no error findings, 1 error findings (e.g. no IRR, g >= r), 2 unreadable/invalid input.

Scope: arithmetic decision support only. Not investment advice, not a valuation opinion and not
an approval of any project or credit.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

SCOPE = "Scope: arithmetic decision support only; not investment advice or an approval of any project."
RATE_FLOOR = -0.999999  # rates must exceed -100%
GRID_LO, GRID_HI = -0.99, 10.0


class InputError(ValueError):
    """Invalid input (maps to exit code 2)."""


# ----------------------------------------------------------------------------- validation
def _num(x, what: str = "value") -> float:
    if isinstance(x, bool) or x is None:
        raise InputError(f"{what} must be numeric, got {x!r}")
    try:
        v = float(x)
    except (TypeError, ValueError):
        raise InputError(f"{what} must be numeric, got {x!r}") from None
    if math.isnan(v) or math.isinf(v):
        raise InputError(f"{what} must be finite, got {x!r}")
    return v


def clean_flows(flows) -> list[float]:
    if not isinstance(flows, (list, tuple)) or len(flows) == 0:
        raise InputError("cash flows must be a non-empty list")
    return [_num(f, f"cash flow[{i}]") for i, f in enumerate(flows)]


def _check_rate(rate: float, what: str = "rate") -> float:
    rate = _num(rate, what)
    if rate <= -1.0:
        raise InputError(f"{what} must be greater than -100% (got {rate})")
    return rate


def _offset(convention: str) -> int:
    if convention not in ("t0", "t1"):
        raise InputError("convention must be 't0' or 't1'")
    return 0 if convention == "t0" else 1


# ----------------------------------------------------------------------------- core maths
def npv(rate: float, flows, convention: str = "t0") -> float:
    """Net present value. 't0': first flow undiscounted; 't1': first flow discounted one period."""
    rate = _check_rate(rate)
    flows = clean_flows(flows)
    off = _offset(convention)
    return sum(cf / (1.0 + rate) ** (k + off) for k, cf in enumerate(flows))


def sign_changes(flows) -> int:
    signs = [1 if f > 0 else -1 for f in flows if f != 0]
    return sum(1 for a, b in zip(signs, signs[1:]) if a != b)


def _bisect(f, lo: float, hi: float, tol: float = 1e-12, max_iter: int = 300) -> float:
    flo = f(lo)
    for _ in range(max_iter):
        mid = (lo + hi) / 2.0
        fm = f(mid)
        if fm == 0 or (hi - lo) / 2.0 < tol:
            return mid
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2.0


def _rate_grid(lo: float = GRID_LO, hi: float = GRID_HI) -> list[float]:
    pts, r = [], lo
    while r < hi:
        pts.append(round(r, 10))
        r += 0.0025 if r < 1.0 else 0.05
    pts.append(hi)
    return pts


def irr_analysis(flows) -> dict:
    """Return {'irr': float|None, 'roots': [...], 'sign_changes': n, 'status': str}.

    status: 'unique' | 'none-no-sign-change' | 'multiple-possible' | 'not-found-in-range'.
    Roots are found by scanning a rate grid in (-99%, 1000%] and bisecting each bracket, so the
    method never diverges; roots outside the grid or tangent roots (no sign change) can be missed.
    IRR is independent of the timing convention (a uniform shift does not move the roots).
    """
    flows = clean_flows(flows)
    n = sign_changes(flows)
    if n == 0:
        return {"irr": None, "roots": [], "sign_changes": 0, "status": "none-no-sign-change"}
    f = lambda r: npv(r, flows)  # noqa: E731
    grid = _rate_grid()
    roots: list[float] = []
    prev_r, prev_v = grid[0], f(grid[0])
    for r in grid[1:]:
        v = f(r)
        if prev_v == 0:
            roots.append(prev_r)
        elif (v > 0) != (prev_v > 0) and v != 0:
            roots.append(_bisect(f, prev_r, r))
        prev_r, prev_v = r, v
    if prev_v == 0:
        roots.append(prev_r)
    roots = sorted({round(x, 10) for x in roots})
    if not roots:
        return {"irr": None, "roots": [], "sign_changes": n, "status": "not-found-in-range"}
    if n == 1 and len(roots) == 1:
        return {"irr": roots[0], "roots": roots, "sign_changes": 1, "status": "unique"}
    return {"irr": roots[0] if len(roots) == 1 else None, "roots": roots, "sign_changes": n,
            "status": "multiple-possible"}


def irr(flows) -> float | None:
    """Unique IRR or None (no IRR or ambiguous). Use irr_analysis() for detail."""
    res = irr_analysis(flows)
    return res["irr"] if res["status"] == "unique" else None


def mirr(flows, finance_rate: float, reinvest_rate: float) -> float:
    """Modified IRR (t0 convention): PV of outflows at finance rate, FV of inflows at reinvest rate."""
    flows = clean_flows(flows)
    fr, rr = _check_rate(finance_rate, "finance_rate"), _check_rate(reinvest_rate, "reinvest_rate")
    n = len(flows) - 1
    if n < 1:
        raise InputError("MIRR needs at least two periods")
    pv_neg = sum(cf / (1 + fr) ** k for k, cf in enumerate(flows) if cf < 0)
    fv_pos = sum(cf * (1 + rr) ** (n - k) for k, cf in enumerate(flows) if cf > 0)
    if pv_neg == 0 or fv_pos == 0:
        raise InputError("MIRR needs at least one negative and one positive flow")
    return (fv_pos / -pv_neg) ** (1.0 / n) - 1.0


def payback(flows, rate: float | None = None) -> dict:
    """Simple (rate None) or discounted payback in periods, linearly interpolated within a period.

    Returns {'period': float|None, 'never': bool, 'reverses': bool}. 'reverses' is True when the
    cumulative position turns negative again after first recovery (later outflows).
    """
    flows = clean_flows(flows)
    if rate is not None:
        rate = _check_rate(rate)
        flows = [cf / (1 + rate) ** k for k, cf in enumerate(flows)]
    cum = 0.0
    found: float | None = None
    was_negative = False
    reverses = False
    for k, cf in enumerate(flows):
        prev = cum
        cum += cf
        if cum < 0:
            was_negative = True
            if found is not None:
                reverses = True
        elif found is None and was_negative:
            found = (k - 1) + (-prev / cf) if cf > 0 else float(k)
    if found is None and not was_negative:
        found = 0.0  # never under water
    return {"period": found, "never": found is None, "reverses": reverses}


def profitability_index(rate: float, flows) -> float:
    """PV of flows after period 0 divided by the period-0 investment (t0 convention)."""
    flows = clean_flows(flows)
    if flows[0] >= 0:
        raise InputError("profitability index needs a negative initial flow (investment) at period 0")
    if len(flows) < 2:
        raise InputError("profitability index needs future flows")
    return npv(rate, [0.0] + flows[1:]) / -flows[0]


def capm_cost_of_equity(risk_free: float, beta: float, equity_risk_premium: float) -> float:
    return _num(risk_free, "risk_free") + _num(beta, "beta") * _num(equity_risk_premium, "equity_risk_premium")


def wacc(equity_value: float, debt_value: float, cost_of_equity: float, cost_of_debt: float,
         tax_rate: float) -> float:
    e, d = _num(equity_value, "equity_value"), _num(debt_value, "debt_value")
    t = _num(tax_rate, "tax_rate")
    if e < 0 or d < 0 or e + d <= 0:
        raise InputError("equity and debt values must be non-negative with a positive total")
    if not 0.0 <= t <= 1.0:
        raise InputError("tax_rate must be between 0 and 1")
    return e / (e + d) * _num(cost_of_equity, "cost_of_equity") + d / (e + d) * _num(cost_of_debt, "cost_of_debt") * (1 - t)


def dcf_enterprise_value(fcf, rate: float, terminal_growth: float) -> dict:
    """Explicit FCFs for years 1..N (end-of-year) plus Gordon terminal value at year N."""
    fcf = clean_flows(fcf)
    r = _check_rate(rate)
    g = _num(terminal_growth, "terminal_growth")
    if g >= r:
        raise ValueError(f"terminal growth {g} must be below the discount rate {r} (Gordon model undefined)")
    n = len(fcf)
    pv_explicit = sum(cf / (1 + r) ** (k + 1) for k, cf in enumerate(fcf))
    tv = fcf[-1] * (1 + g) / (r - g)
    pv_tv = tv / (1 + r) ** n
    ev = pv_explicit + pv_tv
    return {"pv_explicit": pv_explicit, "terminal_value": tv, "pv_terminal": pv_tv,
            "enterprise_value": ev, "terminal_share": pv_tv / ev if ev else None}


# ----------------------------------------------------------------------------- sensitivity
SENS_VARS = ("rate", "inflow_scale", "outflow_scale")


def _npv_with(var: str, value: float, base_rate: float, flows: list[float], convention: str) -> float:
    if var == "rate":
        return npv(value, flows, convention)
    if var == "inflow_scale":
        return npv(base_rate, [cf * value if cf > 0 else cf for cf in flows], convention)
    if var == "outflow_scale":
        return npv(base_rate, [cf * value if cf < 0 else cf for cf in flows], convention)
    raise InputError(f"unknown sensitivity variable '{var}' (use {', '.join(SENS_VARS)})")


def sensitivity_table(var: str, values, base_rate: float, flows, convention: str = "t0") -> list[dict]:
    flows = clean_flows(flows)
    return [{"value": _num(v, var), "npv": _npv_with(var, _num(v, var), base_rate, flows, convention)}
            for v in values]


def switching_value(var: str, base_rate: float, flows, convention: str = "t0",
                    lo: float | None = None, hi: float | None = None) -> dict:
    """Value of `var` at which NPV = 0 (break-even), searched by bisection in [lo, hi]."""
    flows = clean_flows(flows)
    defaults = {"rate": (GRID_LO, GRID_HI), "inflow_scale": (0.0, 100.0), "outflow_scale": (0.0, 100.0)}
    if var not in defaults:
        raise InputError(f"unknown sensitivity variable '{var}'")
    lo = defaults[var][0] if lo is None else lo
    hi = defaults[var][1] if hi is None else hi
    base_value = base_rate if var == "rate" else 1.0
    f = lambda x: _npv_with(var, x, base_rate, flows, convention)  # noqa: E731
    flo, fhi = f(lo), f(hi)
    if flo == 0:
        sv = lo
    elif fhi == 0:
        sv = hi
    elif (flo > 0) == (fhi > 0):
        return {"variable": var, "switching_value": None, "base_value": base_value,
                "note": f"NPV does not cross zero for {var} in [{lo}, {hi}]"}
    else:
        sv = _bisect(f, lo, hi)
    change = (sv - base_value) / base_value if base_value else None
    return {"variable": var, "switching_value": sv, "base_value": base_value, "pct_change_from_base": change}


# ----------------------------------------------------------------------------- case runner
def _f(fid: str, severity: str, rule: str, message: str) -> dict:
    return {"id": fid, "severity": severity, "rule": rule, "message": message}


def analyse(case: dict) -> dict:
    """Run every analysis requested in a case dict. Raises InputError on malformed input."""
    if not isinstance(case, dict):
        raise InputError("case must be a JSON object")
    findings: list[dict] = []
    results: dict = {}
    convention = case.get("convention", "t0")
    _offset(convention)
    assumptions = {"convention": convention,
                   "convention_meaning": ("flows[0] at time 0, undiscounted" if convention == "t0"
                                          else "flows[0] at end of period 1"),
                   "currency": case.get("currency", "unspecified"),
                   "price_basis": case.get("price_basis", "unspecified")}
    if case.get("price_basis") not in ("nominal", "real"):
        findings.append(_f("case", "warning", "price-basis-unstated",
                           "state whether flows and rate are nominal or real; mixing them misstates NPV"))

    # cost of capital helpers
    if "capm" in case:
        c = case["capm"]
        results["capm_cost_of_equity"] = capm_cost_of_equity(c.get("risk_free"), c.get("beta"),
                                                             c.get("equity_risk_premium"))
    if "wacc" in case:
        w = case["wacc"]
        ke = w.get("cost_of_equity")
        if ke == "capm":
            if "capm_cost_of_equity" not in results:
                raise InputError("wacc.cost_of_equity='capm' requires a capm block")
            ke = results["capm_cost_of_equity"]
        results["wacc"] = wacc(w.get("equity_value"), w.get("debt_value"), ke, w.get("cost_of_debt"),
                               w.get("tax_rate"))

    rate = case.get("rate")
    if rate == "wacc":
        if "wacc" not in results:
            raise InputError("rate='wacc' requires a wacc block")
        rate = results["wacc"]
    flows = case.get("flows")
    if flows is not None:
        flows = clean_flows(flows)
        if rate is None:
            raise InputError("a discount rate is required (case 'rate' or --rate)")
        rate = _check_rate(rate)
        results["rate_used"] = rate
        if all(f == 0 for f in flows):
            findings.append(_f("flows", "warning", "all-zero-flows", "every cash flow is zero; metrics are trivial"))
        results["npv"] = npv(rate, flows, convention)
        ia = irr_analysis(flows)
        results["irr"] = ia
        if ia["status"] == "none-no-sign-change":
            findings.append(_f("flows", "error", "no-irr",
                               "cash flows never change sign, so no IRR exists; use NPV"))
        elif ia["status"] == "not-found-in-range":
            findings.append(_f("flows", "error", "irr-not-found",
                               f"no root found for rates in ({GRID_LO}, {GRID_HI}]"))
        elif ia["status"] == "multiple-possible":
            findings.append(_f("flows", "warning", "multiple-irr",
                               f"{ia['sign_changes']} sign changes; roots found {ia['roots']} - IRR is "
                               "ambiguous, decide on NPV (and MIRR)"))
        fr = case.get("finance_rate", rate)
        rr = case.get("reinvest_rate", rate)
        try:
            results["mirr"] = mirr(flows, fr, rr)
        except InputError as exc:
            results["mirr"] = None
            findings.append(_f("flows", "info", "mirr-undefined", str(exc)))
        sp = payback(flows)
        dp = payback(flows, rate)
        results["payback_simple"] = sp
        results["payback_discounted"] = dp
        for label, pb in (("simple", sp), ("discounted", dp)):
            if pb["never"]:
                findings.append(_f("flows", "info", f"payback-{label}-never",
                                   f"{label} payback never reached within the horizon"))
            if pb["reverses"]:
                findings.append(_f("flows", "warning", "payback-reversal",
                                   f"cumulative {label} position turns negative again after payback"))
        try:
            results["profitability_index"] = profitability_index(rate, flows)
        except InputError as exc:
            results["profitability_index"] = None
            findings.append(_f("flows", "info", "pi-undefined", str(exc)))
        sens = case.get("sensitivity", {}) or {}
        results["sensitivity"] = {var: sensitivity_table(var, vals, rate, flows, convention)
                                  for var, vals in sens.items()}
        results["switching_values"] = [switching_value(v, rate, flows, convention)
                                       for v in case.get("breakeven", [])]

    if "dcf" in case:
        d = case["dcf"]
        drate = d.get("rate", rate)
        if drate == "wacc":
            drate = results.get("wacc")
        if drate is None:
            raise InputError("dcf needs a rate")
        try:
            results["dcf"] = dcf_enterprise_value(d.get("fcf"), drate, d.get("terminal_growth"))
            share = results["dcf"]["terminal_share"]
            if share is not None and share > 0.75:
                findings.append(_f("dcf", "warning", "terminal-value-dominates",
                                   f"terminal value is {share:.0%} of EV; test growth and rate assumptions"))
        except InputError:
            raise
        except ValueError as exc:
            results["dcf"] = None
            findings.append(_f("dcf", "error", "terminal-growth-ge-rate", str(exc)))

    if not results:
        raise InputError("nothing to compute: supply flows, dcf, capm or wacc")
    errors = sum(1 for f in findings if f["severity"] == "error")
    warnings = sum(1 for f in findings if f["severity"] == "warning")
    return {"name": case.get("name", ""), "assumptions": assumptions, "results": results,
            "findings": findings,
            "summary": {"errors": errors, "warnings": warnings, "info": len(findings) - errors - warnings}}


# ----------------------------------------------------------------------------- IO
def load_case(path: Path, rate: float | None, convention: str | None) -> dict:
    text = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() == ".csv":
        rows = list(csv.DictReader(text.splitlines()))
        if not rows or "cash_flow" not in rows[0]:
            raise InputError("CSV needs columns period,cash_flow")
        try:
            rows.sort(key=lambda r: int(r.get("period", 0)))
        except ValueError:
            raise InputError("period must be an integer") from None
        periods = [int(r.get("period", i)) for i, r in enumerate(rows)]
        if periods != list(range(periods[0], periods[0] + len(periods))):
            raise InputError("periods must be consecutive integers")
        case = {"flows": [r["cash_flow"] for r in rows]}
        if periods[0] == 1:
            case["convention"] = "t1"
    else:
        try:
            case = json.loads(text)
        except json.JSONDecodeError as exc:
            raise InputError(f"invalid JSON: {exc}") from None
        if not isinstance(case, dict):
            raise InputError("case must be a JSON object")
    if rate is not None:
        case["rate"] = rate
    if convention is not None:
        case["convention"] = convention
    return case


def _fmt(x) -> str:
    return "n/a" if x is None else (f"{x:,.4f}" if isinstance(x, float) else str(x))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="NPV/IRR/MIRR/payback/PI/WACC/DCF calculator.")
    ap.add_argument("input", type=Path, help="case JSON or period,cash_flow CSV")
    ap.add_argument("--rate", type=float, help="discount rate per period (decimal), overrides case")
    ap.add_argument("--convention", choices=["t0", "t1"])
    ap.add_argument("--strict", action="store_true", help="treat warnings as blocking")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        case = load_case(args.input, args.rate, args.convention)
        out = analyse(case)
    except (OSError, UnicodeDecodeError) as exc:
        print(f"cannot read {args.input}: {exc}", file=sys.stderr)
        return 2
    except InputError as exc:
        print(f"invalid input: {exc}", file=sys.stderr)
        return 2
    s = out["summary"]
    failed = s["errors"] > 0 or (args.strict and s["warnings"] > 0)
    out["passed"] = not failed
    out["scope"] = SCOPE
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        r = out["results"]
        print(f"Case: {out['name']}  convention={out['assumptions']['convention']} "
              f"({out['assumptions']['convention_meaning']})")
        for k in ("capm_cost_of_equity", "wacc", "rate_used", "npv", "mirr", "profitability_index"):
            if k in r:
                print(f"  {k:22} {_fmt(r[k])}")
        if "irr" in r:
            print(f"  {'irr':22} {_fmt(r['irr']['irr'])} [{r['irr']['status']}; roots={r['irr']['roots']}]")
        for k in ("payback_simple", "payback_discounted"):
            if k in r:
                pb = r[k]
                print(f"  {k:22} {'never' if pb['never'] else _fmt(pb['period'])}")
        if r.get("dcf"):
            print(f"  {'dcf enterprise value':22} {_fmt(r['dcf']['enterprise_value'])}")
        for var, table in r.get("sensitivity", {}).items():
            print(f"  sensitivity {var}: " + "; ".join(f"{_fmt(t['value'])} -> {_fmt(t['npv'])}" for t in table))
        for sv in r.get("switching_values", []):
            print(f"  switching value {sv['variable']}: {_fmt(sv['switching_value'])}")
        for f in out["findings"]:
            print(f"{f['severity'].upper():8} {f['id']:<8} {f['rule']:<26} {f['message']}")
        print(f"\n{'FAIL' if failed else 'PASS'}: {s}")
        print(SCOPE)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
