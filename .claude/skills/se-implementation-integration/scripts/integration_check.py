#!/usr/bin/env python3
"""Check an integration plan: sequencing, readiness, checks and interface coverage.

Rules
  unknown-item            a step integrates something that is neither a component nor produced by a step
  assembly-not-ready      a step uses an assembly whose producing step is not among its (transitive) prerequisites
  prerequisite-cycle      prerequisites loop
  produced-twice          two steps claim to produce the same assembly
  no-checks               a step has no verification/check activity
  component-not-integrated / no-final-assembly
  unit-not-verified (warning)  component enters integration without unit-level verification
  component-not-available (warning)
  interface-not-checked (warning, with --icd)  an ICD interface between items joined in the plan is never listed

Usage: integration_check.py plan.json [--icd icd.csv] [--json]
Exit: 0 no errors, 1 errors, 2 unreadable.
Scope: plan logic only; it does not show the integration will succeed.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path


def _f(rid, sev, rule, msg):
    return {"id": rid, "severity": sev, "rule": rule, "message": msg}


def check(plan: dict, icd: list[dict] | None = None) -> dict:
    f = []
    comps = {c["id"]: c for c in plan.get("components", [])}
    steps = {s["step_id"]: s for s in plan.get("steps", [])}
    producers: dict[str, list[str]] = {}
    for s in plan.get("steps", []):
        if s.get("produces"):
            producers.setdefault(s["produces"], []).append(s["step_id"])
    for a, ss in producers.items():
        if len(ss) > 1:
            f.append(_f(a, "error", "produced-twice", f"produced by steps {ss}"))
    # prerequisite closure + cycles
    closure: dict[str, set[str]] = {}

    def prereqs(sid: str, stack: tuple = ()) -> set[str]:
        if sid in closure:
            return closure[sid]
        if sid in stack:
            f.append(_f(sid, "error", "prerequisite-cycle", " -> ".join(stack + (sid,))))
            return set()
        out = set()
        for p in steps.get(sid, {}).get("prerequisites", []):
            if p not in steps:
                f.append(_f(sid, "error", "unknown-prerequisite", f"prerequisite '{p}' is not a step"))
                continue
            out |= {p} | prereqs(p, stack + (sid,))
        closure[sid] = out
        return out

    for sid in steps:
        prereqs(sid)
    contents: dict[str, set[str]] = {}  # assembly -> leaf components

    def leaves(item: str, depth: int = 0) -> set[str]:
        if item in comps or depth > 50:
            return {item}
        if item in contents:
            return contents[item]
        out = set()
        for st in producers.get(item, [])[:1]:
            for x in steps[st].get("integrates", []):
                out |= leaves(x, depth + 1)
        contents[item] = out
        return out

    integrated = set()
    for sid, s in steps.items():
        if not s.get("checks"):
            f.append(_f(sid, "error", "no-checks", "integration step has no verification/check activities"))
        for item in s.get("integrates", []):
            if item in comps:
                integrated.add(item)
                c = comps[item]
                if not c.get("unit_verified"):
                    f.append(_f(sid, "warning", "unit-not-verified", f"'{item}' enters integration without unit verification"))
                if c.get("status", "available") != "available":
                    f.append(_f(sid, "warning", "component-not-available", f"'{item}' status is {c.get('status')}"))
            elif item in producers:
                prod = producers[item][0]
                if prod == sid or prod not in closure.get(sid, set()):
                    f.append(_f(sid, "error", "assembly-not-ready",
                                f"uses '{item}' produced by step {prod}, which is not a prerequisite"))
            else:
                f.append(_f(sid, "error", "unknown-item", f"'{item}' is not a component nor produced by any step"))
    for c in comps:
        if c not in integrated:
            f.append(_f(c, "error", "component-not-integrated", "component never enters integration"))
    final = plan.get("final_assembly")
    if not final or final not in producers:
        f.append(_f(final or "-", "error", "no-final-assembly", "final assembly is not produced by any step"))
    if icd is not None:
        listed = {i for s in steps.values() for i in s.get("interfaces", [])}
        joined_pairs = set()
        for s in steps.values():
            groups = [leaves(x) for x in s.get("integrates", [])]
            for i, g1 in enumerate(groups):
                for g2 in groups[i + 1:]:
                    for a in g1:
                        for b in g2:
                            joined_pairs.add(frozenset((a, b)))
        for row in icd:
            pair = frozenset((row.get("from_component"), row.get("to_component")))
            if pair in joined_pairs and row.get("interface_id") not in listed:
                f.append(_f(row.get("interface_id", "?"), "warning", "interface-not-checked",
                            f"interface between {sorted(pair)} is joined in the plan but not listed in any step"))
    order = sorted(steps, key=lambda s: len(closure.get(s, set())))
    sev = Counter(x["severity"] for x in f)
    return {"findings": f, "order": order,
            "summary": {"steps": len(steps), "components": len(comps), "errors": sev.get("error", 0),
                        "warnings": sev.get("warning", 0)}}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check an integration plan.")
    ap.add_argument("plan", type=Path)
    ap.add_argument("--icd", type=Path)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        plan = json.loads(a.plan.read_text(encoding="utf-8"))
        icd = None
        if a.icd:
            with a.icd.open(newline="", encoding="utf-8-sig") as fh:
                icd = [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(fh)]
    except (OSError, json.JSONDecodeError, csv.Error) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 2
    res = check(plan, icd)
    res["passed"] = res["summary"]["errors"] == 0
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        print("Order: " + " -> ".join(res["order"]))
        for x in res["findings"]:
            print(f"{x['severity'].upper():8} {x['id']:<14} {x['rule']:<26} {x['message']}")
        print(f"\n{'PASS' if res['passed'] else 'FAIL'}: {res['summary']}")
        print("Scope: plan logic only; integration success is shown by executed checks and evidence.")
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
