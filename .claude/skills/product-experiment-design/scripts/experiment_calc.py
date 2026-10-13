#!/usr/bin/env python3
"""Two-proportion experiment calculator and experiment-plan checker.

Subcommands
  sample-size  --baseline P1 (--target P2 | --mde D) [--alpha A] [--power B] [--formula pooled|unpooled]
               [--cluster-size M --icc RHO]   (cluster randomisation: design effect 1 + (M-1)*RHO)
  mde          --baseline P1 --n N [--alpha A] [--power B] [--formula ...] [--direction increase|decrease]
  evaluate     --control X N --treatment X N [--alpha A]           (quick result evaluation)
  evaluate     --plan plan.json --results results.json             (primary + guardrails + decision rule)
  plan         plan.json                                            (validate an experiment plan)
All subcommands accept --json.

Formulas (two-sided test of H0: p1 = p2, equal allocation, normal approximation, no continuity
correction; z values from statistics.NormalDist):
  pooled (default; Fleiss without continuity correction):
    n = [z(1-a/2)*sqrt(2*pbar*(1-pbar)) + z(1-b)*sqrt(p1(1-p1) + p2(1-p2))]^2 / (p2-p1)^2,
    pbar = (p1+p2)/2  (pooled variance under H0, unpooled under H1)
  unpooled:
    n = (z(1-a/2) + z(1-b))^2 * (p1(1-p1) + p2(1-p2)) / (p2-p1)^2
  cluster randomisation (optional): design effect DE = 1 + (m - 1) * rho, m = mean cluster size,
    rho = intra-cluster correlation; n_clustered = ceil(n_per_arm * DE), clusters = ceil(n_clustered / m)
    (equal cluster sizes assumed; unequal sizes need a larger DE).
  Result test: z = (p2-p1)/sqrt(p(1-p)(1/n1+1/n2)) with pooled p; two-sided p-value;
  CI on the difference uses the unpooled (Wald) standard error.
Exit codes: 0 ok / no blocking findings, 1 blocking findings, 2 invalid input.

Scope: arithmetic and plan-structure checks only. It cannot tell whether the metric matters,
the randomisation is sound or the experiment is ethical; a ship decision is a human decision.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
import sys
from pathlib import Path
from statistics import NormalDist

Z = NormalDist()
FORMULAS = ("pooled", "unpooled")


class InputError(ValueError):
    """Invalid numeric input (reported with exit code 2)."""


def _f(rid: str, severity: str, rule: str, message: str) -> dict:
    return {"id": rid, "severity": severity, "rule": rule, "message": message}


def _check_prob(name: str, p: float, open_interval: bool = True) -> None:
    if not isinstance(p, (int, float)) or isinstance(p, bool) or math.isnan(p):
        raise InputError(f"{name} must be a number")
    if open_interval and not 0 < p < 1:
        raise InputError(f"{name} must be strictly between 0 and 1 (got {p})")


def _check_alpha_power(alpha: float, power: float) -> None:
    _check_prob("alpha", alpha)
    _check_prob("power", power)
    if alpha >= 0.5:
        raise InputError("alpha must be < 0.5")
    if power <= 0.5:
        raise InputError("power must be > 0.5")


def n_per_arm_exact(p1: float, p2: float, alpha: float = 0.05, power: float = 0.8,
                    formula: str = "pooled") -> float:
    """Unrounded sample size per arm. Raises InputError on invalid input."""
    _check_prob("baseline", p1)
    _check_prob("target", p2)
    _check_alpha_power(alpha, power)
    if formula not in FORMULAS:
        raise InputError(f"formula must be one of {FORMULAS}")
    d = p2 - p1
    if d == 0:
        raise InputError("effect size is zero: no finite sample size detects no difference")
    za = Z.inv_cdf(1 - alpha / 2)
    zb = Z.inv_cdf(power)
    var1 = p1 * (1 - p1) + p2 * (1 - p2)
    if formula == "unpooled":
        return (za + zb) ** 2 * var1 / d ** 2
    pbar = (p1 + p2) / 2
    return (za * math.sqrt(2 * pbar * (1 - pbar)) + zb * math.sqrt(var1)) ** 2 / d ** 2


def sample_size(p1: float, p2: float, alpha: float = 0.05, power: float = 0.8,
                formula: str = "pooled") -> int:
    return math.ceil(n_per_arm_exact(p1, p2, alpha, power, formula) - 1e-9)


def cluster_adjust(n_per_arm: int, cluster_size: float, icc: float) -> dict:
    """Inflate an individually randomised n per arm by the design effect DE = 1 + (m - 1) * rho."""
    for name, v in (("cluster_size", cluster_size), ("icc", icc)):
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
            raise InputError(f"{name} must be a finite number")
    if cluster_size < 1:
        raise InputError(f"cluster_size must be >= 1 (got {cluster_size})")
    if not 0 <= icc <= 1:
        raise InputError(f"icc must satisfy 0 <= icc <= 1 (got {icc})")
    de = 1 + (cluster_size - 1) * icc
    n_c = math.ceil(n_per_arm * de - 1e-9)
    clusters = math.ceil(n_c / cluster_size - 1e-9)
    return {"design_effect": de, "n_per_arm_individual": n_per_arm, "n_per_arm": n_c,
            "clusters_per_arm": clusters, "total": 2 * n_c, "total_clusters": 2 * clusters,
            "individuals_in_whole_clusters_per_arm": clusters * cluster_size}


def mde(p1: float, n: int, alpha: float = 0.05, power: float = 0.8, formula: str = "pooled",
        direction: str = "increase") -> float | None:
    """Smallest absolute difference detectable with n per arm (bisection). None if not reachable."""
    _check_prob("baseline", p1)
    _check_alpha_power(alpha, power)
    if not isinstance(n, int) or n <= 0:
        raise InputError("n must be a positive integer")
    sign = 1 if direction == "increase" else -1
    limit = (1 - p1) if sign > 0 else p1
    lo, hi = 0.0, limit * (1 - 1e-9)
    if n_per_arm_exact(p1, p1 + sign * hi, alpha, power, formula) > n:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2
        if mid == 0 or n_per_arm_exact(p1, p1 + sign * mid, alpha, power, formula) > n:
            lo = mid
        else:
            hi = mid
    return hi


def two_prop_test(x1: int, n1: int, x2: int, n2: int, alpha: float = 0.05) -> dict:
    """Group 1 = control, group 2 = treatment."""
    for name, v in (("control conversions", x1), ("control n", n1), ("treatment conversions", x2),
                    ("treatment n", n2)):
        if not isinstance(v, int) or isinstance(v, bool) or v < 0:
            raise InputError(f"{name} must be a non-negative integer")
    if n1 == 0 or n2 == 0:
        raise InputError("group sizes must be > 0")
    if x1 > n1 or x2 > n2:
        raise InputError("conversions cannot exceed group size")
    _check_prob("alpha", alpha)
    p1, p2 = x1 / n1, x2 / n2
    diff = p2 - p1
    pooled = (x1 + x2) / (n1 + n2)
    se0 = math.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
    se1 = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    zc = Z.inv_cdf(1 - alpha / 2)
    if se0 == 0:
        z, pval = None, None
    else:
        z = diff / se0
        pval = 2 * (1 - Z.cdf(abs(z)))
    return {
        "control_rate": p1, "treatment_rate": p2, "difference": diff,
        "relative_lift": (diff / p1) if p1 > 0 else None,
        "z": z, "p_value": pval,
        "ci": [diff - zc * se1, diff + zc * se1], "ci_level": 1 - alpha,
        "significant": (pval is not None and pval < alpha),
        "note": None if se0 else "no variation in either group: test not computable",
    }


# ---------------------------------------------------------------- plan validation
PLAN_REQUIRED = ["id", "hypothesis", "primary_metric", "baseline", "mde", "alpha", "power",
                 "duration_days", "stopping_rule", "ethics", "decision_rule"]
DIRECTION_WORDS = re.compile(r"\b(increase|increases|decrease|decreases|reduce|reduces|raise|raises|"
                             r"improve|improves|lower|lowers|at least|no more than|fewer|more|higher|less)\b", re.I)
PEEKING = re.compile(r"(as soon as|once|when|until)\b[^.]*\bsignifican|\bpeek|"
                     r"\bwhen (it|results?) look", re.I)
SEQUENTIAL = re.compile(r"\b(sequential|alpha[- ]spending|group[- ]sequential|o'brien|pocock|bayesian)\b", re.I)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and not math.isnan(v)


def check_plan(plan: dict) -> dict:
    findings: list[dict] = []
    pid = str(plan.get("id") or "<plan>")
    for key in PLAN_REQUIRED:
        if key not in plan or plan[key] in (None, "", [], {}):
            findings.append(_f(pid, "error", "plan-missing-field", f"missing '{key}'"))
    hyp = plan.get("hypothesis") or {}
    if isinstance(hyp, dict) and hyp:
        pred = str(hyp.get("prediction", ""))
        if not pred:
            findings.append(_f(pid, "error", "hypothesis-no-prediction", "hypothesis has no falsifiable prediction"))
        elif not (re.search(r"\d", pred) and DIRECTION_WORDS.search(pred)):
            findings.append(_f(pid, "error", "prediction-not-falsifiable",
                               "prediction must name a direction and a number (e.g. 'increases from 10% to at least 12%')"))
        if not hyp.get("statement"):
            findings.append(_f(pid, "warning", "hypothesis-no-statement", "no hypothesis statement (because ... we believe ...)"))
    elif hyp:
        findings.append(_f(pid, "error", "hypothesis-format", "hypothesis must be an object {statement, prediction}"))
    pm = plan.get("primary_metric")
    if isinstance(pm, list):
        findings.append(_f(pid, "error", "multiple-primary-metrics", "choose exactly one primary metric; move others to secondary/guardrails"))
    elif isinstance(pm, dict) and pm and not pm.get("definition"):
        findings.append(_f(pid, "error", "metric-undefined", "primary metric has no definition (numerator/denominator/window)"))

    b, d, a, pw = plan.get("baseline"), plan.get("mde"), plan.get("alpha"), plan.get("power")
    direction = plan.get("direction", "increase")
    numeric_ok = True
    if b is not None and not (_num(b) and 0 < b < 1):
        findings.append(_f(pid, "error", "baseline-range", f"baseline must be a proportion in (0,1), got {b!r}"))
        numeric_ok = False
    if d is not None and not (_num(d) and d > 0):
        findings.append(_f(pid, "error", "mde-range", f"mde must be an absolute difference > 0, got {d!r}"))
        numeric_ok = False
    if a is not None and not (_num(a) and 0 < a < 0.5):
        findings.append(_f(pid, "error", "alpha-range", f"alpha must be in (0, 0.5), got {a!r}"))
        numeric_ok = False
    elif _num(a) and a > 0.1:
        findings.append(_f(pid, "warning", "alpha-high", f"alpha {a} is unusually permissive"))
    if pw is not None and not (_num(pw) and 0.5 < pw < 1):
        findings.append(_f(pid, "error", "power-range", f"power must be in (0.5, 1), got {pw!r}"))
        numeric_ok = False
    elif _num(pw) and pw < 0.8:
        findings.append(_f(pid, "warning", "power-low", f"power {pw} below the common 0.8 convention"))
    if direction not in ("increase", "decrease"):
        findings.append(_f(pid, "error", "direction", "direction must be 'increase' or 'decrease'"))
        numeric_ok = False
    required = None
    if numeric_ok and all(_num(x) for x in (b, d, a, pw)):
        target = b + d if direction == "increase" else b - d
        if not 0 < target < 1:
            findings.append(_f(pid, "error", "mde-range", f"baseline {direction} by mde gives {target:.4f}, outside (0,1)"))
        else:
            required = sample_size(b, target, a, pw, plan.get("formula", "pooled"))
    planned = plan.get("sample_size_per_arm")
    daily = plan.get("expected_eligible_per_day")
    dur = plan.get("duration_days")
    arms = plan.get("arms", 2)
    if dur is not None and not (_num(dur) and dur > 0):
        findings.append(_f(pid, "error", "duration-range", "duration_days must be > 0"))
    elif _num(dur) and dur < 7:
        findings.append(_f(pid, "warning", "duration-short", "under 7 days: weekly booking cycles may bias results"))
    if required is not None:
        if _num(planned) and planned < required:
            findings.append(_f(pid, "error", "underpowered", f"planned {planned}/arm < required {required}/arm"))
        if _num(daily) and _num(dur) and dur > 0 and _num(arms) and arms >= 2:
            achievable = math.floor(daily * dur / arms)
            if achievable < required:
                findings.append(_f(pid, "error", "insufficient-traffic",
                                   f"expected {achievable}/arm over {dur} days < required {required}/arm"))
        if not _num(planned) and not _num(daily):
            findings.append(_f(pid, "warning", "no-sample-plan", "neither sample_size_per_arm nor expected_eligible_per_day given"))
    stop = str(plan.get("stopping_rule") or "")
    if stop and PEEKING.search(stop) and not SEQUENTIAL.search(stop):
        findings.append(_f(pid, "error", "optional-stopping",
                           "stopping when results look significant inflates false positives; fix n/duration or use a sequential design"))
    eth = plan.get("ethics")
    if isinstance(eth, dict) and eth:
        if not str(eth.get("consent_note", "")).strip():
            findings.append(_f(pid, "error", "ethics-no-consent-note", "ethics.consent_note is empty"))
    elif eth:
        findings.append(_f(pid, "error", "ethics-format", "ethics must be an object with consent_note"))
    dr = plan.get("decision_rule")
    if isinstance(dr, dict) and dr:
        if dr.get("set_before_launch") is not True:
            findings.append(_f(pid, "error", "decision-rule-not-preregistered", "decision_rule.set_before_launch must be true"))
        for k in ("ship_if", "do_not_ship_if"):
            if not dr.get(k):
                findings.append(_f(pid, "error", "decision-rule-incomplete", f"decision_rule.{k} missing"))
        rec, launch = dr.get("recorded_on"), plan.get("launch_date")
        if rec and launch and DATE_RE.fullmatch(str(rec)) and DATE_RE.fullmatch(str(launch)):
            if dt.date.fromisoformat(rec) > dt.date.fromisoformat(launch):
                findings.append(_f(pid, "error", "decision-rule-after-launch",
                                   f"decision rule recorded {rec} after launch {launch}"))
    elif dr:
        findings.append(_f(pid, "error", "decision-rule-format", "decision_rule must be an object"))
    guards = plan.get("guardrails") or []
    if not guards:
        findings.append(_f(pid, "warning", "no-guardrails", "no guardrail metrics (e.g. cancellations, complaints, opt-outs)"))
    for g in guards if isinstance(guards, list) else []:
        gname = str(g.get("name", "<guardrail>")) if isinstance(g, dict) else "<guardrail>"
        if not isinstance(g, dict) or g.get("direction") not in ("must_not_increase", "must_not_decrease") \
                or not (_num(g.get("max_abs_change")) and g["max_abs_change"] >= 0):
            findings.append(_f(gname, "error", "guardrail-format",
                               "guardrail needs direction must_not_increase|must_not_decrease and max_abs_change >= 0"))
    errors = sum(1 for f in findings if f["severity"] == "error")
    warnings = sum(1 for f in findings if f["severity"] == "warning")
    return {"findings": findings,
            "summary": {"plan": pid, "required_per_arm": required, "errors": errors, "warnings": warnings},
            "passed": errors == 0}


def _counts(obj: dict, label: str) -> tuple[int, int]:
    try:
        return int(obj["conversions"]), int(obj["n"])
    except (KeyError, TypeError, ValueError) as exc:
        raise InputError(f"{label}: need integer 'conversions' and 'n'") from exc


def evaluate(plan: dict, results: dict) -> dict:
    findings: list[dict] = []
    alpha = plan.get("alpha", 0.05)
    direction = plan.get("direction", "increase")
    prim = results.get("primary") or {}
    x1, n1 = _counts(prim.get("control"), "primary.control")
    x2, n2 = _counts(prim.get("treatment"), "primary.treatment")
    res = two_prop_test(x1, n1, x2, n2, alpha)
    pid = str(plan.get("id") or "<plan>")
    planned = plan.get("sample_size_per_arm")
    if _num(planned) and min(n1, n2) < planned:
        findings.append(_f(pid, "warning", "sample-not-reached", f"min group {min(n1, n2)} < planned {planned}/arm"))
    sign = 1 if direction == "increase" else -1
    lo, hi = res["ci"]
    good_bound, bad_bound = (lo, hi) if sign > 0 else (-hi, -lo)
    guard_out = []
    breach = False
    gplan = {g.get("name"): g for g in plan.get("guardrails") or [] if isinstance(g, dict)}
    for g in results.get("guardrails") or []:
        name = g.get("name")
        spec = gplan.get(name)
        if spec is None:
            findings.append(_f(str(name), "warning", "guardrail-not-in-plan", "guardrail result has no pre-registered threshold"))
            continue
        gx1, gn1 = _counts(g.get("control"), f"guardrail {name} control")
        gx2, gn2 = _counts(g.get("treatment"), f"guardrail {name} treatment")
        t = two_prop_test(gx1, gn1, gx2, gn2, alpha)
        harm = t["difference"] if spec["direction"] == "must_not_increase" else -t["difference"]
        worst = t["ci"][1] if spec["direction"] == "must_not_increase" else -t["ci"][0]
        status = "ok"
        if harm > spec["max_abs_change"]:
            status, breach = "breached", True
            findings.append(_f(str(name), "error", "guardrail-breached",
                               f"observed harmful change {harm:+.4f} exceeds limit {spec['max_abs_change']}"))
        elif worst > spec["max_abs_change"]:
            status = "inconclusive"
            findings.append(_f(str(name), "warning", "guardrail-uncertain",
                               f"CI worst case {worst:+.4f} exceeds limit {spec['max_abs_change']}"))
        guard_out.append({"name": name, "difference": t["difference"], "ci": t["ci"], "status": status})
    for name in gplan:
        if name not in {g.get("name") for g in results.get("guardrails") or []}:
            findings.append(_f(str(name), "warning", "guardrail-missing-result", "pre-registered guardrail has no result"))
    if breach:
        rec = "RECOMMEND_DO_NOT_SHIP"
    elif res["significant"] and good_bound > 0:
        rec = "RECOMMEND_SHIP"
    elif res["significant"] and bad_bound < 0:
        rec = "RECOMMEND_DO_NOT_SHIP"
    else:
        rec = "INCONCLUSIVE"
    errors = sum(1 for f in findings if f["severity"] == "error")
    return {"findings": findings, "primary": res, "guardrails": guard_out,
            "summary": {"plan": pid, "recommendation": rec, "requires_human_decision": True,
                        "decision_rule": (plan.get("decision_rule") or {}).get("ship_if"),
                        "errors": errors, "warnings": sum(1 for f in findings if f["severity"] == "warning")},
            "passed": errors == 0}


# ---------------------------------------------------------------- CLI
def _load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise InputError(f"{path} must contain a JSON object")
    return data


def _fmt(v) -> str:
    return "n/a" if v is None else (f"{v:.6g}" if isinstance(v, float) else str(v))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Two-proportion experiment calculator and plan checker.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sample-size")
    s.add_argument("--baseline", type=float, required=True)
    g = s.add_mutually_exclusive_group(required=True)
    g.add_argument("--target", type=float)
    g.add_argument("--mde", type=float, help="absolute difference (0.02 = 2 percentage points)")
    s.add_argument("--direction", choices=["increase", "decrease"], default="increase")
    s.add_argument("--cluster-size", type=float, help="mean cluster size m (cluster randomisation; needs --icc)")
    s.add_argument("--icc", type=float, help="intra-cluster correlation rho in [0, 1] (needs --cluster-size)")
    m = sub.add_parser("mde")
    m.add_argument("--baseline", type=float, required=True)
    m.add_argument("--n", type=int, required=True, help="sample size per arm")
    m.add_argument("--direction", choices=["increase", "decrease"], default="increase")
    for p in (s, m):
        p.add_argument("--alpha", type=float, default=0.05)
        p.add_argument("--power", type=float, default=0.8)
        p.add_argument("--formula", choices=FORMULAS, default="pooled")
    e = sub.add_parser("evaluate")
    e.add_argument("--control", nargs=2, type=int, metavar=("X", "N"))
    e.add_argument("--treatment", nargs=2, type=int, metavar=("X", "N"))
    e.add_argument("--alpha", type=float, default=0.05)
    e.add_argument("--plan", type=Path)
    e.add_argument("--results", type=Path)
    pl = sub.add_parser("plan")
    pl.add_argument("plan", type=Path)
    for p in (s, m, e, pl):
        p.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "sample-size":
            if args.mde is not None and args.mde <= 0:
                raise InputError("mde must be > 0 (direction is set with --direction)")
            target = args.target if args.target is not None else (
                args.baseline + args.mde if args.direction == "increase" else args.baseline - args.mde)
            exact = n_per_arm_exact(args.baseline, target, args.alpha, args.power, args.formula)
            out = {"calculation": "sample-size", "formula": args.formula,
                   "inputs": {"baseline": args.baseline, "target": round(target, 12), "alpha": args.alpha,
                              "power": args.power, "two_sided": True},
                   "result": {"n_per_arm": math.ceil(exact - 1e-9), "n_per_arm_unrounded": exact,
                              "total": 2 * math.ceil(exact - 1e-9)}}
            if (args.cluster_size is None) != (args.icc is None):
                raise InputError("cluster randomisation needs both --cluster-size and --icc")
            if args.cluster_size is not None:
                cl = cluster_adjust(out["result"]["n_per_arm"], args.cluster_size, args.icc)
                out["inputs"].update(cluster_size=args.cluster_size, icc=args.icc)
                out["cluster_adjustment"] = "design effect DE = 1 + (m - 1) * rho; equal cluster sizes assumed"
                out["result"] = {**cl, "n_per_arm_individual_unrounded": exact}
            code = 0
        elif args.cmd == "mde":
            v = mde(args.baseline, args.n, args.alpha, args.power, args.formula, args.direction)
            out = {"calculation": "mde", "formula": args.formula,
                   "inputs": {"baseline": args.baseline, "n_per_arm": args.n, "alpha": args.alpha,
                              "power": args.power, "direction": args.direction, "two_sided": True},
                   "result": {"mde_absolute": v,
                              "mde_relative": (v / args.baseline) if v is not None else None,
                              "note": None if v is not None else "no detectable effect within (0,1) at this n"}}
            code = 0
        elif args.cmd == "evaluate":
            if args.plan and args.results:
                out = evaluate(_load_json(args.plan), _load_json(args.results))
                code = 0 if out["passed"] else 1
            elif args.control and args.treatment:
                res = two_prop_test(args.control[0], args.control[1], args.treatment[0], args.treatment[1], args.alpha)
                out = {"calculation": "evaluate", "formula": "pooled z-test; unpooled Wald CI",
                       "inputs": {"control": args.control, "treatment": args.treatment, "alpha": args.alpha},
                       "result": res}
                code = 0
            else:
                raise InputError("evaluate needs --control/--treatment or --plan/--results")
        else:
            out = check_plan(_load_json(args.plan))
            code = 0 if out["passed"] else 1
    except InputError as exc:
        print(f"invalid input: {exc}", file=sys.stderr)
        return 2
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        if "findings" in out:
            for f in out["findings"]:
                print(f"{f['severity'].upper():8} {f['id']:<20} {f['rule']:<30} {f['message']}")
        if "result" in out:
            print(f"{out['calculation']} ({out['formula']}): inputs {out['inputs']}")
            for k, v in out["result"].items():
                print(f"  {k}: {_fmt(v) if not isinstance(v, list) else [_fmt(x) for x in v]}")
        if "primary" in out:
            p = out["primary"]
            print(f"primary: diff {p['difference']:+.4f} CI [{p['ci'][0]:+.4f}, {p['ci'][1]:+.4f}] p={_fmt(p['p_value'])}")
        if "summary" in out:
            print(f"\n{'PASS' if out['passed'] else 'FAIL'}: {out['summary']}")
        print("Scope: normal-approximation arithmetic and plan structure only; ship decisions need a human owner.")
    return code


if __name__ == "__main__":
    sys.exit(main())
