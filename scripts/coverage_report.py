#!/usr/bin/env python3
"""Generate MEASURED coverage for skills, sources and the NASA 17-process map.

Per skill (computed, never self-declared):
  implemented  SKILL.md + at least one script or template
  fixtures     at least one *pass* and one *fail* example in assets/examples
  tested       a tests/test_*.py module references the skill AND (with --run-tests) that module passes
  source       weakest access status among the skill's metadata.sources
  human review always "pending" — no expert sign-off is recorded in this repository

Usage: coverage_report.py [--run-tests] [--write] [--json]
  --write writes docs/coverage.md and docs/coverage.json
Exit: 0 report produced (and all run tests passed), 1 a test module failed.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agentlib import ROOT, SKILLS_DIR, frontmatter  # noqa: E402

RANK = {"VERIFIED": 3, "PARTIALLY_VERIFIED": 2, "UNVERIFIED": 1, "INACCESSIBLE": 0}


def test_modules() -> dict[str, str]:
    return {p.stem: p.read_text(encoding="utf-8") for p in sorted((ROOT / "tests").glob("test_*.py"))}


def run_module(name: str) -> tuple[bool, int]:
    p = subprocess.run([sys.executable, "-m", "unittest", f"tests.{name}"], cwd=ROOT, capture_output=True, text=True, timeout=600)
    m = re.search(r"Ran (\d+) tests?", p.stderr)
    return p.returncode == 0, int(m.group(1)) if m else 0


def build(run_tests: bool) -> dict:
    registry = {r["id"]: r for r in json.loads((ROOT / "sources/registry.json").read_text(encoding="utf-8"))}
    mods = test_modules()
    results: dict[str, tuple[bool, int]] = {}
    if run_tests:
        for m in mods:
            results[m] = run_module(m)
    skills = []
    for sm in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        d = sm.parent
        fm, _ = frontmatter.load(sm.read_text(encoding="utf-8"))
        meta = fm.get("metadata", {})
        scripts = sorted(p.name for p in (d / "scripts").glob("*.py")) if (d / "scripts").is_dir() else []
        templates = list((d / "assets" / "templates").glob("*")) if (d / "assets" / "templates").is_dir() else []
        exd = d / "assets" / "examples"
        ex = [p.relative_to(exd).as_posix().lower() for p in exd.rglob("*") if p.is_file()] if exd.is_dir() else []
        has_pass = any(k in e for e in ex for k in ("pass", "good", "benign", "fixed"))
        has_fail = any(k in e for e in ex for k in ("fail", "bad", "malicious", "vulnerable", "draft"))
        manifest = exd / "fixtures.json"
        if manifest.is_file():
            m = json.loads(manifest.read_text(encoding="utf-8"))
            has_pass = has_pass or any((exd / x).exists() for x in m.get("pass", []))
            has_fail = has_fail or any((exd / x).exists() for x in m.get("fail", []))
        refs = [m for m, txt in mods.items() if re.search(rf"['\"]{re.escape(d.name)}['\"]", txt)]
        tests_pass = None
        n_tests = 0
        if run_tests and refs:
            tests_pass = all(results[m][0] for m in refs)
            n_tests = sum(results[m][1] for m in refs)
        srcs = meta.get("sources", "").split()
        weakest = min((registry[s]["access_status"] for s in srcs if s in registry), key=lambda x: RANK[x], default="UNVERIFIED")
        implemented = bool(scripts or templates)
        tested = implemented and has_pass and has_fail and bool(refs) and (tests_pass is not False) and (tests_pass is True or not run_tests)
        status = "tested" if tested and run_tests else ("implemented" if implemented else "mapped")
        if run_tests and refs and tests_pass is False:
            status = "failing"
        skills.append({"skill": d.name, "pack": meta.get("pack"), "scripts": scripts, "fixtures_pass": has_pass,
                       "fixtures_fail": has_fail, "test_modules": refs, "tests_run": n_tests,
                       "tests_pass": tests_pass, "status": status, "sources": srcs,
                       "weakest_source_status": weakest, "human_review": "pending"})
    by_skill = {s["skill"]: s for s in skills}
    sources = []
    for sid, r in registry.items():
        cw = ROOT / "docs" / "crosswalks" / f"{sid}.json"
        rows = json.loads(cw.read_text(encoding="utf-8")).get("rows", []) if cw.is_file() else []
        mapped = sorted({s for row in rows for s in row.get("skills", [])})
        sources.append({"source_id": sid, "access_status": r["access_status"], "crosswalk_rows": len(rows),
                        "row_verification": dict(Counter(row.get("source_verification") for row in rows)),
                        "skills": mapped,
                        "skills_tested": sum(1 for s in mapped if by_skill.get(s, {}).get("status") == "tested")})
    nasa = json.loads((ROOT / "sources/nasa-17-processes.json").read_text(encoding="utf-8"))["processes"]
    procs = [{"id": p["id"], "process": p["process"], "section": p["handbook_section"], "skills": p["skill_ids"],
              "all_tested": all(by_skill.get(s, {}).get("status") == "tested" for s in p["skill_ids"])} for p in nasa]
    packs = defaultdict(Counter)
    for s in skills:
        packs[s["pack"]][s["status"]] += 1
    return {"run_tests": run_tests, "skills": skills, "sources": sources, "nasa_processes": procs,
            "packs": {k: dict(v) for k, v in packs.items()},
            "totals": {"skills": len(skills), "by_status": dict(Counter(s["status"] for s in skills)),
                       "tests_run": sum(r[1] for r in results.values()),
                       "test_modules_failed": sorted(m for m, r in results.items() if not r[0]),
                       "sources_by_access": dict(Counter(s["access_status"] for s in sources)),
                       "nasa_processes_all_tested": sum(p["all_tested"] for p in procs)}}


def markdown(c: dict) -> str:
    t = c["totals"]
    L = ["# Measured coverage", "",
         "_Generated by `python3 scripts/coverage_report.py --run-tests --write`. Do not edit by hand._", "",
         "Status levels are computed: **mapped** (skill exists) → **implemented** (script/template) → **tested**",
         "(pass + fail fixtures, a test module that references the skill, and that module passing in this run).",
         "**Human expert review is pending for every capability** — nothing here is professionally validated.",
         "Source access is reported separately: a tested skill built on an INACCESSIBLE source has verified",
         "*mechanics* but unverified *source fidelity*.", "",
         f"- Skills: **{t['skills']}** — " + ", ".join(f"{k}: {v}" for k, v in sorted(t['by_status'].items())),
         f"- Unit tests executed in this run: **{t['tests_run']}**; failing modules: {t['test_modules_failed'] or 'none'}",
         f"- Sources by access status: " + ", ".join(f"{k}: {v}" for k, v in sorted(t['sources_by_access'].items())),
         f"- NASA processes whose mapped skills are all tested: **{t['nasa_processes_all_tested']}/17**", "",
         "## By pack", "| Pack | Status counts |", "|---|---|"]
    L += [f"| {k} | " + ", ".join(f"{s}: {n}" for s, n in sorted(v.items())) + " |" for k, v in sorted(c["packs"].items())]
    L += ["", "## Skills", "| Skill | Pack | Status | Scripts | Pass/fail fixtures | Tests run | Weakest source | Human review |",
          "|---|---|---|---|---|---|---|---|"]
    for s in c["skills"]:
        L.append(f"| `{s['skill']}` | {s['pack']} | {s['status']} | {len(s['scripts'])} | "
                 f"{'✓' if s['fixtures_pass'] else '✗'}/{'✓' if s['fixtures_fail'] else '✗'} | {s['tests_run']} | "
                 f"{s['weakest_source_status']} | {s['human_review']} |")
    L += ["", "## Sources", "| Source | Access | Crosswalk rows | Row verification | Skills mapped | Skills tested |", "|---|---|---|---|---|---|"]
    for s in c["sources"]:
        L.append(f"| `{s['source_id']}` | {s['access_status']} | {s['crosswalk_rows']} | "
                 + ", ".join(f"{k}: {v}" for k, v in s["row_verification"].items()) + f" | {len(s['skills'])} | {s['skills_tested']} |")
    L += ["", "## NASA 17 common technical processes", "| ID | § (secondary) | Process | Skills | All tested |", "|---|---|---|---|---|"]
    for p in c["nasa_processes"]:
        L.append(f"| {p['id']} | {p['section']} | {p['process']} | {', '.join('`'+x+'`' for x in p['skills'])} | {'✓' if p['all_tested'] else '✗'} |")
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run-tests", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    c = build(a.run_tests)
    if a.write:
        (ROOT / "docs" / "coverage.md").write_text(markdown(c), encoding="utf-8")
        (ROOT / "docs" / "coverage.json").write_text(json.dumps(c, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(c["totals"], indent=2) if a.json else markdown(c))
    return 1 if c["totals"]["test_modules_failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
