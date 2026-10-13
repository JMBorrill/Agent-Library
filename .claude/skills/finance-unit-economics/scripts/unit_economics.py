#!/usr/bin/env python3
"""Subscription unit economics with an assumption ledger: CAC, margins, churn, LTV, LTV:CAC,
CAC payback, scenarios, sensitivity and cohort retention.

Metric definitions follow common SaaS industry practice (not a single authoritative source):
  blended CAC      = sales & marketing spend / all new customers (same period)
  paid CAC         = paid acquisition spend / paid-attributed new customers
  gross margin/acc = ARPA x gross margin %
  contribution/acc = ARPA x gross margin % - other variable cost per account
  lifetime (months)= expected active months within the horizon H under geometric survival:
                     sum_{t=1..H} (1-churn)^(t-1) = (1 - (1-churn)^H) / churn  (churn 0 -> H, flagged);
                     the untruncated 1/churn is reported alongside for reference
  LTV (simple)     = contribution per month x lifetime  (= discounted LTV at a 0% discount rate)
  LTV (discounted) = sum_{t=1..H} c (1-churn)^(t-1) / (1+d_m)^t, d_m = (1+annual)^(1/12) - 1
  Both LTVs use the same survival curve and horizon, so they agree when the discount rate is 0.
  CAC payback      = blended CAC / contribution per month (never if contribution <= 0)

Usage:
  unit_economics.py model.json [--cohorts cohorts.csv] [--strict] [--json]
  unit_economics.py --cohorts cohorts.csv [--json]
Exit: 0 no errors, 1 error findings (e.g. undefined CAC, inconsistent inputs), 2 unreadable input.

Scope: decision-support arithmetic on stated assumptions; not a forecast, valuation or investment advice.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

SCOPE = "Scope: arithmetic on stated assumptions; not a forecast, valuation or investment advice."
TAGS = {"measured", "estimate", "benchmark"}
REQUIRED = ["sales_marketing_spend", "new_customers", "arpa_monthly", "gross_margin_pct", "monthly_churn"]
OPTIONAL_DEFAULTS = {"paid_spend": None, "paid_new_customers": None,
                     "variable_cost_per_account_monthly": 0.0, "discount_rate_annual": None,
                     "horizon_months": 60.0}
NON_NEGATIVE = ["sales_marketing_spend", "new_customers", "arpa_monthly", "monthly_churn", "paid_spend",
                "paid_new_customers", "variable_cost_per_account_monthly", "horizon_months"]


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


# ----------------------------------------------------------------------------- ledger
def build_ledger(inputs: dict) -> tuple[dict, list[dict], list[dict]]:
    """Return (values, ledger rows, findings). Each input is a number or {value, tag, source, owner}."""
    if not isinstance(inputs, dict):
        raise InputError("'inputs' must be an object")
    values: dict[str, float | None] = {}
    ledger, findings = [], []
    for key in REQUIRED:
        if key not in inputs or inputs[key] is None:
            findings.append(_f(key, "error", "missing-input", f"required input '{key}' is missing"))
    for key, raw in inputs.items():
        entry = raw if isinstance(raw, dict) else {"value": raw}
        val = entry.get("value")
        values[key] = None if val is None else _num(val, key)
        tag, source = entry.get("tag"), entry.get("source", "")
        row = {"input": key, "value": values[key], "tag": tag, "source": source,
               "owner": entry.get("owner", ""), "as_of": entry.get("as_of", "")}
        ledger.append(row)
        if tag is None:
            findings.append(_f(key, "warning", "assumption-untagged",
                               "tag each input as measured | estimate | benchmark"))
        elif tag not in TAGS:
            findings.append(_f(key, "error", "assumption-bad-tag", f"tag '{tag}' not in {sorted(TAGS)}"))
        elif tag in ("benchmark", "measured") and not source:
            findings.append(_f(key, "error", f"{tag}-without-source",
                               f"{tag} input needs a source (dataset/report, date)"))
        elif tag == "estimate" and not (source or row["owner"]):
            findings.append(_f(key, "warning", "estimate-without-owner", "record who made the estimate and how"))
    for key, default in OPTIONAL_DEFAULTS.items():
        values.setdefault(key, default)
        if values[key] is None and key in ("horizon_months",):
            values[key] = default
    return values, ledger, findings


def consistency(v: dict) -> list[dict]:
    out = []
    for key in NON_NEGATIVE:
        if v.get(key) is not None and v[key] < 0:
            out.append(_f(key, "error", "negative-input", f"{key} cannot be negative ({v[key]})"))
    ch = v.get("monthly_churn")
    if ch is not None and ch > 1:
        out.append(_f("monthly_churn", "error", "churn-out-of-range",
                      "monthly churn is a fraction 0..1 (enter 2% as 0.02)"))
    gm = v.get("gross_margin_pct")
    if gm is not None:
        if gm > 1:
            out.append(_f("gross_margin_pct", "error", "margin-out-of-range",
                          "gross margin is a fraction <= 1 (enter 80% as 0.80)"))
        elif gm < 0:
            out.append(_f("gross_margin_pct", "warning", "negative-gross-margin",
                          "negative gross margin: every account loses money before acquisition cost"))
    if v.get("paid_new_customers") is not None and v.get("new_customers") is not None \
            and v["paid_new_customers"] > v["new_customers"]:
        out.append(_f("paid_new_customers", "error", "inconsistent-customers",
                      "paid-attributed new customers exceed total new customers"))
    if v.get("paid_spend") is not None and v.get("sales_marketing_spend") is not None \
            and v["paid_spend"] > v["sales_marketing_spend"]:
        out.append(_f("paid_spend", "error", "inconsistent-spend",
                      "paid acquisition spend exceeds total sales & marketing spend"))
    hz = v.get("horizon_months")
    if hz is not None and hz <= 0:
        out.append(_f("horizon_months", "error", "bad-horizon", "horizon_months must be positive"))
    dr = v.get("discount_rate_annual")
    if dr is not None and dr <= -1:
        out.append(_f("discount_rate_annual", "error", "bad-discount-rate", "discount rate must exceed -100%"))
    return out


# ----------------------------------------------------------------------------- metrics
def safe_div(a: float | None, b: float | None) -> float | None:
    if a is None or b is None or b == 0:
        return None
    return a / b


def expected_lifetime(churn: float, horizon: float) -> tuple[float, bool]:
    """Expected active months within the horizon: sum_{t=1..H} (1-churn)^(t-1).

    Same survival curve and horizon as discounted_ltv, so simple LTV = discounted LTV at 0%.
    Returns (lifetime, capped); capped is True when churn is 0 or 1/churn exceeds the horizon
    (the horizon, not churn, then dominates the result).
    """
    h = int(horizon)
    if churn <= 0:
        return float(h), True
    life = (1.0 - (1.0 - churn) ** h) / churn
    return life, (1.0 / churn) > horizon


def discounted_ltv(contribution: float, churn: float, annual_rate: float, horizon_months: int) -> float:
    d = (1 + annual_rate) ** (1 / 12) - 1
    return sum(contribution * (1 - churn) ** (t - 1) / (1 + d) ** t for t in range(1, int(horizon_months) + 1))


def metrics(v: dict) -> dict:
    """Compute metrics from a values dict; undefined values are None (never divide by zero)."""
    arpa, gm = v["arpa_monthly"], v["gross_margin_pct"]
    churn, horizon = v["monthly_churn"], v.get("horizon_months") or 60.0
    var = v.get("variable_cost_per_account_monthly") or 0.0
    gross = arpa * gm
    contrib = gross - var
    life, capped = expected_lifetime(churn, horizon)
    cac = safe_div(v["sales_marketing_spend"], v["new_customers"])
    paid_cac = safe_div(v.get("paid_spend"), v.get("paid_new_customers"))
    ltv = contrib * life
    m = {
        "blended_cac": cac,
        "paid_cac": paid_cac,
        "gross_margin_per_account_monthly": gross,
        "contribution_per_account_monthly": contrib,
        "contribution_margin_pct": safe_div(contrib, arpa),
        "expected_lifetime_months": life,
        "lifetime_untruncated_months": (1.0 / churn) if churn > 0 else None,
        "lifetime_definition": f"expected active months within {int(horizon)}-month horizon "
                               "(geometric survival sum; same basis as discounted LTV)",
        "lifetime_capped_at_horizon": capped,
        "ltv": ltv,
        "ltv_discounted": None,
        "ltv_to_cac": safe_div(ltv, cac) if cac else None,
        "cac_payback_months": None,
        "cac_payback_never": False,
        "cac_payback_gross_margin_months": None,
    }
    if v.get("discount_rate_annual") is not None:
        m["ltv_discounted"] = discounted_ltv(contrib, churn, v["discount_rate_annual"], int(horizon))
        m["ltv_discounted_to_cac"] = safe_div(m["ltv_discounted"], cac) if cac else None
    if cac is not None:
        if contrib <= 0:
            m["cac_payback_never"] = True
        else:
            m["cac_payback_months"] = cac / contrib
        m["cac_payback_gross_margin_months"] = cac / gross if gross > 0 else None
    return m


def metric_findings(m: dict, v: dict) -> list[dict]:
    out = []
    if v.get("new_customers") == 0:
        out.append(_f("new_customers", "error", "cac-undefined", "zero new customers: CAC is undefined"))
    if v.get("paid_spend") is not None and v.get("paid_new_customers") == 0:
        out.append(_f("paid_new_customers", "error", "paid-cac-undefined",
                      "zero paid-attributed customers: paid CAC is undefined"))
    if v.get("monthly_churn") == 0:
        out.append(_f("monthly_churn", "warning", "churn-zero-capped",
                      f"churn 0: lifetime capped at horizon {v.get('horizon_months')} months; LTV depends on the cap"))
    elif m["lifetime_capped_at_horizon"]:
        out.append(_f("monthly_churn", "info", "lifetime-capped",
                      "1/churn exceeds horizon; lifetime is dominated by the horizon truncation"))
    if m["contribution_per_account_monthly"] <= 0:
        out.append(_f("contribution", "warning", "non-positive-contribution",
                      "contribution per account <= 0: LTV <= 0 and CAC never pays back"))
    if m["cac_payback_never"]:
        out.append(_f("cac_payback", "warning", "cac-never-pays-back", "CAC never pays back at current contribution"))
    return out


KNOWN_INPUTS = set(REQUIRED) | set(OPTIONAL_DEFAULTS)


def unknown_keys(keys, where: str) -> list[dict]:
    return [_f(f"{where}:{k}", "error", "unknown-override-key",
               f"'{k}' is not a model input (known: {sorted(KNOWN_INPUTS)}); possible typo; not evaluated")
            for k in keys if k not in KNOWN_INPUTS]


def ledger_findings(ledger: list[dict]) -> list[dict]:
    """Inputs tagged benchmark are flagged even when sourced (SKILL.md decision criteria)."""
    return [_f(r["input"], "warning", "benchmark-input",
               "input is a benchmark, not your own data: replace with measured data before relying on the result")
            for r in ledger if r["tag"] == "benchmark"]


def apply_overrides(values: dict, overrides: dict) -> dict:
    out = dict(values)
    for k, raw in (overrides or {}).items():
        val = raw.get("value") if isinstance(raw, dict) else raw
        out[k] = _num(val, f"override {k}")
    return out


def run_model(model: dict) -> dict:
    if not isinstance(model, dict):
        raise InputError("model must be a JSON object")
    values, ledger, findings = build_ledger(model.get("inputs", {}))
    findings += unknown_keys(model.get("inputs", {}), "inputs")
    findings += ledger_findings(ledger)
    findings += consistency(values)
    result: dict = {"name": model.get("name", ""), "currency": model.get("currency", "unspecified"),
                    "period": "month", "assumption_ledger": ledger}
    blocking = any(f["severity"] == "error" and f["rule"] in ("missing-input", "negative-input",
                   "churn-out-of-range", "margin-out-of-range", "bad-horizon", "bad-discount-rate")
                   for f in findings)
    if not blocking:
        base = metrics(values)
        findings += metric_findings(base, values)
        result["base"] = base
        scen = {}
        for name, ov in (model.get("scenarios") or {}).items():
            uk = unknown_keys(ov or {}, f"scenario {name}")
            if uk:
                findings += uk
                continue
            sv = apply_overrides(values, ov)
            sf = consistency(sv)
            if any(f["severity"] == "error" for f in sf):
                for f in sf:
                    f["id"] = f"{name}:{f['id']}"
                findings += sf
                continue
            scen[name] = metrics(sv)
            scen[name]["overrides"] = {k: sv[k] for k in ov}
            r = scen[name]["ltv_to_cac"]
            if "downside" in name.lower() and r is not None and r < 1:
                findings.append(_f(f"scenario {name}", "warning", "downside-ltv-cac-below-1",
                                   f"downside LTV:CAC {r:.2f} < 1: growth destroys value under plausible "
                                   "assumptions; escalate to financial-analyst and independent-reviewer "
                                   "before scaling acquisition spend"))
        result["scenarios"] = scen
        sens = {}
        for var, vals in (model.get("sensitivity") or {}).items():
            uk = unknown_keys([var], "sensitivity")
            if uk:
                findings += uk
                continue
            rows = []
            for x in vals:
                sv = apply_overrides(values, {var: x})
                if any(f["severity"] == "error" for f in consistency(sv)):
                    raise InputError(f"sensitivity value {x} for {var} is invalid")
                mm = metrics(sv)
                rows.append({"value": sv[var], "ltv": mm["ltv"], "ltv_to_cac": mm["ltv_to_cac"],
                             "cac_payback_months": mm["cac_payback_months"]})
            sens[var] = rows
        result["sensitivity"] = sens
    result["findings"] = findings
    return result


# ----------------------------------------------------------------------------- cohorts
def cohort_table(rows: list[dict]) -> tuple[dict, list[dict]]:
    """rows: cohort, month_index, active_customers -> retention table and findings."""
    findings: list[dict] = []
    data: dict[str, dict[int, float]] = defaultdict(dict)
    for i, r in enumerate(rows, start=2):
        try:
            c = (r.get("cohort") or "").strip()
            mi = int(r["month_index"])
            act = _num(r["active_customers"], "active_customers")
        except (KeyError, ValueError, TypeError) as exc:
            raise InputError(f"cohort CSV row {i}: {exc}") from None
        if not c or mi < 0 or act < 0:
            raise InputError(f"cohort CSV row {i}: blank cohort or negative value")
        if mi in data[c]:
            findings.append(_f(c, "error", "duplicate-cohort-month", f"cohort {c} month {mi} repeated"))
        data[c][mi] = act
    table: dict[str, dict] = {}
    by_month: dict[int, list[float]] = defaultdict(list)
    for c in sorted(data):
        months = data[c]
        start = months.get(0)
        if not start:
            findings.append(_f(c, "error", "cohort-no-month-0", f"cohort {c} has no positive month-0 size"))
            continue
        ret = {}
        for mi in sorted(months):
            r = months[mi] / start
            ret[mi] = r
            by_month[mi].append(r)
            if r > 1:
                findings.append(_f(c, "warning", "retention-above-100",
                                   f"cohort {c} month {mi} retention {r:.0%} > 100% (reactivations or data error)"))
        table[c] = {"size": start, "retention": {str(k): v for k, v in ret.items()}}
    avg = {str(mi): sum(v) / len(v) for mi, v in sorted(by_month.items())}
    implied = None
    keys = sorted(int(k) for k in avg)
    if len(keys) >= 2 and keys[-1] > 0 and avg[str(keys[-1])] > 0:
        implied = 1 - avg[str(keys[-1])] ** (1 / keys[-1])
    return {"cohorts": table, "average_retention": avg, "implied_monthly_churn": implied}, findings


def read_cohorts(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        missing = {"cohort", "month_index", "active_customers"} - set(reader.fieldnames or [])
        if missing:
            raise InputError(f"cohort CSV missing columns: {sorted(missing)}")
        return list(reader)


# ----------------------------------------------------------------------------- CLI
def _fmt(x) -> str:
    if x is None:
        return "n/a"
    if isinstance(x, bool):
        return str(x)
    return f"{x:,.2f}" if isinstance(x, float) else str(x)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="SaaS unit economics with assumption ledger.")
    ap.add_argument("model", nargs="?", type=Path)
    ap.add_argument("--cohorts", type=Path, help="CSV cohort,month_index,active_customers")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if not args.model and not args.cohorts:
        ap.print_usage(sys.stderr)
        return 2
    try:
        out: dict = {"findings": []}
        if args.model:
            out = run_model(json.loads(args.model.read_text(encoding="utf-8")))
        if args.cohorts:
            table, cf = cohort_table(read_cohorts(args.cohorts))
            out["cohort_retention"] = table
            out["findings"] = out.get("findings", []) + cf
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, csv.Error) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 2
    except InputError as exc:
        print(f"invalid input: {exc}", file=sys.stderr)
        return 2
    sev = [f["severity"] for f in out["findings"]]
    out["summary"] = {"errors": sev.count("error"), "warnings": sev.count("warning"), "info": sev.count("info")}
    failed = out["summary"]["errors"] > 0 or (args.strict and out["summary"]["warnings"] > 0)
    out["passed"] = not failed
    out["scope"] = SCOPE
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        if out.get("assumption_ledger"):
            print("Assumption ledger:")
            for r in out["assumption_ledger"]:
                print(f"  {r['input']:36} {_fmt(r['value']):>12}  {r['tag'] or 'UNTAGGED':10} {r['source']}")
        for label, m in [("base", out.get("base"))] + list((out.get("scenarios") or {}).items()):
            if m:
                pb = "never" if m["cac_payback_never"] else _fmt(m["cac_payback_months"])
                print(f"[{label}] CAC {_fmt(m['blended_cac'])}  contribution/mo {_fmt(m['contribution_per_account_monthly'])}"
                      f"  lifetime {_fmt(m['expected_lifetime_months'])}  LTV {_fmt(m['ltv'])}"
                      f"  LTV:CAC {_fmt(m['ltv_to_cac'])}  payback {pb}")
        if out.get("cohort_retention"):
            print("Average retention:", {k: round(v, 3) for k, v in out["cohort_retention"]["average_retention"].items()})
        for f in out["findings"]:
            print(f"{f['severity'].upper():8} {f['id']:<28} {f['rule']:<28} {f['message']}")
        print(f"\n{'FAIL' if failed else 'PASS'}: {out['summary']}")
        print(SCOPE)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
