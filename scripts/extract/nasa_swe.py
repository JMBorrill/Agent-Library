#!/usr/bin/env python3
"""Extract NPR 7150.2D and NASA-STD-8739.8B into machine-readable catalogs.

Outputs
-------
catalog/npr-7150-2d.json
    * every ``[SWE-nnn]`` requirement in Chapters 2-5 (130 in NPR 7150.2D),
      statement text verbatim (whitespace normalised), section, actor, notes,
      PDF page(s);
    * Appendix C Requirements Mapping Matrix applicability (Classes A-F, the
      "Authority" columns) for the 100 requirements of Chapters 3-5, read from
      the PDF with pdfplumber using the fixed x-positions of the class columns;
    * Appendix D software classification definitions (Classes A-F) as
      structured criteria/exclusions in ``parameters.classes``;
    * Table 1 (SWE-052 bi-directional traceability by class) and the Appendix C
      legend in ``parameters``.

catalog/nasa-std-8739-8b.json
    * SASS-01 (section 4.3) and the Table 1 Software Assurance and Software
      Safety Requirements Mapping Matrix: SA/SS tasks per SWE (103 rows;
      SWE-065 is split into 065a-065d in the standard);
    * section 4.2 safety-critical software determination criteria (a-e);
    * section 4.4.2 IV&V requirements (4.4.2.1-4.4.2.49);
    * section 4.5 tailoring "shall" statements and tailoring levels;
    * Appendix A Table 2 software cause areas for hazard analysis.

Method
------
Body text is read with ``pdftotext -layout`` (poppler) from the pinned PDFs
(SHA-256 checked against sources/pdf-manifest.json). Running headers/footers
are removed; NPR 7150.2D repeats the last line of a page at the top of the next
page, so a first line equal to the previous page's last line is dropped. Tables
are read with pdfplumber word coordinates. Sanity assertions pin the expected
counts; a change in the PDF makes the script fail loudly instead of silently
producing a different catalog.

Usage: python scripts/extract/nasa_swe.py [--check]   (--check: compare, do not write)
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import logging
import re
import subprocess
import sys
from pathlib import Path

import pdfplumber

logging.getLogger("pdfminer").setLevel(logging.ERROR)

ROOT = Path(__file__).resolve().parents[2]
NPR_PDF = ROOT / "sources" / "pdfs" / "nasa-software-engineering-requirements-7150-2d.pdf"
STD_PDF = ROOT / "sources" / "pdfs" / "nasa-software-assurance-8739-8b.pdf"
NPR_OUT = ROOT / "catalog" / "npr-7150-2d.json"
STD_OUT = ROOT / "catalog" / "nasa-std-8739-8b.json"
EXTRACTION_DATE = "2026-10-13"

EXPECTED_SWE_TOTAL = 130
EXPECTED_APPENDIX_C_ROWS = 100
EXPECTED_SA_ROWS = 103  # 99 SWEs + SWE-065 split into a-d (=> 100 distinct SWEs)
EXPECTED_IVV = 49


# ----------------------------------------------------------------------------- helpers
def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_pinned(path: Path, source_id: str) -> None:
    manifest = json.loads((ROOT / "sources" / "pdf-manifest.json").read_text(encoding="utf-8"))
    src = next(s for s in manifest["sources"] if s["id"] == source_id)
    if sha256(path) != src["sha256"]:
        raise SystemExit(f"{path.name}: SHA-256 differs from the manifest; refusing to extract")


def pdftotext_pages(path: Path) -> list[str]:
    out = subprocess.run(["pdftotext", "-layout", str(path), "-"], check=True, capture_output=True, text=True).stdout
    pages = out.split("\f")
    if pages and not pages[-1].strip():
        pages = pages[:-1]
    return pages


def norm(text: str) -> str:
    """Join lines with spaces, collapse whitespace, normalise quotes/dashes that pdftotext emits."""
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = text.replace("®", "")  # registered-trademark sign (CMMI®)
    text = re.sub(r"(\w)-\s*\n\s*(?=[a-z])", r"\1-", text)  # keep compound words split at line ends
    return re.sub(r"\s+", " ", text).strip()


def assert_in(snippet: str, haystack: str, where: str) -> None:
    if norm(snippet).lower() not in norm(haystack).lower():
        raise AssertionError(f"expected text not found on {where}: {snippet[:80]!r}")


# ----------------------------------------------------------------------------- NPR 7150.2D body
NPR_FOOTER = re.compile(r"This document does not bind the public")
NPR_HEADER = re.compile(r"^NPR 7150\.2D -- \S+\s+Page \d+ of 89\s*$")
PARA_RE = re.compile(r"^(\d{1,2}\.\d{1,2}(?:\.\d{1,2})*)\s+(.*)$")  # 1-2 digit parts: "7150.2 ..." is not a paragraph
TAG_RE = re.compile(r"\[SWE-(\d{3})\]\.?")
LIST_RE = re.compile(r"^([a-z])\.\s")

CHAPTERS = [
    ("ch2", "Chapter 2. Roles, Responsibilities, and Principles Related to Tailoring of the Requirements", 11),
    ("ch3", "Chapter 3: Software Management Requirements", 20),
    ("ch4", "Chapter 4: Software Engineering Life Cycle Requirements", 32),
    ("ch5", "Chapter 5: Supporting Software Life Cycle Requirements", 39),
]
SECTIONS = [  # (id, title, pdf page) - verified against the page text below
    ("2.1", "Roles and Responsibilities Associated with this Directive", 11),
    ("2.2", "Principles Related to Tailoring Requirements", 17),
    ("3.1", "Software Life Cycle Planning", 20),
    ("3.2", "Software Cost Estimation", 23),
    ("3.3", "Software Schedules", 24),
    ("3.4", "Software Training", 24),
    ("3.5", "Software Classification Assessments", 24),
    ("3.6", "Software Assurance and Software Independent Verification & Validation", 25),
    ("3.7", "Safety-Critical Software", 26),
    ("3.8", "Automatic Generation of Software Source Code", 27),
    ("3.9", "Software Development Processes and Practices", 28),
    ("3.10", "Software Reuse", 29),
    ("3.11", "Software Cybersecurity", 30),
    ("3.12", "Software Bi-Directional Traceability", 31),
    ("4.1", "Software Requirements", 32),
    ("4.2", "Software Architecture", 33),
    ("4.3", "Software Design", 33),
    ("4.4", "Software Implementation", 34),
    ("4.5", "Software Testing", 35),
    ("4.6", "Software Operations, Maintenance, and Retirement", 37),
    ("5.1", "Software Configuration Management (SCM)", 39),
    ("5.2", "Software Risk Management", 40),
    ("5.3", "Software Peer Reviews and Inspections", 40),
    ("5.4", "Software Measurements", 41),
    ("5.5", "Software Non-conformance or Defect Management", 42),
]
CH2_ACTORS = {  # chapter 2 sub-section -> responsible role (from the sub-section headings, pp. 11-16)
    "2.1.1": "NASA Office of the Chief Engineer (OCE)",
    "2.1.2": "NASA Chief, Safety and Mission Assurance (SMA)",
    "2.1.5": "Center Director (or designee)",
    "2.1.7": "Contracting Officers / Agreement Managers",
    "2.1.8": "Technical and Institutional Authorities",
}


def npr_clean_pages(pages: list[str]) -> list[list[str]]:
    """Return per-page lists of body lines (header/footer removed, repeated carry-over line dropped)."""
    cleaned: list[list[str]] = []
    prev_last = None
    for raw in pages:
        lines = raw.split("\n")
        body: list[str] = []
        for ln in lines:
            if NPR_FOOTER.search(ln):
                break
            body.append(ln.rstrip())
        if body and NPR_HEADER.match(body[0].strip()):
            body = body[1:]
        nonblank = [i for i, ln in enumerate(body) if ln.strip()]
        if nonblank and prev_last is not None and body[nonblank[0]].strip() == prev_last:
            del body[nonblank[0]]
        nonblank = [ln for ln in body if ln.strip()]
        prev_last = nonblank[-1].strip() if nonblank else None
        cleaned.append(body)
    return cleaned


def extract_npr_requirements(pages: list[str]) -> list[dict]:
    clean = npr_clean_pages(pages)
    flat: list[tuple[int, str]] = []  # (pdf page, line)
    for pno in range(11, 44):  # chapters 2-5
        for ln in clean[pno - 1]:
            flat.append((pno, ln))

    def is_para(ln: str) -> re.Match | None:
        return PARA_RE.match(ln) if ln and not ln.startswith(" ") else None

    def is_boundary(ln: str) -> bool:
        return bool(is_para(ln)) or ln.startswith("Chapter ")

    tags = [(i, m) for i, (_, ln) in enumerate(flat) for m in TAG_RE.finditer(ln)]
    reqs = []
    for idx, m in tags:
        # statement start: nearest paragraph-number line at or before the tag
        start = idx
        while start >= 0 and not is_para(flat[start][1]):
            start -= 1
        para = is_para(flat[start][1])
        section = para.group(1)
        stmt_lines = [ln for _, ln in flat[start: idx + 1]]
        stmt_lines[-1] = stmt_lines[-1][: m.end()]
        if section.count(".") == 1 and "shall" not in stmt_lines[0]:
            # heading line followed by un-numbered requirement text (only SWE-086, section 5.2)
            stmt_lines = stmt_lines[1:]
        else:
            stmt_lines[0] = para.group(2)
        statement = norm("\n".join(stmt_lines))
        statement = TAG_RE.sub("", statement).strip()
        pages_used = {flat[start][0], flat[idx][0]}
        # list items following the tag (a., b., (1) ...), resuming after an interposed note
        list_lines: list[str] = []
        note_lines: list[str] = []
        j = idx + 1
        last_letter = None
        in_list = True
        # Blank lines are ignored (page breaks insert them mid-list); notes are recognised by their
        # 5-space indentation in the -layout text.
        while j < len(flat):
            pno, ln = flat[j]
            j += 1
            if not ln.strip():
                continue
            if is_boundary(ln):
                break
            lm = LIST_RE.match(ln)
            indented = ln.startswith(" ")
            if in_list and not indented and (lm or last_letter):
                if lm:
                    last_letter = lm.group(1)
                list_lines.append(ln)
                pages_used.add(pno)
            elif lm and last_letter and ord(lm.group(1)) == ord(last_letter) + 1:
                in_list = True  # list resumes after a note (e.g. SWE-126 b., SWE-148 f.)
                last_letter = lm.group(1)
                list_lines.append(ln)
                pages_used.add(pno)
            else:
                in_list = False
                note_lines.append(ln.strip())
        swe = f"SWE-{m.group(1)}"
        notes = norm("\n".join(note_lines))
        table = None
        if swe == "SWE-052":
            notes = re.sub(r"Table 1\..*?(?=Note:)", "", notes).strip()
            table = True
        text = statement + (" " + norm("\n".join(list_lines)) if list_lines else "")
        reqs.append({
            "id": swe,
            "section": section,
            "statement": statement,
            "list_items": norm("\n".join(list_lines)) if list_lines else "",
            "text": text.strip(),
            "notes": notes,
            "pages": sorted(pages_used),
            "start_page": flat[start][0],
            "has_table": bool(table),
        })
    return reqs


def actor_for(req: dict) -> str:
    t = req["statement"]
    if re.search(r"\bprogram manager shall\b", t):
        return "Program manager"
    if re.search(r"\bproject manager(?:'s .*?)? shall\b", t) or req["section"][0] in "345":
        return "Project manager"
    if re.search(r"authorities shall", t):
        return "Engineering, CIO and SMA authorities"
    for prefix, actor in CH2_ACTORS.items():
        if req["section"].startswith(prefix + "."):
            return actor
    raise AssertionError(f"no actor for {req['id']}")


def condition_for(req: dict) -> str | None:
    t = req["statement"]
    if re.match(r"If a project has safety-critical software or mission-critical software", t):
        return "safety-or-mission-critical"
    if re.match(r"If a project has safety-critical software", t):
        return "safety-critical"
    if re.match(r"If software IV&V is (required|performed)", t):
        return "ivv"
    if req["id"] in ("SWE-141", "SWE-143"):
        return "project-category"  # Category 1 / Category 2 (Class A/B payload risk) projects
    if req["id"] == "SWE-032":
        return "class-a-or-b"
    if req["id"] == "SWE-146":
        return None
    return None


# ----------------------------------------------------------------------------- NPR Appendix C
CLASS_X = {373: "A", 390: "B", 407: "C", 424: "D", 441: "E"}


def extract_appendix_c(pdf: pdfplumber.PDF) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for pno in range(56, 79):
        page = pdf.pages[pno - 1]
        words = [w for w in page.extract_words() if 30 < w["top"] < 725]
        lines = collections.defaultdict(list)
        for w in words:
            lines[round(w["top"])].append(w)
        tops = sorted(lines)
        starts = []
        for t in tops:
            ln = sorted(lines[t], key=lambda w: w["x0"])
            swe = [w for w in ln if 90 <= w["x0"] <= 100 and re.fullmatch(r"\d{3}", w["text"])]
            if swe:
                starts.append(t)
        for k, t in enumerate(starts):
            ln = sorted(lines[t], key=lambda w: w["x0"])
            sec = " ".join(w["text"] for w in ln if w["x0"] < 90)
            num = next(w["text"] for w in ln if 90 <= w["x0"] <= 100)
            # region of this row: until the next row or a section heading line (word in section column)
            region = [t]
            for t2 in tops:
                if t2 <= t:
                    continue
                if k + 1 < len(starts) and t2 >= starts[k + 1]:
                    break
                if any(w["x0"] < 90 for w in lines[t2]):
                    break
                region.append(t2)
            auth = " ".join(w["text"] for r in region for w in sorted(lines[r], key=lambda w: w["x0"])
                            if 300 <= w["x0"] < 372)
            fauth = " ".join(w["text"] for r in region for w in lines[r] if 455 <= w["x0"] < 525)
            classes = [CLASS_X[round(w["x0"])] for w in ln if w["text"] == "X" and round(w["x0"]) in CLASS_X]
            f_x = any(w["text"] == "X" and w["x0"] >= 525 for w in ln)
            swe = f"SWE-{num}"
            if swe in rows:
                raise AssertionError(f"duplicate Appendix C row {swe}")
            rows[swe] = {
                "section": sec,
                "authority": auth,
                "classes": {c: (c in classes) for c in "ABCDE"} | {"F": f_x},
                "class_f_authority": fauth,
                "pdf_page": pno,
            }
    return rows


# ----------------------------------------------------------------------------- NPR Appendix D
CLASS_DEFS = {
    "A": {
        "title": "Human Rated Space Software Systems",
        "page": 79,
        "criteria": [
            ("A-1a", 79, "Required to operate the vehicle or space asset (e.g., spacesuit, rover, or outpost), including commanding of the vehicle or asset."),
            ("A-1b", 79, "Required to sustain a safe, habitable1 environment for the crew."),
            ("A-1c", 79, "Required to achieve the primary mission objectives."),
            ("A-1d", 79, "Required to directly prepare resources (e.g., data, fuel, power) that are consumed by the above functions."),
        ],
        "scope": (79, "Ground and flight software systems developed or operated by or for NASA needed to perform a primary mission objective of human space flight and directly interact with human space flight systems."),
        "exclusions": [
            ("A-x1", 80, "Software that happens to fly in space but is superfluous to mission objectives (e.g., software contained in an iPod carried on board by an astronaut for personal use)"),
            ("A-x2", 80, "Software that exclusively supports aeronautics, research and technology, and science conducted without space flight applications"),
            ("A-x3", 80, "Systems (e.g., simulators, emulators, facilities) used to test Class A systems containing software in a development environment."),
        ],
    },
    "B": {
        "title": "Non-Human Space Rated Software Systems or Large Scale Aeronautics Vehicles",
        "page": 80,
        "scope": (80, "Space Systems involve flight and ground software that should perform reliably to accomplish primary mission objectives or major function(s) in non-human space rated systems."),
        "criteria": [
            ("B-1a", 81, "Required to operate the vehicle or space asset (e.g., orbiter, lander, probe, flyby spacecraft, rover, launch vehicle, or primary instrument) such as commanding of the vehicle or asset;"),
            ("B-1b", 81, "Required to achieve the primary mission objectives; or"),
            ("B-1c", 81, "Required to directly prepare resources (data, fuel, power) that are consumed by the above functions."),
            ("B-2a", 81, "Is integral to the control of an airborne vehicle;"),
            ("B-2b", 81, "Monitors and controls the cabin environment; or"),
            ("B-2c", 81, "Monitors and controls the vehicle's emergency systems."),
        ],
        "notes": [(81, "Large-scale (life cycle cost exceeding $250M) fully integrated technology development system")],
        "exclusions": [
            ("B-x1", 81, "Software that exclusively supports non-primary instruments on non-human space rated systems (e.g., low-cost, non-primary, university supplied instruments)"),
            ("B-x2", 81, "Systems (e.g., simulators, emulators, facilities) used in testing Class B systems containing software in a development environment"),
            ("B-x3", 82, "Software for NASA Class D payloads, as defined in NPR 8705.4."),
        ],
    },
    "C": {
        "title": "Mission Support Software or Aeronautic Vehicles, or Major Engineering/Research Facility Software",
        "page": 82,
        "criteria": [
            ("C-1a", 82, "Flight or ground software necessary for the science return from a single (non-primary) instrument;"),
            ("C-1b", 82, "Flight or ground software used to analyze or process mission data;"),
            ("C-1c", 82, "Other software for which a defect could adversely impact the attainment of some secondary mission objectives or cause operational problems;"),
            ("C-1d", 82, "Software used for the testing of space assets;"),
            ("C-1e", 82, "Software used to verify system requirements of space assets by analysis; or"),
            ("C-1f", 82, "Software for space flight operations not covered by Class A or B software."),
            ("C-2", 82, "Aeronautic Vehicles include systems for non-large scale aeronautic software systems in which the software: (a) Is integral to the control of an airborne vehicle; (b) Monitors and controls the cabin environment; or (c) Monitors and controls the vehicle's emergency system."),
            ("C-2r", 82, "Also included are systems on an airborne vehicle (including large-scale vehicles) that acquire, store, or transmit the official record copy of flight or test data."),
            ("C-3", 82, "Major Engineering/Research Facility is systems that operate a major facility for research, development, test, or evaluation (e.g., facility controls and monitoring, systems that operate facility-owned instruments, apparatus, and data acquisition equipment)."),
            ("C-4", 82, "Sounding Rockets and Sounding Rocket payloads."),
            ("C-5", 82, "Software for NASA Class D payloads, as defined in NPR 8705.4."),
        ],
        "exclusions": [
            ("C-x1", 83, "Systems unique to research, development, test, or evaluation activities in a major engineering/research facility or airborne vehicle in which the system is not part of the facility or vehicle and does not impact the operation of the facility or vehicle."),
        ],
    },
    "D": {
        "title": "Basic Science/Engineering Design and Research and Technology Software",
        "page": 83,
        "criteria": [
            ("D-1a", 83, "Ground software that performs secondary science data analysis;"),
            ("D-1b", 83, "Ground software tools that support engineering development;"),
            ("D-1c", 83, "Ground software or software tools used for informal testing of software systems;"),
            ("D-1d", 83, "Ground software tools that support mission planning or formulation;"),
            ("D-1e", 83, "Ground software that operates a research, development, test, or evaluation laboratory (i.e., not a major engineering/research facility); or"),
            ("D-1f", 83, "Ground software that provides decision support for non-mission critical situations."),
            ("D-2a", 84, "Software whose anomalous behavior would cause or contribute to a failure of system function resulting in a minor failure condition for the airborne vehicle"),
            ("D-2b", 84, "Software whose anomalous behavior would cause or contribute to a failure of system function with no effect on airborne vehicle operational capability or pilot workload"),
            ("D-2c", 84, "Ground software tools that perform research associated with airborne vehicles or systems."),
            ("D-3", 84, "Major Engineering/Research Facility related software includes research software that executes in a major engineering/research facility but is independent of the operation of the facility."),
        ],
        "exclusions": [
            ("D-x1", 84, "Software that can impact primary or secondary mission objectives or cause loss of data that is generated by space systems;"),
            ("D-x2", 84, "Software that operates a major engineering/research facility;"),
            ("D-x3", 84, "Software that operates an airborne vehicle; or"),
            ("D-x4", 84, "Flight software (i.e., software that meets the flight portions of Class A, B, or C Software Classifications)."),
        ],
    },
    "E": {
        "title": "Design Concept, Research, Technology, and General Purpose Software",
        "page": 84,
        "criteria": [
            ("E-1", 85, "Software developed to explore a design concept or hypothesis but not used to make decisions for an operational Class A, B, or C system or a to-be-built Class A, B, or C system."),
            ("E-2", 85, "Software used to perform minor analyses of science or experimental data."),
        ],
        "notes": [
            (85, "Class E software cannot be safety-critical software. If the software is classified as safety-critical software, then it has to be classified as Class D or higher."),
            (85, "Class E software runs in a general-purpose computing environment or a board top environment. Class E software does not support ground tests, flight tests, or operations."),
        ],
        "exclusions": [
            ("E-x1", 85, "Flight systems (i.e., software that meets the flight portions of Class A, B, C, or D Software Classifications);"),
            ("E-x2", 85, "Software developed by or for NASA to directly support an operational system"),
            ("E-x3", 85, "Software developed by or for NASA to be flight qualified to support an operational system;"),
            ("E-x4", 85, "Software that directly affects primary or secondary mission objectives;"),
            ("E-x5", 85, "Software that can adversely affect the integrity of engineering/scientific artifacts;"),
            ("E-x6", 85, "Software used in technical decisions concerning operational systems, or systems being developed for operation;"),
            ("E-x7", 85, "Software that has an impact on operational vehicles; or"),
            ("E-x8", 85, "Software that is safety-critical."),
        ],
    },
    "F": {
        "title": "General Purpose Computing, Business, and IT Software",
        "page": 85,
        "criteria": [
            ("F-1", 86, "General purpose computing Business and IT software used in support of the Agency, multiple Centers, multiple programs/projects, single Centers/projects, or locally deployed General Purpose Infrastructure To-Be Component of the NASA Enterprise Architecture."),
        ],
        "notes": [
            (86, "A defect in Class F software is likely to affect the productivity of multiple users across a single geographic location or several geographic locations and may affect mission objectives or system safety."),
        ],
        "exclusions": [],
    },
}
CLASSIFICATION_RULES = [
    (79, "If more than one software class appears to apply, then assign the higher of the classes to the system/subsystem."),
    (79, "Classes A through E cover engineering-related software. Class F cover Business and Information Technology Infrastructure Software."),
    (79, "The NASA Chief Engineer is the ultimate TA for software classification disputes concerning definitions in this NPR."),
]
TRACEABILITY_TABLE = {  # Table 1, PDF page 31 (SWE-052)
    "page": 31,
    "columns": ["Class A, B, and C", "Class D", "Class F"],
    "rows": [
        ("Higher-level requirements to the software requirements", ["A", "B", "C", "F"]),
        ("Software requirements to the system hazards", ["A", "B", "C", "D"]),
        ("Software requirements to the software design components", ["A", "B", "C"]),
        ("Software design components to the software code", ["A", "B", "C"]),
        ("Software requirements to the software verification(s)", ["A", "B", "C", "D", "F"]),
        ("Software requirements to the software non-conformances", ["A", "B", "C", "D", "F"]),
    ],
}


def verify_traceability_table(pdf: pdfplumber.PDF) -> None:
    page = pdf.pages[TRACEABILITY_TABLE["page"] - 1]
    words = page.extract_words()
    lines = collections.defaultdict(list)
    for w in words:
        lines[round(w["top"])].append(w)
    xs_header = {}
    for t in sorted(lines):
        txt = " ".join(w["text"] for w in sorted(lines[t], key=lambda w: w["x0"]))
        if "Class D" in txt and "Class F" in txt:
            ws = sorted(lines[t], key=lambda w: w["x0"])
            for a, b in zip(ws, ws[1:]):
                if a["text"] == "Class" and b["text"] in ("D", "F"):
                    xs_header[b["text"]] = a["x0"]  # left edge of the "Class D" / "Class F" header
    found = 0
    for label, classes in TRACEABILITY_TABLE["rows"]:
        for t in sorted(lines):
            ln = sorted(lines[t], key=lambda w: w["x0"])
            txt = " ".join(w["text"] for w in ln)
            if txt.startswith(label):
                xs = [w["x0"] for w in ln if w["text"] == "X"]
                got = []
                for x in xs:
                    if x < xs_header["D"] - 5:
                        got += ["A", "B", "C"]
                    elif x < xs_header["F"] - 5:
                        got.append("D")
                    else:
                        got.append("F")
                if sorted(got) != sorted(classes):
                    raise AssertionError(f"Table 1 row {label!r}: PDF gives {got}, expected {classes}")
                found += 1
                break
    if found != len(TRACEABILITY_TABLE["rows"]):
        raise AssertionError("Table 1 (traceability) rows not all found")


def build_npr() -> dict:
    check_pinned(NPR_PDF, "nasa-software-requirements")
    pages = pdftotext_pages(NPR_PDF)
    assert len(pages) == 89, len(pages)
    reqs = extract_npr_requirements(pages)
    ids = [r["id"] for r in reqs]
    assert len(ids) == len(set(ids)), "duplicate SWE ids"
    assert len(ids) == EXPECTED_SWE_TOTAL, f"expected {EXPECTED_SWE_TOTAL} SWE requirements, found {len(ids)}"

    with pdfplumber.open(NPR_PDF) as pdf:
        appc = extract_appendix_c(pdf)
        verify_traceability_table(pdf)
    assert len(appc) == EXPECTED_APPENDIX_C_ROWS, len(appc)
    ch345 = {r["id"] for r in reqs if r["section"][0] in "345"}
    assert set(appc) == ch345, f"Appendix C rows differ from chapter 3-5 SWEs: {set(appc) ^ ch345}"
    for r in reqs:
        if r["id"] in appc and appc[r["id"]]["section"] != r["section"]:
            raise AssertionError(f"{r['id']}: Appendix C section {appc[r['id']]['section']} != body {r['section']}")
    # spot checks of the matrix read against the PDF text (visually verified rows)
    assert appc["SWE-141"]["authority"] == "HQ OSMA"
    assert appc["SWE-032"]["authority"] == "HQ OCE and HQ OSMA"
    assert [c for c, v in appc["SWE-033"]["classes"].items() if v] == list("ABCDEF")
    assert [c for c, v in appc["SWE-141"]["classes"].items() if v] == ["A", "B"]
    assert [c for c, v in appc["SWE-174"]["classes"].items() if v] == list("ABCD")
    assert appc["SWE-015"]["classes"]["F"] and appc["SWE-015"]["class_f_authority"] == ""

    full = "\n".join(pages)
    for sid, title, page in SECTIONS:
        first = title.split(" (")[0].split(" &")[0]
        if not re.search(rf"^\s*{re.escape(sid)}\s+{re.escape(first[:20])}", pages[page - 1], re.M):
            raise AssertionError(f"section heading {sid} {title!r} not found on page {page}")
    for cls, d in CLASS_DEFS.items():
        assert_in(f"Class {cls}:", pages[d["page"] - 1], f"p.{d['page']}")
        for cid, page, txt in d["criteria"] + d["exclusions"]:
            src = pages[page - 1] + ("\n" + pages[page] if page < 89 else "")
            probe = re.sub(r"\s*\(a\).*", "", txt) if cid in ("C-2",) else txt
            assert_in(probe, src, f"p.{page} ({cid})")
        if "scope" in d:
            assert_in(d["scope"][1], pages[d["scope"][0] - 1], f"p.{d['scope'][0]}")
        for page, txt in d.get("notes", []):
            assert_in(txt.split(". ")[0], pages[page - 1], f"p.{page}")
    for page, txt in CLASSIFICATION_RULES:
        assert_in(txt, pages[page - 1], f"p.{page}")

    groups = []
    for gid, title, page in CHAPTERS:
        groups.append({"id": gid, "title": title, "parent": None, "citation": {"pdf_page": page, "printed_page": page}})
    for sid, title, page in SECTIONS:
        groups.append({"id": sid, "title": title, "parent": f"ch{sid.split('.')[0]}",
                       "citation": {"pdf_page": page, "printed_page": page, "section": sid}})

    items = []
    for r in reqs:
        chapter = int(r["section"].split(".")[0])
        sec2 = ".".join(r["section"].split(".")[:2])
        item = {
            "id": r["id"],
            "text": r["text"],
            "statement": r["statement"],
            "section": r["section"],
            "chapter": chapter,
            "group": sec2,
            "actor": actor_for(r),
            "citation": {"pdf_page": r["start_page"], "printed_page": r["start_page"], "section": r["section"]},
            "pages": r["pages"],
        }
        if r["list_items"]:
            item["list_items"] = r["list_items"]
        if r["notes"]:
            item["notes"] = r["notes"]
        cond = condition_for(r)
        if cond:
            item["condition"] = cond
        if r["id"] in appc:
            row = appc[r["id"]]
            item["applicability"] = {
                **{c: ("X" if v else "") for c, v in row["classes"].items()},
                "authority": row["authority"],
                "class_f_authority": row["class_f_authority"],
                "citation": {"pdf_page": row["pdf_page"], "printed_page": row["pdf_page"], "section": "Appendix C"},
            }
        else:
            item["applicability"] = None
            item["applicability_note"] = ("Chapter 2 requirement: not part of the Appendix C Requirements Mapping "
                                          "Matrix (para 1.3.1, p. 9); applicability is stated in the requirement wording.")
        if r["id"] == "SWE-052":
            item["traceability_table"] = {
                "title": "Table 1. Bi-directional traceability by software classification",
                "pdf_page": TRACEABILITY_TABLE["page"],
                "rows": [{"trace": lbl, "classes": cls} for lbl, cls in TRACEABILITY_TABLE["rows"]],
            }
        items.append(item)
    items.sort(key=lambda it: (it["chapter"], [int(x) for x in it["section"].split(".")]))

    classes = {}
    for cls, d in CLASS_DEFS.items():
        classes[cls] = {
            "title": d["title"],
            "citation": {"pdf_page": d["page"], "printed_page": d["page"], "section": f"Appendix D, Class {cls}"},
            "engineering": cls != "F",
            "criteria": [{"id": cid, "text": txt, "pdf_page": p} for cid, p, txt in d["criteria"]],
            "exclusions": [{"id": cid, "text": txt, "pdf_page": p} for cid, p, txt in d["exclusions"]],
        }
        if "scope" in d:
            classes[cls]["scope"] = {"text": d["scope"][1], "pdf_page": d["scope"][0]}
        if d.get("notes"):
            classes[cls]["notes"] = [{"text": t, "pdf_page": p} for p, t in d["notes"]]

    n_x = {c: sum(1 for it in items if it["applicability"] and it["applicability"][c] == "X") for c in "ABCDEF"}
    return {
        "catalog_id": "npr-7150-2d",
        "source_id": "nasa-software-requirements",
        "title": "NPR 7150.2D NASA Software Engineering Requirements",
        "edition": "NPR 7150.2D (effective 2022-03-08, expires 2027-03-08)",
        "description": ("Every [SWE-nnn] requirement of NPR 7150.2D (Chapters 2-5) with the Appendix C Requirements "
                        "Mapping Matrix applicability by software class (A-F) and Authority, plus Appendix D "
                        "software classification definitions. Used by `python -m agentlib nasa-swe`."),
        "extraction": {
            "method": ("scripts/extract/nasa_swe.py: pdftotext -layout for body text (headers/footers removed, "
                       "repeated page-carry-over line dropped); pdfplumber word x-positions for Appendix C class "
                       "columns (A x=373, B 390, C 407, D 424, E 441, F x>=525) and Table 1 (p.31)."),
            "date": EXTRACTION_DATE,
            "fidelity": "verbatim-normalised-whitespace",
            "pages_reviewed": "8-45 (Ch.1-6), 55-78 (Appendix C), 79-86 (Appendix D)",
            "notes": (
                f"{len(items)} SWE requirements ({len(items) - len(appc)} in Chapter 2, {len(appc)} in Chapters 3-5). "
                "Appendix C in NPR 7150.2D uses only 'X' (invoked) and blank (optional/not invoked) per para 2.2.4 "
                "(p.18) and C.3 (p.55); there are no P(Center) notations in this revision. Applicability was read "
                "from the PDF class-column x-positions and spot-checked against the rendered table. SWE-015 has an "
                "'X' for Class F but an empty Class F Authority cell in the PDF (recorded as-is). Item text is the "
                "Chapter 2-5 body statement (Appendix C repeats it with minor wording differences). 'condition' is a "
                "library annotation for requirements whose wording makes them conditional (safety-critical, IV&V, "
                "project category). citation.pdf_page is where the paragraph starts; 'pages' lists all pages used. "
                "Printed page numbers equal PDF page numbers ('Page N of 89')."
            ),
        },
        "levels": {
            "classes": ["A", "B", "C", "D", "E", "F"],
            "applicable_counts": n_x,
        },
        "parameters": {
            "classes": classes,
            "classification_rules": [{"text": t, "pdf_page": p} for p, t in CLASSIFICATION_RULES],
            "classification_factors": {
                "pdf_page": 79,
                "text": ("(1) usage of the software with or within a NASA system, (2) criticality of the system to "
                         "NASA's major programs and projects, (3) extent to which humans depend upon the system, "
                         "(4) developmental and operational complexity, and (5) extent of the Agency's investment."),
            },
            "matrix_legend": {
                "pdf_page": 55,
                "X": "Indicates an invoked requirement by this NPR consistent with Software Classification (ref. SWE-139). May be tailored with TA approval (ref. Chapter 2.2).",
                "blank": "Optional/Not invoked by this NPR.",
                "Center": ("Center Director or the Center Director's designated ETA, the Center Director's designated SMA TA, "
                           "and the CHMO designated for Health and Medical TA."),
                "CIO": "The NASA CIO, or the designee Center CIO, has institutional authority on all Class F software projects and joint responsibility with the ETA on the cybersecurity requirements in section 3.11.",
            },
            "tailoring_principles": {
                "pdf_pages": [17, 18, 19],
                "summary": ("Tailoring = seeking relief from NPR requirements (2.2.1). Approval of the Authority designated "
                            "in Appendix C is required for all tailoring of 'X' requirements (2.2.5); the request includes "
                            "rationale, a risk evaluation and supporting material (Note to 2.2.5). Relief may be requested "
                            "in the streamlined form of a Requirements Mapping Matrix with engineering, CIO and SMA "
                            "signatures; SAISO signature for cybersecurity relief (2.2.6)."),
            },
        },
        "groups": groups,
        "items": items,
    }


# ----------------------------------------------------------------------------- NASA-STD-8739.8B
STD_FOOTER = re.compile(r"^\s*\d+ of 65\s*$")
GARBAGE = re.compile(r"--[‘',\-]{6,}---")


def std_words(page) -> list[dict]:
    bottom = page.height - 45  # above the "N of 65" page number and the supplier watermark
    out = []
    for w in page.extract_words():
        if w["x0"] < 40 or w["top"] < 60 or w["top"] > bottom:
            continue
        text = GARBAGE.sub("", w["text"])
        if not text:
            continue
        out.append({**w, "text": text})
    return out


def lines_of(words: list[dict]) -> dict[int, list[dict]]:
    lines = collections.defaultdict(list)
    for w in words:
        lines[round(w["top"])].append(w)
    merged: dict[int, list[dict]] = {}
    for t, v in sorted(lines.items()):
        v = sorted(v, key=lambda w: w["x0"])
        out: list[dict] = []
        for w in v:
            # a watermark glyph run can split a list number ("1" + "8.") - re-join adjacent digit fragments
            if out and re.fullmatch(r"\d", out[-1]["text"]) and re.match(r"\d", w["text"]) and w["x0"] - out[-1]["x1"] < 8:
                out[-1] = {**out[-1], "text": out[-1]["text"] + w["text"], "x1": w["x1"]}
                continue
            out.append(w)
        merged[t] = out
    # merge lines whose tops differ by <= 3pt (the split number sits 2pt higher than its text)
    result: dict[int, list[dict]] = {}
    for t, v in merged.items():
        near = next((k for k in result if abs(k - t) <= 3), None)
        if near is None:
            result[t] = v
        else:
            result[near] = sorted(result[near] + v, key=lambda w: w["x0"])
            joined: list[dict] = []
            for w in result[near]:
                if joined and re.fullmatch(r"\d", joined[-1]["text"]) and re.match(r"\d", w["text"]) and w["x0"] - joined[-1]["x1"] < 8:
                    joined[-1] = {**joined[-1], "text": joined[-1]["text"] + w["text"], "x1": w["x1"]}
                    continue
                joined.append(w)
            result[near] = joined
    return result


def join_line(prev: str, nxt: str) -> str:
    """Join two wrapped table lines; a trailing hyphen after a letter is a compound-word break."""
    if re.search(r"[A-Za-z]-$", prev):
        return prev + nxt
    return prev + " " + nxt


def extract_sa_table(pdf: pdfplumber.PDF) -> tuple[list[dict], list[dict]]:
    """Table 1 rows: SWE -> SA/SS tasks. Columns: section x<120, SWE# 120-160, NPR text 160-415, tasks >=415."""
    stream: list[tuple[int, int, list[dict]]] = []
    for pno in range(17, 48):
        lines = lines_of(std_words(pdf.pages[pno - 1]))
        for t, ln in lines.items():
            txt = " ".join(w["text"] for w in ln)
            if (txt.startswith(("Table 1.", "NPR SWE")) or txt in ("7150.2 #", "Section")
                    or txt in ("Software Assurance and Software Safety Tasks", "NPR 7150.2 Requirement")):
                continue  # repeated column-header row
            stream.append((pno, t, ln))
    rows: list[dict] = []
    headings: list[dict] = []
    cur = None
    for pno, t, ln in stream:
        sec = [w["text"] for w in ln if w["x0"] < 120]
        num = [w["text"] for w in ln if 120 <= w["x0"] < 160]
        req = [w["text"] for w in ln if 160 <= w["x0"] < 415]
        task = [w["text"] for w in ln if w["x0"] >= 415]
        if num and re.fullmatch(r"\d{3}[a-d]?", num[0]):
            cur = {"section": " ".join(sec), "num": num[0], "pdf_page": pno, "pages": {pno},
                   "req_lines": [], "task_lines": []}
            rows.append(cur)
        elif sec and not num:
            # section heading row (e.g. "3.2 Software Cost Estimation"); it carries no tasks, and task
            # text on later lines/pages still belongs to the current row
            headings.append({"section": sec[0], "title": " ".join(req), "pdf_page": pno})
            continue
        if cur is None:
            continue
        if req:
            cur["req_lines"].append(" ".join(req))
        if task:
            cur["task_lines"].append(" ".join(task))
            cur["pages"].add(pno)
    out = []
    for r in rows:
        tasks: list[str] = []
        expected = 1
        for ln in r["task_lines"]:
            m = re.match(r"^(\d{1,2})\.\s+(.*)$", ln)
            if m and int(m.group(1)) == expected:
                tasks.append(m.group(2))
                expected += 1
            elif tasks:
                tasks[-1] = join_line(tasks[-1], ln)
            else:
                raise AssertionError(f"SWE-{r['num']}: task text before task 1: {ln!r}")
        out.append({
            "num": r["num"], "section": r["section"], "pdf_page": r["pdf_page"], "pages": sorted(r["pages"]),
            "tasks": [norm(t) for t in tasks],
        })
    return out, headings


def extract_ivv(pages: list[str]) -> list[dict]:
    lines: list[tuple[int, str]] = []
    for pno in range(48, 57):
        for ln in pages[pno - 1].split("\n"):
            if STD_FOOTER.match(ln) or ln.strip() == "NASA-STD-8739.8B":
                continue
            lines.append((pno, ln))
    reqs = []
    cur = None
    for pno, ln in lines:
        s = ln.strip()
        m = re.match(r"^(4\.4\.2\.\d+)\s+(.*)$", s)
        if m:
            cur = {"id": m.group(1), "pdf_page": pno, "text": [m.group(2)], "notes": [], "mode": "text"}
            reqs.append(cur)
            continue
        if re.match(r"^4\.5\s", s):
            break
        if cur is None or not s:
            continue
        if s.startswith("Note"):
            cur["mode"] = "note"
        cur["notes" if cur["mode"] == "note" else "text"].append(s)
    out = []
    for r in reqs:
        text = norm("\n".join(r["text"]))
        actor = "NASA SMA Technical Authority" if text.startswith("The NASA SMA Technical Authority") else "IV&V Provider"
        out.append({"id": r["id"], "pdf_page": r["pdf_page"], "text": text, "notes": norm("\n".join(r["notes"])),
                    "actor": actor})
    return out


def extract_hazard_causes(pdf: pdfplumber.PDF) -> list[dict]:
    areas: list[dict] = []
    cur = None
    pending_area: list[str] = []
    for pno in range(59, 66):
        lines = lines_of(std_words(pdf.pages[pno - 1]))
        for t, ln in lines.items():
            txt = " ".join(w["text"] for w in ln)
            if txt.startswith("Table 2") or txt.startswith("Software Cause Areas") or txt == "to Consider":
                continue
            left = [w["text"] for w in ln if w["x0"] < 180]
            right = [w for w in ln if w["x0"] >= 180]
            num = right[0]["text"] if right and re.fullmatch(r"\d{1,2}\.", right[0]["text"]) else None
            if left and re.fullmatch(r"\d{1,2}\.", left[-1]):
                num = left.pop()  # number printed inside the area column (x~183 vs area x~69)
            if left:
                if num == "1." or cur is None:
                    cur = {"area": " ".join(left), "pdf_page": pno, "causes": []}
                    areas.append(cur)
                else:
                    cur["area"] += " " + " ".join(left)
            body = " ".join(w["text"] for w in right if not (num and w is right[0] and w["text"] == num))
            if num:
                cur["causes"].append(body)
            elif body and cur and cur["causes"]:
                cur["causes"][-1] = join_line(cur["causes"][-1], body)
    for a in areas:
        a["area"] = norm(a["area"])
        a["causes"] = [norm(c) for c in a["causes"]]
    return areas


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


SC_CRITERIA = [
    ("a", 15, "Causes or contributes to a system hazardous condition/event,"),
    ("b", 15, "Provides control or mitigation for a system hazardous condition/event,"),
    ("c", 16, "Controls safety-critical functions,"),
    ("d", 16, "Mitigates damage if a hazardous condition/event occurs,"),
    ("e", 16, "Detects, reports, and takes corrective action if the system reaches a potentially hazardous state."),
]
STD_SECTIONS = [  # (id, title, page)
    ("4.1", "Software Assurance Description", 15),
    ("4.2", "Safety-Critical Software Determination", 15),
    ("4.3", "Software Assurance and Software Safety Requirements", 16),
    ("4.4", "Independent Verification & Validation", 48),
    ("4.5", "Principles Related to Tailoring the Standard Requirements", 56),
    ("A", "Guidelines for the Hazard Development Involving Software", 58),
]
SASS01 = ("The responsible project manager shall perform the software assurance and software safety activities "
          "defined in Table 1 per the requirements marked applicable in the software engineering requirements "
          "mapping matrix for the software component.")
TAILOR_SHALLS = [
    ("4.5-1", 56, "The SMA TA for the project shall review and concur with any tailored Software Assurance and Software Safety Standard requirements."),
    ("4.5-2", 57, "If a system or subsystem development evolves to meet a higher or lower software classification defined in NPR 7150.2, the software assurance, software safety, and IV&V organizations shall update their plan(s) to fulfill the applicable requirements per the Requirements Mapping Matrix and any approved changes and initiate adjustments to applicable contracts to meet the modified requirements."),
]
TAILOR_LEVELS = [
    (56, "The first level of tailoring is the Software Classification Decision, see NPR 7150.2."),
    (57, "The second level of tailoring is the project's Software Requirements Mapping Matrix, see NPR 7150.2."),
    (57, "The third level of tailoring is the tailoring by the Software Assurance TA of the Software Assurance and Software Safety Standard requirements that correspond to the project's Software Requirements Mapping Matrix requirements."),
]


def build_std(npr: dict) -> dict:
    check_pinned(STD_PDF, "nasa-software-assurance")
    pages = pdftotext_pages(STD_PDF)
    assert len(pages) == 65, len(pages)
    for _, page, txt in SC_CRITERIA:
        assert_in(txt, pages[page - 1], f"p.{page}")
    assert_in(SASS01, pages[15], "p.16")
    assert_in("(SASS-01)", pages[15], "p.16")
    for _, page, txt in TAILOR_SHALLS:
        assert_in(txt, pages[page - 1], f"p.{page}")
    for page, txt in TAILOR_LEVELS:
        assert_in(txt, pages[page - 1], f"p.{page}")
    for sid, title, page in STD_SECTIONS:
        assert_in(title.split(" &")[0], pages[page - 1], f"p.{page} ({sid})")

    with pdfplumber.open(STD_PDF) as pdf:
        sa_rows, _ = extract_sa_table(pdf)
        hazards = extract_hazard_causes(pdf)
    ivv = extract_ivv(pages)

    assert len(sa_rows) == EXPECTED_SA_ROWS, f"expected {EXPECTED_SA_ROWS} Table 1 rows, got {len(sa_rows)}"
    nums = [r["num"] for r in sa_rows]
    assert len(set(nums)) == len(nums)
    npr_appc = {it["id"] for it in npr["items"] if it["applicability"]}
    sa_swes = {f"SWE-{n[:3]}" for n in nums}
    assert sa_swes == npr_appc, f"Table 1 SWEs differ from NPR Appendix C: {sa_swes ^ npr_appc}"
    for r in sa_rows:
        assert r["tasks"], f"SWE-{r['num']} has no tasks"
    assert [r["id"] for r in ivv] == [f"4.4.2.{i}" for i in range(1, EXPECTED_IVV + 1)], [r["id"] for r in ivv]
    expected_areas = {"Data errors", "Commanding errors", "Flight computer errors", "Operating systems errors",
                      "Programmable logic device errors", "Flight system time management errors",
                      "Coding, logic, and algorithm failures, algorithm specification errors",
                      "Fault tolerance and fault management errors", "Human-machine interface errors",
                      "Security and virus errors", "Unknown/Unknowns errors", "Software processes errors"}
    got_areas = {a["area"] for a in hazards}
    missing = expected_areas - got_areas
    assert not missing and len(hazards) == len(expected_areas), f"hazard cause areas: missing {missing}; got {got_areas}"
    for a in hazards:
        assert a["causes"], a["area"]

    npr_sections = {it["id"]: it["section"] for it in npr["items"]}
    groups = [{"id": sid, "title": title, "parent": None,
               "citation": {"pdf_page": page, "printed_page": page, "section": sid}} for sid, title, page in STD_SECTIONS]
    groups.append({"id": "table-1", "title": "Table 1. Software Assurance and Software Safety Requirements Mapping Matrix",
                   "parent": "4.3", "citation": {"pdf_page": 17, "printed_page": 17, "section": "4.3, Table 1"}})
    groups.append({"id": "table-2", "title": "Table 2. Additional considerations when identifying software causes in hazard analysis",
                   "parent": "A", "citation": {"pdf_page": 59, "printed_page": 59, "section": "A.1.4, Table 2"}})

    items = [{
        "id": "SASS-01", "kind": "requirement", "group": "4.3", "text": SASS01,
        "actor": "Project manager (SA/SS tasks may be delegated within the project)",
        "citation": {"pdf_page": 16, "printed_page": 16, "section": "4.3"},
    }]
    for letter, page, txt in SC_CRITERIA:
        items.append({"id": f"SC-4.2-{letter}", "kind": "safety-critical-criterion", "group": "4.2", "criterion": letter,
                      "text": txt.rstrip(","), "citation": {"pdf_page": page, "printed_page": page, "section": f"4.2 {letter}."}})
    for r in sa_rows:
        swe = f"SWE-{r['num'][:3]}"
        sc_related = [i + 1 for i, t in enumerate(r["tasks"]) if re.search(r"safety|hazard", t, re.I)]
        items.append({
            "id": f"SA-SWE-{r['num']}",
            "kind": "sa-task-set",
            "group": "table-1",
            "swe": swe,
            "swe_part": r["num"][3:] or None,
            "npr_section_in_table": r["section"],
            "npr_section": npr_sections.get(swe),
            "text": " ".join(f"{i}. {t}" for i, t in enumerate(r["tasks"], 1)),
            "tasks": [{"n": i, "text": t} for i, t in enumerate(r["tasks"], 1)],
            "safety_related_tasks": sc_related,
            "citation": {"pdf_page": r["pdf_page"], "printed_page": r["pdf_page"], "section": f"Table 1, {r['section']}"},
            "pages": r["pages"],
        })
    for r in ivv:
        item = {"id": r["id"], "kind": "ivv-requirement", "group": "4.4", "actor": r["actor"], "text": r["text"],
                "citation": {"pdf_page": r["pdf_page"], "printed_page": r["pdf_page"], "section": r["id"]}}
        if r["notes"]:
            item["notes"] = r["notes"]
        items.append(item)
    for tid, page, txt in TAILOR_SHALLS:
        items.append({"id": tid, "kind": "tailoring-requirement", "group": "4.5", "text": txt,
                      "id_assigned_by_library": True,
                      "citation": {"pdf_page": page, "printed_page": page, "section": "4.5"}})
    for a in hazards:
        items.append({
            "id": f"HAZ-{slug(a['area'])}",
            "kind": "hazard-cause-area",
            "group": "table-2",
            "title": a["area"],
            "text": f"{a['area']}: " + "; ".join(a["causes"]),
            "causes": a["causes"],
            "id_assigned_by_library": True,
            "citation": {"pdf_page": a["pdf_page"], "printed_page": a["pdf_page"], "section": "Appendix A, Table 2"},
        })

    n_tasks = sum(len(r["tasks"]) for r in sa_rows)
    return {
        "catalog_id": "nasa-std-8739-8b",
        "source_id": "nasa-software-assurance",
        "title": "NASA-STD-8739.8B Software Assurance and Software Safety Standard",
        "edition": "NASA-STD-8739.8B (approved 2022-09-08)",
        "description": ("SASS-01 and the Table 1 Software Assurance and Software Safety Requirements Mapping Matrix "
                        "(SA/SS tasks per NPR 7150.2 SWE), safety-critical software criteria (4.2), IV&V requirements "
                        "(4.4.2.1-4.4.2.49), tailoring principles (4.5) and Appendix A Table 2 software hazard cause areas."),
        "extraction": {
            "method": ("scripts/extract/nasa_swe.py: pdfplumber word positions for Table 1 (columns: section x<120, "
                       "SWE# 120-160, NPR text 160-415, SA/SS tasks x>=415; tasks split on '<n>.' at line start in "
                       "sequence) and Table 2 (area column x<180); pdftotext -layout for sections 4.2-4.5. A supplier "
                       "watermark in the page margin (x<40 / y>565) is excluded."),
            "date": EXTRACTION_DATE,
            "fidelity": "verbatim-normalised-whitespace",
            "pages_reviewed": "2, 5-6, 12-13, 15-65",
            "notes": (
                f"{len(sa_rows)} Table 1 rows covering {len(sa_swes)} SWEs ({n_tasks} SA/SS tasks); SWE-065 is split "
                "into 065a-065d in the standard. Table 1 lists NPR section numbers from the standard (e.g. SWE-032 "
                "as 3.9.3, SWE-086 as 5.2.1) which differ slightly from NPR 7150.2D (3.9.2, 5.2); both are kept "
                "(npr_section_in_table vs npr_section). 'safety_related_tasks' is a library keyword flag (task text "
                "mentions safety/hazard), not a classification in the standard. Ids SC-4.2-x, 4.5-n and HAZ-* are "
                "assigned by this library (the standard does not number them); 4.4.2.n and SASS-01 are the "
                "standard's own identifiers. Printed page = PDF page ('N of 65')."
            ),
        },
        "parameters": {
            "safety_critical_definition": {
                "pdf_page": 15,
                "rule": "Software is classified as safety-critical if it meets at least one of the following criteria (4.2 a-e).",
                "note": ("Software is classified as safety-critical if the software is determined by and traceable to "
                         "hazard analysis (Note to 4.2, p.16). See SWE-205."),
            },
            "ivv_independence": {
                "pdf_page": 48,
                "text": "Three parameters define the independence of IV&V: technical independence, managerial independence, and financial independence.",
            },
            "tailoring_levels": [{"level": i + 1, "text": t, "pdf_page": p} for i, (p, t) in enumerate(TAILOR_LEVELS)],
            "counts": {"sa_rows": len(sa_rows), "sa_swes": len(sa_swes), "sa_tasks": n_tasks, "ivv": len(ivv),
                       "hazard_cause_areas": len(hazards)},
        },
        "groups": groups,
        "items": items,
    }


def dump(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="compare with the committed catalogs; do not write")
    args = ap.parse_args(argv)
    npr = build_npr()
    std = build_std(npr)
    status = 0
    for path, data in ((NPR_OUT, npr), (STD_OUT, std)):
        text = dump(data)
        if args.check:
            same = path.is_file() and path.read_text(encoding="utf-8") == text
            print(f"{path.relative_to(ROOT)}: {'up to date' if same else 'DIFFERS'}")
            status |= 0 if same else 1
        else:
            path.write_text(text, encoding="utf-8")
            print(f"wrote {path.relative_to(ROOT)} ({len(data['items'])} items)")
    return status


if __name__ == "__main__":
    sys.exit(main())
