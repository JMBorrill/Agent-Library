#!/usr/bin/env python3
"""Extract NIST SP 800-218 (SSDF 1.1) Table 1 into catalog/nist-ssdf.json.

Reads the pinned PDF ``sources/pdfs/nist-ssdf-1-1.pdf`` with pdfplumber.

Table 1 (PDF pages 14-28, landscape) has four fixed-width columns whose
borders are drawn as rectangles at the same x positions on every page:

    Practices  x 39-243 | Tasks x 243-472 | Notional Implementation Examples x 473-810 | References x 810-1186

Each column is cropped and read line by line (``extract_text_lines``). A task
row starts at a line matching ``XX.n.n:`` in the Tasks column; every example /
reference line whose (page, top) lies between that task's start and the next
task's start belongs to that task. Practices start at a bold line in the
Practices column that follows a non-bold line. Group header rows ("Prepare the
Organization (PO)" ...) are bold one-liners matched by name.

Text is verbatim with whitespace normalised (line breaks joined with a space;
a line ending in a hyphen is joined without a space, which preserves compound
words such as "open-source" split across lines).

Usage: python scripts/extract/ssdf.py [--check]   (--check: compare, do not write)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "sources" / "pdfs" / "nist-ssdf-1-1.pdf"
OUT = ROOT / "catalog" / "nist-ssdf.json"

TABLE_PAGES = range(14, 29)  # 1-based PDF pages holding Table 1
PRINTED_OFFSET = 9  # printed page label = pdf page - 9 for the body (p.10 -> "1")
COLS = {"practice": (39, 243), "task": (243, 472), "example": (473, 810), "reference": (810, 1186)}
TOP_MIN = 88.0  # below running header and column header row
BOTTOM_MAX = 725.0  # above page number
GROUP_PAGE = 13  # Section 2 group definitions
EO_TABLE_PAGE = 33  # Appendix A, Table 2
EXTRACTION_DATE = "2026-10-13"  # pinned so re-running the script is byte-reproducible

GROUPS = [
    ("PO", "Prepare the Organization"),
    ("PS", "Protect the Software"),
    ("PW", "Produce Well-Secured Software"),
    ("RV", "Respond to Vulnerabilities"),
]
EXPECTED_ACTIVE_PRACTICES = {"PO": 5, "PS": 3, "PW": 8, "RV": 3}  # 19
EXPECTED_ACTIVE_TASKS = 42
EXPECTED_RETIRED = {"PW.3", "PW.3.1", "PW.3.2", "PW.4.3", "PW.4.5", "PW.5.2"}  # per Change Log, PDF p.36

TASK_RE = re.compile(r"^((?:PO|PS|PW|RV)\.\d+\.\d+):\s*(.*)$")
PRACTICE_ID_RE = re.compile(r"\(((?:PO|PS|PW|RV)\.\d+)\):\s*")
REF_RE = re.compile(r"^([A-Z][A-Za-z0-9]+):\s*(.*)$")
EXAMPLE_RE = re.compile(r"Example\s+(\d+):\s*")
MOVED_RE = re.compile(r"^Moved to (.+)$")
ID_RE = re.compile(r"(?:PO|PS|PW|RV)\.\d+(?:\.\d+)?")
GROUP_ROW_RE = re.compile(r"^([A-Z][A-Za-z -]+) \((PO|PS|PW|RV)\)$")
FORMERLY_RE = re.compile(r"\[Formerly ((?:PO|PS|PW|RV)\.\d+\.\d+)\]")


def join_lines(lines: list[str]) -> str:
    out = ""
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        if not out:
            out = ln
        elif out.endswith("-") and not out.endswith(" -"):
            out += ln
        else:
            out += " " + ln
    out = re.sub(r"\s+", " ", out).strip()
    # a removed superscript footnote marker can leave "architecture ." behind
    return re.sub(r" ([.,;:])(?=\s|$)", r"\1", out)


def footnote_rule_top(page) -> float:
    """Top of the short footnote separator rule (x 36-180), or BOTTOM_MAX if the page has none."""
    rules = [r["top"] for r in page.rects
             if abs(r["x0"] - 36) < 2 and abs(r["x1"] - 180) < 2 and r["bottom"] - r["top"] < 2]
    return min(rules) if rules else BOTTOM_MAX


def column_lines(page, page_no: int, col: str) -> list[dict]:
    x0, x1 = COLS[col]
    bottom = footnote_rule_top(page)
    # drop superscript footnote markers (6-7pt) so they do not leak into the text
    crop = page.crop((x0, TOP_MIN, x1, bottom)).filter(
        lambda o: o.get("object_type") != "char" or o.get("size", 9) >= 8)
    rows = []
    for ln in crop.extract_text_lines(return_chars=True, strip=True):
        chars = [c for c in ln["chars"] if c.get("upright", True)]
        if not chars or not ln["text"].strip():
            continue
        rows.append({
            "page": page_no,
            "top": float(ln["top"]),
            "text": ln["text"].strip(),
            "bold": "Bold" in chars[0]["fontname"],
        })
    return rows


def pos(row: dict) -> tuple[int, float]:
    return (row["page"], row["top"])


def extract(pdf_path: Path = PDF) -> dict:
    pdf = pdfplumber.open(str(pdf_path))
    cols: dict[str, list[dict]] = {c: [] for c in COLS}
    for n in TABLE_PAGES:
        page = pdf.pages[n - 1]
        for c in COLS:
            rows = column_lines(page, n, c)
            # drop the repeated column header row
            rows = [r for r in rows if r["text"] not in {"Practices", "Tasks", "Notional Implementation Examples", "References"}]
            cols[c] += rows

    # ---- group headers and practices (Practices column)
    # Table 1 labels PS as "Protect Software (PS)"; Section 2 says "Protect the Software (PS)".
    group_rows: dict[str, dict] = {}
    practice_rows: list[dict] = []
    for r in cols["practice"]:
        gm = GROUP_ROW_RE.match(r["text"])
        if r["bold"] and gm:
            group_rows[gm.group(2)] = {**r, "label": gm.group(1)}
        else:
            practice_rows.append(r)
    practices_raw: list[list[dict]] = []
    prev_bold = False
    for r in practice_rows:
        if r["bold"] and not prev_bold:
            practices_raw.append([])
        if not practices_raw:
            raise AssertionError(f"practice text before first practice: {r}")
        practices_raw[-1].append(r)
        prev_bold = r["bold"]

    practices = []
    for chunk in practices_raw:
        text = join_lines([r["text"] for r in chunk])
        m = PRACTICE_ID_RE.search(text)
        if not m:
            raise AssertionError(f"no practice id in {text[:80]!r}")
        pid = m.group(1)
        name = text[: m.start()].strip()
        desc = text[m.end():].strip()
        practices.append({"id": pid, "name": name, "text": desc, "start": pos(chunk[0])})

    # ---- tasks (Tasks column)
    tasks = []
    for r in cols["task"]:
        m = TASK_RE.match(r["text"])
        if m:
            tasks.append({"id": m.group(1), "lines": [m.group(2)], "start": pos(r)})
        else:
            if not tasks:
                raise AssertionError(f"task text before first task: {r}")
            tasks[-1]["lines"].append(r["text"])

    TOL = 6.0  # row padding differs slightly between columns

    def owner(row: dict, starts: list[tuple[int, float]]) -> int | None:
        idx = None
        for i, (pg, top) in enumerate(starts):
            if (row["page"], row["top"] + TOL) >= (pg, top):
                idx = i
        return idx

    starts = [t["start"] for t in tasks]
    ex_lines: dict[int, list[dict]] = {}
    ref_lines: dict[int, list[dict]] = {}
    for c, bucket in (("example", ex_lines), ("reference", ref_lines)):
        for r in cols[c]:
            i = owner(r, starts)
            if i is None:
                raise AssertionError(f"{c} line before first task: {r}")
            bucket.setdefault(i, []).append(r)

    pstarts = [p["start"] for p in practices]
    items = []
    group_of = {}
    for p in practices:
        gid = p["id"].split(".")[0]
        moved = MOVED_RE.match(p["text"])
        item = {
            "id": p["id"],
            "kind": "practice",
            "title": p["name"],
            "text": p["text"],
            "group": gid,
            "status": "retired" if moved else "active",
            "citation": {"pdf_page": p["start"][0], "printed_page": p["start"][0] - PRINTED_OFFSET,
                         "section": "Table 1"},
        }
        if moved:
            item["moved_to"] = ID_RE.findall(moved.group(1))
        items.append(item)
        group_of[p["id"]] = gid

    for i, t in enumerate(tasks):
        text = join_lines(t["lines"])
        practice_id = ".".join(t["id"].split(".")[:2])
        if practice_id not in group_of:
            raise AssertionError(f"task {t['id']} has no practice")
        # sanity: the task row lies inside its practice's span in the table
        pi = owner({"page": t["start"][0], "top": t["start"][1]}, pstarts)
        if practices[pi]["id"] != practice_id:
            raise AssertionError(f"task {t['id']} sits under practice {practices[pi]['id']}")
        moved = MOVED_RE.match(text)
        ex_text = join_lines([r["text"] for r in ex_lines.get(i, [])])
        examples = []
        if ex_text:
            parts = EXAMPLE_RE.split(ex_text)
            if parts[0].strip():
                raise AssertionError(f"{t['id']}: example text without 'Example n:' prefix: {parts[0][:60]!r}")
            for num, body in zip(parts[1::2], parts[2::2]):
                examples.append(body.strip())
                if int(num) != len(examples):
                    raise AssertionError(f"{t['id']}: example numbering gap at {num}")
        refs: list[dict] = []
        for r in ref_lines.get(i, []):
            m = REF_RE.match(r["text"])
            if r["bold"] and m:
                refs.append({"ref": m.group(1), "lines": [m.group(2)]})
            else:
                if not refs:
                    raise AssertionError(f"{t['id']}: reference continuation without key: {r}")
                refs[-1]["lines"].append(r["text"])
        references = [{"ref": x["ref"], "text": join_lines(x["lines"])} for x in refs]
        item = {
            "id": t["id"],
            "kind": "task",
            "title": t["id"],
            "text": text,
            "group": practice_id.split(".")[0],
            "practice": practice_id,
            "status": "retired" if moved else "active",
            "examples": examples,
            "references": references,
            "citation": {"pdf_page": t["start"][0], "printed_page": t["start"][0] - PRINTED_OFFSET,
                         "section": "Table 1"},
        }
        pages = sorted({t["start"][0]} | {r["page"] for r in ex_lines.get(i, []) + ref_lines.get(i, [])})
        if len(pages) > 1:
            item["pdf_pages"] = pages
        fm = FORMERLY_RE.search(text)
        if fm:
            item["formerly"] = fm.group(1)
        if moved:
            item["moved_to"] = ID_RE.findall(moved.group(1))
        items.append(item)

    # order: practice followed by its tasks, in document order
    order = {p["id"]: n for n, p in enumerate(practices)}
    items.sort(key=lambda it: (order[it.get("practice", it["id"])], 0 if it["kind"] == "practice" else 1,
                               [int(x) for x in it["id"].split(".")[1:]]))

    # ---- groups (Section 2, PDF p.13)
    sec2 = join_lines((pdf.pages[GROUP_PAGE - 1].extract_text() or "").splitlines())
    sec2 = sec2.replace("This publication is available free of charge from: https://doi.org/10.6028/NIST.SP.800-218 ", "")
    groups = []
    for gid, name in GROUPS:
        m = re.search(rf"{re.escape(name)} \({gid}\): (.*?)(?= \d\. [A-Z][a-z]+ |\s+Each practice definition)", sec2)
        if not m:
            raise AssertionError(f"group definition for {gid} not found on p.{GROUP_PAGE}")
        groups.append({
            "id": gid,
            "title": name,
            "parent": None,
            "text": m.group(1).strip(),
            "citation": {"pdf_page": GROUP_PAGE, "printed_page": GROUP_PAGE - PRINTED_OFFSET, "section": "2"},
            "table_label": group_rows[gid]["label"],
            "table_header_page": group_rows[gid]["page"],
        })

    # ---- Appendix A Table 2: EO 14028 4e subsections -> SSDF tasks
    eo_text = pdf.pages[EO_TABLE_PAGE - 1].extract_text() or ""
    eo_map: dict[str, list[str] | str] = {}
    cur = None
    for ln in eo_text.splitlines():
        ln = ln.strip()
        m = re.match(r"^(4e\([ivx]+\)(?:\([A-F]\))?)\s+(.*)$", ln)
        if m:
            cur = m.group(1)
            eo_map[cur] = m.group(2)
        elif cur and re.match(r"^(?:(?:PO|PS|PW|RV)\.\d+\.\d+,?\s*)+$", ln):
            eo_map[cur] += " " + ln
        elif cur and ln.startswith("To coincide"):
            cur = None
    for k, v in list(eo_map.items()):
        ids = re.findall(r"(?:PO|PS|PW|RV)\.\d+\.\d+", v)
        eo_map[k] = ids if ids else v.strip()

    pdf.close()
    catalog = {
        "catalog_id": "nist-ssdf",
        "source_id": "nist-ssdf",
        "title": "Secure Software Development Framework (SSDF) Version 1.1 - practices and tasks",
        "edition": "NIST SP 800-218, SSDF Version 1.1 (February 2022)",
        "description": (
            "The four SSDF practice groups (PO, PS, PW, RV), every practice and task from Table 1 with "
            "notional implementation examples and informative references, plus Appendix A Table 2 "
            "(EO 14028 Section 4e to SSDF tasks). Retired identifiers listed in Table 1 are kept with "
            "status 'retired'. Source: NIST public information; attribution retained; no endorsement."
        ),
        "extraction": {
            "method": "pdfplumber column-cropped line extraction of Table 1 (scripts/extract/ssdf.py); "
                      "rows aligned by task start position; group text from Section 2",
            "date": EXTRACTION_DATE,
            "fidelity": "verbatim-normalised-whitespace",
            "pages_reviewed": "13-28 (Section 2 and Table 1), 33 (Appendix A Table 2), 36 (Change Log)",
            "notes": (
                "Practice, task, example and reference text is verbatim with line breaks normalised to single "
                "spaces; words hyphenated at a line break are joined keeping the hyphen (the SSDF table only "
                "breaks lines at real hyphens in compounds). Examples are split on the 'Example n:' prefixes. "
                "References are split on bold 'KEY:' prefixes; the reference keys are the document's own "
                "bibliography tags (e.g. SP80053 = NIST SP 800-53 Rev. 5). printed_page = pdf_page - 9. "
                "Retired ids (PW.3, PW.3.1, PW.3.2, PW.4.3, PW.4.5, PW.5.2) are kept for traceability with "
                "status 'retired' and moved_to. Tasks whose examples/references continue onto the next page "
                "carry pdf_pages."
            ),
        },
        "levels": {
            "assessment_status": ["implemented", "partial", "planned", "not-implemented", "not-applicable"],
        },
        "groups": groups,
        "items": items,
        "parameters": {"eo14028_4e_mapping": {"pdf_page": EO_TABLE_PAGE, "table": "Table 2", "mapping": eo_map}},
    }
    sanity(catalog)
    return catalog


def sanity(cat: dict) -> None:
    items = cat["items"]
    active_p = [i for i in items if i["kind"] == "practice" and i["status"] == "active"]
    active_t = [i for i in items if i["kind"] == "task" and i["status"] == "active"]
    retired = {i["id"] for i in items if i["status"] == "retired"}
    per_group = {g: sum(1 for p in active_p if p["group"] == g) for g in EXPECTED_ACTIVE_PRACTICES}
    assert per_group == EXPECTED_ACTIVE_PRACTICES, per_group
    assert len(active_p) == 19, len(active_p)
    assert len(active_t) == EXPECTED_ACTIVE_TASKS, len(active_t)
    assert retired == EXPECTED_RETIRED, retired
    ids = [i["id"] for i in items]
    assert len(ids) == len(set(ids)), "duplicate ids"
    for t in active_t:
        assert t["examples"], f"{t['id']} has no examples"
        assert t["references"], f"{t['id']} has no references"
        assert t["text"].endswith((".", "]")), f"{t['id']} text looks truncated: {t['text'][-40:]!r}"
        assert 14 <= t["citation"]["pdf_page"] <= 28
    for p in active_p:
        assert p["text"].endswith("."), f"{p['id']} text looks truncated"
        assert any(t["practice"] == p["id"] for t in active_t), f"{p['id']} has no tasks"
    # spot checks against the PDF
    by = {i["id"]: i for i in items}
    assert by["PO.1.1"]["text"].startswith("Identify and document all security requirements for the organization")
    assert by["PO.1.3"].get("formerly") == "PW.3.1"
    assert by["PW.4.3"]["moved_to"] == ["PW.1.3"]
    assert by["PW.4.5"]["moved_to"] == ["PW.4.1", "PW.4.4"]
    assert by["RV.3.4"]["citation"]["pdf_page"] == 27
    assert len(by["PO.1.2"]["examples"]) == 7
    assert cat["parameters"]["eo14028_4e_mapping"]["mapping"]["4e(vii)"] == ["PS.3.2"]
    assert len(cat["parameters"]["eo14028_4e_mapping"]["mapping"]) == 15  # 4e(i)(A)-(F) + 4e(ii)-(x)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="verify catalog/nist-ssdf.json matches a fresh extraction")
    args = ap.parse_args(argv)
    cat = extract()
    if args.check:
        current = json.loads(OUT.read_text(encoding="utf-8"))
        if current != cat:
            print("catalog/nist-ssdf.json differs from a fresh extraction", file=sys.stderr)
            return 1
        print("catalog/nist-ssdf.json matches the PDF extraction")
        return 0
    OUT.write_text(json.dumps(cat, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    n_t = sum(1 for i in cat["items"] if i["kind"] == "task" and i["status"] == "active")
    n_p = sum(1 for i in cat["items"] if i["kind"] == "practice" and i["status"] == "active")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(cat['groups'])} groups, {n_p} practices, {n_t} tasks "
          f"(+{len(EXPECTED_RETIRED)} retired ids)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
