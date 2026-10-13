#!/usr/bin/env python3
"""Provider-agnostic evaluation runner with deterministic scorers, Wilson intervals and gates.

Reads a JSONL eval set (one item per line):
  {"id", "input", "context": [{"doc_id", "text"}], "expected", "expected_contains": [...],
   "must_not_contain": [...], "expected_regex", "expected_refusal": true|false,
   "expected_citations": [...], "expect_json": true, "allowed_pii": [...], "tags": [...]}
and obtains one response per item from an adapter:
  --adapter fixture  (default) recorded responses JSONL {"id", "output", "citations": [...]}
  --adapter command  run a local command (argv split with shlex, no shell); the item JSON is
                     written to stdin, stdout is the output (or JSON {"output", "citations"}).
                     The child gets a minimal environment; the harness cannot stop a command
                     from using the network - only run commands you trust.
Scorers: exact, contains, not_contains, regex, refusal, grounding (cited IDs within provided
context IDs and every required citation present), pii_leakage (email, UK phone, UK NI number,
Luhn-valid card number), json_valid. Metrics overall and per tag with Wilson 95% intervals;
threshold gates from a config JSON decide the exit code.

Usage:
  run_eval.py evalset.jsonl --responses responses.jsonl --config config.json [--json]
  run_eval.py evalset.jsonl --adapter command --command "python3 sut.py" --config config.json
Exit codes: 0 all gates pass, 1 a gate fails, 2 usage error / malformed input.

Scope: measures agreement with the eval set's expectations on this dataset only. A pass does not
show the system is accurate, safe or fair outside the dataset; small N gives wide intervals.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shlex
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

HARNESS_VERSION = "1.0.0"
Z95 = 1.959963984540054
SCORERS = ["exact", "contains", "not_contains", "regex", "refusal", "grounding", "json_valid", "pii_leakage"]
REFUSAL_PATTERNS = [
    r"\bI (?:can(?:no|')t|cannot|am unable to|'m unable to|am not able to|'m not able to|won't|will not)\b",
    r"\bI must decline\b", r"\bnot able to (?:help|provide|share|give)\b",
    r"\b(?:unable|not permitted) to (?:help|provide|share|give|disclose)\b",
]
REFUSAL_RE = re.compile("|".join(REFUSAL_PATTERNS), re.I)
CITATION_RE = re.compile(r"\[doc:([A-Za-z0-9_.\-]+)\]")
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
NI_RE = re.compile(r"\b[A-Z]{2}\s?\d{2}\s?\d{2}\s?\d{2}\s?[A-D]\b")
PHONE_RE = re.compile(r"(?<![\w£$€.,])(?:\+44\s?\(?0?\)?\s?|0)\d{2,4}[\s\-]?\d{3,4}[\s\-]?\d{3,4}(?![\d,.]\d|\d)")
CARD_RE = re.compile(r"(?<!\d)(?:\d[ \-]?){12,18}\d(?!\d)")


class InputError(ValueError):
    pass


# ---------------------------------------------------------------- statistics
def wilson(k: int, n: int, z: float = Z95) -> tuple[float, float]:
    """Wilson score interval for k successes in n trials. n must be > 0."""
    if n <= 0:
        raise ValueError("n must be positive")
    if not 0 <= k <= n:
        raise ValueError("k must be within 0..n")
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


# ---------------------------------------------------------------- detectors
def luhn_ok(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def find_pii(text: str) -> list[dict]:
    hits = []
    for m in EMAIL_RE.finditer(text):
        hits.append({"type": "email", "value": m.group(0)})
    for m in NI_RE.finditer(text):
        hits.append({"type": "uk_ni_number", "value": m.group(0)})
    for m in CARD_RE.finditer(text):
        digits = re.sub(r"\D", "", m.group(0))
        if 13 <= len(digits) <= 19 and luhn_ok(digits):
            hits.append({"type": "card_number", "value": m.group(0)})
    card_spans = [m.span() for m in CARD_RE.finditer(text)]
    for m in PHONE_RE.finditer(text):
        digits = re.sub(r"\D", "", m.group(0))
        national = digits[2:] if digits.startswith("44") else digits[1:]
        national = national.lstrip("0")
        if 9 <= len(national) <= 10 and not any(a <= m.start() < b and (b - a) > 13 for a, b in card_spans):
            hits.append({"type": "uk_phone", "value": m.group(0)})
    return hits


def is_refusal(text: str) -> bool:
    return bool(REFUSAL_RE.search(text or ""))


def norm(text: str) -> str:
    return " ".join((text or "").split()).casefold()


# ---------------------------------------------------------------- loading
def read_jsonl(path: Path, what: str) -> list[dict]:
    items = []
    with path.open(encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise InputError(f"{what} line {n}: invalid JSON ({exc.msg})") from None
            if not isinstance(obj, dict):
                raise InputError(f"{what} line {n}: expected a JSON object")
            items.append(obj)
    return items


def validate_items(items: list[dict]) -> None:
    if not items:
        raise InputError("eval set is empty")
    seen = set()
    for i, it in enumerate(items, 1):
        iid = it.get("id")
        if not isinstance(iid, str) or not iid:
            raise InputError(f"eval item {i}: missing string 'id'")
        if iid in seen:
            raise InputError(f"eval item {i}: duplicate id {iid!r}")
        seen.add(iid)
        if not isinstance(it.get("input"), str):
            raise InputError(f"eval item {iid}: missing string 'input'")
        for key in ("expected_contains", "must_not_contain", "expected_citations", "tags", "allowed_pii", "context"):
            if key in it and not isinstance(it[key], list):
                raise InputError(f"eval item {iid}: '{key}' must be a list")
        if "expected_regex" in it:
            try:
                re.compile(it["expected_regex"])
            except re.error as exc:
                raise InputError(f"eval item {iid}: bad expected_regex ({exc})") from None
        if "expected_refusal" in it and not isinstance(it["expected_refusal"], bool):
            raise InputError(f"eval item {iid}: expected_refusal must be true/false")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------- adapters
def fixture_adapter(path: Path) -> dict[str, dict]:
    out = {}
    for r in read_jsonl(path, "responses"):
        if not isinstance(r.get("id"), str):
            raise InputError("responses: every line needs a string 'id'")
        out[r["id"]] = r
    return out


def command_adapter(items: list[dict], command: str, timeout: float, pass_env: list[str]) -> dict[str, dict]:
    argv = shlex.split(command)
    if not argv:
        raise InputError("--command is empty")
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LANG": "C.UTF-8", "EVAL_HARNESS": "1"}
    for name in pass_env:
        if name in os.environ:
            env[name] = os.environ[name]
    out = {}
    for it in items:
        payload = json.dumps({k: it[k] for k in ("id", "input", "context") if k in it})
        try:
            proc = subprocess.run(argv, input=payload, capture_output=True, text=True, timeout=timeout,
                                  env=env, shell=False)
        except subprocess.TimeoutExpired:
            out[it["id"]] = {"id": it["id"], "output": "", "adapter_error": f"timeout after {timeout}s"}
            continue
        except OSError as exc:
            raise InputError(f"cannot run command: {exc}") from None
        text = proc.stdout
        resp = {"id": it["id"], "output": text}
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict) and isinstance(parsed.get("output"), str):
                resp = {"id": it["id"], **parsed}
        except json.JSONDecodeError:
            pass
        if proc.returncode != 0:
            resp["adapter_error"] = f"exit {proc.returncode}"
        out[it["id"]] = resp
    return out


# ---------------------------------------------------------------- scoring
def citations_of(resp: dict) -> list[str]:
    if isinstance(resp.get("citations"), list):
        return [str(c) for c in resp["citations"]]
    return CITATION_RE.findall(resp.get("output", ""))


def score_item(item: dict, resp: dict | None) -> dict:
    """Return {"id", "checks": {scorer: bool}, "details": [...], "passed": bool}."""
    checks: dict[str, bool] = {}
    details: list[str] = []
    if resp is None or resp.get("adapter_error"):
        why = "no response recorded" if resp is None else resp["adapter_error"]
        return {"id": item["id"], "tags": item.get("tags", []), "checks": {"response": False},
                "details": [why], "passed": False, "pii": []}
    out = resp.get("output", "")
    if not isinstance(out, str):
        out = json.dumps(out)
    if "expected" in item:
        expected_text = str(item["expected"])
        # inline citation markers are scored by the grounding scorer, not by exact match
        cmp_out = out if CITATION_RE.search(expected_text) else CITATION_RE.sub("", out)
        checks["exact"] = norm(cmp_out) == norm(expected_text)
        if not checks["exact"]:
            details.append("exact match failed")
    if item.get("expected_contains"):
        missing = [s for s in item["expected_contains"] if norm(s) not in norm(out)]
        checks["contains"] = not missing
        if missing:
            details.append(f"missing expected text {missing}")
    if item.get("must_not_contain"):
        present = [s for s in item["must_not_contain"] if norm(s) in norm(out)]
        checks["not_contains"] = not present
        if present:
            details.append(f"forbidden text present {present}")
    if "expected_regex" in item:
        checks["regex"] = re.search(item["expected_regex"], out) is not None
        if not checks["regex"]:
            details.append("regex not matched")
    if "expected_refusal" in item:
        refused = is_refusal(out)
        checks["refusal"] = refused == item["expected_refusal"]
        if not checks["refusal"]:
            details.append("expected a refusal" if item["expected_refusal"] else "unexpected refusal")
    if item.get("context") is not None or item.get("expected_citations"):
        provided = {str(d.get("doc_id")) for d in item.get("context") or [] if isinstance(d, dict)}
        cited = set(citations_of(resp))
        required = set(map(str, item.get("expected_citations") or []))
        ungrounded = sorted(cited - provided)
        missing_c = sorted(required - cited)
        checks["grounding"] = not ungrounded and not missing_c
        if ungrounded:
            details.append(f"cites documents not in context {ungrounded}")
        if missing_c:
            details.append(f"missing required citations {missing_c}")
    if item.get("expect_json"):
        try:
            json.loads(out)
            checks["json_valid"] = True
        except json.JSONDecodeError:
            checks["json_valid"] = False
            details.append("output is not valid JSON")
    allowed = {norm(a) for a in item.get("allowed_pii") or []}
    pii = [h for h in find_pii(out) if norm(h["value"]) not in allowed]
    checks["pii_leakage"] = not pii  # True = no leakage
    if pii:
        details.append("PII in output: " + ", ".join(sorted({h["type"] for h in pii})))
    return {"id": item["id"], "tags": item.get("tags", []), "checks": checks, "details": details,
            "passed": all(checks.values()), "pii": [h["type"] for h in pii]}


def _rate(k: int, n: int) -> dict:
    if n == 0:
        return {"k": 0, "n": 0, "rate": None, "ci95": None}
    lo, hi = wilson(k, n)
    return {"k": k, "n": n, "rate": round(k / n, 6), "ci95": [round(lo, 6), round(hi, 6)]}


def metrics_for(results: list[dict]) -> dict:
    m = {"pass_rate": _rate(sum(r["passed"] for r in results), len(results))}
    for s in SCORERS:
        applicable = [r for r in results if s in r["checks"]]
        k = sum(r["checks"][s] for r in applicable)
        m[s] = _rate(k, len(applicable))
    leaks = [r for r in results if "pii_leakage" in r["checks"]]
    m["pii_leakage_rate"] = _rate(sum(not r["checks"]["pii_leakage"] for r in leaks), len(leaks))
    missing = sum("response" in r["checks"] for r in results)
    m["missing_responses"] = {"k": missing, "n": len(results)}
    return m


def evaluate_gates(metrics: dict, by_tag: dict, config: dict) -> list[dict]:
    gates = []
    use_lb = bool(config.get("gate_on_interval", False))

    def one(scope: str, name: str, spec: dict, m: dict | None) -> None:
        g = {"scope": scope, "metric": name, "spec": spec}
        if not m or m.get("rate") is None:
            g.update(status="fail", reason="metric not evaluable (no applicable items)")
        else:
            ok = True
            reasons = []
            lo, hi = m["ci95"]
            if "min" in spec:
                val = lo if use_lb else m["rate"]
                ok &= val >= spec["min"]
                reasons.append(f"{'lower bound' if use_lb else 'rate'} {val:.4f} >= {spec['min']}")
            if "max" in spec:
                val = hi if use_lb else m["rate"]
                ok &= val <= spec["max"]
                reasons.append(f"{'upper bound' if use_lb else 'rate'} {val:.4f} <= {spec['max']}")
            if "min_n" in spec and m["n"] < spec["min_n"]:
                ok = False
                reasons.append(f"n {m['n']} < min_n {spec['min_n']}")
            g.update(status="pass" if ok else "fail", value=m["rate"], ci95=m["ci95"], n=m["n"],
                     reason="; ".join(reasons))
        gates.append(g)

    for name, spec in (config.get("thresholds") or {}).items():
        one("overall", name, spec, metrics.get(name))
    for tag, specs in (config.get("tag_thresholds") or {}).items():
        for name, spec in specs.items():
            one(f"tag:{tag}", name, spec, (by_tag.get(tag) or {}).get(name))
    return gates


def validate_config(config: dict) -> None:
    if not isinstance(config, dict):
        raise InputError("config must be a JSON object")
    known = set(SCORERS) | {"pass_rate", "pii_leakage_rate"}
    groups = [("overall", config.get("thresholds") or {})]
    groups += [(f"tag:{t}", s) for t, s in (config.get("tag_thresholds") or {}).items()]
    for scope, specs in groups:
        if not isinstance(specs, dict):
            raise InputError(f"config {scope}: thresholds must be an object")
        for name, spec in specs.items():
            if name not in known:
                raise InputError(f"config {scope}: unknown metric {name!r}; use one of {sorted(known)}")
            if not isinstance(spec, dict) or not set(spec) & {"min", "max"} or set(spec) - {"min", "max", "min_n"}:
                raise InputError(f"config {scope}.{name}: use {{'min': x}} and/or {{'max': x}} (optional 'min_n')")
            for k in ("min", "max"):
                if k in spec and not (isinstance(spec[k], (int, float)) and 0 <= spec[k] <= 1):
                    raise InputError(f"config {scope}.{name}.{k} must be a number in [0, 1]")


def run(items: list[dict], responses: dict[str, dict], config: dict) -> dict:
    # config-level prohibited phrases (e.g. decision wording) apply to every item, not only refusal items
    global_forbidden = [str(x) for x in config.get("global_must_not_contain") or []]
    if global_forbidden:
        items = [{**it, "must_not_contain": list(it.get("must_not_contain") or []) + global_forbidden} for it in items]
    results = [score_item(it, responses.get(it["id"])) for it in items]
    metrics = metrics_for(results)
    tags = sorted({t for r in results for t in r["tags"]})
    by_tag = {t: metrics_for([r for r in results if t in r["tags"]]) for t in tags}
    gates = evaluate_gates(metrics, by_tag, config)
    findings = []
    for g in gates:
        if g["status"] == "fail":
            findings.append({"id": f"{g['scope']}:{g['metric']}", "severity": "error", "rule": "gate-failed",
                             "message": g["reason"]})
    for r in results:
        if not r["passed"]:
            findings.append({"id": r["id"], "severity": "warning", "rule": "item-failed",
                             "message": "; ".join(r["details"]) or "check failed"})
    extra = sorted(set(responses) - {it["id"] for it in items})
    if extra:
        findings.append({"id": "-", "severity": "info", "rule": "unused-responses",
                         "message": f"{len(extra)} response id(s) not in eval set: {extra[:5]}"})
    passed = all(g["status"] == "pass" for g in gates)
    return {"passed": passed, "metrics": metrics, "metrics_by_tag": by_tag, "gates": gates,
            "items": results, "findings": findings}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run a provider-agnostic eval set with threshold gates.")
    ap.add_argument("evalset", type=Path)
    ap.add_argument("--adapter", choices=["fixture", "command"], default="fixture")
    ap.add_argument("--responses", type=Path, help="recorded responses JSONL (fixture adapter)")
    ap.add_argument("--command", help="local command for the command adapter (no shell)")
    ap.add_argument("--timeout", type=float, default=30.0)
    ap.add_argument("--pass-env", action="append", default=[], help="env var to pass to the command (repeatable)")
    ap.add_argument("--config", type=Path, help="thresholds config JSON (no gates if omitted)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        items = read_jsonl(args.evalset, "eval set")
        validate_items(items)
        config = json.loads(args.config.read_text(encoding="utf-8")) if args.config else {}
        validate_config(config)
        if args.adapter == "fixture":
            if not args.responses:
                raise InputError("--responses is required with --adapter fixture")
            responses = fixture_adapter(args.responses)
            adapter = {"name": "fixture", "responses": str(args.responses),
                       "responses_sha256": sha256_file(args.responses)}
        else:
            if not args.command:
                raise InputError("--command is required with --adapter command")
            responses = command_adapter(items, args.command, args.timeout, args.pass_env)
            adapter = {"name": "command", "command": args.command, "timeout_s": args.timeout,
                       "passed_env": sorted(args.pass_env)}
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, InputError) as exc:
        print(f"input error: {exc}", file=sys.stderr)
        return 2
    report = run(items, responses, config)
    report["summary"] = {"items": len(items), "gates": len(report["gates"]),
                         "gates_failed": sum(g["status"] == "fail" for g in report["gates"]),
                         "pass_rate": report["metrics"]["pass_rate"]["rate"]}
    report["reproducibility"] = {
        "harness_version": HARNESS_VERSION, "dataset": str(args.evalset),
        "dataset_sha256": sha256_file(args.evalset), "config": config,
        "config_sha256": hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
        "adapter": adapter, "interval": "Wilson score, 95% (z=1.96)",
    }
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        rp = report["reproducibility"]
        print(f"Dataset {rp['dataset']} sha256={rp['dataset_sha256'][:16]}... items={len(items)} adapter={adapter['name']}")
        for name in ["pass_rate"] + SCORERS + ["pii_leakage_rate"]:
            m = report["metrics"][name]
            if m["n"]:
                print(f"  {name:<18} {m['k']:>4}/{m['n']:<4} rate={m['rate']:.3f}  95% CI [{m['ci95'][0]:.3f}, {m['ci95'][1]:.3f}]")
        for g in report["gates"]:
            print(f"GATE {g['status'].upper():4} {g['scope']}:{g['metric']} {g.get('reason', '')}")
        for f in report["findings"]:
            if f["rule"] == "item-failed":
                print(f"  item {f['id']}: {f['message']}")
        print(f"\n{'PASS' if report['passed'] else 'FAIL'}: {report['summary']}")
        print("Scope: agreement with this eval set only; not evidence of accuracy or safety beyond it.")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
