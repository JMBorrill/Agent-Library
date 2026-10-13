#!/usr/bin/env python3
"""Validate a STRIDE-style data-flow threat model (JSON) and its OWASP ASVS 5.0.0 mitigation mapping.

Checks: structure and cross-references (components, assets, trust boundaries, flows, threats);
every trust-boundary-crossing data flow has at least one threat per required STRIDE category
(default T,I,D per flow; configurable globally or per flow, with justified not-applicable
entries); likelihood x impact risk rating; unmitigated or unowned high risks; mitigation ASVS IDs
are version-qualified (v5.0.0-<chapter>.<section>.<req>) and exist in the bundled ASVS index;
multi-tenant systems model tenant-isolation threats.

Usage:
  threat_model_check.py model.json [--categories TID] [--asvs-index PATH] [--strict] [--json]
Exit codes: 0 no errors, 1 errors, 2 unreadable input.

Scope: checks completeness and consistency of the model as written. It cannot discover threats the
team did not think of, nor confirm that a cited ASVS requirement actually mitigates the threat.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

DEFAULT_INDEX = Path(__file__).resolve().parents[1] / "assets" / "data" / "asvs-5.0.0-index.json"
ASVS_VERSION = "5.0.0"
STRIDE = {"S": "Spoofing", "T": "Tampering", "R": "Repudiation", "I": "Information disclosure",
          "D": "Denial of service", "E": "Elevation of privilege"}
STRIDE_BY_NAME = {v.lower(): k for k, v in STRIDE.items()}
DEFAULT_FLOW_CATEGORIES = "TID"  # STRIDE-per-element convention for data flows
SCALE = {"low": 1, "medium": 2, "high": 3}
COMPONENT_TYPES = {"external_entity", "process", "data_store"}
THREAT_STATUSES = {"open", "mitigated", "accepted", "transferred"}
MITIGATION_STATUSES = {"planned", "implemented", "verified"}
CLEARTEXT = {"http", "ftp", "telnet", "smtp", "ldap", "plain-tcp", "unencrypted"}
ASVS_ID = re.compile(r"^(?:ASVS-)?v(\d+\.\d+\.\d+)-(\d+)\.(\d+)\.(\d+)$")
BARE_ID = re.compile(r"^V?(\d+)\.(\d+)\.(\d+)$")


def _finding(fid: str, severity: str, rule: str, message: str) -> dict:
    return {"id": fid, "severity": severity, "rule": rule, "message": message}


def load_index(path: Path) -> dict[str, int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != ASVS_VERSION:
        raise ValueError(f"ASVS index version {data.get('version')} != {ASVS_VERSION}")
    return {r["id"]: int(r["level"]) for r in data["requirements"]}


def stride_code(value: str) -> str | None:
    v = (value or "").strip()
    if v.upper() in STRIDE:
        return v.upper()
    return STRIDE_BY_NAME.get(v.lower())


def risk_rating(likelihood: str, impact: str) -> str | None:
    lk, im = SCALE.get((likelihood or "").lower()), SCALE.get((impact or "").lower())
    if lk is None or im is None:
        return None
    score = lk * im
    return "high" if score >= 6 else ("medium" if score >= 3 else "low")


def check_asvs_id(raw: str, index: dict[str, int]) -> tuple[str | None, str | None]:
    """Return (normalised 'v5.0.0-x.y.z' or None, error rule or None)."""
    s = (raw or "").strip()
    m = ASVS_ID.match(s)
    if not m:
        return None, ("asvs-unversioned" if BARE_ID.match(s) else "asvs-bad-format")
    if m.group(1) != ASVS_VERSION:
        return None, "asvs-version-mismatch"
    rid = f"{m.group(2)}.{m.group(3)}.{m.group(4)}"
    if rid not in index:
        return None, "asvs-unknown-id"
    return f"v{ASVS_VERSION}-{rid}", None


def check(model: dict, index: dict[str, int], categories: str = DEFAULT_FLOW_CATEGORIES) -> dict:
    findings: list[dict] = []
    add = lambda *a: findings.append(_finding(*a))  # noqa: E731
    for key in ("system", "owner", "components", "data_flows", "threats", "assets", "trust_boundaries"):
        if key not in model or model[key] in (None, "", []):
            add("-", "error", "missing-field", f"top-level '{key}' missing or empty")
    comps = {c.get("id"): c for c in model.get("components", []) if isinstance(c, dict)}
    assets = {a.get("id"): a for a in model.get("assets", []) if isinstance(a, dict)}
    bounds = {b.get("id"): b for b in model.get("trust_boundaries", []) if isinstance(b, dict)}
    flows = {f.get("id"): f for f in model.get("data_flows", []) if isinstance(f, dict)}
    threats = [t for t in model.get("threats", []) if isinstance(t, dict)]
    ids = [x.get("id") for coll in ("components", "assets", "trust_boundaries", "data_flows", "threats")
           for x in model.get(coll, []) if isinstance(x, dict)]
    for dup, n in Counter(ids).items():
        if n > 1:
            add(str(dup), "error", "duplicate-id", f"identifier used {n} times")
    for cid, c in comps.items():
        if c.get("type") not in COMPONENT_TYPES:
            add(str(cid), "error", "component-type", f"type '{c.get('type')}' not in {sorted(COMPONENT_TYPES)}")
    for fid, f in flows.items():
        for end in ("from", "to"):
            if f.get(end) not in comps:
                add(str(fid), "error", "unknown-component", f"flow '{end}' references unknown component '{f.get(end)}'")
        for a in f.get("data", []):
            if a not in assets:
                add(str(fid), "error", "unknown-asset", f"flow carries unknown asset '{a}'")
        if not isinstance(f.get("crosses_boundary"), bool):
            add(str(fid), "error", "crossing-flag", "crosses_boundary must be true or false")
        if f.get("crosses_boundary"):
            if not f.get("boundary"):
                add(str(fid), "error", "boundary-missing", "boundary-crossing flow names no trust boundary")
            elif f["boundary"] not in bounds:
                add(str(fid), "error", "unknown-boundary", f"unknown trust boundary '{f['boundary']}'")
            sensitive = [a for a in f.get("data", []) if assets.get(a, {}).get("classification") in
                         {"confidential", "restricted"}]
            if sensitive and str(f.get("protocol", "")).lower() in CLEARTEXT:
                add(str(fid), "error", "cleartext-crossing",
                    f"sensitive asset(s) {sensitive} cross a trust boundary over '{f.get('protocol')}'")
    # threats
    by_target: dict[str, set[str]] = {}
    cited: set[str] = set()
    risk_count: Counter = Counter()
    stride_count: Counter = Counter()
    tenant_threats = []
    for t in threats:
        tid = str(t.get("id", "<no id>"))
        code = stride_code(t.get("stride", ""))
        if code is None:
            add(tid, "error", "stride-category", f"'{t.get('stride')}' is not a STRIDE category")
        else:
            stride_count[code] += 1
        targets = t.get("targets") or []
        if not targets:
            add(tid, "error", "no-target", "threat has no target flow/component")
        for tg in targets:
            if tg not in flows and tg not in comps:
                add(tid, "error", "unknown-target", f"target '{tg}' is not a flow or component")
            elif code:
                by_target.setdefault(tg, set()).add(code)
        risk = risk_rating(t.get("likelihood", ""), t.get("impact", ""))
        if risk is None:
            add(tid, "error", "risk-rating", "likelihood and impact must each be low|medium|high")
        else:
            risk_count[risk] += 1
        status = (t.get("status") or "open").lower()
        if status not in THREAT_STATUSES:
            add(tid, "error", "threat-status", f"status '{t.get('status')}' not in {sorted(THREAT_STATUSES)}")
        mits = t.get("mitigations") or []
        live = [m for m in mits if (m.get("status") or "planned").lower() in {"implemented", "verified"}]
        for m in mits:
            if (m.get("status") or "planned").lower() not in MITIGATION_STATUSES:
                add(tid, "error", "mitigation-status", f"mitigation status '{m.get('status')}' invalid")
            refs = m.get("asvs") or []
            if not refs:
                add(tid, "warning", "mitigation-unmapped", f"mitigation '{m.get('description', '')[:50]}' cites no ASVS ID")
            for raw in refs:
                norm, err = check_asvs_id(raw, index)
                if err:
                    add(tid, "error", err, f"ASVS reference '{raw}' — use v{ASVS_VERSION}-<chapter>.<section>.<req> "
                        "present in the index")
                else:
                    cited.add(norm)
        if status in {"accepted", "transferred"}:
            if not t.get("accepted_by") or not t.get("acceptance_rationale"):
                add(tid, "error", "acceptance-incomplete", f"{status} threat needs accepted_by and acceptance_rationale")
            elif risk == "high":
                add(tid, "info", "high-risk-accepted", f"high risk {status} by {t.get('accepted_by')}: needs recorded "
                    "risk-owner sign-off")
        elif risk == "high" and not mits:
            add(tid, "error", "unmitigated-high", "high-risk threat has no mitigation and is not accepted/transferred")
        elif risk == "high" and not live:
            add(tid, "warning", "high-mitigation-planned-only", "high-risk threat mitigations are only planned")
        if status == "mitigated" and not live:
            add(tid, "error", "mitigated-without-implementation", "status 'mitigated' but no implemented/verified mitigation")
        if t.get("tenant_isolation") is True:
            tenant_threats.append(t)
    # coverage of boundary-crossing flows
    coverage = {}
    for fid, f in flows.items():
        if not f.get("crosses_boundary"):
            continue
        required = (f.get("required_categories") or categories).upper()
        na = f.get("not_applicable") or {}
        for k, why in na.items():
            if not str(why).strip():
                add(str(fid), "error", "na-without-justification", f"category {k} marked not applicable without reason")
        have = by_target.get(fid, set())
        missing = [c for c in required if c in STRIDE and c not in have and not str(na.get(c, "")).strip()]
        coverage[str(fid)] = {"required": required, "covered": "".join(sorted(have)), "missing": "".join(missing)}
        if missing:
            add(str(fid), "error", "missing-stride-coverage",
                "boundary-crossing flow lacks threats for " + ", ".join(f"{c} ({STRIDE[c]})" for c in missing))
    if model.get("multi_tenant") is True:
        if not tenant_threats:
            add("-", "error", "no-tenant-isolation-threat",
                "multi-tenant system models no tenant-isolation threat (cross-tenant read/write, tenant ID spoofing)")
        for t in tenant_threats:
            refs = [r for m in t.get("mitigations") or [] for r in m.get("asvs") or []]
            if t.get("status", "open") not in {"accepted", "transferred"} and not any(
                    re.search(r"-8\.\d+\.\d+$", r) for r in refs):
                add(str(t.get("id")), "warning", "tenant-threat-no-authz-control",
                    "tenant-isolation threat cites no ASVS V8 (Authorization) requirement")
    level = model.get("asvs_target_level")
    if level in (1, 2, 3):
        above = sorted(c for c in cited if index[c.split("-", 1)[1]] > level)
        if above:
            add("-", "info", "asvs-above-target-level", f"{len(above)} cited requirement(s) above L{level}: {above[:5]}")
    sev = Counter(f["severity"] for f in findings)
    summary = {"system": model.get("system"), "components": len(comps), "data_flows": len(flows),
               "boundary_crossing_flows": sum(1 for f in flows.values() if f.get("crosses_boundary")),
               "threats": len(threats), "by_stride": dict(stride_count), "by_risk": dict(risk_count),
               "asvs_ids_cited": sorted(cited), "coverage": coverage,
               "errors": sev.get("error", 0), "warnings": sev.get("warning", 0), "info": sev.get("info", 0)}
    return {"findings": findings, "summary": summary}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate a STRIDE data-flow threat model.")
    ap.add_argument("model", type=Path)
    ap.add_argument("--categories", default=DEFAULT_FLOW_CATEGORIES,
                    help="STRIDE letters required per boundary-crossing flow (default TID)")
    ap.add_argument("--asvs-index", type=Path, default=DEFAULT_INDEX)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if set(args.categories.upper()) - set(STRIDE):
        print(f"--categories must use letters from {''.join(STRIDE)}", file=sys.stderr)
        return 2
    try:
        model = json.loads(args.model.read_text(encoding="utf-8"))
        if not isinstance(model, dict):
            raise ValueError("model must be a JSON object")
        index = load_index(args.asvs_index)
    except (OSError, UnicodeDecodeError, ValueError, KeyError) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 2
    result = check(model, index, args.categories.upper())
    s = result["summary"]
    failed = s["errors"] > 0 or (args.strict and s["warnings"] > 0)
    result["passed"] = not failed
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for f in result["findings"]:
            print(f"{f['severity'].upper():8} {f['id']:<8} {f['rule']:<34} {f['message']}")
        print(f"\nCoverage (boundary-crossing flows): {json.dumps(s['coverage'])}")
        print(f"{'FAIL' if failed else 'PASS'}: {s['threats']} threats, {s['errors']} errors, {s['warnings']} warnings")
        print("Scope: model completeness/consistency only; not a security assessment or proof that mitigations work.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
