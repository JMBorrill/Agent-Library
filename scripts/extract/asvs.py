#!/usr/bin/env python3
"""Extract the OWASP ASVS 5.0.0 requirement catalog from the pinned PDF.

Source : sources/pdfs/owasp-asvs-5-0-0-en.pdf (source id ``owasp-asvs``)
Licence: Copyright (c) 2008-2025 The OWASP Foundation, CC BY-SA 4.0.
         The generated catalog is a derivative (requirement text reproduced
         verbatim with whitespace/hyphen normalisation) and carries the same
         attribution and licence.
Output : catalog/owasp-asvs-5.json

Method
------
``pdftotext -layout`` renders each PDF page (form-feed separated, so the Nth
chunk is PDF page N). In 5.0.0 every requirement table row starts with the
identifier ``<chapter>.<section>.<requirement>`` in the first column, the
description in the second column and the level (1, 2 or 3) at the end of the
row's first line. Continuation lines of the description are indented under
the description column. Chapter (``V<n> Title``) and section
(``V<n>.<m> Title``) headings start in column 0.

Run:  python scripts/extract/asvs.py [--check]
``--check`` regenerates in memory and fails if catalog/owasp-asvs-5.json differs.
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
PDF = ROOT / "sources" / "pdfs" / "owasp-asvs-5-0-0-en.pdf"
OUT = ROOT / "catalog" / "owasp-asvs-5.json"
EXTRACTION_DATE = "2026-10-13"

# Sanity expectations, all verified against the document text:
#  * 17 chapters, V1..V17 (Contents, PDF pp. 3-6; "17 chapters", PDF p. 15)
#  * "In 5.0.0 there are 70 L1 requirements out of a total of 345" (PDF p. 23)
EXPECTED_CHAPTERS = 17
EXPECTED_SECTIONS = 80
EXPECTED_REQUIREMENTS = 345
EXPECTED_L1 = 70
PRINTED_PAGE_OFFSET = 1  # printed page label = PDF page - 1 (cover is unnumbered)

REQ_RE = re.compile(r"^\s{1,8}(\d+)\.(\d+)\.(\d+)\s{2,}(\S.*?)\s{2,}([123])\s*$")
CHAPTER_RE = re.compile(r"^V(\d+) (\S.*?)\s*$")
SECTION_RE = re.compile(r"^V(\d+)\.(\d+) (\S.*?)\s*$")
FOOTER_RE = re.compile(r"^\s*\d+\s*$")

LEVELS = {
    "cumulative": True,
    "statement": (
        "Levels are cumulative: complying with a level means meeting every requirement at that "
        "level and below (e.g. L2 = all L1 and L2 requirements); requirements of higher levels are "
        "recommendations."
    ),
    "statement_citations": [
        {"pdf_page": 13, "printed_page": 12, "section": "Application Security Verification Levels"},
        {"pdf_page": 14, "printed_page": 13, "section": "Level 2"},
    ],
    "1": {
        "name": "Level 1",
        "summary": (
            "Minimum, critical starting point (~20% of requirements): first-layer-of-defence "
            "controls against common attacks that need no other vulnerability or precondition. "
            "Not necessarily verifiable by black-box testing alone."
        ),
        "citation": {"pdf_page": 14, "printed_page": 13, "section": "Level 1"},
    },
    "2": {
        "name": "Level 2",
        "summary": (
            "The level most applications should strive for. Adds ~50% of requirements (less common "
            "attacks or more complicated protections); compliance needs all L1 and L2 "
            "requirements (~70% of the ASVS)."
        ),
        "citation": {"pdf_page": 14, "printed_page": 13, "section": "Level 2"},
    },
    "3": {
        "name": "Level 3",
        "summary": (
            "For applications demonstrating the highest levels of security; the final ~30% of "
            "requirements, generally defence-in-depth or hard-to-implement controls."
        ),
        "citation": {"pdf_page": 15, "printed_page": 14, "section": "Level 3"},
    },
    "selection_guidance": {
        "summary": (
            "ASVS does not prescribe a level; the organisation analyses its risks, application "
            "sensitivity and user expectations to choose one (e.g. a start-up with limited "
            "sensitive data may target L1; online banking may struggle to justify less than L3)."
        ),
        "citation": {"pdf_page": 15, "printed_page": 14, "section": "Which level to achieve"},
    },
}


def normalise(text: str) -> str:
    # U+2011 non-breaking hyphen is used throughout the PDF for ordinary hyphens.
    text = text.replace("‑", "-").replace(" ", " ")
    return re.sub(r"\s+", " ", text).strip()


def pdf_pages(pdf: Path) -> list[str]:
    exe = shutil.which("pdftotext")
    if not exe:
        sys.exit("pdftotext (poppler-utils) is required")
    out = subprocess.run([exe, "-layout", str(pdf), "-"], check=True, capture_output=True).stdout
    pages = out.decode("utf-8").split("\f")
    if pages and not pages[-1].strip():
        pages = pages[:-1]
    return pages


def extract(pages: list[str]) -> dict:
    groups: list[dict] = []
    items: list[dict] = []
    group_ids: set[str] = set()
    started = False
    for pno, page in enumerate(pages, start=1):
        lines = page.split("\n")
        current: dict | None = None
        for line in lines:
            if not started:
                # Skip the table of contents (PDF pp. 2-6); body starts at "V1 Encoding" on p. 24.
                if pno >= 20 and line.startswith("V1 Encoding and Sanitization"):
                    started = True
                else:
                    continue
            if line.startswith("Appendix A: Glossary"):
                return {"groups": groups, "items": items}
            m = SECTION_RE.match(line)
            if m:
                current = None
                gid = f"V{m.group(1)}.{m.group(2)}"
                if gid not in group_ids:
                    groups.append({"id": gid, "title": normalise(m.group(3)), "parent": f"V{m.group(1)}",
                                   "kind": "section", "citation": _cit(pno, gid)})
                    group_ids.add(gid)
                continue
            m = CHAPTER_RE.match(line)
            if m:
                current = None
                gid = f"V{m.group(1)}"
                if gid not in group_ids:
                    groups.append({"id": gid, "title": normalise(m.group(2)), "parent": None,
                                   "kind": "chapter", "citation": _cit(pno, gid)})
                    group_ids.add(gid)
                continue
            m = REQ_RE.match(line)
            if m:
                ch, sec, num = m.group(1), m.group(2), m.group(3)
                rid = f"{ch}.{sec}.{num}"
                current = {
                    "id": rid,
                    "text": m.group(4),
                    "level": int(m.group(5)),
                    "chapter": f"V{ch}",
                    "group": f"V{ch}.{sec}",
                    "citation": _cit(pno, f"V{ch}.{sec}"),
                }
                items.append(current)
                continue
            if current is None:
                continue
            if not line.strip():
                continue  # blank line inside or after a row; next non-blank decides
            indent = len(line) - len(line.lstrip(" "))
            if indent >= 10 and not FOOTER_RE.match(line):
                current["text"] += " " + line.strip()
            else:
                current = None
    raise SystemExit("did not reach Appendix A; extraction incomplete")


def _cit(pno: int, section: str) -> dict:
    return {"pdf_page": pno, "printed_page": pno - PRINTED_PAGE_OFFSET, "section": section}


def build() -> dict:
    pages = pdf_pages(PDF)
    data = extract(pages)
    groups, items = data["groups"], data["items"]
    for it in items:
        it["text"] = normalise(it["text"])
        it["canonical_ref"] = f"v5.0.0-{it['id']}"
    for g in groups:
        g["requirement_count"] = sum(1 for it in items if it["group"] == g["id"] or it["chapter"] == g["id"])

    chapters = [g for g in groups if g["kind"] == "chapter"]
    sections = [g for g in groups if g["kind"] == "section"]
    ids = [it["id"] for it in items]
    by_level = {lv: sum(1 for it in items if it["level"] == lv) for lv in (1, 2, 3)}
    # ---- sanity assertions
    assert len(chapters) == EXPECTED_CHAPTERS, len(chapters)
    assert [c["id"] for c in chapters] == [f"V{i}" for i in range(1, 18)]
    assert len(sections) == EXPECTED_SECTIONS, len(sections)
    assert len(items) == EXPECTED_REQUIREMENTS, len(items)
    assert len(set(ids)) == len(ids), "duplicate requirement ids"
    assert by_level[1] == EXPECTED_L1, by_level
    gids = {g["id"] for g in groups}
    for it in items:
        assert it["group"] in gids, it["id"]
        assert it["text"].startswith("Verify"), (it["id"], it["text"][:40])
        assert 24 <= it["citation"]["pdf_page"] <= 96, it["id"]
    # requirement numbers are contiguous within each section
    for s in sections:
        nums = [int(it["id"].split(".")[2]) for it in items if it["group"] == s["id"]]
        assert nums == list(range(1, len(nums) + 1)), (s["id"], nums)
        assert nums, f"empty section {s['id']}"

    return {
        "catalog_id": "owasp-asvs-5",
        "source_id": "owasp-asvs",
        "title": "OWASP Application Security Verification Standard",
        "edition": "5.0.0 (May 2025)",
        "description": (
            "All 17 chapters, 80 sections and 345 requirements of ASVS 5.0.0 with verbatim "
            "requirement text, level (1/2/3) and PDF page. Identifiers use the document's "
            "<chapter>.<section>.<requirement> form (e.g. 1.2.5); the version-qualified form "
            "v5.0.0-1.2.5 recommended by the standard (PDF p. 16) is stored as canonical_ref. "
            "Copyright (c) 2008-2025 The OWASP Foundation; licensed CC BY-SA 4.0 "
            "(https://creativecommons.org/licenses/by-sa/4.0/). This catalog is a derivative "
            "work distributed under the same licence."
        ),
        "extraction": {
            "method": "scripts/extract/asvs.py: pdftotext -layout, regex over requirement table rows",
            "date": EXTRACTION_DATE,
            "fidelity": "verbatim-normalised-whitespace",
            "notes": (
                "Whitespace collapsed; U+2011 non-breaking hyphens rendered as '-'. Some missing "
                "spaces after closing curly quotes are artefacts of the PDF text layer and are kept. "
                "Counts asserted: 17 chapters, 80 sections, 345 requirements, 70 at L1 (PDF p. 23 "
                "states 70 L1 of 345). printed_page = pdf_page - 1. Chapter introductions, notes "
                "below tables and appendices are not itemised."
            ),
            "pages_reviewed": "1-24 (front matter, levels, verification guidance), 24-96 (V1-V17)",
        },
        "levels": LEVELS,
        "parameters": {
            "license": "CC-BY-SA-4.0 (https://creativecommons.org/licenses/by-sa/4.0/)",
            "attribution": "OWASP Application Security Verification Standard 5.0.0, Copyright (c) 2008-2025 The OWASP Foundation",
            "requirement_counts": {"total": len(items), "L1": by_level[1], "L2": by_level[2], "L3": by_level[3],
                                    "cumulative": {"1": by_level[1], "2": by_level[1] + by_level[2],
                                                   "3": len(items)}},
            "id_format": "<chapter>.<section>.<requirement> (PDF p. 16); version-qualified v5.0.0-<id>",
            "assessment_statuses": ["pass", "fail", "not-applicable", "not-verified"],
        },
        "groups": groups,
        "items": items,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="fail if the committed catalog differs")
    args = ap.parse_args(argv)
    data = build()
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if args.check:
        if not OUT.is_file() or OUT.read_text(encoding="utf-8") != text:
            print(f"{OUT} is stale; rerun scripts/extract/asvs.py", file=sys.stderr)
            return 1
        print("catalog up to date")
        return 0
    OUT.write_text(text, encoding="utf-8")
    c = data["parameters"]["requirement_counts"]
    print(f"wrote {OUT.relative_to(ROOT)}: {len(data['groups'])} groups, {c['total']} requirements "
          f"(L1 {c['L1']}, L2 {c['L2']}, L3 {c['L3']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
