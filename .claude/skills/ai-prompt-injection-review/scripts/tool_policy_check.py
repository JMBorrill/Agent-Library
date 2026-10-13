#!/usr/bin/env python3
"""Evaluate proposed agent tool calls against a tool-use policy: allow / deny / require_approval.

Each call: {"call_id", "tool", "args": {...}, "provenance": "user|system|retrieved_content|tool_output",
            "data_classification": "public|internal|confidential|personal|special_category",
            optional "expected_decision"}.
Policy: {"allowed_tools", "side_effecting_tools", "untrusted_provenance", "forbidden_domains",
         "allowed_egress_domains", "personal_data_classifications", "pii_egress_allowed_domains"}.

Rules (most restrictive decision wins: deny > require_approval > allow):
  TP-UNKNOWN-TOOL            tool not allowlisted                                  -> deny
  TP-BAD-PROVENANCE          provenance missing/unknown (treated as untrusted)      -> deny
  TP-UNTRUSTED-SIDE-EFFECT   side-effecting tool requested by retrieved content or
                             tool output (indirect prompt injection path)          -> deny
  TP-FORBIDDEN-DESTINATION   any URL/email/host in args on a forbidden domain       -> deny
  TP-PII-EGRESS              personal data to a domain not allowed for personal data -> deny
  TP-EGRESS-UNLISTED         side-effecting call to a domain outside allowed egress -> require_approval
  TP-CLASSIFICATION-MISMATCH args contain PII patterns but classification says it is
                             not personal data                                    -> require_approval
  TP-INJECTION-IN-ARGS       args contain instruction-override phrases              -> require_approval
  TP-SIDE-EFFECT-APPROVAL    side-effecting tool from user/system                   -> require_approval
  TP-DATA-CLASSIFICATION     unknown classification (treated as personal)           -> require_approval
Domains match exactly or as subdomains.

Usage:
  tool_policy_check.py calls.json --policy policy.json [--expect] [--json]
Exit codes: 0 every call allowed (or, with --expect, every decision matched expected_decision);
            1 any call denied / needing approval (or, with --expect, any mismatch); 2 bad input.

Scope: deterministic policy evaluation of the calls as described. It does not see calls the agent
never reports, cannot verify provenance labels, and is one layer of defence, not a guarantee.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

PROVENANCE = {"user", "system", "retrieved_content", "tool_output"}
CLASSIFICATIONS = {"public", "internal", "confidential", "personal", "special_category"}
DECISIONS = ("allow", "require_approval", "deny")
RANK = {d: i for i, d in enumerate(DECISIONS)}
URL_RE = re.compile(r"https?://[^\s\"'<>)]+", re.I)
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@([A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)+)\b")
HOST_KEYS = {"domain", "host", "hostname"}
ADDRESS_KEYS = {"to", "cc", "bcc", "from", "recipient", "recipients", "url", "reply_to"}
PII_RES = [re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
           re.compile(r"\b[A-Z]{2}\s?\d{2}\s?\d{2}\s?\d{2}\s?[A-D]\b"),
           re.compile(r"(?<![\d])(?:\+44\s?7\d{3}|07\d{3})\s?\d{3}\s?\d{3}(?!\d)")]
INJECTION_RE = re.compile(
    r"\b(?:ignore|disregard|forget)\b[^.\n]{0,40}\b(?:previous|prior|above|all|your)\b[^.\n]{0,30}\binstructions?\b"
    r"|\byou are now\b|\bsystem prompt\b", re.I)


class PolicyError(ValueError):
    pass


def _walk_strings(obj, key: str = ""):
    if isinstance(obj, str):
        yield key, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk_strings(v, str(k))
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_strings(v, key)


def destinations(args) -> set[str]:
    """Hostnames/email domains referenced anywhere in the call arguments (lower-case)."""
    out: set[str] = set()
    for key, s in _walk_strings(args):
        for u in URL_RE.findall(s):
            host = urlparse(u).hostname
            if host:
                out.add(host.lower().rstrip("."))
        for dom in EMAIL_RE.findall(s):
            out.add(dom.lower().rstrip("."))
        if key.lower() in HOST_KEYS and re.fullmatch(r"[A-Za-z0-9.\-]+", s.strip()):
            out.add(s.strip().lower().rstrip("."))
    return out


def domain_in(host: str, domains) -> bool:
    return any(host == d or host.endswith("." + d) for d in (x.lower() for x in domains))


def validate_policy(policy) -> None:
    if not isinstance(policy, dict):
        raise PolicyError("policy must be a JSON object")
    for key in ("allowed_tools", "side_effecting_tools"):
        if not isinstance(policy.get(key), list):
            raise PolicyError(f"policy.{key} must be a list")
    for key in ("forbidden_domains", "allowed_egress_domains", "pii_egress_allowed_domains",
                "untrusted_provenance", "personal_data_classifications"):
        if key in policy and not isinstance(policy[key], list):
            raise PolicyError(f"policy.{key} must be a list")
    unknown = set(policy["side_effecting_tools"]) - set(policy["allowed_tools"])
    if unknown:
        raise PolicyError(f"side_effecting_tools not in allowed_tools: {sorted(unknown)}")


def decide(call: dict, policy: dict) -> dict:
    reasons: list[dict] = []

    def add(decision: str, rule: str, msg: str) -> None:
        reasons.append({"decision": decision, "rule": rule, "message": msg})

    tool = call.get("tool")
    args = call.get("args", {})
    prov = call.get("provenance")
    cls = call.get("data_classification", "")
    untrusted = set(policy.get("untrusted_provenance", ["retrieved_content", "tool_output"]))
    side_effecting = tool in set(policy["side_effecting_tools"])
    personal = set(policy.get("personal_data_classifications", ["personal", "special_category"]))

    if tool not in set(policy["allowed_tools"]):
        add("deny", "TP-UNKNOWN-TOOL", f"tool {tool!r} is not allowlisted")
    if prov not in PROVENANCE:
        add("deny", "TP-BAD-PROVENANCE", f"provenance {prov!r} unknown; treated as untrusted")
        prov_untrusted = True
    else:
        prov_untrusted = prov in untrusted
    if side_effecting and prov_untrusted:
        add("deny", "TP-UNTRUSTED-SIDE-EFFECT",
            f"side-effecting tool {tool!r} requested by {prov} content (possible indirect injection)")
    if cls not in CLASSIFICATIONS:
        add("require_approval", "TP-DATA-CLASSIFICATION", f"classification {cls!r} unknown; treated as personal")
        is_personal = True
    else:
        is_personal = cls in personal
    dests = destinations(args)
    for host in sorted(dests):
        if domain_in(host, policy.get("forbidden_domains", [])):
            add("deny", "TP-FORBIDDEN-DESTINATION", f"destination {host} is forbidden")
        elif is_personal and side_effecting and not domain_in(host, policy.get("pii_egress_allowed_domains", [])):
            add("deny", "TP-PII-EGRESS", f"{cls or 'personal'} data may not be sent to {host}")
        elif side_effecting and "allowed_egress_domains" in policy and not domain_in(host, policy["allowed_egress_domains"]):
            add("require_approval", "TP-EGRESS-UNLISTED", f"destination {host} is not on the egress allowlist")
    strings = [s for _, s in _walk_strings(args)]
    content = [s for k, s in _walk_strings(args) if k.lower() not in ADDRESS_KEYS]
    if not is_personal and any(p.search(s) for p in PII_RES for s in content):
        add("require_approval", "TP-CLASSIFICATION-MISMATCH",
            f"arguments look like they contain personal data but classification is {cls!r}")
    if any(INJECTION_RE.search(s) for s in strings):
        add("require_approval", "TP-INJECTION-IN-ARGS", "arguments contain instruction-override phrasing")
    if side_effecting and not prov_untrusted:
        add("require_approval", "TP-SIDE-EFFECT-APPROVAL", f"side-effecting tool {tool!r} needs human approval")
    decision = max((r["decision"] for r in reasons), key=RANK.__getitem__, default="allow")
    if not reasons:
        reasons.append({"decision": "allow", "rule": "TP-ALLOW", "message": "allowlisted, not side-effecting, no restricted destination or content"})
    return {"call_id": str(call.get("call_id", "?")), "tool": tool, "provenance": prov,
            "decision": decision, "reasons": reasons, "destinations": sorted(dests)}


def evaluate(calls: list[dict], policy: dict, expect: bool = False) -> dict:
    results = []
    for c in calls:
        r = decide(c, policy)
        if expect:
            r["expected_decision"] = c.get("expected_decision")
            r["matches_expected"] = r["expected_decision"] == r["decision"]
        results.append(r)
    counts = {d: sum(r["decision"] == d for r in results) for d in DECISIONS}
    summary = {"calls": len(results), **counts}
    findings = []
    for r in results:
        if r["decision"] != "allow":
            sev = "error" if r["decision"] == "deny" else "warning"
            for reason in r["reasons"]:
                findings.append({"id": r["call_id"], "severity": sev,
                                 "rule": reason["rule"].lower(), "message": reason["message"]})
    if expect:
        mism = [r["call_id"] for r in results if not r["matches_expected"]]
        summary["mismatches"] = mism
        summary["expected_agreement"] = round((len(results) - len(mism)) / len(results), 4) if results else None
        passed = not mism
    else:
        passed = counts["deny"] == 0 and counts["require_approval"] == 0
    return {"decisions": results, "summary": summary, "findings": findings, "passed": passed}


def load_calls(data) -> list[dict]:
    calls = data.get("calls") if isinstance(data, dict) else data
    if not isinstance(calls, list):
        raise PolicyError("calls file must be a list or an object with a 'calls' list")
    for i, c in enumerate(calls):
        if not isinstance(c, dict) or not isinstance(c.get("tool"), str):
            raise PolicyError(f"call {i}: need an object with string 'tool'")
        if "args" in c and not isinstance(c["args"], dict):
            raise PolicyError(f"call {i}: 'args' must be an object")
        if c.get("expected_decision") not in (None, *DECISIONS):
            raise PolicyError(f"call {i}: expected_decision must be one of {DECISIONS}")
    return calls


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Evaluate agent tool calls against a tool-use policy.")
    ap.add_argument("calls", type=Path)
    ap.add_argument("--policy", type=Path, required=True)
    ap.add_argument("--expect", action="store_true", help="compare with each call's expected_decision")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        policy = json.loads(args.policy.read_text(encoding="utf-8"))
        validate_policy(policy)
        calls = load_calls(json.loads(args.calls.read_text(encoding="utf-8")))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, PolicyError) as exc:
        print(f"input error: {exc}", file=sys.stderr)
        return 2
    report = evaluate(calls, policy, args.expect)
    report["policy"] = {"policy_id": policy.get("policy_id"), "version": policy.get("version")}
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for r in report["decisions"]:
            tail = ""
            if args.expect:
                tail = "  (expected " + str(r["expected_decision"]) + (")" if r["matches_expected"] else ") MISMATCH")
            print(f"{r['decision'].upper():16} {r['call_id']:<10} {r['tool']} [{r['provenance']}]{tail}")
            for reason in r["reasons"]:
                print(f"    {reason['rule']:<27} {reason['message']}")
        print(f"\n{'PASS' if report['passed'] else 'FAIL'}: {report['summary']}")
        print("Scope: policy evaluation of reported calls only; provenance labels are trusted as given.")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
