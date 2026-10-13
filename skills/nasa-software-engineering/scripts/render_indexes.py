#!/usr/bin/env python3
"""Render the reference index tables of the two NASA skills from the catalogs.

Usage: python skills/nasa-software-engineering/scripts/render_indexes.py
Writes skills/nasa-software-engineering/references/requirements-index.md and
skills/nasa-software-assurance/references/sa-task-index.md (do not hand-edit those files).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from agentlib.paths import load_catalog
npr = load_catalog("npr-7150-2d"); std = load_catalog("nasa-std-8739-8b")
groups = {g["id"]: g for g in npr["groups"]}

def trunc(s, n=220):
    return s if len(s) <= n else s[: n - 1].rsplit(" ", 1)[0] + " …"

L = ["# NPR 7150.2D requirements index (generated from catalog/npr-7150-2d.json)", "",
     "Rendered by `skills/nasa-software-engineering/scripts/render_indexes.py`; regenerate, do not hand-edit. Statements are",
     "quoted verbatim (whitespace normalised) and truncated with \"…\" - run `python -m agentlib nasa-swe show SWE-xxx`",
     "for the full text, list items, notes and the mapped software assurance tasks.", "",
     "Columns A-F show the Appendix C Requirements Mapping Matrix: `X` = invoked for that class, `-` = blank",
     "(optional / not invoked). \"PDF p.\" is the page of the pinned PDF where the paragraph starts (printed page",
     "numbers are identical, \"Page N of 89\"). Chapter 2 requirements are institutional and are not part of the",
     "Appendix C matrix (para 1.3.1, PDF p. 9).", ""]
cur = None
for it in npr["items"]:
    g = it["group"]
    if g != cur:
        cur = g
        gg = groups[g]
        L += ["", f"## {g} {gg['title']} (PDF p. {gg['citation']['pdf_page']})", ""]
        if it["applicability"]:
            L += ["| SWE | Para | PDF p. | A | B | C | D | E | F | Authority | Requirement (truncated) |", "|---|---|---|---|---|---|---|---|---|---|---|"]
        else:
            L += ["| SWE | Para | PDF p. | Actor | Requirement (truncated) |", "|---|---|---|---|---|"]
    st = trunc(it["text"]).replace("|", "\\|")
    if it["applicability"]:
        a = it["applicability"]
        cells = " | ".join(a[c] or "-" for c in "ABCDEF")
        L.append(f"| {it['id']} | {it['section']} | {it['citation']['pdf_page']} | {cells} | {a['authority']} | {st} |")
    else:
        L.append(f"| {it['id']} | {it['section']} | {it['citation']['pdf_page']} | {it['actor']} | {st} |")
L.append("")
open(ROOT / "skills/nasa-software-engineering/references/requirements-index.md", "w", encoding="utf-8").write("\n".join(L))

L = ["# NASA-STD-8739.8B Table 1 index (generated from catalog/nasa-std-8739-8b.json)", "",
     "One row per Table 1 entry (SWE-065 is split into 065a-065d by the standard). \"Safety tasks\" lists the task",
     "numbers whose text mentions safety or hazards (a library keyword flag, not a category defined by the",
     "standard). Run `python -m agentlib nasa-swe sa-tasks --swe SWE-xxx` for the full verbatim task text.", "",
     "| Table 1 row | NPR para | PDF p. | Tasks | Safety tasks | Task 1 (truncated) |", "|---|---|---|---|---|---|"]
for it in std["items"]:
    if it["kind"] != "sa-task-set":
        continue
    label = it["swe"] + (it["swe_part"] or "")
    pages = "-".join(map(str, [it["pages"][0], it["pages"][-1]])) if len(it["pages"]) > 1 else str(it["pages"][0])
    sc = ", ".join(map(str, it["safety_related_tasks"])) or "-"
    L.append(f"| {label} | {it['npr_section']} | {pages} | {len(it['tasks'])} | {sc} | {trunc(it['tasks'][0]['text'], 140).replace('|', '/')} |")
L += ["", "## IV&V requirements (4.4.2.1-4.4.2.49)", "", "| Id | PDF p. | Actor | Requirement (truncated) |", "|---|---|---|---|"]
for it in std["items"]:
    if it["kind"] == "ivv-requirement":
        L.append(f"| {it['id']} | {it['citation']['pdf_page']} | {it['actor']} | {trunc(it['text'], 200)} |")
L.append("")
open(ROOT / "skills/nasa-software-assurance/references/sa-task-index.md", "w", encoding="utf-8").write("\n".join(L))
print("wrote reference indexes")
