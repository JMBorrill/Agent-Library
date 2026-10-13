#!/usr/bin/env python3
"""Trace the impact of a proposed change through requirements, V&V, interfaces and risks.

Builds a trace graph from whichever registers are supplied:
  requirements CSV  (id, parent, verification_id)
  V&V matrix CSV    (activity_id, requirement_id, need_id, result)
  ICD CSV           (interface_id, requirement_ids, verification_id, status)
  risk register CSV (risk_id, related_ids)
  links CSV         (from_id, to_id[, relation])  — any extra trace links
and walks it from the changed IDs. Downward propagation follows derived requirements (children);
parents are reported one level up for a "still satisfied?" check.

Usage:
  change_impact.py --changed ID [ID ...] | --cr change-request.json
                   [--requirements R.csv] [--vmatrix V.csv] [--icd I.csv] [--risks K.csv] [--links L.csv] [--json]
Exit: 0 analysis produced, 1 a changed ID is unknown to every register, 2 unreadable input.
Scope: impact is limited to links recorded in the registers; unrecorded dependencies are invisible.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict, deque
from pathlib import Path


def read(path: Path | None) -> list[dict]:
    if not path:
        return []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(fh)]


def ids(v: str) -> list[str]:
    return [x.strip() for x in re.split(r"[;,]", v or "") if x.strip()]


class Graph:
    def __init__(self) -> None:
        self.kind: dict[str, str] = {}
        self.children: dict[str, set[str]] = defaultdict(set)   # requirement -> derived requirements
        self.parents: dict[str, set[str]] = defaultdict(set)
        self.assoc: dict[str, set[str]] = defaultdict(set)      # symmetric non-hierarchical links
        self.meta: dict[str, dict] = {}

    def link(self, a: str, b: str) -> None:
        self.assoc[a].add(b)
        self.assoc[b].add(a)


def build(reqs, vm, icd, risks, links) -> Graph:
    g = Graph()
    for r in reqs:
        if not r.get("id"):
            continue
        g.kind[r["id"]] = "requirement"
        g.meta[r["id"]] = r
        for p in ids(r.get("parent", "")):
            g.children[p].add(r["id"])
            g.parents[r["id"]].add(p)
    for a in vm:
        aid = a.get("activity_id")
        if not aid:
            continue
        g.kind[aid] = "verification" if a.get("type", "verification").lower() != "validation" else "validation"
        g.meta[aid] = a
        for q in ids(a.get("requirement_id", "")) + ids(a.get("need_id", "")):
            g.link(aid, q)
    for i in icd:
        iid = i.get("interface_id")
        if not iid:
            continue
        g.kind[iid] = "interface"
        g.meta.setdefault(iid, i)
        for q in ids(i.get("requirement_ids", "")) + ids(i.get("verification_id", "")):
            g.link(iid, q)
    for k in risks:
        rid = k.get("risk_id")
        if not rid:
            continue
        g.kind[rid] = "risk"
        g.meta[rid] = k
        for q in ids(k.get("related_ids", "")):
            g.link(rid, q)
    for ln in links:
        if ln.get("from_id") and ln.get("to_id"):
            g.kind.setdefault(ln["from_id"], "other")
            g.kind.setdefault(ln["to_id"], "other")
            g.link(ln["from_id"], ln["to_id"])
    return g


def impact(g: Graph, changed: list[str]) -> dict:
    unknown = [c for c in changed if c not in g.kind and c not in g.children]
    seen: dict[str, str] = {}
    q = deque((c, "changed") for c in changed if c not in unknown)
    while q:
        node, why = q.popleft()
        if node in seen:
            continue
        seen[node] = why
        kind = g.kind.get(node, "other")
        if kind == "requirement" or node in g.children:
            for ch in sorted(g.children.get(node, ())):
                q.append((ch, f"derived from {node}"))
        # associations propagate from requirements and interfaces; activities/risks are leaves
        if kind in ("requirement", "interface", "other") or why == "changed":
            for a in sorted(g.assoc.get(node, ())):
                k2 = g.kind.get(a, "other")
                if k2 in ("verification", "validation", "risk", "interface"):
                    q.append((a, f"linked to {node}"))
    parents = sorted({p for n in seen if g.kind.get(n) == "requirement" for p in g.parents.get(n, ()) if p not in seen})
    out = defaultdict(list)
    actions = []
    for node, why in seen.items():
        kind = g.kind.get(node, "other")
        m = g.meta.get(node, {})
        entry = {"id": node, "why": why}
        if kind in ("verification", "validation"):
            entry["result"] = m.get("result", "")
            if m.get("result", "").lower() in ("pass", "fail"):
                actions.append({"id": node, "action": "re-verify",
                                "reason": f"prior result '{m['result']}' ({m.get('evidence_ref') or 'no ref'}) was obtained "
                                          f"on configuration '{m.get('configuration') or 'unknown'}' — invalid after change"})
        if kind == "interface" and m.get("status", "").lower() in ("agreed", "baselined"):
            actions.append({"id": node, "action": "interface-renegotiation",
                            "reason": f"{m.get('status')} interface — both owners ({m.get('owner_from')}, {m.get('owner_to')}) must approve"})
        if kind == "requirement" and m.get("status", "").lower() == "approved" and why == "changed":
            actions.append({"id": node, "action": "baseline-change",
                            "reason": "approved requirement — needs change-board/owner approval before edit"})
        if kind == "risk":
            actions.append({"id": node, "action": "reassess-risk", "reason": "linked risk may change likelihood/consequence"})
        out[kind].append(entry)
    for p in parents:
        actions.append({"id": p, "action": "check-parent", "reason": "confirm parent requirement is still satisfied by its children"})
    return {"changed": changed, "unknown": unknown, "impacted": {k: sorted(v, key=lambda e: e["id"]) for k, v in out.items()},
            "parents_to_check": parents, "actions": actions,
            "summary": {k: len(v) for k, v in out.items()} | {"actions": len(actions), "unknown": len(unknown)}}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Trace change impact across SE registers.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--changed", nargs="+")
    g.add_argument("--cr", type=Path, help="change request JSON with changed_ids")
    for name in ("requirements", "vmatrix", "icd", "risks", "links"):
        ap.add_argument(f"--{name}", type=Path)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        cr = json.loads(a.cr.read_text(encoding="utf-8")) if a.cr else {}
        changed = a.changed or cr.get("changed_ids", [])
        graph = build(read(a.requirements), read(a.vmatrix), read(a.icd), read(a.risks), read(a.links))
    except (OSError, json.JSONDecodeError, csv.Error) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 2
    res = impact(graph, changed)
    res["cr_id"] = cr.get("cr_id")
    res["passed"] = not res["unknown"]
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        print(f"Change {res['cr_id'] or ''} on {changed}")
        for kind, items in res["impacted"].items():
            print(f"\n{kind} ({len(items)}):")
            for e in items:
                print(f"  {e['id']:<16} {e['why']}" + (f"  [result={e['result']}]" if e.get("result") else ""))
        print("\nRequired actions:")
        for x in res["actions"]:
            print(f"  {x['action']:<24} {x['id']:<16} {x['reason']}")
        if res["unknown"]:
            print(f"\nERROR unknown changed ids: {res['unknown']}")
        print("\nScope: only recorded trace links are followed; unrecorded dependencies need engineering judgement.")
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
