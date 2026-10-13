#!/usr/bin/env python3
"""Green Book-style options appraisal checker and NPSV calculator.

Reads an options JSON (assets/schemas/options-input.schema.json) and:
  * checks structure: a do-minimum/BAU counterfactual exists (exactly one), every option uses the
    same appraisal period and price base year, nominal series can be converted to real, series
    lengths match the period, non-monetised effects are recorded, CSFs and the long list -> short
    list trail exist, and the five cases are outlined;
  * converts nominal to real prices with a user-supplied inflation assumption;
  * applies user-supplied optimism bias (no official rates are hard-coded);
  * discounts with a declining schedule (default: commonly cited STPR schedule, UNVERIFIED -
    confirm against Green Book 2026 and its discounting guidance before use);
  * reports PV costs, PV benefits, NPSV, NPSV relative to the counterfactual, BCR and switching
    values, with non-monetised effects listed alongside each option.

Usage: options_appraisal.py options.json [--schedule schedule.json] [--strict] [--json]
Exit: 0 no errors, 1 error findings, 2 unreadable/invalid input.

Scope: appraisal arithmetic and structure checks only; it does not choose or approve an option.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

SCOPE = ("Scope: appraisal arithmetic and structure checks only; not a decision or approval. "
         "Discount schedule and any optimism bias must be confirmed against current HM Treasury guidance.")

# Commonly cited Green Book STPR schedule (real, per year). UNVERIFIED in this repository: secondary
# sources corroborate 3.5% (0-30), 3.0% (31-75), 2.5% thereafter; the 2.0/1.5/1.0% tail bands are
# from memory of earlier editions and were NOT confirmed for the 2026 edition.
DEFAULT_SCHEDULE = [
    {"from_year": 0, "to_year": 30, "rate": 0.035},
    {"from_year": 31, "to_year": 75, "rate": 0.030},
    {"from_year": 76, "to_year": 125, "rate": 0.025},
    {"from_year": 126, "to_year": 200, "rate": 0.020},
    {"from_year": 201, "to_year": 300, "rate": 0.015},
    {"from_year": 301, "to_year": None, "rate": 0.010},
]
DEFAULT_SCHEDULE_LABEL = "default STPR schedule (unverified - confirm against Green Book 2026)"
FIVE_CASES = ["strategic", "economic", "commercial", "financial", "management"]
CSF_RESULTS = {"meets", "partial", "fails"}


class InputError(ValueError):
    pass


def _f(fid: str, severity: str, rule: str, message: str) -> dict:
    return {"id": fid, "severity": severity, "rule": rule, "message": message}


def _num(x, what: str) -> float:
    if isinstance(x, bool) or x is None:
        raise InputError(f"{what} must be numeric, got {x!r}")
    try:
        v = float(x)
    except (TypeError, ValueError):
        raise InputError(f"{what} must be numeric, got {x!r}") from None
    if math.isnan(v) or math.isinf(v):
        raise InputError(f"{what} must be finite")
    return v


# ----------------------------------------------------------------------------- discounting
def validate_schedule(schedule) -> list[dict]:
    if not isinstance(schedule, list) or not schedule:
        raise InputError("discount schedule must be a non-empty list of {from_year, to_year, rate}")
    out, expect = [], 0
    for i, band in enumerate(schedule):
        lo = int(_num(band.get("from_year"), f"schedule[{i}].from_year"))
        hi = band.get("to_year")
        hi = None if hi is None else int(_num(hi, f"schedule[{i}].to_year"))
        rate = _num(band.get("rate"), f"schedule[{i}].rate")
        if lo != expect:
            raise InputError(f"schedule band {i} starts at year {lo}; expected {expect} (gap or overlap)")
        if hi is not None and hi < lo:
            raise InputError(f"schedule band {i} ends before it starts")
        if rate <= -1:
            raise InputError("discount rates must exceed -100%")
        if hi is None and i != len(schedule) - 1:
            raise InputError("only the last schedule band may be open-ended")
        out.append({"from_year": lo, "to_year": hi, "rate": rate})
        expect = (hi + 1) if hi is not None else None
    return out


def rate_for_year(year: int, schedule: list[dict]) -> float:
    for band in schedule:
        if band["from_year"] <= year and (band["to_year"] is None or year <= band["to_year"]):
            return band["rate"]
    raise InputError(f"no discount rate covers year {year}; extend the schedule")


def discount_factors(n_years: int, schedule: list[dict] | None = None) -> list[float]:
    """DF_0 = 1; DF_t = DF_(t-1) / (1 + r(t)) - the product of one-year factors, so a rate change
    applies only to years inside its band (stepped/declining schedule)."""
    schedule = validate_schedule(schedule or DEFAULT_SCHEDULE)
    dfs = [1.0]
    for t in range(1, n_years + 1):
        dfs.append(dfs[-1] / (1 + rate_for_year(t, schedule)))
    return dfs


def present_value(series: list[float], dfs: list[float]) -> float:
    return sum(v * d for v, d in zip(series, dfs))


def to_real(series: list[float], inflation: float) -> list[float]:
    """Deflate a nominal series to base-year (year 0) real prices."""
    return [v / (1 + inflation) ** t for t, v in enumerate(series)]


# ----------------------------------------------------------------------------- appraisal
def _series(opt: dict, key: str, n: int, findings: list[dict]) -> list[float] | None:
    raw = opt.get(key)
    if raw is None:
        findings.append(_f(opt.get("id", "?"), "error", "series-missing", f"'{key}' series missing"))
        return None
    if not isinstance(raw, list):
        raise InputError(f"{opt.get('id')}: '{key}' must be a list")
    vals = [_num(v, f"{opt.get('id')}.{key}[{i}]") for i, v in enumerate(raw)]
    if len(vals) != n + 1:
        findings.append(_f(opt.get("id", "?"), "error", "series-length",
                           f"'{key}' has {len(vals)} values; appraisal period needs {n + 1} (years 0..{n})"))
        return None
    if any(v < 0 for v in vals):
        findings.append(_f(opt.get("id", "?"), "error", "negative-series-value",
                           f"'{key}' contains negative values; enter savings as benefits, costs as positive"))
    return vals


def structure_checks(doc: dict) -> list[dict]:
    findings: list[dict] = []
    csfs = doc.get("critical_success_factors") or []
    if not csfs:
        findings.append(_f("csf", "error", "csf-missing", "no critical success factors recorded"))
    long_list = doc.get("long_list") or []
    if not long_list:
        findings.append(_f("long_list", "warning", "long-list-missing",
                           "no long list recorded; show how the short list was derived"))
    ll_ids = {o.get("id") for o in long_list}
    cf_ids = {o.get("id") for o in (doc.get("options") or []) if o.get("is_counterfactual")}
    for o in long_list:
        assess = o.get("csf_assessment") or {}
        gaps = [c for c in csfs if c not in assess]
        bad = [v for v in assess.values() if v not in CSF_RESULTS]
        if gaps:
            findings.append(_f(o.get("id", "?"), "warning", "long-list-csf-gap",
                               f"not assessed against CSFs: {gaps}"))
        if bad:
            findings.append(_f(o.get("id", "?"), "error", "csf-bad-value", f"CSF results must be {sorted(CSF_RESULTS)}"))
        if o.get("shortlisted") and "fails" in assess.values() and o.get("id") not in cf_ids:
            findings.append(_f(o.get("id", "?"), "warning", "shortlist-fails-csf",
                               "shortlisted despite failing a CSF; record the justification"))
        if not o.get("shortlisted") and not o.get("reason"):
            findings.append(_f(o.get("id", "?"), "warning", "discard-without-reason",
                               "long-list option discarded without a recorded reason"))
    five = doc.get("five_case") or {}
    missing = [c for c in FIVE_CASES if not five.get(c)]
    if missing:
        findings.append(_f("five_case", "warning", "five-case-incomplete",
                           f"five case outline missing: {missing}"))
    opts = doc.get("options") or []
    if long_list:
        for o in opts:
            if o.get("id") not in ll_ids and not o.get("is_counterfactual"):
                findings.append(_f(o.get("id", "?"), "warning", "shortlist-not-in-long-list",
                                   "short-listed option does not appear in the long list"))
    return findings


def appraise(doc: dict, schedule: list[dict] | None = None) -> dict:
    if not isinstance(doc, dict):
        raise InputError("options file must be a JSON object")
    ap = doc.get("appraisal") or {}
    findings = structure_checks(doc)
    sched_label = "user-supplied schedule"
    if schedule is None:
        schedule = ap.get("discount_schedule")
        if schedule in (None, "default"):
            schedule, sched_label = DEFAULT_SCHEDULE, DEFAULT_SCHEDULE_LABEL
            findings.append(_f("discount_schedule", "info", "schedule-default-unverified", DEFAULT_SCHEDULE_LABEL))
    schedule = validate_schedule(schedule)
    period = ap.get("appraisal_period_years")
    base_year = ap.get("price_base_year")
    if period is None or base_year is None:
        raise InputError("appraisal.appraisal_period_years and appraisal.price_base_year are required")
    period = int(_num(period, "appraisal_period_years"))
    if period < 1:
        raise InputError("appraisal period must be at least 1 year")
    opts = doc.get("options")
    if not isinstance(opts, list) or not opts:
        raise InputError("'options' must be a non-empty list (short list incl. counterfactual)")
    ids = [o.get("id") for o in opts]
    for i in {x for x in ids if ids.count(x) > 1}:
        findings.append(_f(str(i), "error", "duplicate-option-id", "option id used more than once"))
    cfs = [o for o in opts if o.get("is_counterfactual")]
    if not cfs:
        findings.append(_f("options", "error", "no-counterfactual",
                           "no do-minimum/business-as-usual counterfactual; every option must be compared with one"))
    elif len(cfs) > 1:
        findings.append(_f("options", "error", "multiple-counterfactuals", "exactly one counterfactual is allowed"))
    if len(opts) < 3:
        findings.append(_f("options", "warning", "shortlist-too-small",
                           "short list has fewer than 3 options including the counterfactual"))

    dfs = discount_factors(period, schedule)
    results = []
    for o in opts:
        oid = o.get("id", "?")
        if int(_num(o.get("appraisal_period_years", period), f"{oid}.appraisal_period_years")) != period:
            findings.append(_f(oid, "error", "appraisal-period-mismatch",
                               f"appraisal period differs from the common period of {period} years"))
            continue
        if o.get("price_base_year", base_year) != base_year:
            findings.append(_f(oid, "error", "price-base-mismatch",
                               f"price base year {o.get('price_base_year')} differs from {base_year}"))
            continue
        nme = o.get("non_monetised_effects")
        if nme is None:
            findings.append(_f(oid, "error", "non-monetised-missing",
                               "non_monetised_effects not recorded (use [] only after considering them)"))
        elif not nme:
            findings.append(_f(oid, "warning", "non-monetised-empty",
                               "no non-monetised effects listed; confirm none were identified"))
        costs = _series(o, "costs", period, findings)
        bens = _series(o, "benefits", period, findings)
        if costs is None or bens is None:
            continue
        basis = o.get("price_basis", ap.get("price_basis", "real"))
        if basis == "nominal":
            infl = o.get("inflation_rate", ap.get("inflation_rate"))
            if infl is None:
                findings.append(_f(oid, "error", "price-basis-unconvertible",
                                   "nominal series without an inflation_rate assumption cannot be put in real terms"))
                continue
            infl = _num(infl, f"{oid}.inflation_rate")
            costs, bens = to_real(costs, infl), to_real(bens, infl)
            findings.append(_f(oid, "info", "converted-nominal-to-real",
                               f"deflated at {infl:.2%} a year to {base_year} prices (assumption; state its source)"))
        elif basis != "real":
            findings.append(_f(oid, "error", "price-basis-unknown", "price_basis must be 'real' or 'nominal'"))
            continue
        ob = o.get("optimism_bias")
        ob_c = ob_b = 0.0
        if ob:
            ob_c = _num(ob.get("costs_pct", 0), f"{oid}.optimism_bias.costs_pct")
            ob_b = _num(ob.get("benefits_pct", 0), f"{oid}.optimism_bias.benefits_pct")
            if not ob.get("source"):
                findings.append(_f(oid, "warning", "optimism-bias-unsourced",
                                   "optimism bias % has no recorded source/justification"))
            if not (0 <= ob_c <= 5 and 0 <= ob_b < 1):
                findings.append(_f(oid, "error", "optimism-bias-range",
                                   "costs_pct must be 0..5 (uplift) and benefits_pct 0..<1 (reduction)"))
        elif not o.get("is_counterfactual") and any(costs):
            findings.append(_f(oid, "warning", "optimism-bias-not-considered",
                               "no optimism bias adjustment recorded; state the uplift used or why none applies"))
        adj_c = [c * (1 + ob_c) for c in costs]
        adj_b = [b * (1 - ob_b) for b in bens]
        pvc, pvb = present_value(adj_c, dfs), present_value(adj_b, dfs)
        results.append({"id": oid, "name": o.get("name", ""), "is_counterfactual": bool(o.get("is_counterfactual")),
                        "pv_costs": pvc, "pv_benefits": pvb, "npsv": pvb - pvc,
                        "bcr": pvb / pvc if pvc else None,
                        "optimism_bias": {"costs_pct": ob_c, "benefits_pct": ob_b,
                                          "source": (ob or {}).get("source", "")},
                        "non_monetised_effects": nme or []})

    cf = next((r for r in results if r["is_counterfactual"]), None)
    if cf and len(cfs) == 1:
        for r in results:
            if r is cf:
                continue
            inc_b, inc_c = r["pv_benefits"] - cf["pv_benefits"], r["pv_costs"] - cf["pv_costs"]
            inc = r["npsv"] - cf["npsv"]
            r["incremental"] = {
                "pv_benefits": inc_b, "pv_costs": inc_c, "npsv": inc,
                "bcr": inc_b / inc_c if inc_c > 0 else None,
                "switching_value_benefits_pct": (-inc / inc_b) if inc_b else None,
                "switching_value_costs_pct": (inc / inc_c) if inc_c else None,
            }
    ranked = sorted((r for r in results if not r["is_counterfactual"]), key=lambda r: r["npsv"], reverse=True)
    sev = [f["severity"] for f in findings]
    return {
        "title": ap.get("title", ""),
        "price_base_year": base_year, "price_basis": "real", "appraisal_period_years": period,
        "discount_schedule": {"label": sched_label, "bands": schedule},
        "discount_factors": dfs,
        "options": results,
        "highest_npsv_option": ranked[0]["id"] if ranked else None,
        "ranking_note": ("Highest NPSV is one input to the preferred-way-forward judgement; weigh it with "
                         "non-monetised effects, risk, affordability and deliverability. Not a decision."),
        "findings": findings,
        "summary": {"errors": sev.count("error"), "warnings": sev.count("warning"), "info": sev.count("info")},
    }


def _fmt(x) -> str:
    return "n/a" if x is None else f"{x:,.2f}"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Green Book-style options appraisal (NPSV, switching values).")
    p.add_argument("options", type=Path)
    p.add_argument("--schedule", type=Path, help="discount schedule JSON (list of bands or {bands:[...]})")
    p.add_argument("--strict", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    try:
        doc = json.loads(args.options.read_text(encoding="utf-8"))
        sched = None
        if args.schedule:
            sd = json.loads(args.schedule.read_text(encoding="utf-8"))
            sched = sd.get("bands") if isinstance(sd, dict) else sd
        out = appraise(doc, sched)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
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
        print(f"{out['title']} | {out['price_base_year']} prices, real | {out['appraisal_period_years']} years | "
              f"{out['discount_schedule']['label']}")
        for r in out["options"]:
            inc = r.get("incremental", {})
            print(f"  {r['id']:<8} PVC {_fmt(r['pv_costs']):>14} PVB {_fmt(r['pv_benefits']):>14} "
                  f"NPSV {_fmt(r['npsv']):>14}  vs counterfactual {_fmt(inc.get('npsv')) if inc else '-':>12}"
                  f"  SV(benefits) {_fmt(inc.get('switching_value_benefits_pct')) if inc else '-'}")
            for e in r["non_monetised_effects"]:
                print(f"           non-monetised: {e.get('effect', e) if isinstance(e, dict) else e}")
        print(f"  Highest NPSV (indicative): {out['highest_npsv_option']}")
        for f in out["findings"]:
            print(f"{f['severity'].upper():8} {f['id']:<18} {f['rule']:<30} {f['message']}")
        print(f"\n{'FAIL' if failed else 'PASS'}: {s}")
        print(SCOPE)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
