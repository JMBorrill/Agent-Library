#!/usr/bin/env python3
"""Evaluate proposed agent tool calls against a tool-use policy: allow / deny / require_approval.

Each call: {"call_id", "tool", "args": {...}, "provenance": "user|system|retrieved_content|tool_output",
            "data_classification": "public|internal|confidential|personal|special_category",
            optional "turn_context_provenance": [provenances present in the model's context that turn],
            optional "thread_recipients": [recipients of record for the thread], optional "expected_decision"}.
            A calls file may also set "turn_context_provenance" / "thread_recipients" at batch level;
            a call's own context list is merged with the batch one, its own recipients replace the batch ones.
Policy: {"allowed_tools", "side_effecting_tools", "untrusted_provenance", "forbidden_domains",
         "allowed_egress_domains", "personal_data_classifications", "pii_egress_allowed_domains",
         optional "taint_side_effects": "deny"|"require_approval" (default deny),
         optional "bind_recipient_to_thread": {tool: arg name | [arg names]} (or a list of tools, using
                  the default recipient args to/to_number/recipient/recipients/cc/bcc),
         optional "default_deny_unlisted_destinations": bool, "allowed_destination_domains": [...]
                  (falls back to allowed_egress_domains when absent),
         optional "tool_classification": {tool: classification} (derived classification wins)}.

Provenance tainting: effective provenance = the most untrusted of the declared provenance and every
turn-context provenance (system < user < tool_output < retrieved_content; unknown = most untrusted).
Without turn_context_provenance the declared label is trusted as given (info finding).

Rules (most restrictive decision wins: deny > require_approval > allow):
  TP-UNKNOWN-TOOL            tool not allowlisted                                  -> deny
  TP-BAD-PROVENANCE          provenance missing/unknown (treated as untrusted)      -> deny
  TP-UNTRUSTED-SIDE-EFFECT   side-effecting tool requested by retrieved content or
                             tool output (indirect prompt injection path)          -> deny
  TP-PROVENANCE-TAINTED      side-effecting tool declared user/system but proposed in a
                             turn whose context held untrusted content             -> taint_side_effects
  TP-RECIPIENT-NOT-BOUND-TO-THREAD  bound tool's recipient not in thread_recipients -> deny
  TP-THREAD-RECIPIENTS-MISSING      bound tool without thread_recipients          -> require_approval
  TP-RECIPIENT-ARG-MISSING          bound tool with no recipient argument          -> require_approval
  TP-FORBIDDEN-DESTINATION   any URL/email/host in args on a forbidden domain       -> deny
  TP-DESTINATION-NOT-ALLOWLISTED  default-deny on: side-effecting call to a destination
                             outside allowed_destination_domains (any classification) -> deny
  TP-PII-EGRESS              personal data to a domain not allowed for personal data -> deny
  TP-EGRESS-UNLISTED         side-effecting call to a domain outside allowed egress -> require_approval
  A recipient that passed thread binding is exempt from the destination-domain checks above
  (it is checked more tightly by the binding); forbidden domains still apply.
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

Advisory findings (do not change the decision): provenance-tainted (warning; declared differs from
effective provenance), provenance-untainted-trust (info; no turn context, labels trusted as given),
classification-self-declared (info; classification supplied by the caller, not derived from policy),
classification-overridden (warning; caller's classification differs from the derived one).

Scope: deterministic policy evaluation of the calls as described. It does not see calls the agent
never reports, cannot verify that turn_context_provenance or thread_recipients are complete and come
from the orchestrator/customer record, and is one layer of defence, not a guarantee.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

PROVENANCE = {"user", "system", "retrieved_content", "tool_output"}
TRUST_ORDER = {"system": 0, "user": 1, "tool_output": 2, "retrieved_content": 3}  # higher = less trusted
TAINT_OPTIONS = ("deny", "require_approval")
DEFAULT_RECIPIENT_ARGS = ("to", "to_number", "recipient", "recipients", "cc", "bcc")
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


def effective_provenance(declared, context) -> str:
    """Most untrusted of the declared provenance and every context provenance (unknown = most untrusted)."""
    worst, rank = declared, TRUST_ORDER.get(declared, 99)
    for p in context or []:
        r = TRUST_ORDER.get(p, 99)
        if r > rank:
            worst, rank = p, r
    return worst


def normalise_recipient(value: str) -> str:
    """Case-fold; for non-email values drop spaces and phone punctuation (+44 7700 900111 == +447700900111)."""
    v = value.strip().lower()
    if "@" not in v:
        v = re.sub(r"[\s\-().]", "", v)
    return v


def recipient_args(policy: dict, tool) -> list[str] | None:
    """Recipient argument names bound to the thread for this tool, or None if the tool is not bound."""
    bind = policy.get("bind_recipient_to_thread")
    if isinstance(bind, dict) and tool in bind:
        spec = bind[tool]
        return [spec] if isinstance(spec, str) else list(spec)
    if isinstance(bind, list) and tool in bind:
        return list(DEFAULT_RECIPIENT_ARGS)
    return None


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
    if policy.get("taint_side_effects", "deny") not in TAINT_OPTIONS:
        raise PolicyError(f"policy.taint_side_effects must be one of {TAINT_OPTIONS}")
    bind = policy.get("bind_recipient_to_thread")
    if bind is not None:
        if isinstance(bind, list):
            tools = bind
        elif isinstance(bind, dict):
            tools = list(bind)
            for t, spec in bind.items():
                ok = (isinstance(spec, str) and spec) or (
                    isinstance(spec, list) and spec and all(isinstance(x, str) and x for x in spec))
                if not ok:
                    raise PolicyError(f"bind_recipient_to_thread[{t!r}] must be an arg name or list of arg names")
        else:
            raise PolicyError("policy.bind_recipient_to_thread must be an object {tool: arg} or a list of tools")
        stray = set(tools) - set(policy["allowed_tools"])
        if stray:
            raise PolicyError(f"bind_recipient_to_thread tools not in allowed_tools: {sorted(stray)}")
    if not isinstance(policy.get("default_deny_unlisted_destinations", False), bool):
        raise PolicyError("policy.default_deny_unlisted_destinations must be true or false")
    if "allowed_destination_domains" in policy and not isinstance(policy["allowed_destination_domains"], list):
        raise PolicyError("policy.allowed_destination_domains must be a list")
    tc = policy.get("tool_classification", {})
    if not isinstance(tc, dict) or any(v not in CLASSIFICATIONS for v in tc.values()):
        raise PolicyError(f"policy.tool_classification must map tool -> one of {sorted(CLASSIFICATIONS)}")


def decide(call: dict, policy: dict) -> dict:
    reasons: list[dict] = []

    def add(decision: str, rule: str, msg: str) -> None:
        reasons.append({"decision": decision, "rule": rule, "message": msg})

    tool = call.get("tool")
    args = call.get("args", {})
    prov = call.get("provenance")
    context = call.get("turn_context_provenance")
    eff = effective_provenance(prov, context)
    declared_cls = call.get("data_classification", "")
    derived = policy.get("tool_classification", {}).get(tool)
    cls, cls_source = (derived, "derived") if derived else (declared_cls, "self_declared")
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
    eff_untrusted = prov_untrusted or eff not in PROVENANCE or eff in untrusted
    if side_effecting and prov_untrusted:
        add("deny", "TP-UNTRUSTED-SIDE-EFFECT",
            f"side-effecting tool {tool!r} requested by {prov} content (possible indirect injection)")
    elif side_effecting and eff_untrusted:
        add(policy.get("taint_side_effects", "deny"), "TP-PROVENANCE-TAINTED",
            f"side-effecting tool {tool!r} declared {prov!r} but proposed in a turn whose context held "
            f"{eff!r} content; effective provenance is {eff!r}")
    # recipient binding to the thread's recipients of record
    bound_ok_keys: set[str] = set()
    rargs = recipient_args(policy, tool)
    if rargs is not None:
        present = {k: v for k, v in args.items() if k in rargs}
        thread = call.get("thread_recipients")
        if not present:
            add("require_approval", "TP-RECIPIENT-ARG-MISSING",
                f"tool {tool!r} is bound to the thread but has none of the recipient args {rargs}")
        elif not isinstance(thread, list) or not thread:
            add("require_approval", "TP-THREAD-RECIPIENTS-MISSING",
                f"tool {tool!r} is bound to the thread but the call carries no thread_recipients; recipient unchecked")
        else:
            allowed = {normalise_recipient(str(x)) for x in thread}
            for k, v in present.items():
                values = v if isinstance(v, list) else [v]
                bad = [str(x) for x in values if normalise_recipient(str(x)) not in allowed]
                if bad:
                    add("deny", "TP-RECIPIENT-NOT-BOUND-TO-THREAD",
                        f"{k}={', '.join(bad)} is not a recipient of record for this thread")
                else:
                    bound_ok_keys.add(k)
    if cls not in CLASSIFICATIONS:
        add("require_approval", "TP-DATA-CLASSIFICATION", f"classification {cls!r} unknown; treated as personal")
        is_personal = True
    else:
        is_personal = cls in personal
    dests = destinations(args)
    checked = destinations({k: v for k, v in args.items() if k not in bound_ok_keys})
    default_deny = policy.get("default_deny_unlisted_destinations", False)
    dest_allow = policy.get("allowed_destination_domains", policy.get("allowed_egress_domains", []))
    for host in sorted(dests):
        if domain_in(host, policy.get("forbidden_domains", [])):
            add("deny", "TP-FORBIDDEN-DESTINATION", f"destination {host} is forbidden")
        elif host not in checked:
            continue  # only referenced by a recipient that passed thread binding
        elif default_deny and side_effecting and not domain_in(host, dest_allow):
            add("deny", "TP-DESTINATION-NOT-ALLOWLISTED",
                f"destination {host} is not on allowed_destination_domains (default deny, any classification)")
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
    if side_effecting and not eff_untrusted:
        add("require_approval", "TP-SIDE-EFFECT-APPROVAL", f"side-effecting tool {tool!r} needs human approval")
    decision = max((r["decision"] for r in reasons), key=RANK.__getitem__, default="allow")
    if not reasons:
        reasons.append({"decision": "allow", "rule": "TP-ALLOW", "message": "allowlisted, not side-effecting, no restricted destination or content"})
    return {"call_id": str(call.get("call_id", "?")), "tool": tool, "provenance": prov,
            "declared_provenance": prov, "effective_provenance": eff,
            "context_provenance": list(context) if isinstance(context, list) else None,
            "data_classification": cls, "declared_classification": declared_cls,
            "classification_source": cls_source,
            "decision": decision, "reasons": reasons, "destinations": sorted(dests)}


def advisory_findings(r: dict) -> list[dict]:
    """Findings that explain trust assumptions without changing the decision."""
    out = []
    cid = r["call_id"]
    if r["context_provenance"] is None:
        out.append({"id": cid, "severity": "info", "rule": "provenance-untainted-trust",
                    "message": f"no turn_context_provenance: provenance label {r['declared_provenance']!r} trusted as given"})
    elif r["effective_provenance"] != r["declared_provenance"]:
        out.append({"id": cid, "severity": "warning", "rule": "provenance-tainted",
                    "message": f"declared {r['declared_provenance']!r} but effective provenance is "
                               f"{r['effective_provenance']!r} from the turn context"})
    if r["classification_source"] == "self_declared":
        out.append({"id": cid, "severity": "info", "rule": "classification-self-declared",
                    "message": f"classification {r['declared_classification']!r} supplied by the caller, "
                               "not derived from policy.tool_classification"})
    elif r["declared_classification"] and r["declared_classification"] != r["data_classification"]:
        out.append({"id": cid, "severity": "warning", "rule": "classification-overridden",
                    "message": f"caller declared {r['declared_classification']!r}; derived "
                               f"{r['data_classification']!r} used"})
    return out


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
        findings.extend(advisory_findings(r))
    if expect:
        mism = [r["call_id"] for r in results if not r["matches_expected"]]
        summary["mismatches"] = mism
        summary["expected_agreement"] = round((len(results) - len(mism)) / len(results), 4) if results else None
        passed = not mism
    else:
        passed = counts["deny"] == 0 and counts["require_approval"] == 0
    return {"decisions": results, "summary": summary, "findings": findings, "passed": passed}


def _str_list(value, where: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
        raise PolicyError(f"{where} must be a list of strings")
    return value


def load_calls(data) -> list[dict]:
    """Return calls; batch-level turn_context_provenance is merged into, and thread_recipients
    defaulted onto, each call (copies; the input is not modified)."""
    calls = data.get("calls") if isinstance(data, dict) else data
    if not isinstance(calls, list):
        raise PolicyError("calls file must be a list or an object with a 'calls' list")
    batch_ctx = batch_rcpt = None
    if isinstance(data, dict):
        if "turn_context_provenance" in data:
            batch_ctx = _str_list(data["turn_context_provenance"], "batch turn_context_provenance")
        if "thread_recipients" in data:
            batch_rcpt = _str_list(data["thread_recipients"], "batch thread_recipients")
    out = []
    for i, c in enumerate(calls):
        if not isinstance(c, dict) or not isinstance(c.get("tool"), str):
            raise PolicyError(f"call {i}: need an object with string 'tool'")
        if "args" in c and not isinstance(c["args"], dict):
            raise PolicyError(f"call {i}: 'args' must be an object")
        if c.get("expected_decision") not in (None, *DECISIONS):
            raise PolicyError(f"call {i}: expected_decision must be one of {DECISIONS}")
        c = dict(c)
        if "turn_context_provenance" in c:
            _str_list(c["turn_context_provenance"], f"call {i}: turn_context_provenance")
        if batch_ctx is not None:
            c["turn_context_provenance"] = [*batch_ctx, *c.get("turn_context_provenance", [])]
        if "thread_recipients" in c:
            _str_list(c["thread_recipients"], f"call {i}: thread_recipients")
        elif batch_rcpt is not None:
            c["thread_recipients"] = list(batch_rcpt)
        out.append(c)
    return out


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
            prov = r["declared_provenance"]
            if r["effective_provenance"] != prov:
                prov = f"{prov} -> effective {r['effective_provenance']}"
            print(f"{r['decision'].upper():16} {r['call_id']:<10} {r['tool']} [{prov}]{tail}")
            for reason in r["reasons"]:
                print(f"    {reason['rule']:<27} {reason['message']}")
        print(f"\n{'PASS' if report['passed'] else 'FAIL'}: {report['summary']}")
        untainted = sum(r["context_provenance"] is None for r in report["decisions"])
        trust = (f"{untainted} call(s) had no turn_context_provenance, so their provenance labels were trusted as given"
                 if untainted else "provenance tainted from the reported turn context, which must come from the orchestrator")
        print(f"Scope: policy evaluation of reported calls only; {trust}.")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
