#!/usr/bin/env python3
"""Check a functional decomposition: tree integrity, naming, allocation, data-flow closure, traceability.

functions CSV columns: function_id, parent_function, name, inputs, outputs, allocated_to, requirement_ids
(list fields separated by ';'; items prefixed 'EXT:' cross the system boundary).

Checks
  tree: duplicate IDs, unknown parents, cycles
  naming: verb-object names (noun-like first word flagged)
  allocation: every leaf function allocated to >= 1 element (and elements exist if --components)
  flow closure: each leaf input is produced by some function output or is external; each output
                is consumed or external (warning)
  traceability: functions trace to requirements; approved system requirements are covered (if --requirements)

Usage: function_check.py functions.csv [--components C.csv] [--requirements R.csv] [--json]
Exit: 0 no errors, 1 errors, 2 unreadable.
Scope: structural; whether the decomposition is the right one is an engineering judgement.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

NOUN_ENDINGS = ("tion", "sion", "ment", "ness", "ity", "ance", "ence", "age", "ery", "ism")
VERB_EXCEPTIONS = {"sequence", "balance", "advance", "enhance", "reference", "influence", "evidence",
                   "finance", "license", "licence", "silence", "commence", "manage", "package", "engage", "stage",
                   "damage", "average", "leverage", "mention", "position", "partition", "condition", "function",
                   "query", "deliver", "recover", "cover", "filter", "enter", "register", "monitor"}
NOUN_WORDS = {"system", "module", "unit", "subsystem", "data", "energy", "power", "hop", "robot", "controller", "sensor"}


def _f(rid, sev, rule, msg):
    return {"id": rid, "severity": sev, "rule": rule, "message": msg}


def items(v: str) -> list[str]:
    return [x.strip() for x in (v or "").split(";") if x.strip()]


def read(p: Path) -> list[dict]:
    with p.open(newline="", encoding="utf-8-sig") as fh:
        return [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(fh)]


def check(funcs: list[dict], components: set[str] | None = None, reqs: list[dict] | None = None) -> dict:
    f = []
    ids = Counter(x["function_id"] for x in funcs)
    known = set(ids)
    children: dict[str, list[str]] = {}
    for x in funcs:
        fid = x["function_id"] or "<blank>"
        if ids[x["function_id"]] > 1:
            f.append(_f(fid, "error", "duplicate-id", "function id used more than once"))
        p = x.get("parent_function", "")
        if p:
            if p not in known:
                f.append(_f(fid, "error", "unknown-parent", f"parent '{p}' not defined"))
            children.setdefault(p, []).append(x["function_id"])
        first = (x.get("name", "").split() or [""])[0].lower()
        if not first:
            f.append(_f(fid, "error", "no-name", "function has no name"))
        elif first not in VERB_EXCEPTIONS and (first in NOUN_WORDS or first.endswith(NOUN_ENDINGS)):
            f.append(_f(fid, "warning", "not-verb-object", f"name '{x['name']}' should be verb–object (e.g. 'Store energy')"))
    # cycles
    parent = {x["function_id"]: x.get("parent_function", "") for x in funcs}
    for start in parent:
        seen, cur = set(), start
        while cur:
            if cur in seen:
                f.append(_f(start, "error", "tree-cycle", "parent chain loops"))
                break
            seen.add(cur)
            cur = parent.get(cur, "")
    leaves = [x for x in funcs if x["function_id"] not in children]
    produced = {o for x in leaves for o in items(x.get("outputs", "")) if not o.startswith("EXT:")}
    consumed = {i for x in leaves for i in items(x.get("inputs", "")) if not i.startswith("EXT:")}
    for x in leaves:
        fid = x["function_id"]
        alloc = items(x.get("allocated_to", ""))
        if not alloc:
            f.append(_f(fid, "error", "unallocated-leaf", "leaf function not allocated to any element"))
        if components is not None:
            for a in alloc:
                if a not in components:
                    f.append(_f(fid, "error", "unknown-element", f"allocated to unknown element '{a}'"))
        for i in items(x.get("inputs", "")):
            if not i.startswith("EXT:") and i not in produced:
                f.append(_f(fid, "error", "unproduced-input", f"input '{i}' is produced by no function and not marked EXT:"))
        for o in items(x.get("outputs", "")):
            if not o.startswith("EXT:") and o not in consumed:
                f.append(_f(fid, "warning", "unconsumed-output", f"output '{o}' is used by no function and not marked EXT:"))
        if not x.get("requirement_ids"):
            f.append(_f(fid, "warning", "untraced-function", "function traces to no requirement (gold-plating?)"))
    if reqs is not None:
        req_ids = {r["id"] for r in reqs if r.get("id")}
        covered = {q for x in funcs for q in items(x.get("requirement_ids", "").replace(",", ";"))}
        for q in covered - req_ids:
            f.append(_f(q, "error", "unknown-requirement", "function references a requirement not in the register"))
        for r in reqs:
            if r.get("level", "").lower() == "system" and r.get("status", "").lower() == "approved" and r["id"] not in covered:
                f.append(_f(r["id"], "warning", "requirement-not-allocated", "approved system requirement realised by no function"))
    sev = Counter(x["severity"] for x in f)
    return {"findings": f, "summary": {"functions": len(funcs), "leaves": len(leaves),
                                       "errors": sev.get("error", 0), "warnings": sev.get("warning", 0)}}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check a functional decomposition.")
    ap.add_argument("csv", type=Path)
    ap.add_argument("--components", type=Path)
    ap.add_argument("--requirements", type=Path)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        funcs = read(a.csv)
        comps = {r["component_id"] for r in read(a.components)} if a.components else None
        reqs = read(a.requirements) if a.requirements else None
    except (OSError, KeyError, csv.Error) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 2
    res = check(funcs, comps, reqs)
    res["passed"] = res["summary"]["errors"] == 0
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        for x in res["findings"]:
            print(f"{x['severity'].upper():8} {x['id']:<14} {x['rule']:<26} {x['message']}")
        print(f"\n{'PASS' if res['passed'] else 'FAIL'}: {res['summary']}")
        print("Scope: structural check of the decomposition; adequacy is an engineering judgement.")
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
