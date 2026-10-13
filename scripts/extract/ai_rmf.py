#!/usr/bin/env python3
"""Extract the NIST AI RMF 1.0 Core and the NIST AI RMF Playbook into catalogs.

Sources
-------
* ``sources/pdfs/nist-ai-rmf-1-0.pdf`` (source id ``nist-ai``) - NIST AI 100-1,
  *Artificial Intelligence Risk Management Framework (AI RMF 1.0)*, January 2023.
* ``sources/pdfs/nist-ai-rmf-playbook.pdf`` (source id ``nist-ai-playbook``) -
  *NIST AI RMF Playbook* (142 numbered pages, 147 PDF pages).

Both are U.S. Government works published by NIST; text is reproduced with
attribution. Outputs:

* ``catalog/nist-ai-rmf.json`` - 4 functions and 19 categories (``groups``),
  72 subcategories (``items``, verbatim with whitespace/hyphenation normalised)
  and the 7 trustworthy-AI characteristics (``parameters``).
* ``catalog/nist-ai-rmf-playbook.json`` - per subcategory, the Playbook's
  Suggested Actions (``<SUB>/action-N``) and Transparency & Documentation
  questions (``<SUB>/question-N``).

Method - AI RMF Core (Tables 1-4, PDF pp. 27-29, 31-38)
-------------------------------------------------------
The Core tables have two columns (Categories | Subcategories). ``pdftotext
-layout`` on the full page interleaves the columns (sometimes with a single
space between them), so for each table page we use ``pdfplumber`` only for
geometry - the x position of the "Subcategories" header and the vertical extent
of the table (header to "Continued on next page" / next section heading) - and
then run ``pdftotext -layout`` on the *cropped* column. Lines are joined and
end-of-line hyphenation is removed except for genuine compounds listed in
``KEEP_HYPHEN`` (verified by reading the page). Category statements are taken
from the left column the same way.

Method - Playbook
-----------------
The Playbook is single-column. ``pdftotext -layout`` text is parsed line by line:
subcategory headings (``GOVERN 1.1`` alone on a line) start a section; the
statement follows; "Suggested Actions", "Transparency & Documentation" /
"Organizations can document the following", "AI Transparency Resources" and
"References" delimit blocks. Top-level bullets (``•`` at indentation <= 4)
become items; deeper-indented bullets become ``sub_actions`` of the preceding
item; unbulleted lead-in text (e.g. "Organizational AI risk management policies
should be designed to:") is kept as ``lead_in``. Page footers ("N of 142") are
dropped. Cross-checked against pypdf text (word-sequence similarity >= 0.95
on every page; see docs/frameworks/ai_rmf.md).

Run:  python scripts/extract/ai_rmf.py [--check]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RMF_PDF = ROOT / "sources" / "pdfs" / "nist-ai-rmf-1-0.pdf"
PB_PDF = ROOT / "sources" / "pdfs" / "nist-ai-rmf-playbook.pdf"
RMF_OUT = ROOT / "catalog" / "nist-ai-rmf.json"
PB_OUT = ROOT / "catalog" / "nist-ai-rmf-playbook.json"
EXTRACTION_DATE = "2026-10-13"

# --------------------------------------------------------------- expectations
# AI RMF 1.0 Tables 1-4 (PDF pp. 27-38). Counts verified by reading the tables.
EXPECTED = {
    "GOVERN": {1: 7, 2: 3, 3: 2, 4: 3, 5: 2, 6: 2},          # 19
    "MAP": {1: 6, 2: 3, 3: 5, 4: 2, 5: 2},                  # 18
    "MEASURE": {1: 3, 2: 13, 3: 3, 4: 3},                   # 22
    "MANAGE": {1: 4, 2: 4, 3: 2, 4: 3},                     # 13
}
EXPECTED_SUBCATEGORIES = 72
EXPECTED_CATEGORIES = 19
RMF_PRINTED_OFFSET = 5     # printed "Page N" = PDF page - 5 (Part 1 onwards)
PB_PRINTED_OFFSET = 3      # printed "N of 142" = PDF page - 3 (body pages)
PB_EXPECTED_PAGES = 147

FUNCTIONS = ["GOVERN", "MAP", "MEASURE", "MANAGE"]
TABLE_PAGES = {
    "GOVERN": [27, 28, 29],
    "MAP": [31, 32, 33],
    "MEASURE": [34, 35, 36],
    "MANAGE": [37, 38],
}
# Function sections (Section 5.1-5.4) - start page and a paraphrased summary.
FUNCTION_META = {
    "GOVERN": (26, "5.1", "Cross-cutting function that cultivates a culture of risk management: "
               "policies, accountability, workforce diversity, risk culture, stakeholder engagement and "
               "third-party/supply-chain risk. Infused throughout the other three functions."),
    "MAP": (29, "5.2", "Establishes the context to frame risks related to an AI system: purposes, "
            "categorisation, capabilities/costs/benefits, risks of components incl. third parties, and "
            "impacts on individuals, groups, organisations and society. Informs an initial go/no-go decision."),
    "MEASURE": (33, "5.3", "Employs quantitative, qualitative or mixed-method tools to analyse, assess, "
                "benchmark and monitor AI risk and impacts, including TEVV of trustworthy characteristics, "
                "tracking of emergent risks and feedback on measurement efficacy."),
    "MANAGE": (36, "5.4", "Allocates risk resources to mapped and measured risks on a regular basis: "
               "prioritise and respond to risks, maximise benefits, manage third-party risk, and document "
               "response, recovery, communication and monitoring plans."),
}

# Genuine hyphenated compounds that are split at a line end in the tables.
KEEP_HYPHEN = {"context-specific", "context-relevant"}

# Trustworthy AI characteristics, Section 3 (PDF pp. 17-23). Heading and start
# page are asserted against the PDF text below; summary is paraphrased.
TRUSTWORTHY = [
    ("valid-reliable", "3.1", "Valid and Reliable", 18,
     "Validation confirms, with objective evidence, that requirements for a specific intended use are met; "
     "reliability is the ability to perform as required without failure over time under given conditions. "
     "Accuracy and robustness contribute to validity. Shown in Fig. 4 as the necessary base for the other "
     "characteristics."),
    ("safe", "3.2", "Safe", 19,
     "AI systems should not, under defined conditions, lead to a state endangering human life, health, "
     "property or the environment. Supported by responsible design and deployment, clear information to "
     "deployers, responsible use, and documentation of risks based on incident evidence; risks of serious "
     "injury or death warrant the most urgent prioritisation."),
    ("secure-resilient", "3.3", "Secure and Resilient", 20,
     "Resilient systems withstand unexpected adverse events or changes and degrade safely; secure systems "
     "maintain confidentiality, integrity and availability via protection mechanisms and protocols to "
     "avoid, protect against, respond to or recover from attacks (e.g. adversarial examples, data "
     "poisoning, model or data exfiltration)."),
    ("accountable-transparent", "3.4", "Accountable and Transparent", 20,
     "Accountability presupposes transparency: the extent to which information about an AI system and its "
     "outputs is available to those interacting with it, tailored to role and lifecycle stage. Shown in "
     "Fig. 4 as relating to all other characteristics."),
    ("explainable-interpretable", "3.5", "Explainable and Interpretable", 21,
     "Explainability represents the mechanisms underlying system operation (how a decision was made); "
     "interpretability is the meaning of outputs in the context of the designed purpose (why). Together "
     "they help operators, overseers and users understand functionality and trustworthiness."),
    ("privacy-enhanced", "3.6", "Privacy-Enhanced", 22,
     "Norms and practices that safeguard human autonomy, identity and dignity (freedom from intrusion, "
     "limiting observation, consent and control). Privacy-enhancing technologies and data minimisation "
     "support privacy-enhanced design; tradeoffs with accuracy and fairness may arise."),
    ("fair-bias-managed", "3.7", "Fair – with Harmful Bias Managed", 22,
     "Fairness concerns equality and equity by addressing harmful bias and discrimination. NIST identifies "
     "three major categories of AI bias - systemic, computational and statistical, and human-cognitive - "
     "each of which can occur without prejudice or discriminatory intent."),
]

SUB_RE = re.compile(r"\b(GOVERN|MAP|MEASURE|MANAGE) (\d+)\.(\d+):")
CAT_RE = re.compile(r"\b(GOVERN|MAP|MEASURE|MANAGE) (\d+):")


# --------------------------------------------------------------- helpers
def _need(tool: str) -> None:
    if not shutil.which(tool):
        sys.exit(f"{tool} not found on PATH (install poppler-utils)")


def pdftotext(pdf: Path, first: int, last: int | None = None, crop: tuple[float, float, float, float] | None = None,
              layout: bool = True) -> str:
    _need("pdftotext")
    cmd = ["pdftotext", "-f", str(first), "-l", str(last or first)]
    if layout:
        cmd.append("-layout")
    if crop:
        x, y, w, h = crop
        cmd += ["-x", str(int(x)), "-y", str(int(y)), "-W", str(int(w)), "-H", str(int(h))]
    cmd += [str(pdf), "-"]
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def join_lines(lines: list[str], soft_hyphens: bool = True) -> str:
    """Join wrapped lines.

    ``soft_hyphens=True`` (AI RMF 1.0, justified LaTeX text): remove end-of-line
    hyphenation except for the real compounds in ``KEEP_HYPHEN``.
    ``soft_hyphens=False`` (Playbook, ragged-right text with no automatic
    hyphenation): a line-end hyphen is part of a compound (e.g. ``third-party``)
    and is kept, joining without a space."""
    out = ""
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if not out:
            out = line
            continue
        if out.endswith("-") and not out.endswith(" -") and line[:1].islower():
            head = re.search(r"(\S+)-$", out).group(1)
            tail = re.match(r"[\w’']+", line).group(0)
            if not soft_hyphens or f"{head}-{tail}".lower() in KEEP_HYPHEN:
                out = out + line
            else:
                out = out[:-1] + line
        else:
            out = out + " " + line
    return re.sub(r"\s+", " ", out).strip()


# --------------------------------------------------------------- AI RMF core
def _table_geometry(page) -> tuple[float, float, float]:
    """Return (column_x, top, bottom) of the Core table on a pdfplumber page."""
    words = page.extract_words()
    head = [w for w in words if w["text"].startswith("Subcategories")]
    assert head, f"no 'Subcategories' header on PDF page {page.page_number}"
    col_x = head[0]["x0"] - 4
    top = head[0]["bottom"] + 1
    bottom = page.height - 60  # above the "Page N" footer
    for w in words:
        if w["top"] <= top:
            continue
        if w["text"].startswith("Continued") or (w["x0"] < 100 and re.match(r"^\d\.\d?$", w["text"])):
            bottom = min(bottom, w["top"] - 1)
    # sanity: nothing in the left column crosses the column boundary
    for w in words:
        if top < w["top"] < bottom and w["x0"] < col_x < w["x1"]:
            raise AssertionError(f"word {w['text']!r} straddles column boundary on PDF page {page.page_number}")
    return col_x, top, bottom


def extract_core() -> tuple[list[dict], list[dict]]:
    import pdfplumber

    sub_text: dict[str, list[str]] = {}
    sub_page: dict[str, int] = {}
    cat_text: dict[str, list[str]] = {}
    cat_page: dict[str, int] = {}
    order: list[str] = []
    with pdfplumber.open(RMF_PDF) as pdf:
        for fn in FUNCTIONS:
            cur_sub = cur_cat = None
            for pno in TABLE_PAGES[fn]:
                page = pdf.pages[pno - 1]
                col_x, top, bottom = _table_geometry(page)
                right = pdftotext(RMF_PDF, pno, crop=(col_x, top, page.width - col_x, bottom - top))
                left = pdftotext(RMF_PDF, pno, crop=(0, top, col_x, bottom - top))
                for line in right.splitlines():
                    m = SUB_RE.search(line)
                    if m:
                        cur_sub = f"{m.group(1)} {m.group(2)}.{m.group(3)}"
                        assert m.group(1) == fn, (cur_sub, pno)
                        assert cur_sub not in sub_text, f"duplicate {cur_sub}"
                        sub_text[cur_sub] = [line[m.end():]]
                        sub_page[cur_sub] = pno
                        order.append(cur_sub)
                    elif cur_sub and line.strip():
                        sub_text[cur_sub].append(line)
                for line in left.splitlines():
                    m = CAT_RE.search(line)
                    if m:
                        cur_cat = f"{m.group(1)} {m.group(2)}"
                        cat_text[cur_cat] = [line[m.end():]]
                        cat_page[cur_cat] = pno
                    elif cur_cat and line.strip():
                        cat_text[cur_cat].append(line)

    categories = []
    for cid, lines in cat_text.items():
        fn = cid.split()[0]
        categories.append({
            "id": cid,
            "title": join_lines(lines),
            "kind": "category",
            "parent": fn,
            "citation": {"pdf_page": cat_page[cid], "printed_page": cat_page[cid] - RMF_PRINTED_OFFSET,
                         "section": f"{FUNCTION_META[fn][1]} Table {FUNCTIONS.index(fn) + 1}"},
        })
    items = []
    for sid in order:
        fn, num = sid.split()
        cat = f"{fn} {num.split('.')[0]}"
        items.append({
            "id": sid,
            "function": fn,
            "group": cat,
            "text": join_lines(sub_text[sid]),
            "citation": {"pdf_page": sub_page[sid], "printed_page": sub_page[sid] - RMF_PRINTED_OFFSET,
                         "section": f"{FUNCTION_META[fn][1]} Table {FUNCTIONS.index(fn) + 1}"},
        })
    return categories, items


def extract_trustworthy() -> list[dict]:
    out = []
    for cid, num, name, page, summary in TRUSTWORTHY:
        text = pdftotext(RMF_PDF, page)
        pat = re.compile(rf"^\s*{re.escape(num)}\s+{re.escape(name)}\s*$", re.M)
        assert pat.search(text), f"heading '{num} {name}' not found on PDF page {page}"
        out.append({"id": cid, "section": num, "name": name, "summary": summary,
                    "summary_fidelity": "paraphrased",
                    "citation": {"pdf_page": page, "printed_page": page - RMF_PRINTED_OFFSET,
                                 "section": f"{num} {name}"}})
    return out


def check_core(categories: list[dict], items: list[dict]) -> None:
    assert len(categories) == EXPECTED_CATEGORIES, len(categories)
    assert len(items) == EXPECTED_SUBCATEGORIES, len(items)
    for fn, cats in EXPECTED.items():
        for cat, n in cats.items():
            got = [i for i in items if i["group"] == f"{fn} {cat}"]
            assert len(got) == n, (fn, cat, len(got), n)
            assert [i["id"] for i in got] == [f"{fn} {cat}.{k}" for k in range(1, n + 1)], (fn, cat)
    for i in items:
        t = i["text"]
        assert len(t) > 40, (i["id"], t)
        assert t[-1] in ".)", (i["id"], t)
        assert "Continued" not in t and "Page " not in t, (i["id"], t)
        assert not re.search(r"[a-z]- [a-z]", t), (i["id"], "suspicious hyphenation", t)
    for c in categories:
        assert c["title"].endswith("."), c
    # spot checks against the PDF (Table 1-4 wording)
    by = {i["id"]: i["text"] for i in items}
    assert by["GOVERN 1.1"] == "Legal and regulatory requirements involving AI are understood, managed, and documented."
    assert by["MAP 1.5"] == "Organizational risk tolerances are determined and documented."
    assert by["MANAGE 1.3"].endswith("Risk response options can include mitigating, transferring, avoiding, or accepting.")
    assert "context-specific laws" in by["MAP 1.1"]
    assert "context-relevant risks" in by["MEASURE 4.3"]


def build_core() -> dict:
    categories, items = extract_core()
    check_core(categories, items)
    functions = []
    for fn in FUNCTIONS:
        page, sec, summary = FUNCTION_META[fn]
        functions.append({"id": fn, "title": fn.capitalize(), "kind": "function", "parent": None,
                          "summary": summary,
                          "citation": {"pdf_page": page, "printed_page": page - RMF_PRINTED_OFFSET,
                                       "section": f"{sec} {fn.capitalize()}"}})
    trust = extract_trustworthy()
    counts = {fn: sum(1 for i in items if i["function"] == fn) for fn in FUNCTIONS}
    return {
        "catalog_id": "nist-ai-rmf",
        "source_id": "nist-ai",
        "title": "NIST AI Risk Management Framework (AI RMF 1.0) Core - functions, categories and subcategories",
        "edition": "NIST AI 100-1, AI RMF 1.0, January 2023",
        "description": (
            "The AI RMF Core (Part 2, Section 5, Tables 1-4): 4 functions, 19 categories and 72 subcategories, "
            "plus the 7 characteristics of trustworthy AI (Section 3). Subcategory text is reproduced verbatim "
            "(whitespace and end-of-line hyphenation normalised) from NIST AI 100-1, a U.S. Government work. "
            "Function summaries and trustworthy-characteristic summaries are paraphrased."),
        "extraction": {
            "method": "scripts/extract/ai_rmf.py: pdfplumber table geometry + pdftotext -layout on cropped columns",
            "date": EXTRACTION_DATE,
            "fidelity": "verbatim-normalised-whitespace",
            "notes": ("Items (subcategories) and group titles for categories are verbatim with whitespace and "
                      "hyphenation normalised; function 'summary' and trustworthy 'summary' fields are paraphrased. "
                      "printed_page = pdf_page - 5."),
            "pages_reviewed": "17-23 (Section 3), 25-38 (Section 5 and Tables 1-4)",
        },
        "levels": {},
        "groups": functions + categories,
        "items": items,
        "parameters": {
            "functions": FUNCTIONS,
            "subcategory_counts": counts,
            "category_counts": {fn: len(EXPECTED[fn]) for fn in FUNCTIONS},
            "total_subcategories": len(items),
            "trustworthy_characteristics": trust,
            "trustworthy_characteristics_note": (
                "Section 3, PDF p. 17 (printed p. 12) lists the characteristics; Fig. 4 shows Valid & Reliable as "
                "the base and Accountable & Transparent as relating to all others. Safe, Secure & Resilient, "
                "Explainable & Interpretable, Privacy-Enhanced and Fair with harmful bias managed sit on that base."),
            "profiles": {
                "summary": ("Section 6 (PDF p. 38, printed p. 33): use-case profiles implement the functions, "
                            "categories and subcategories for a specific setting; temporal profiles describe a "
                            "Current Profile and a Target Profile; comparing them reveals gaps for action plans."),
                "citation": {"pdf_page": 38, "printed_page": 33, "section": "6 AI RMF Profiles"},
            },
            "risk_response_options": {
                "values": ["mitigate", "transfer", "avoid", "accept"],
                "citation": {"pdf_page": 37, "printed_page": 32, "section": "MANAGE 1.3"},
            },
        },
    }


# --------------------------------------------------------------- Playbook
HEAD_RE = re.compile(r"^(GOVERN|MAP|MEASURE|MANAGE) (\d+\.\d+)\s*$")
FOOTER_RE = re.compile(r"^\s*(\d+) of 142\s*$")
BULLET_RE = re.compile(r"^(\s*)[•●▪]\s*(.*)$")
SECTION_HEADS = {
    "About": "about",
    "Suggested Actions": "actions",
    "Transparency & Documentation": "td",
    "Organizations can document the following": "questions",
    "Organizations can document the following:": "questions",
    "AI Transparency Resources": "resources",
    "References": "references",
}


def _pb_lines() -> list[tuple[int, str]]:
    text = pdftotext(PB_PDF, 1, PB_EXPECTED_PAGES)
    pages = text.split("\f")
    assert len(pages) >= PB_EXPECTED_PAGES, len(pages)
    out = []
    for pno, page in enumerate(pages[:PB_EXPECTED_PAGES], start=1):
        for line in page.splitlines():
            if FOOTER_RE.match(line):
                continue
            out.append((pno, line.rstrip()))
    return out


def _bullets(block: list[tuple[int, str]]) -> tuple[list[dict], list[str]]:
    """Parse a block of lines into top-level bullets with nested sub-bullets.

    Returns (items, unbulleted_text_paragraphs)."""
    items: list[dict] = []
    loose: list[list[str]] = []
    cur = None          # current top-level item
    cur_sub = None      # current nested bullet (list of lines)
    target = None       # list of lines receiving continuations
    for pno, line in block:
        if not line.strip():
            if target is not None and target is not cur_sub and cur is None:
                pass
            continue
        m = BULLET_RE.match(line)
        if m:
            indent = len(m.group(1))
            if indent <= 2:
                cur = {"page": pno, "lines": [m.group(2)], "subs": [], "indent": indent}
                items.append(cur)
                cur_sub = None
                target = cur["lines"]
            else:
                if cur is None:  # nested bullet with no parent: treat as top-level
                    cur = {"page": pno, "lines": [m.group(2)], "subs": [], "indent": indent}
                    items.append(cur)
                    target = cur["lines"]
                else:
                    cur_sub = [m.group(2)]
                    cur["subs"].append(cur_sub)
                    target = cur_sub
            continue
        indent = len(line) - len(line.lstrip())
        if target is not None and indent >= 2:
            target.append(line)
        else:
            # unbulleted text at column 0: lead-in or prose
            cur = cur_sub = None
            target = None
            if loose and loose[-1] and not loose[-1][-1].rstrip().endswith((".", ":")):
                loose[-1].append(line)
            else:
                loose.append([line])
    result = []
    for it in items:
        result.append({"page": it["page"], "text": join_lines(it["lines"], False),
                       "subs": [join_lines(s, False) for s in it["subs"]]})
    return result, [join_lines(p, False) for p in loose if p]


def extract_playbook(core_ids: list[str]) -> tuple[list[dict], dict, list[str]]:
    lines = _pb_lines()
    sections: dict[str, dict] = {}
    order = []
    cur = None
    mode = None
    i = 0
    while i < len(lines):
        pno, line = lines[i]
        m = HEAD_RE.match(line.strip()) if line.strip() == line.strip() else None
        if m and not line.startswith(" "):
            sid = f"{m.group(1)} {m.group(2)}"
            assert sid not in sections, f"duplicate playbook heading {sid}"
            # statement: following non-blank lines until blank
            stmt = []
            j = i + 1
            while j < len(lines) and lines[j][1].strip():
                stmt.append(lines[j][1])
                j += 1
            cur = {"id": sid, "page": pno, "statement": join_lines(stmt, False),
                   "blocks": {k: [] for k in ("about", "actions", "td", "questions", "resources", "references")}}
            sections[sid] = cur
            order.append(sid)
            mode = None
            i = j
            continue
        key = SECTION_HEADS.get(line.strip())
        if cur is not None and key and not line.startswith("  "):
            mode = key
        elif cur is not None and mode:
            cur["blocks"][mode].append((pno, line))
        i += 1

    assert order and set(order) == set(core_ids), (sorted(set(core_ids) - set(order)), sorted(set(order) - set(core_ids)))
    items: list[dict] = []
    per_sub: dict[str, dict] = {}
    gaps: list[str] = []
    for sid in core_ids:
        sec = sections[sid]
        actions, act_loose = _bullets(sec["blocks"]["actions"])
        questions, q_loose = _bullets(sec["blocks"]["questions"] + sec["blocks"]["td"])
        lead_in = " ".join(act_loose) if act_loose else None
        if not actions:
            gaps.append(f"{sid}: no bulleted suggested actions found")
        if not questions:
            gaps.append(f"{sid}: no transparency & documentation questions found")
        for n, a in enumerate(actions, 1):
            item = {"id": f"{sid}/action-{n}", "subcategory": sid, "kind": "suggested-action",
                    "group": sid.split()[0], "text": a["text"],
                    "citation": {"pdf_page": a["page"], "printed_page": f"{a['page'] - PB_PRINTED_OFFSET} of 142",
                                 "section": f"{sid} Suggested Actions"}}
            if a["subs"]:
                item["sub_actions"] = a["subs"]
            if lead_in:
                item["lead_in"] = lead_in
            items.append(item)
        for n, q in enumerate(questions, 1):
            text = q["text"] + ((" " + " ".join(q["subs"])) if q["subs"] else "")
            items.append({"id": f"{sid}/question-{n}", "subcategory": sid, "kind": "documentation-question",
                          "group": sid.split()[0], "text": text,
                          "citation": {"pdf_page": q["page"], "printed_page": f"{q['page'] - PB_PRINTED_OFFSET} of 142",
                                       "section": f"{sid} Transparency & Documentation"}})
        per_sub[sid] = {"pdf_page": sec["page"], "statement": sec["statement"],
                        "actions": len(actions), "questions": len(questions)}
    return items, per_sub, gaps


def check_playbook(items: list[dict], per_sub: dict, core: dict) -> None:
    assert len(per_sub) == EXPECTED_SUBCATEGORIES
    for sid, info in per_sub.items():
        assert info["actions"] >= 1, sid
        assert 6 <= info["pdf_page"] <= PB_EXPECTED_PAGES, sid
    for it in items:
        t = it["text"]
        assert len(t) >= 3, it
        assert not FOOTER_RE.search(t), it
        assert "Transparency & Documentation" not in t and "Suggested Actions" not in t, it
    ids = [i["id"] for i in items]
    assert len(ids) == len(set(ids))
    # spot checks (PDF p. 6, GOVERN 1.1)
    by = {i["id"]: i["text"] for i in items}
    assert by["GOVERN 1.1/action-2"] == "Align risk management efforts with applicable legal standards."
    assert by["GOVERN 1.1/question-1"].startswith("To what extent has the entity defined and documented the regulatory")


def build_playbook(core: dict) -> dict:
    core_ids = [i["id"] for i in core["items"]]
    items, per_sub, gaps = extract_playbook(core_ids)
    check_playbook(items, per_sub, core)
    statement_diffs = sorted(sid for sid, info in per_sub.items()
                             if re.sub(r"\W", "", info["statement"].lower()) !=
                             re.sub(r"\W", "", next(i["text"] for i in core["items"] if i["id"] == sid).lower()))
    n_actions = sum(1 for i in items if i["kind"] == "suggested-action")
    n_q = len(items) - n_actions
    return {
        "catalog_id": "nist-ai-rmf-playbook",
        "source_id": "nist-ai-playbook",
        "title": "NIST AI RMF Playbook - suggested actions and transparency & documentation questions",
        "edition": "NIST AI RMF Playbook (companion to AI RMF 1.0; 142 numbered pages)",
        "description": (
            "Per AI RMF subcategory, the Playbook's Suggested Actions (ids '<SUBCATEGORY>/action-N') and the "
            "Transparency & Documentation questions ('<SUBCATEGORY>/question-N'). Text reproduced from the NIST "
            "Playbook (U.S. Government work) with whitespace and line-end hyphenation normalised. 'About' prose, "
            "AI Transparency Resources and References are not reproduced. The Playbook is voluntary guidance; "
            "actions are suggestions, not requirements."),
        "extraction": {
            "method": "scripts/extract/ai_rmf.py: pdftotext -layout line parser (bullets, nested bullets, lead-ins)",
            "date": EXTRACTION_DATE,
            "fidelity": "verbatim-normalised-whitespace",
            "notes": ("Nested bullets are kept in 'sub_actions'; unbulleted lead-in text in 'lead_in'. "
                      "Source typos are preserved (e.g. 'stablish' in MANAGE 2.2, PDF p. 46). "
                      "printed_page = pdf_page - 3 ('N of 142'). Text cross-checked against pypdf; "
                      f"subcategory statements differing in wording from AI RMF 1.0 tables: {', '.join(statement_diffs)}. "
                      + ("Gaps: " + "; ".join(gaps) if gaps else "No extraction gaps detected.")),
            "pages_reviewed": "4-147",
        },
        "groups": [{"id": fn, "title": fn.capitalize(),
                    "citation": {"pdf_page": min(v["pdf_page"] for k, v in per_sub.items() if k.startswith(fn + " ")) - 1}}
                   for fn in FUNCTIONS],
        "items": items,
        "parameters": {
            "subcategories": per_sub,
            "counts": {"suggested_actions": n_actions, "documentation_questions": n_q},
            "statement_wording_differs_from_ai_rmf": statement_diffs,
            "gaps": gaps,
        },
    }


# --------------------------------------------------------------- main
def dump(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="fail if the committed catalogs differ")
    args = ap.parse_args(argv)
    core = build_core()
    pb = build_playbook(core)
    outputs = {RMF_OUT: dump(core), PB_OUT: dump(pb)}
    if args.check:
        stale = [p for p, txt in outputs.items() if not p.is_file() or p.read_text(encoding="utf-8") != txt]
        if stale:
            print("stale: " + ", ".join(str(p.relative_to(ROOT)) for p in stale), file=sys.stderr)
            return 1
        print("catalogs up to date")
        return 0
    for path, txt in outputs.items():
        path.write_text(txt, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")
    print(f"AI RMF: {len(core['groups'])} groups, {len(core['items'])} subcategories; "
          f"Playbook: {pb['parameters']['counts']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
