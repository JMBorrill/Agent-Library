#!/usr/bin/env python3
"""Check an interface control register (ICD CSV) and print an N-squared interface matrix.

Checks: ID format and duplicates (same interface_id+parameter), self-interfaces, unknown components
(if a component list is given), unit compatibility between the two sides (same unit / convertible
scale / incompatible dimension), missing owners, failure behaviour, version, and baselined/agreed
interfaces lacking requirement or verification links.

Usage: icd_check.py icd.csv [--components components.csv] [--n2] [--json]
Exit: 0 no errors, 1 errors, 2 unreadable.
Scope: register consistency only — physical/electrical/data compatibility must be verified by test.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

TYPES = {"mechanical", "electrical", "data", "software", "thermal", "fluid", "optical", "rf",
         "operational", "human", "power"}
STATUSES = {"draft", "agreed", "baselined", "retired"}
REQUIRED = ["interface_id", "from_component", "to_component", "type", "parameter", "units_from",
            "units_to", "owner_from", "owner_to", "version", "status"]
IF_ID = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-IF-[0-9]{3,}$")

# unit -> (dimension, scale to SI base)
UNITS = {
    "v": ("voltage", 1), "mv": ("voltage", 1e-3), "kv": ("voltage", 1e3),
    "a": ("current", 1), "ma": ("current", 1e-3),
    "w": ("power", 1), "mw": ("power", 1e-3), "kw": ("power", 1e3),
    "n": ("force", 1), "kn": ("force", 1e3), "lbf": ("force", 4.448222),
    "n·m": ("torque", 1), "nm": ("torque", 1), "n.m": ("torque", 1),
    "m": ("length", 1), "mm": ("length", 1e-3), "cm": ("length", 1e-2), "km": ("length", 1e3), "in": ("length", 0.0254),
    "kg": ("mass", 1), "g": ("mass", 1e-3),
    "s": ("time", 1), "ms": ("time", 1e-3), "us": ("time", 1e-6), "µs": ("time", 1e-6),
    "hz": ("frequency", 1), "khz": ("frequency", 1e3), "mhz": ("frequency", 1e6),
    "°c": ("temperature", None), "degc": ("temperature", None), "k": ("temperature", None),
    "pa": ("pressure", 1), "kpa": ("pressure", 1e3), "bar": ("pressure", 1e5), "psi": ("pressure", 6894.757),
    "bit/s": ("datarate", 1), "kbit/s": ("datarate", 1e3), "mbit/s": ("datarate", 1e6),
    "byte": ("data", 8), "kb": ("data", 8e3), "mb": ("data", 8e6), "bit": ("data", 1),
    "dbm": ("rfpower", None), "db": ("ratio", None), "%": ("ratio", None),
    "rad": ("angle", 1), "deg": ("angle", 0.0174533), "°": ("angle", 0.0174533),
    "m/s": ("speed", 1), "m/s^2": ("acceleration", 1), "m/s²": ("acceleration", 1),
    "-": ("dimensionless", 1), "n/a": ("dimensionless", 1),
}


def _f(rid, sev, rule, msg):
    return {"id": rid, "severity": sev, "rule": rule, "message": msg}


def unit_relation(a: str, b: str) -> str:
    """Return 'same', 'convertible', 'incompatible' or 'unknown'."""
    ka, kb = a.strip().lower(), b.strip().lower()
    if ka == kb:
        return "same"
    ua, ub = UNITS.get(ka), UNITS.get(kb)
    if not ua or not ub:
        return "unknown"
    if ua[0] != ub[0]:
        return "incompatible"
    return "convertible"


def check(cols, rows, components: set[str] | None = None, requirement_ids: set[str] | None = None) -> dict:
    findings = []
    missing = [c for c in REQUIRED if c not in cols]
    if missing:
        return {"findings": [_f("-", "error", "missing-columns", ", ".join(missing))], "summary": {}}
    keys = Counter((r["interface_id"], r["parameter"].lower()) for r in rows)
    for r in rows:
        iid = r["interface_id"] or "<blank>"
        status = r["status"].lower()
        if not IF_ID.fullmatch(r["interface_id"]):
            findings.append(_f(iid, "error", "id-format", "interface id must look like <PROJECT>-IF-NNN"))
        if keys[(r["interface_id"], r["parameter"].lower())] > 1:
            findings.append(_f(iid, "error", "duplicate-parameter",
                               f"parameter '{r['parameter']}' defined more than once — conflicting definitions"))
        if status not in STATUSES:
            findings.append(_f(iid, "error", "status", f"status '{r['status']}' not in {sorted(STATUSES)}"))
        if r["type"].lower() not in TYPES:
            findings.append(_f(iid, "warning", "type", f"type '{r['type']}' not in {sorted(TYPES)}"))
        if r["from_component"] == r["to_component"]:
            findings.append(_f(iid, "error", "self-interface", "interface connects a component to itself"))
        if components is not None:
            for side in ("from_component", "to_component"):
                if r[side] not in components:
                    findings.append(_f(iid, "error", "unknown-component", f"{side} '{r[side]}' not in component list"))
        uf, ut = r["units_from"], r["units_to"]
        if not uf or not ut:
            findings.append(_f(iid, "error" if status in {"agreed", "baselined"} else "warning", "missing-units",
                               "both sides must declare units (use '-' for dimensionless)"))
        else:
            rel = unit_relation(uf, ut)
            if rel == "incompatible":
                findings.append(_f(iid, "error", "unit-incompatible", f"'{uf}' vs '{ut}' are different physical dimensions"))
            elif rel == "convertible":
                findings.append(_f(iid, "error" if status == "baselined" else "warning", "unit-conversion",
                                   f"'{uf}' vs '{ut}' need conversion — agree a single unit in the ICD"))
            elif rel == "unknown":
                findings.append(_f(iid, "info", "unit-unknown", f"units '{uf}'/'{ut}' not in the checker's table; verify manually"))
        if status in {"agreed", "baselined"}:
            for col in ("owner_from", "owner_to"):
                if not r[col]:
                    findings.append(_f(iid, "error", f"missing-{col.replace('_', '-')}", "agreed interface needs owners on both sides"))
            if not r.get("failure_behavior"):
                findings.append(_f(iid, "error", "no-failure-behaviour", "agreed interface must define behaviour on failure/out-of-range"))
            if not r.get("verification_id"):
                findings.append(_f(iid, "error" if status == "baselined" else "warning", "no-verification",
                                   "interface has no verification activity"))
            if not r.get("requirement_ids"):
                findings.append(_f(iid, "warning", "no-requirement-link", "interface not linked to any requirement"))
            if not r.get("value") and not r.get("range_or_protocol"):
                findings.append(_f(iid, "error", "undefined-parameter", "no value or range/protocol defined"))
        if requirement_ids is not None:
            for q in [x.strip() for x in re.split(r"[;,]", r.get("requirement_ids", "")) if x.strip()]:
                if q not in requirement_ids:
                    findings.append(_f(iid, "error", "unknown-requirement", f"requirement '{q}' not in register"))
        if not r["version"]:
            findings.append(_f(iid, "error", "no-version", "interface definition has no version"))
    sev = Counter(f["severity"] for f in findings)
    comps = sorted({r["from_component"] for r in rows} | {r["to_component"] for r in rows})
    return {"findings": findings,
            "summary": {"interfaces": len({r["interface_id"] for r in rows}), "parameters": len(rows),
                        "components": len(comps), "by_status": dict(Counter(r["status"].lower() for r in rows)),
                        "errors": sev.get("error", 0), "warnings": sev.get("warning", 0)},
            "n2": n2(rows)}


def n2(rows) -> dict:
    comps = sorted({r["from_component"] for r in rows} | {r["to_component"] for r in rows})
    cells: dict[str, dict[str, list[str]]] = {c: {} for c in comps}
    for r in rows:
        cells[r["from_component"]].setdefault(r["to_component"], [])
        if r["interface_id"] not in cells[r["from_component"]][r["to_component"]]:
            cells[r["from_component"]][r["to_component"]].append(r["interface_id"])
    return {"components": comps, "cells": cells}


def n2_markdown(matrix: dict) -> str:
    comps = matrix["components"]
    lines = ["| from \\ to | " + " | ".join(comps) + " |", "|---" * (len(comps) + 1) + "|"]
    for a in comps:
        row = []
        for b in comps:
            row.append("**" + a + "**" if a == b else ", ".join(matrix["cells"][a].get(b, [])))
        lines.append(f"| {a} | " + " | ".join(row) + " |")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check an ICD register.")
    ap.add_argument("csv", type=Path)
    ap.add_argument("--components", type=Path)
    ap.add_argument("--requirements", type=Path, help="requirements CSV to validate requirement_ids")
    ap.add_argument("--n2", action="store_true", help="print N-squared matrix (Markdown)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        with a.csv.open(newline="", encoding="utf-8-sig") as fh:
            rd = csv.DictReader(fh)
            rows = [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in rd]
            cols = [c.strip() for c in rd.fieldnames or []]
        comps = None
        if a.components:
            with a.components.open(newline="", encoding="utf-8-sig") as fh:
                comps = {r["component_id"].strip() for r in csv.DictReader(fh)}
        reqs = None
        if a.requirements:
            with a.requirements.open(newline="", encoding="utf-8-sig") as fh:
                reqs = {r["id"].strip() for r in csv.DictReader(fh) if r.get("id")}
    except (OSError, KeyError, csv.Error) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 2
    res = check(cols, rows, comps, reqs)
    res["passed"] = res["summary"].get("errors", 1) == 0
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        for f in res["findings"]:
            print(f"{f['severity'].upper():8} {f['id']:<14} {f['rule']:<24} {f['message']}")
        if a.n2 and "n2" in res:
            print("\n" + n2_markdown(res["n2"]))
        print(f"\n{'PASS' if res['passed'] else 'FAIL'}: {res['summary']}")
        print("Scope: register consistency only; interface compatibility must be verified by analysis/test.")
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
