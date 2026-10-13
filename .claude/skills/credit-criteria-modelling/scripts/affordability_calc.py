#!/usr/bin/env python3
"""Mortgage affordability arithmetic: LTV, CLTV (second charge), LTI, annuity repayment at the
product rate and at a stressed rate, DTI, payment-to-income and net disposable income.

Input JSON (assets/schemas/affordability-input.schema.json), all money in one currency, monthly
where stated:
  property_value, loan_amount, term_years, product_rate_pct, stress_margin_pct,
  stress_margin_source (lender policy label), [stress_floor_rate_pct], repayment_type
  (repayment | interest_only), gross_annual_income, net_monthly_income,
  monthly_committed_expenditure (existing credit commitments), monthly_essential_expenditure,
  [charge: first | second], [existing_first_charge_balance], [existing_first_charge_payment]

Formulas:
  annuity payment = P i / (1 - (1+i)^-n), i = annual rate / 12, n = months; i = 0 -> P / n
  interest-only payment = P i
  LTV = loan / value; CLTV = (first-charge balance + loan) / value (second charge)
  LTI = loan / gross annual income (and total secured debt / income)
  DTI = (committed credit + existing first-charge payment + stressed new payment) / gross monthly income
  NDI = net monthly income - essential - committed - existing first-charge payment - stressed payment

Usage: affordability_calc.py case.json [--json]
Exit: 0 no error findings, 1 error findings (e.g. LTV/CLTV > 100%, zero income), 2 invalid input
(negative or non-numeric values, missing fields).

Scope: arithmetic only. The stress margin is a lender-policy input, not a regulatory figure; the
output is not an affordability assessment, lending decision or advice.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

SCOPE = ("Scope: affordability arithmetic only; stress margin is lender policy input. Not an "
         "affordability assessment, lending decision or advice.")
REQUIRED = ["property_value", "loan_amount", "term_years", "product_rate_pct", "stress_margin_pct",
            "gross_annual_income", "net_monthly_income"]
OPTIONAL_ZERO = ["monthly_committed_expenditure", "monthly_essential_expenditure",
                 "existing_first_charge_balance", "existing_first_charge_payment", "stress_floor_rate_pct"]


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
    if v < 0:
        raise InputError(f"{what} cannot be negative ({v})")
    return v


def monthly_payment(principal: float, annual_rate_pct: float, term_years: float,
                    repayment_type: str = "repayment") -> float:
    p = _num(principal, "principal")
    r = _num(annual_rate_pct, "annual_rate_pct") / 100 / 12
    n = round(_num(term_years, "term_years") * 12)
    if n <= 0:
        raise InputError("term must be at least one month")
    if repayment_type == "interest_only":
        return p * r
    if repayment_type != "repayment":
        raise InputError("repayment_type must be 'repayment' or 'interest_only'")
    if r == 0:
        return p / n
    return p * r / (1 - (1 + r) ** -n)


def ratio(a: float, b: float) -> float | None:
    return None if b == 0 else a / b


def calculate(case: dict) -> dict:
    if not isinstance(case, dict):
        raise InputError("case must be a JSON object")
    missing = [k for k in REQUIRED if k not in case]
    if missing:
        raise InputError(f"missing fields: {missing}")
    v = {k: _num(case[k], k) for k in REQUIRED}
    for k in OPTIONAL_ZERO:
        v[k] = _num(case.get(k, 0) or 0, k)
    rtype = case.get("repayment_type", "repayment")
    charge = case.get("charge", "first")
    if charge not in ("first", "second"):
        raise InputError("charge must be 'first' or 'second'")
    findings: list[dict] = []
    if v["property_value"] == 0:
        raise InputError("property_value must be positive")
    if v["loan_amount"] == 0:
        findings.append(_f("loan_amount", "warning", "zero-loan", "loan amount is zero"))
    if not case.get("stress_margin_source"):
        findings.append(_f("stress_margin_pct", "warning", "stress-margin-unsourced",
                           "label the stress margin with the lender policy it comes from"))
    stressed_rate = max(v["product_rate_pct"] + v["stress_margin_pct"], v["stress_floor_rate_pct"])
    pay = monthly_payment(v["loan_amount"], v["product_rate_pct"], v["term_years"], rtype)
    pay_s = monthly_payment(v["loan_amount"], stressed_rate, v["term_years"], rtype)
    ltv = v["loan_amount"] / v["property_value"] * 100
    total_secured = v["loan_amount"] + (v["existing_first_charge_balance"] if charge == "second" else 0)
    cltv = total_secured / v["property_value"] * 100 if charge == "second" else None
    gross_m = v["gross_annual_income"] / 12
    first_pay = v["existing_first_charge_payment"] if charge == "second" else 0.0
    debt_service = v["monthly_committed_expenditure"] + first_pay + pay_s
    res = {
        "charge": charge,
        "repayment_type": rtype,
        "ltv_pct": ltv,
        "cltv_pct": cltv,
        "lti": ratio(v["loan_amount"], v["gross_annual_income"]),
        "lti_total_secured": ratio(total_secured, v["gross_annual_income"]),
        "monthly_payment_product_rate": pay,
        "stressed_rate_pct": stressed_rate,
        "stress_margin_basis": f"lender policy: {case.get('stress_margin_source') or 'UNSPECIFIED'}",
        "monthly_payment_stressed": pay_s,
        "dti_pct": None if gross_m == 0 else debt_service / gross_m * 100,
        "payment_to_net_income_pct": None if v["net_monthly_income"] == 0 else pay_s / v["net_monthly_income"] * 100,
        "net_disposable_income_monthly": v["net_monthly_income"] - v["monthly_essential_expenditure"]
        - v["monthly_committed_expenditure"] - first_pay - pay_s,
    }
    if ltv > 100:
        findings.append(_f("ltv_pct", "error", "ltv-exceeds-100", f"LTV {ltv:.2f}% exceeds 100% (negative equity)"))
    if cltv is not None and cltv > 100:
        findings.append(_f("cltv_pct", "error", "cltv-exceeds-100", f"combined LTV {cltv:.2f}% exceeds 100%"))
    if charge == "second" and v["existing_first_charge_balance"] == 0:
        findings.append(_f("existing_first_charge_balance", "warning", "second-charge-no-first-balance",
                           "second charge case with zero first-charge balance; confirm the first charge"))
    if v["gross_annual_income"] == 0:
        findings.append(_f("gross_annual_income", "error", "income-zero",
                           "gross income is zero: LTI and DTI undefined; refer to human review"))
    if v["net_monthly_income"] == 0:
        findings.append(_f("net_monthly_income", "error", "net-income-zero",
                           "net income is zero: payment-to-income undefined"))
    if res["net_disposable_income_monthly"] < 0:
        findings.append(_f("ndi", "warning", "negative-ndi",
                           "net disposable income is negative at the stressed payment"))
    if rtype == "interest_only":
        findings.append(_f("repayment_type", "info", "interest-only",
                           "interest-only: a credible repayment strategy must be evidenced separately"))
    sev = [f["severity"] for f in findings]
    return {"inputs": {**v, "repayment_type": rtype, "charge": charge}, "results": res, "findings": findings,
            "summary": {"errors": sev.count("error"), "warnings": sev.count("warning"), "info": sev.count("info")}}


def _fmt(x) -> str:
    return "undefined" if x is None else (f"{x:,.2f}" if isinstance(x, float) else str(x))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Mortgage affordability arithmetic (LTV, CLTV, LTI, stressed payment, DTI, NDI).")
    ap.add_argument("case", type=Path)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        out = calculate(json.loads(args.case.read_text(encoding="utf-8")))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 2
    except InputError as exc:
        print(f"invalid input: {exc}", file=sys.stderr)
        return 2
    failed = out["summary"]["errors"] > 0
    out["passed"] = not failed
    out["scope"] = SCOPE
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        for k, val in out["results"].items():
            print(f"  {k:32} {_fmt(val)}")
        for f in out["findings"]:
            print(f"{f['severity'].upper():8} {f['id']:<30} {f['rule']:<30} {f['message']}")
        print(f"\n{'FAIL' if failed else 'PASS'}: {out['summary']}")
        print(SCOPE)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
