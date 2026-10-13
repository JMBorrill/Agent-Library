#!/usr/bin/env python3
"""Extract NASA Systems Engineering Handbook (Rev 2) catalogs from the pinned PDF.

Source : sources/pdfs/nasa-systems-engineering-handbook-rev2.pdf (source id ``nasa-se``)
         NASA/SP-2016-6105 Rev 2 (2016). US Government work, public release.
Outputs: catalog/nasa-se-processes.json         17 common technical processes (SE engine)
         catalog/nasa-se-lifecycle.json         life-cycle phases, KDPs, technical reviews, TRLs
         catalog/nasa-requirements-checklist.json  Appendix C checklist + requirement metadata,
                                                verification methods and validation steps

Method
------
``pdftotext -layout`` renders each PDF page (form-feed separated, so the Nth chunk is PDF page N).
Printed page labels are the PDF page minus 13 throughout Part 1 (verified on every page footer
"NASA Systems Engineering Handbook Rev 2 <n>"; asserted below).

* Every item is located in the PDF by an *anchor* string; the PDF page is computed by searching the
  extracted text (whitespace/quote/dash-normalised), never typed by hand. Extraction fails if an
  anchor is missing, so the catalog cannot silently drift from the source.
* Process activity titles are the verbatim ``X.Y.1.2.n`` sub-section headings, parsed from the text.
* Process input/output names are the handbook's bullet labels; each is asserted to occur inside the
  section's text span. Purposes, phase/review descriptions are short paraphrases (fidelity noted).
* Appendix C checklist items are sliced verbatim from the text between consecutive anchors
  (whitespace normalised; checkbox glyphs are not rendered by pdftotext).
* Figure G.4-1 (TRL scale) and Table 3.0-1 (SE product maturity) are raster/graphic figures whose
  cell positions pdftotext cannot reliably align; their content was transcribed from page renders
  (pdftoppm) and is cross-checked here against tokens that pdftotext does recover.

Run:  python scripts/extract/nasa_se.py [--check]
``--check`` regenerates in memory and fails if any committed catalog differs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "sources" / "pdfs" / "nasa-systems-engineering-handbook-rev2.pdf"
CATALOG_DIR = ROOT / "catalog"
SOURCE_ID = "nasa-se"
EDITION = "NASA/SP-2016-6105 Rev 2 (2016)"
EXTRACTION_DATE = "2026-10-13"
PRINTED_OFFSET = 13  # printed page = pdf page - 13 (Part 1, pages 14..356)
EXPECTED_PAGES = 356
FOOTER_RE = re.compile(r"^\s*NASA Systems Engineering Handbook\s+Rev\s*2\s+\S+\s*$", re.M)


# --------------------------------------------------------------------------- text helpers
def normalise(text: str) -> str:
    """Whitespace/quote/dash normalisation used for anchor matching and verbatim slices."""
    rep = {
        "‑": "-", "‐": "-", "–": "-", "—": "-", "‘": "'", "’": "'",
        "“": '"', "”": '"', "": " ", "•": " ", " ": " ", "…": "...",
        "‒": "-",
    }
    for k, v in rep.items():
        text = text.replace(k, v)
    return re.sub(r"\s+", " ", text).strip()


def _key(text: str) -> str:
    return normalise(text).lower()


def pdf_pages(pdf: Path = PDF) -> list[str]:
    exe = shutil.which("pdftotext")
    if not exe:
        raise SystemExit("pdftotext (poppler-utils) is required")
    out = subprocess.run([exe, "-layout", str(pdf), "-"], check=True, capture_output=True).stdout
    pages = out.decode("utf-8").split("\f")
    if pages and not pages[-1].strip():
        pages = pages[:-1]
    assert len(pages) == EXPECTED_PAGES, f"expected {EXPECTED_PAGES} pages, got {len(pages)}"
    return pages


def verify_pdf() -> None:
    manifest = json.loads((ROOT / "sources" / "pdf-manifest.json").read_text(encoding="utf-8"))
    entry = next(s for s in manifest["sources"] if s["id"] == SOURCE_ID)
    digest = hashlib.sha256(PDF.read_bytes()).hexdigest()
    assert digest == entry["sha256"], "pinned PDF hash differs from sources/pdf-manifest.json"
    assert entry["pages"] == EXPECTED_PAGES


class Doc:
    def __init__(self, pages: list[str]):
        self.pages = pages
        self.keys = [_key(p) for p in pages]
        for pno in range(14, EXPECTED_PAGES + 1):  # printed-page offset sanity check
            m = re.findall(r"Rev\s*2\s+(\d+)\s*$", pages[pno - 1].rstrip())
            if m:
                assert int(m[-1]) == pno - PRINTED_OFFSET, f"printed page offset broken on PDF p.{pno}"

    def find(self, anchor: str, start: int = 14, end: int | None = None) -> int:
        """1-based PDF page of the first page in [start, end] containing ``anchor``."""
        k = _key(anchor)
        end = end or len(self.pages)
        for pno in range(start, end + 1):
            if k in self.keys[pno - 1]:
                return pno
        raise AssertionError(f"anchor not found in PDF pp.{start}-{end}: {anchor!r}")

    def require(self, pno: int, *anchors: str) -> None:
        for a in anchors:
            assert _key(a) in self.keys[pno - 1], f"PDF p.{pno} lacks expected text {a!r}"

    def span(self, first: int, last: int) -> tuple[str, list[tuple[int, int]]]:
        """Footer-stripped normalised text of pages first..last plus (offset, pdf_page) marks."""
        parts, marks, pos = [], [], 0
        for pno in range(first, last + 1):
            txt = normalise(FOOTER_RE.sub("", self.pages[pno - 1])) + " "
            marks.append((pos, pno))
            parts.append(txt)
            pos += len(txt)
        return "".join(parts), marks

    def raw_span(self, first: int, last: int) -> str:
        return "\n".join(FOOTER_RE.sub("", self.pages[p - 1]) for p in range(first, last + 1))


def page_at(marks: list[tuple[int, int]], offset: int) -> int:
    page = marks[0][1]
    for pos, pno in marks:
        if pos <= offset:
            page = pno
    return page


def cit(pno: int, section: str | None = None) -> dict:
    c: dict = {"pdf_page": pno}
    if pno >= 14:
        c["printed_page"] = pno - PRINTED_OFFSET
    if section:
        c["section"] = section
    return c


# --------------------------------------------------------------------------- processes
GROUPS = [
    ("system-design", "System Design Processes", "4.0", "4.0 System Design Processes",
     "Define and baseline stakeholder expectations, generate and baseline technical requirements, "
     "decompose them into logical/behavioural models and convert them into a design solution; applied "
     "top-down to each product layer until products can be built, bought or reused."),
    ("product-realization", "Product Realization Processes", "5.0", "5.0 Product Realization",
     "Applied bottom-up from the lowest product to create the design solution (buy, code, build, reuse) "
     "and to verify, validate and transition products that satisfy their design solutions and "
     "stakeholder expectations."),
    ("technical-management", "Technical Management Processes", "6.0", "6.0 Crosscutting Technical Management",
     "Crosscutting processes used to establish and evolve technical plans, manage communication across "
     "interfaces, assess progress against plans and requirements, control technical execution and aid "
     "decision-making."),
]

# (number, slug, title, section, group, purpose paraphrase, inputs, outputs)
PROCESSES = [
    (1, "stakeholder-expectations-definition", "Stakeholder Expectations Definition", "4.1", "system-design",
     "Identify who the stakeholders are and how they intend to use the product, capture their needs, goals "
     "and objectives (typically via use cases/Design Reference Missions and the ConOps) and baseline the "
     "validated expectations that found the rest of the SE engine.",
     ["Initial Customer Expectations", "Other Stakeholder Expectations", "Customer Flow-down Requirements"],
     ["Validated Stakeholder Expectations", "Concept of Operations", "Enabling Product Support Strategies",
      "Measures of Effectiveness", "Human/Systems Function Allocation"]),
    (2, "technical-requirements-definition", "Technical Requirements Definition", "4.2", "system-design",
     "Transform baselined stakeholder expectations into a definition of the problem and a complete set of "
     "validated technical requirements, written as \"shall\" statements, for the product breakdown "
     "structure and enabling products; define MOPs and TPMs and baseline the requirements.",
     ["Baselined Stakeholder Expectations", "Baselined Concept of Operations",
      "Baselined Enabling Support Strategies", "Measures of Effectiveness", "Human/Systems Function Allocation"],
     ["Validated Technical Requirements", "Measures of Performance", "Technical Performance Measures"]),
    (3, "logical-decomposition", "Logical Decomposition", "4.3", "system-design",
     "Use functional analysis to create the system architecture and decompose parent requirements into "
     "logical decomposition models and derived technical requirements allocated down to the lowest "
     "desired level (the \"what\" at each level).",
     ["Technical Requirements", "Technical Measures"],
     ["Logical Decomposition Models", "Derived Technical requirements", "Logical Decomposition Work Products"]),
    (4, "design-solution-definition", "Design Solution Definition", "4.4", "system-design",
     "Translate requirements and logical decomposition models into alternative design solutions, analyse "
     "them through trade studies, select and fully define the preferred alternative, and produce the "
     "specifications used to build and verify the product.",
     ["Technical Requirements", "Logical Decomposition Models"],
     ["The System Specification", "The System External Interface Specifications",
      "The End-Product Specifications", "The End-Product Interface Specifications",
      "Initial Subsystem Specifications", "Enabling Product Requirements", "Product Verification Plan",
      "Product Validation Plan", "Logistics and Operate-to Procedures"]),
    (5, "product-implementation", "Product Implementation", "5.1", "product-realization",
     "Generate a specified product by buying, making/coding or reusing hardware, software, models or "
     "studies, in a form appropriate to the life-cycle phase, that satisfies the design solution.",
     ["Inputs If Purchasing the End Product", "Inputs If Making/Coding the End Product",
      "Inputs Needed If Reusing an End Product", "Enabling Products"],
     ["End Product for Verification", "End Product Documents and Manuals",
      "Product Implementation Work Products"]),
    (6, "product-integration", "Product Integration", "5.2", "product-realization",
     "Engineer subsystem interactions and their interactions with natural and induced environments; "
     "assemble lower-level products into higher-level products and check that the integrated product "
     "functions properly without adverse emergent behaviour.",
     ["Lower-level products to be integrated", "End product design specifications and configuration documentation",
      "Product integration-enabling products"],
     ["Integrated product(s) with all system interactions identified and properly balanced",
      "Documentation and manuals", "Work products"]),
    (7, "product-verification", "Product Verification", "5.3", "product-realization",
     "Prove that an end product (built, coded, bought or reused) conforms to its requirements or "
     "specifications (\"was the end product realized right?\") using test, analysis, inspection or "
     "demonstration.",
     ["The product to be verified", "Verification plan", "Specified requirements baseline", "Enabling products"],
     ["Verified product ready for validation", "Product verification results",
      "Product verification report(s)", "Product verification work products"]),
    (8, "product-validation", "Product Validation", "5.4", "product-realization",
     "Confirm that the verified end product accomplishes its intended purpose in the intended environment "
     "and meets stakeholder expectations as captured in the MOEs, MOPs and ConOps (\"was the right end "
     "product realized?\").",
     ["End product to be validated", "Validation plan", "Baselined stakeholder expectations",
      "Any enabling products"],
     ["Validated end product", "Product validation results", "Product validation report", "Work products"]),
    (9, "product-transition", "Product Transition", "5.5", "product-realization",
     "Transition a verified and validated end product to the customer at the next level of the system "
     "structure for integration or, for the top-level product, to the intended end user, with the "
     "required documentation, packaging, site preparation and training.",
     ["The end product or products to be transitioned",
      "Documentation including manuals, procedures, and processes that are to accompany",
      "Product transition-enabling products"],
     ["Delivered end product with applicable documentation",
      "Work products from transition activities to technical data management",
      "Realized enabling end products to appropriate life-cycle support organization"]),
    (10, "technical-planning", "Technical Planning", "6.1", "technical-management",
     "Establish a plan for applying and managing each common technical process and for identifying and "
     "defining the technical effort needed to meet project objectives and life-cycle phase success "
     "criteria within cost, schedule and risk constraints; produces the SEMP and other technical plans.",
     ["Project Technical Effort Requirements and Project Resource Constraints",
      "Agreements, Capability Needs, Applicable Product Life-Cycle Phase",
      "Applicable Policies, Procedures, Standards, and Organizational Processes",
      "Prior Phase or Baseline Plans", "Replanning Needs"],
     ["Technical work cost estimates, schedules, and resource needs", "Product and process measures",
      "SEMP and other technical plans", "Technical work directives", "Technical Planning Process work products"]),
    (11, "requirements-management", "Requirements Management", "6.2", "technical-management",
     "Identify, control, decompose and allocate requirements across all levels of the WBS, provide "
     "bidirectional traceability and manage changes to established requirement baselines over the "
     "product life cycle.",
     ["Expectations and requirements to be managed", "Requirement change requests",
      "TPM estimation/evaluation results", "Product verification and validation results"],
     ["Requirements Documents", "Approved Changes to the Requirements Baselines",
      "Various Requirements Management Work Products"]),
    (12, "interface-management", "Interface Management", "6.3", "technical-management",
     "Define, manage and control internal and external interfaces when work is divided among parties, and "
     "maintain compliance among products that must interoperate.",
     ["Interface Requirements", "Interface Change Requests", "System Description", "System Boundaries",
      "Organizational Structure", "Boards Structure"],
     ["Interface control documentation", "Approved interface requirement changes", "Other work products"]),
    (13, "technical-risk-management", "Technical Risk Management", "6.4", "technical-management",
     "Identify technical risks (scenario, likelihood, consequence), develop mitigation and contingency "
     "plans, monitor risk status and retire or escalate risks; NASA risk management combines "
     "Risk-Informed Decision Making (RIDM) and Continuous Risk Management (CRM).",
     ["Project Risk Management Plan", "Technical Risk Issues", "Technical Risk Status Measurements",
      "Technical Risk Reporting Requirements", "Other Plans and Policies", "Technical Inputs"],
     ["Technical Risk Mitigation and/or Contingency Actions", "Technical Risk Reports", "Work Products"]),
    (14, "configuration-management", "Configuration Management", "6.5", "technical-management",
     "Provide visibility into and control changes to the performance, functional and physical "
     "characteristics of products over the life cycle, so the configuration is known, reflected in "
     "product information and changed only through managed, beneficial changes.",
     ["CM plan", "Engineering change proposals", "Expectation, requirements and interface documents",
      "Approved requirements baseline changes", "Designated configuration items to be controlled"],
     ["List of configuration items under control", "Current baselines", "CM reports", "Other CM work products"]),
    (15, "technical-data-management", "Technical Data Management", "6.6", "technical-management",
     "Plan for, acquire, access, manage, protect and use technical data across the total system life cycle, "
     "including retention after retirement, working alongside configuration management.",
     ["Technical data products to be managed", "Technical data requests"],
     ["Form of Technical Data Products", "Technical Data Electronic Exchange Formats", "Delivered Technical Data"]),
    (16, "technical-assessment", "Technical Assessment", "6.7", "technical-management",
     "Monitor technical progress through periodic technical (life-cycle) reviews and technical measures "
     "(MOEs, MOPs, KPPs, TPMs), providing status that supports design, realization and management "
     "decisions.",
     ["Technical Plans", "Technical Process and Product Measures", "Reporting Requirements"],
     ["Assessment Results, Findings, and Recommendations", "Technical Review Reports/Minutes",
      "Other Work Products"]),
    (17, "decision-analysis", "Decision Analysis", "6.8", "technical-management",
     "Formulate and characterise decision alternatives against defined criteria, evaluate them with "
     "suitable methods (including uncertainty) and recommend the alternative that best implements the "
     "decision-maker's priorities, documenting rationale and assumptions.",
     ["Decision need, identified alternatives, issues, or problems and supporting data",
      "Analysis support requests"],
     ["Alternative Selection and Decision Support Recommendations and Impacts"]),
]

# Activity headings per process (count of X.Y.1.2.n headings) — verified against the text.
EXPECTED_ACTIVITIES = {"4.1": 10, "4.2": 7, "4.3": 3, "4.4": 10, "5.1": 3, "5.2": 7, "5.3": 4, "5.4": 4,
                       "5.5": 5, "6.1": 7, "6.2": 6, "6.3": 5, "6.4": 7, "6.5": 6, "6.6": 3, "6.7": 3, "6.8": 7}
ACT_RE = re.compile(r"^(\d\.\d\.1\.2\.\d+)\s+(\S.*?)\s*$")


def _section_bounds(doc: Doc) -> dict[str, tuple[int, int]]:
    """section -> (start pdf page, end pdf page) using the next section heading."""
    starts = {}
    for _, _, title, sec, *_ in PROCESSES:
        starts[sec] = doc.find(f"{sec} {title}", start=60)
    order = [p[3] for p in PROCESSES]
    bounds = {}
    for i, sec in enumerate(order):
        end = starts[order[i + 1]] if i + 1 < len(order) else doc.find("Appendix A: Acronyms", start=200)
        bounds[sec] = (starts[sec], end)
    return bounds


def _section_text(doc: Doc, sec: str, title: str, nxt: str | None, first: int, last: int) -> str:
    raw = doc.raw_span(first, last)
    i = raw.find(f"{sec} {title}")
    assert i >= 0, sec
    j = raw.find(nxt, i + 10) if nxt else -1
    return raw[i:j] if j > 0 else raw[i:]


def _activities(doc: Doc, sec: str, text: str, first: int, last: int) -> list[dict]:
    lines = text.splitlines()
    acts = []
    for n, line in enumerate(lines):
        m = ACT_RE.match(line)
        if not m:
            continue
        title = m.group(2)
        nxt = lines[n + 1] if n + 1 < len(lines) else ""
        if re.match(r"^\s{6,}\S", nxt) and len(nxt.strip()) < 60 and not re.match(r"^\s*\d", nxt):
            title += " " + nxt.strip()
        acts.append({"section": m.group(1), "title": normalise(title),
                     "pdf_page": doc.find(normalise(m.group(1) + " " + m.group(2)), start=first, end=last)})
    assert len(acts) == EXPECTED_ACTIVITIES[sec], f"{sec}: {len(acts)} activities"
    return acts


def build_processes(doc: Doc) -> dict:
    bounds = _section_bounds(doc)
    groups = []
    for gid, title, chapter, anchor, desc in GROUPS:
        groups.append({"id": gid, "title": title, "chapter": chapter, "description": desc,
                       "citation": cit(doc.find(anchor, start=60), chapter)})
    items = []
    for idx, (num, slug, title, sec, group, purpose, inputs, outputs) in enumerate(PROCESSES):
        first, last = bounds[sec]
        nxt = f"{PROCESSES[idx + 1][3]} {PROCESSES[idx + 1][2]}" if idx + 1 < len(PROCESSES) else "Appendix A"
        text = _section_text(doc, sec, title, nxt, first, last)
        ntext = _key(text)
        for name in inputs + outputs:
            assert _key(name) in ntext, f"{sec}: input/output label {name!r} not in section text"
        inp_page = doc.find(f"{sec}.1.1 Inputs", start=first, end=last)
        out_page = doc.find(f"{sec}.1.3 Outputs", start=first, end=last)
        items.append({
            "id": slug,
            "number": num,
            "title": title,
            "group": group,
            "text": purpose,
            "inputs": inputs,
            "outputs": outputs,
            "activities": _activities(doc, sec, text, first, last),
            "inputs_citation": cit(inp_page, f"{sec}.1.1"),
            "outputs_citation": cit(out_page, f"{sec}.1.3"),
            "citation": cit(first, sec),
        })
    assert len(items) == 17 and [i["number"] for i in items] == list(range(1, 18))
    assert sum(1 for i in items if i["group"] == "system-design") == 4
    assert sum(1 for i in items if i["group"] == "product-realization") == 5
    assert sum(1 for i in items if i["group"] == "technical-management") == 8

    engine_page = doc.find("Figure 2.1-1 The Systems Engineering Engine (NPR 7123.1)", start=14, end=40)
    doc.require(engine_page, "17. Decision Analysis", "10. Technical Planning", "1. Stakeholders Expectations")
    intro_page = doc.find("Processes 1 through 9 indicated in Figure 2.1-1", start=14, end=40)
    iter_page = doc.find("the processes within the SE engine are used both iteratively and recursively", 14, 40)
    vv_page = doc.find("2.4 Distinctions between Product Verification and Product Validation", 14, 40)
    return {
        "catalog_id": "nasa-se-processes",
        "source_id": SOURCE_ID,
        "title": "NASA SE Engine: the 17 Common Technical Processes",
        "edition": EDITION,
        "description": (
            "The 17 common technical processes of the NASA systems engineering engine (NPR 7123.1 as "
            "described in the NASA SE Handbook Rev 2), grouped into system design (1-4), product realization "
            "(5-9) and technical management (10-17), with purpose, typical inputs/outputs and the handbook's "
            "process-activity headings."),
        "extraction": {
            "method": ("pdftotext -layout of the pinned PDF; section pages located by heading anchors; activity "
                       "titles parsed from X.Y.1.2.n headings; input/output labels asserted present in each "
                       "section; purposes paraphrased (scripts/extract/nasa_se.py)"),
            "date": EXTRACTION_DATE,
            "fidelity": "paraphrased",
            "notes": ("'text' (purpose) is a paraphrase. 'inputs'/'outputs' are the handbook's bullet labels "
                      "(verbatim, occasionally truncated before the description). 'activities' titles are verbatim "
                      "sub-section headings; the handbook misnumbers two CM headings as 6.4.1.2.5/6.4.1.2.6 inside "
                      "section 6.5 and they are kept as printed. Detailed guidance for each process lives in the "
                      "separate NASA Expanded Guidance for SE document, which is not part of this source."),
            "pages_reviewed": "17-25, 63-215",
        },
        "groups": groups,
        "items": items,
        "parameters": {
            "engine": {
                "summary": ("Processes 1-9 are the tasks executing the project; processes 10-17 are crosscutting "
                            "tools for carrying out those processes. The engine is applied iteratively and "
                            "recursively at every product layer and life-cycle phase."),
                "figure": "Figure 2.1-1 The Systems Engineering Engine (NPR 7123.1)",
                "citation": cit(engine_page, "2.1"),
                "task_vs_crosscutting_citation": cit(intro_page, "2.1"),
                "iterative_recursive_citation": cit(iter_page, "2.1"),
            },
            "verification_vs_validation": {
                "verification": ("Proof of compliance with requirements: the product meets each 'shall' "
                                 "statement, shown by test, analysis, inspection or demonstration."),
                "validation": ("The product accomplishes its intended purpose in the intended environment and "
                               "meets customer/stakeholder expectations; relates back to the ConOps."),
                "citation": cit(vv_page, "2.4"),
            },
        },
    }


# --------------------------------------------------------------------------- life cycle
PHASES = [
    # id, title, stage, section, blue-box anchor, purpose paraphrase, outcomes, key activities, reviews
    ("pre-phase-a", "Pre-Phase A: Concept Studies", "Pre-Formulation", "3.3",
     "Space Flight Pre Phase A: Concept Studies",
     "Produce a broad spectrum of mission ideas and alternatives from which new programs/projects can be "
     "selected; determine feasibility, develop mission concepts, draft system-level requirements, assess "
     "performance/cost/schedule feasibility and identify technology needs and scope.",
     "Feasible system concepts (simulations, analyses, study reports, models, mockups)",
     ["Identify key stakeholders and capture expectations as needs, goals and objectives (NGOs)",
      "Define measures of effectiveness", "Develop and baseline the Concept of Operations",
      "Perform trade-offs and analyses of alternatives", "Identify risk classification and initial technical risks",
      "Develop preliminary SEMP and baseline the Technology Development Plan",
      "Define preliminary verification and validation approach",
      "Prepare proposals incl. high-level WBS and ROM cost, schedule and risk estimates"],
     ["MCR", "Informal proposal review"]),
    ("phase-a", "Phase A: Concept and Technology Development", "Formulation", "3.4",
     "Space Flight Phase A: Concept and Technology Development",
     "Determine the feasibility and desirability of the suggested system and establish an initial baseline; "
     "develop the final mission concept, system-level requirements, needed technology developments and "
     "technical management plans.",
     "System concept definition (simulations, analyses, engineering models and mockups, trade study definition)",
     ["Develop and baseline top-level requirements and constraints incl. internal and external interfaces",
      "Allocate system requirements to functions and to the next lower level", "Validate requirements",
      "Baseline the SEMP, HSI Plan and control plans (risk, CM, data management, S&MA, software)",
      "Develop preliminary Verification and Validation Plan",
      "Develop and baseline mission architecture; perform and archive trade studies",
      "Provide technical cost estimate and range; define the WBS; develop SOWs",
      "Identify, analyze and update risks"],
     ["SRR", "MDR/SDR"]),
    ("phase-b", "Phase B: Preliminary Design and Technology Completion", "Formulation", "3.5",
     "Space Flight Phase B: Preliminary Design and Technology Completion",
     "Define the project in enough detail to establish an initial baseline capable of meeting mission needs; "
     "develop end-product and enabling-product requirements and a preliminary design for each system "
     "structure end product.",
     "Mockups, trade study results, specification and interface documents, prototypes",
     ["Develop the preliminary design incl. internal and external interfaces; select a preliminary design solution",
      "Develop operations plans based on the matured ConOps", "Report technology development results",
      "Update cost range estimate and schedule data", "Identify and update risks",
      "Develop preliminary orbital debris assessment, decommissioning and disposal plans"],
     ["PDR", "Safety review"]),
    ("phase-c", "Phase C: Final Design and Fabrication", "Implementation", "3.6",
     "Space Flight Phase C: Final Design and Fabrication",
     "Complete the detailed design of the system (including operations systems), fabricate hardware and "
     "code software; generate final designs for each system structure end product.",
     "End-product detailed designs, component fabrication and software development",
     ["Develop and document hardware and software detailed designs; fully document final design and data package",
      "Baseline interface definitions, implementation, integration, V&V and operations plans",
      "Develop/refine procedures for integration, manufacturing/assembly and V&V",
      "Fabricate (or code) the product", "Identify and update risks"],
     ["CDR", "PRR", "SIR", "Safety review"]),
    ("phase-d", "Phase D: System Assembly, Integration and Test, Launch", "Implementation", "3.7",
     "Space Flight Phase D: System Assembly, Integration and Test, Launch",
     "Assemble and integrate the system (hardware, software and humans) while developing confidence that it "
     "meets the system requirements; launch and prepare for operations; transition to use.",
     "Operations-ready system end product with supporting related enabling products",
     ["Integrate/assemble components according to the integration plans",
      "Perform verification and validation per the V&V Plan (qualification, acceptance, end-to-end tests)",
      "Resolve V&V discrepancies and baseline the verification and validation report",
      "Prepare and baseline operator's and maintenance manuals and operations handbook",
      "Train operators and maintainers; confirm readiness for flight", "Document lessons learned"],
     ["TRR", "SAR", "ORR", "FRR", "System functional and physical configuration audits", "Safety review"]),
    ("phase-e", "Phase E: Operations and Sustainment", "Implementation", "3.8",
     "Space Flight Phase E: Operations and Sustainment",
     "Conduct the mission to meet the initially identified need and maintain support for that need; "
     "implement the mission operations plan.",
     "Desired system",
     ["Conduct the prime mission(s) and provide sustaining support", "Collect and analyse engineering and science data",
      "Address problem/failure reports; identify and update risks", "Apply for mission extensions if warranted",
      "Prepare for deactivation and decommissioning; capture lessons learned"],
     ["PLAR", "CERR", "PFAR", "DR", "System upgrade review", "Safety review"]),
    ("phase-f", "Phase F: Closeout", "Implementation", "3.9", "Phase F: Closeout",
     "Implement the systems decommissioning/disposal plan developed in Phase E and analyse returned data "
     "and any returned samples.",
     "Product closeout",
     ["Dispose of the system and supporting processes", "Baseline the mission final report", "Archive data",
      "Capture lessons learned"],
     ["DRR"]),
]

KDPS = [  # id, title, from-phase, to-phase
    ("KDP-A", "Key Decision Point A", "pre-phase-a", "phase-a"),
    ("KDP-B", "Key Decision Point B", "phase-a", "phase-b"),
    ("KDP-C", "Key Decision Point C", "phase-b", "phase-c"),
    ("KDP-D", "Key Decision Point D", "phase-c", "phase-d"),
    ("KDP-E", "Key Decision Point E", "phase-d", "phase-e"),
    ("KDP-F", "Key Decision Point F", "phase-e", "phase-f"),
]

# Table 6.7-1 rows (+TRR from section 5.3 / glossary). Paraphrased purpose, timing and results.
REVIEWS = [
    ("MCR", "Mission Concept Review", ["pre-phase-a"], "Mission Concept Review (MCR)", "G-3",
     "Affirm the mission need and evaluate the proposed objectives and the concept for meeting them.",
     "Completed before entering the concept development phase (Phase A).",
     "Supports a determination that the mission meets the customer need and merits further study as a "
     "candidate Phase A effort."),
    ("SRR", "System Requirements Review", ["phase-a"], "System Requirements Review (SRR)", "G-4",
     "Evaluate the functional and performance requirements defined for the system and the preliminary "
     "program/project plan, and ensure that the requirements and selected concept will satisfy the mission.",
     "Conducted during concept development (Phase A), before the SDR or MDR.",
     "Freezes program/project requirements and leads to a formal decision to proceed with proposal request "
     "preparations for project implementation. (Program-level SRR criteria: NPR 7123.1 Table G-1.)"),
    ("MDR-SDR", "Mission Definition Review / System Definition Review", ["phase-a"],
     "Sometimes called the MDR by robotic", "G-5",
     "Evaluate whether the proposed architecture is responsive to the functional and performance requirements "
     "and that the requirements have been allocated to all functional elements of the mission/system "
     "(called MDR for robotic projects, SDR for human flight projects).",
     "Conducted during concept development (Phase A), prior to KDP B and the start of preliminary design.",
     "Supports the decision to further develop the architecture/design and any needed technology; the "
     "system and its operation are understood well enough to warrant design and acquisition of end items. "
     "(Program-level criteria: NPR 7123.1 Table G-2.)"),
    ("PDR", "Preliminary Design Review", ["phase-b"], "Preliminary Design Review", "G-6",
     "Demonstrate that the preliminary design meets all system requirements with acceptable risk and within "
     "cost and schedule constraints: correct design options selected, interfaces identified, verification "
     "methods described, critical system-wide issues resolved.",
     "Near the completion of preliminary design (Phase B), as the last review in the Formulation Phase.",
     "The design-to baseline is approved and the project is authorized to proceed into Implementation and "
     "toward final design."),
    ("CDR", "Critical Design Review", ["phase-c"], "Critical Design Review", "G-7",
     "Demonstrate that design maturity supports proceeding with full-scale fabrication, assembly, integration "
     "and test, and that the technical effort is on track to meet mission performance requirements within "
     "cost and schedule.",
     "During the final design phase (Phase C).",
     "The build-to baseline, production and verification plans are approved; coding of deliverable software "
     "and system qualification testing and integration are authorized; open issues have closure actions."),
    ("PRR", "Production Readiness Review", ["phase-c"], "Production Readiness Review", "G-8",
     "For projects producing multiple or similar systems (more than three, or as determined by the project): "
     "determine readiness to efficiently produce the required number of systems, with production plans, "
     "enabling products and personnel in place.",
     "During the final design phase (Phase C).",
     "The final production build-to baseline, production and verification plans are approved and drawings are "
     "released for production."),
    ("SIR", "System Integration Review", ["phase-c"], "System Integration Review", "G-9",
     "Ensure segments, components and subsystems are on schedule to be integrated and that integration "
     "facilities, support personnel and integration plans and procedures are on schedule.",
     "At the end of final design (Phase C), before system assembly, integration and test (Phase D) begins.",
     "The final as-built baseline and verification plans are approved; drawings released to support "
     "integration; integration procedures, GSE, facilities, logistics and personnel ready."),
    ("TRR", "Test Readiness Review", ["phase-d"], "Test Readiness Review", None,
     "Ensure that the test article (hardware/software), test facility, support personnel and test procedures "
     "are ready for testing; held (informally early, more formally later) to assess readiness for verification "
     "and validation, with tailored entrance/success criteria.",
     "Before verification/validation test events; typically several TRRs, listed among Phase D reviews.",
     "Confirmed readiness and availability of test ranges, facilities, trained testers, instrumentation, "
     "integration labs, support equipment and other enabling products."),
    ("SAR", "System Acceptance Review", ["phase-d"], "System Acceptance Review", "G-11",
     "Verify the completeness of specific end products relative to their expected maturity, assess compliance "
     "with stakeholder expectations and ensure sufficient technical maturity to authorize shipment to the "
     "operational facility or launch site.",
     "Phase D (generally applies to human space flight; robotic projects may hold a pre-ship review).",
     "The system is accepted by the buyer and shipment and installation for operational use are authorized."),
    ("ORR", "Operational Readiness Review", ["phase-d"], "Operational Readiness Review", "G-12",
     "Examine the actual system characteristics and operating procedures; ensure all flight and ground "
     "hardware, software, personnel, procedures and user documentation reflect the deployed state.",
     "Phase D, before operations.",
     "The system is ready to assume normal operations."),
    ("FRR", "Flight Readiness Review", ["phase-d"], "Flight Readiness Review", "G-13",
     "Examine tests, demonstrations, analyses and audits that determine readiness for a safe and successful "
     "flight or launch and subsequent flight operations; ensure flight and ground systems, personnel and "
     "procedures are operationally ready.",
     "Phase D, before launch (Phase D activities focus on preparing for the FRR/MRR).",
     "Technical and procedural maturity exists for launch and flight authorization and, in some cases, "
     "initiation of operations."),
    ("PLAR", "Post-Launch Assessment Review", ["phase-e"], "Post-Launch", "G-14",
     "Post-deployment evaluation of readiness to proceed with full, routine operations, including transfer of "
     "responsibility from the development to the operations organization.",
     "Typically after early flight operations and initial checkout.",
     "The system is ready to assume in-space operations."),
    ("CERR", "Critical Event Readiness Review", ["phase-e"], "Critical Event", "G-15",
     "Confirm readiness to execute the mission's critical activities during flight operations (e.g., orbit "
     "insertion, rendezvous and docking, re-entry, scientific encounters).",
     "Before each critical event (established at the discretion of the program).",
     "The system is ready to assume (or resume) in-space operations."),
    ("PFAR", "Post-Flight Assessment Review", ["phase-e"], "Post-Flight", "G-16",
     "Evaluate flight activities after recovery, identify all anomalies and determine actions to mitigate or "
     "resolve them for future flights (human space flight).",
     "After flight and recovery.",
     "Report documenting flight performance and recommendations is complete; all anomalies documented and "
     "dispositioned."),
    ("DR", "Decommissioning Review", ["phase-e"], "Decommission", "G-17",
     "Confirm the decision to terminate or decommission the system and assess readiness for safe "
     "decommissioning and disposal of system assets.",
     "Normally near the end of routine mission operations; may be advanced or delayed by events or extensions.",
     "Decommissioning and disposal of system items and processes are appropriate and effective."),
    ("DRR", "Disposal Readiness Review", ["phase-f"], "Disposal", "G-18",
     "Confirm readiness for the final disposal of the system assets.",
     "Held as major assets are ready for final disposal.",
     "Disposal of system items and processes is appropriate and effective."),
]
REVIEW_ALIASES = {"MDR-SDR": ["MDR", "SDR", "MDR/SDR"], "FRR": ["MRR"], "SAR": ["pre-ship review"]}

# Table 3.0-1 SE Product Maturity (transcribed from page render, PDF p.35). "**" => required product.
MATURITY_COLUMNS = ["MCR", "SRR", "MDR/SDR", "PDR", "CDR", "SIR", "ORR", "FRR", "DR", "DRR"]
MATURITY_ROWS = [
    ("Stakeholder identification and", ["**Baseline", "Update", "Update", "Update"]),
    ("Concept definition", ["**Baseline", "Update", "Update", "Update", "Update"]),
    ("Measure of Effectiveness definition", ["**Approve"]),
    ("Cost and schedule for technical", ["Initial", "Update", "Update", "Baseline", "Update", "Update", "Update",
                                         "Update", "Update", "Update"]),
    ("SEMP", ["Preliminary", "**Baseline", "**Baseline", "Update", "Update", "Update"]),
    ("Requirements", ["Preliminary", "**Baseline", "Update", "Update", "Update"]),
    ("Technical Performance Measures definition", [None, None, "**Approve"]),
    ("Architecture definition", [None, None, "**Baseline"]),
    ("Allocation of requirements to next lower level", [None, None, "**Baseline"]),
    ("Required leading indicator trends", [None, None, "**Initial", "Update", "Update", "Update"]),
    ("Design solution definition", [None, None, "Preliminary", "**Preliminary", "**Baseline", "Update", "Update"]),
    ("Interface definition(s)", [None, None, "Preliminary", "Baseline", "Update", "Update"]),
    ("Implementation plans (Make/code, buy, reuse)", [None, None, "Preliminary", "Baseline", "Update"]),
    ("Integration plans", [None, None, "Preliminary", "Baseline", "Update", "**Update"]),
    ("Verification and Validation plans", ["Approach", None, "Preliminary", "Baseline", "Update", "Update"]),
    ("Verification and Validation results", [None, None, None, None, None, "**Initial", "**Preliminary", "**Baseline"]),
    ("Transportation criteria and instructions", [None, None, None, None, "Initial", "Final", "Update"]),
    ("Operations plans", [None, None, None, "Baseline", "Update", "Update", "**Update"]),
    ("Operational procedures", [None, None, None, None, "Preliminary", "Baseline", "**Update", "Update"]),
    ("Certification (flight/use)", [None, None, None, None, None, None, "Preliminary", "**Final"]),
    ("Decommissioning plans", [None, None, None, "Preliminary", "Preliminary", "Preliminary", "**Baseline", "Update",
                               "**Update"]),
    ("Disposal plans", [None, None, None, "Preliminary", "Preliminary", "Preliminary", "**Baseline", "Update", "Update",
                        "**Update"]),
]
MATURITY_FOOTNOTE = ("SEMP is baselined at SRR for projects, tightly coupled programs and single-project programs, "
                     "and at MDR/SDR for uncoupled and loosely coupled programs.")

# Figure G.4-1 (raster figure, transcribed from the PDF p.264 render). Verbatim wording.
TRLS = [
    (1, "Basic principles observed and reported"),
    (2, "Technology concept and/or application formulated"),
    (3, "Analytical and experimental critical function and/or characteristic proof-of-concept"),
    (4, "Component and/or breadboard validation in laboratory environment"),
    (5, "Component and/or breadboard validation in relevant environment"),
    (6, "System/subsystem model or prototype demonstration in a relevant environment (ground or space)"),
    (7, "System prototype demonstration in a target/space environment"),
    (8, "Actual system completed and \"flight qualified\" through test and demonstration (ground or flight)"),
    (9, "Actual system \"flight proven\" through successful mission operations"),
]

ASSESSMENT_CRITERIA = [
    "Alignment with and contribution to Agency strategic goals",
    "Adequacy of management approach",
    "Adequacy of technical approach",
    "Adequacy of the integrated cost and schedule estimates and funding strategy",
    "Adequacy and availability of non-budgetary resources",
    "Adequacy of the risk management approach",
]
REVIEW_ACTIVITIES = [
    "Identify, plan and conduct phase-to-phase technical reviews",
    "Establish each review's purpose, objective, and entry and success criteria",
    "Establish the makeup of the review team",
    "Identify and resolve action items resulting from the review",
]
TAILORING_CRITERIA = ["Type of mission", "Criticality of the mission in meeting the Agency Strategic Plan",
                      "Acceptable risk level", "National significance", "Complexity", "Mission lifetime",
                      "Cost of mission", "Launch constraints"]


def build_lifecycle(doc: Doc) -> dict:
    t221 = doc.find("Table 2.2-1 Project Life Cycle Phases", 14, 40)
    fig301 = doc.find("Figure 3.0-1 NASA Spaceflight Project Life Cycle from NPR 7120.5E", 14, 60)
    kdp_def = doc.find("KDPs are the events at which the decision authority determines the readiness", 14, 60)
    t301 = doc.find("Table 3.0-1 SE Product Maturity from NPR 7123.1", 30, 40)
    t671 = doc.find("Table 6.7-1 Purpose and Results for Life-Cycle Reviews for Spaceflight Projects", 190, 210)
    trl_fig = doc.find("Figure G.4-1 Technology Readiness Levels", 250, 280)
    groups = [
        {"id": "phases", "title": "Project life-cycle phases (Pre-Phase A to F)", "citation": cit(t221, "2.2")},
        {"id": "kdps", "title": "Key Decision Points", "citation": cit(kdp_def, "3.0")},
        {"id": "reviews", "title": "Life-cycle technical reviews", "citation": cit(t671, "6.7")},
        {"id": "trl", "title": "Technology Readiness Levels", "citation": cit(trl_fig, "G.4")},
    ]
    items: list[dict] = []
    phase_pages = {}
    for pid, title, stage, sec, box, purpose, outcomes, acts, reviews in PHASES:
        start = doc.find(f"{sec} Project {title.split(':')[0]}", 30, 60) if pid != "phase-f" else doc.find("3.9 Project Phase F: Closeout", 30, 60)
        bpage = doc.find(box, start, start + 3)
        doc.require(bpage, "Purpose", "Reviews")
        for r in reviews:
            if r in ("MDR/SDR",):
                doc.require(bpage, "MDR/SDR")
        phase_pages[pid] = bpage
        items.append({"id": pid, "kind": "phase", "group": "phases", "title": title, "stage": stage,
                      "text": purpose, "typical_outcomes": outcomes, "key_activities": acts, "reviews": reviews,
                      "section_citation": cit(start, sec), "citation": cit(bpage, sec)})
    # every phase purpose row is on Table 2.2-1 (pp. t221..t221+1)
    doc.require(t221, "Pre-Phase A", "Phase A", "Phase B", "Phase C", "Phase D")
    doc.require(t221 + 1, "Phase E", "Phase F")
    for kid, title, frm, to in KDPS:
        doc.require(fig301, kid.replace("-", " "))
        items.append({"id": kid, "kind": "kdp", "group": "kdps", "title": title,
                      "text": (f"Decision gate at which the decision authority determines readiness to progress from "
                               f"{frm} to {to}; decisions may carry liens, and a project failing a KDP may retry "
                               f"after addressing deficiencies or be terminated."),
                      "precedes_phase": to, "follows_phase": frm, "citation": cit(fig301, "3.0"),
                      "definition_citation": cit(kdp_def, "3.0")})
    maturity_by_review: dict[str, list[dict]] = {c: [] for c in MATURITY_COLUMNS}
    for row, cells in MATURITY_ROWS:
        doc.require(t301, " ".join(row.split()[:2]))  # labels wrap in the text layer
        for col, cell in zip(MATURITY_COLUMNS, cells):
            if cell:
                maturity_by_review[col].append({"product": row.replace("Stakeholder identification and",
                                                                       "Stakeholder identification and understanding*"),
                                                "maturity": cell.lstrip("*"), "required": cell.startswith("**")})
    for rid, name, phases, anchor, gtable, purpose, timing, results in REVIEWS:
        if rid == "TRR":
            page = doc.find("these Test Readiness Reviews (TRRs) may be held informally", 100, 140)
            gloss = doc.find("Test Readiness Review", 230, 250)
            doc.require(gloss, "test procedures are ready for testing")
            entry = {"criteria_reference": "Tailored by the project (TRRs are an activity of the Technical "
                                           "Assessment Process); see NPR 7123.1 for any required criteria.",
                     "glossary_citation": cit(gloss, "Appendix B")}
            section = "5.3.1.2.1"
        else:
            page = doc.find(f"({rid.split('-')[0]})", t671, t671 + 5)
            num = gtable.split("-")[1]
            # the criteria cell wraps inside the table; allow the split "G-" ... "<n> of NPR"
            assert re.search(rf"g-(?:{num}\b|\s?.{{0,150}}?\b{num} of npr)", doc.keys[page - 1]), (rid, gtable)
            entry = {"criteria_reference": f"NPR 7123.1 Table {gtable}"}
            section = "6.7 (Table 6.7-1)"
        mat_key = "MDR/SDR" if rid == "MDR-SDR" else rid
        item = {"id": rid, "kind": "review", "group": "reviews", "acronym": rid.replace("-", "/"), "title": name,
                "aliases": REVIEW_ALIASES.get(rid, []), "phases": phases, "text": purpose, "timing": timing,
                "results": results, **entry, "citation": cit(page, section)}
        if mat_key in maturity_by_review:
            item["product_maturity"] = maturity_by_review[mat_key]
            item["product_maturity_citation"] = cit(t301, "3.0 (Table 3.0-1)")
        items.append(item)
    doc.require(trl_fig, "Technology Readiness Levels")
    for n, desc in TRLS:
        items.append({"id": f"TRL-{n}", "kind": "trl", "group": "trl", "level": n, "title": f"TRL {n}",
                      "text": desc, "citation": cit(trl_fig, "G.4 (Figure G.4-1)")})
    heritage = doc.find("environment have changed, then the TRL drops to TRL 5", 250, 280)
    lowest = doc.find("The TRL of the system is determined by the lowest TRL present in the system", 250, 280)
    trl6 = doc.find("Typically, a TRL of 6", 230, 250)
    assess = doc.find("There are 6 criteria considered in", 190, 200)
    rev_acts = doc.find("Typical activities performed for technical reviews include", 190, 205)
    tail = doc.find("3.11.2 Criteria for Tailoring", 50, 60)
    tail_ways = doc.find("3.11.4 Ways to Tailor a SE Requirement", 50, 60)
    combine = doc.find("A small project may decide to combine the SRR and the SDR", 50, 60)
    defs = doc.find("NPR 7123.1 defines \"tailoring\" as", 50, 60)
    for c in TAILORING_CRITERIA:
        doc.require(tail, c)
    assert len([i for i in items if i["kind"] == "phase"]) == 7
    assert len([i for i in items if i["kind"] == "review"]) == 16
    assert len([i for i in items if i["kind"] == "trl"]) == 9
    return {
        "catalog_id": "nasa-se-lifecycle",
        "source_id": SOURCE_ID,
        "title": "NASA Project Life Cycle, Key Decision Points, Technical Reviews and TRLs",
        "edition": EDITION,
        "description": ("Space flight project life-cycle phases (Pre-Phase A to F), KDPs, the life-cycle technical "
                        "reviews of Table 6.7-1 (plus TRR), the SE product maturity expected at each review "
                        "(Table 3.0-1) and the TRL scale (Figure G.4-1), as presented in NASA SE Handbook Rev 2."),
        "extraction": {
            "method": ("pdftotext -layout of the pinned PDF with anchor-based page location; Table 3.0-1 and "
                       "Figure G.4-1 transcribed from pdftoppm page renders and cross-checked against recovered "
                       "text tokens (scripts/extract/nasa_se.py)"),
            "date": EXTRACTION_DATE,
            "fidelity": "paraphrased",
            "notes": ("Phase purposes, review purposes/timing/results and KDP text are paraphrases. TRL "
                      "descriptions and product-maturity cells are verbatim from the figures. Entrance and success "
                      "criteria for each review are NOT reproduced in the handbook; it points to NPR 7123.1 "
                      "Appendix G tables, recorded here as 'criteria_reference'. TRR is not a row of Table 6.7-1; "
                      "it is taken from the Section 5.3 note and the Appendix B glossary. Life cycles for IT "
                      "(NPR 7120.7), R&T (NPR 7120.8) and software (NPR 7150.2) differ and are not modelled."),
            "pages_reviewed": "22-23, 32-56, 60, 122, 196-205, 246, 263-268",
        },
        "groups": groups,
        "items": items,
        "parameters": {
            "se_product_maturity": {
                "title": "Table 3.0-1 SE Product Maturity from NPR 7123.1",
                "columns": MATURITY_COLUMNS,
                "rows": [{"product": r, "cells": (c + [None] * len(MATURITY_COLUMNS))[:len(MATURITY_COLUMNS)]}
                         for r, c in MATURITY_ROWS],
                "legend": "'**' prefix = item is a required product for that review",
                "footnote": MATURITY_FOOTNOTE,
                "note": "The first row label is truncated in the source table ('Stakeholder identification and').",
                "citation": cit(t301, "3.0"),
            },
            "technical_assessment_criteria": {"items": ASSESSMENT_CRITERIA, "citation": cit(assess, "6.7.1")},
            "review_activities": {"items": REVIEW_ACTIVITIES, "citation": cit(rev_acts, "6.7.1.2.2")},
            "trl_rules": {
                "system_trl_is_lowest": ("The TRL of a system is determined by the lowest TRL present in it; "
                                         "elements never integrated as a unit lower the unit's TRL."),
                "system_trl_citation": cit(lowest, "G.4"),
                "heritage": ("If the architecture and environment have changed, a heritage system's TRL drops to "
                             "TRL 5, at least initially; further analysis may justify TRL 6 or 7 but not TRL 9."),
                "heritage_citation": cit(heritage, "G.4"),
                "typical_integration_threshold": ("Typically TRL 6 (technology demonstrated in a relevant "
                                                  "environment) is required for a technology to be integrated "
                                                  "into an SE process (glossary)."),
                "typical_integration_threshold_citation": cit(trl6, "Appendix B"),
            },
            "tailoring": {
                "definition": ("Tailoring seeks relief from SE NPR requirements (results in deviations/waivers "
                               "documented e.g. via the Compliance Matrix in the SEMP); customization modifies "
                               "recommended practices and needs no waiver, but significant customization should be "
                               "documented in the SEMP."),
                "definition_citation": cit(defs, "3.11.1"),
                "criteria": TAILORING_CRITERIA,
                "criteria_citation": cit(tail, "3.11.2"),
                "ways": ["Eliminate a requirement that does not apply",
                         "Eliminate a requirement that is overly burdensome",
                         "Scale the requirement to balance implementation cost and project risk",
                         "Customize: adjust how each of the 17 SE processes is implemented",
                         "Customize: adjust the formality and timing of reviews"],
                "ways_citation": cit(tail_ways, "3.11.4"),
                "combining_reviews": ("A small project may combine SRR and SDR/MDR without an SE NPR waiver as long "
                                      "as the intent of both is accomplished; dropping a required review needs a "
                                      "waiver or deviation; the governing PM NPR may still require one."),
                "combining_reviews_citation": cit(combine, "3.11.4.3"),
            },
        },
    }


# --------------------------------------------------------------------------- requirements checklist
# Sequence of (item id or None for a heading separator, group, start anchor). Item text runs from its
# anchor to the next anchor in the sequence. All anchors lie in Appendix C, PDF pp. 249-252.
APPC_SEQ = [
    ("c1-shall", "c1-terms", "Shall = requirement"),
    ("c1-will", "c1-terms", "Will = facts or declaration of purpose"),
    ("c1-should", "c1-terms", "Should = goal"),
    (None, None, "C.2 Editorial Checklist"),
    (None, None, "Personnel Requirement"),
    ("c2-personnel-active-voice", "c2-editorial", "The requirement is in the form \"responsible party shall"),
    (None, None, "Product Requirement"),
    ("c2-product-form", "c2-editorial", "The requirement is in the form \"product ABC shall XYZ.\""),
    ("c2-consistent-terminology", "c2-editorial", "The requirement uses consistent terminology to refer"),
    ("c2-tolerances", "c2-editorial", "Complete with tolerances for qualitative/performance values"),
    ("c2-free-of-implementation", "c2-editorial", "Is the requirement free of implementation?"),
    ("c2-free-of-operations", "c2-editorial", "Free of descriptions of operations?"),
    (None, None, "Example Product Requirements"),
    (None, None, "C.3 General Goodness Checklist"),
    ("c3-grammar", "c3-general-goodness", "The requirement is grammatically correct."),
    ("c3-typos", "c3-general-goodness", "The requirement is free of typos"),
    ("c3-template", "c3-general-goodness", "The requirement complies with the project's template"),
    ("c3-positive", "c3-general-goodness", "The requirement is stated positively"),
    ("c3-tbd-tbr", "c3-general-goodness", "The use of \"To Be Determined\" (TBD) values should be minimized."),
    ("c3-rationale", "c3-general-goodness", "The requirement is accompanied by an intelligible rationale"),
    ("c3-location", "c3-general-goodness", "The requirement is located in the proper section"),
    (None, None, "C.4 Requirements Validation Checklist"),
    (None, None, "Clarity"),
    ("c4-clarity-unambiguous", "c4-clarity", "Are the requirements clear and unambiguous?"),
    ("c4-clarity-concise", "c4-clarity", "Are the requirements concise and simple?"),
    ("c4-clarity-one-thought", "c4-clarity", "Do the requirements express only one thought"),
    ("c4-clarity-one-subject-predicate", "c4-clarity", "Does the requirement statement have one subject"),
    (None, None, "Completeness"),
    ("c4-completeness-tbd-tbr", "c4-completeness", "Are requirements stated as completely as possible?"),
    ("c4-completeness-missing", "c4-completeness", "Are any requirements missing?"),
    ("c4-completeness-assumptions", "c4-completeness", "Have all assumptions been explicitly stated?"),
    (None, None, "Compliance"),
    ("c4-compliance-level", "c4-compliance", "Are all requirements at the correct level"),
    ("c4-compliance-implementation", "c4-compliance", "Are requirements free of implementation specifics?"),
    ("c4-compliance-operations", "c4-compliance", "Are requirements free of descriptions of operations?"),
    ("c4-compliance-personnel", "c4-compliance", "Are requirements free of personnel or task assignments?"),
    (None, None, "Consistency"),
    ("c4-consistency-no-contradiction", "c4-consistency", "Are the requirements stated consistently"),
    ("c4-consistency-user-terminology", "c4-consistency", "Is the terminology consistent with the user"),
    ("c4-consistency-document-terminology", "c4-consistency", "Is the terminology consistently used throughout"),
    (None, None, "Traceability"),
    ("c4-traceability-needed", "c4-traceability", "Are all requirements needed?"),
    ("c4-traceability-bidirectional", "c4-traceability", "Are all requirements (functions, structures, and constraints)"),
    ("c4-traceability-unique-id", "c4-traceability", "Is each requirement stated in such a manner that it can be"),
    (None, None, "Correctness"),
    ("c4-correctness-correct", "c4-correctness", "Is each requirement correct?"),
    ("c4-correctness-assumptions", "c4-correctness", "Is each stated assumption correct?"),
    ("c4-correctness-feasible", "c4-correctness", "Are the requirements technically feasible?"),
    (None, None, "Functionality"),
    ("c4-functionality-sufficient", "c4-functionality", "Are all described functions necessary"),
    (None, None, "Performance"),
    ("c4-performance-margins", "c4-performance", "Are all required performance specifications and margins"),
    ("c4-performance-realistic", "c4-performance", "Is each performance requirement realistic?"),
    ("c4-performance-tolerances", "c4-performance", "Are the tolerances overly tight?"),
    (None, None, "Interfaces"),
    ("c4-interfaces-external", "c4-interfaces", "Are all external interfaces clearly defined?"),
    ("c4-interfaces-internal", "c4-interfaces", "Are all internal interfaces clearly defined?"),
    ("c4-interfaces-consistent", "c4-interfaces", "Are all interfaces necessary, sufficient, and consistent"),
    (None, None, "Maintainability"),
    ("c4-maintainability-measurable", "c4-maintainability", "Have the requirements for maintainability"),
    ("c4-maintainability-ripple", "c4-maintainability", "Are requirements written so that ripple effects"),
    (None, None, "Reliability"),
    ("c4-reliability-measurable", "c4-reliability", "Are clearly defined, measurable, and verifiable reliability"),
    ("c4-reliability-error-handling", "c4-reliability", "Are there error detection, reporting, handling"),
    ("c4-reliability-undesired-events", "c4-reliability", "Are undesired events"),
    ("c4-reliability-sequences", "c4-reliability", "Have assumptions about the intended sequence of functions"),
    ("c4-reliability-survivability", "c4-reliability", "Do these requirements adequately address the survivability"),
    (None, None, "Verifiability/Testability"),
    ("c4-verifiability-method", "c4-verifiability", "Can the system be tested, demonstrated, inspected, or analyzed"),
    ("c4-verifiability-measure", "c4-verifiability", "Does a means exist to measure the accomplishment"),
    ("c4-verifiability-precise", "c4-verifiability", "Are the requirements stated precisely to facilitate"),
    ("c4-verifiability-unverifiable-terms", "c4-verifiability", "Are the requirements free of unverifiable terms"),
    (None, None, "Data Usage"),
    ("c4-data-usage-dont-care", "c4-data-usage", "Where applicable, are \"don't care\" conditions truly"),
    (None, None, "Appendix D: Requirements Verification Matrix"),
]
APPC_GROUPS = [
    ("c1-terms", "C.1 Use of Correct Terms", "C.1 Use of Correct Terms"),
    ("c2-editorial", "C.2 Editorial Checklist", "C.2 Editorial Checklist"),
    ("c3-general-goodness", "C.3 General Goodness Checklist", "C.3 General Goodness Checklist"),
    ("c4-clarity", "C.4 Validation: Clarity", "Clarity"),
    ("c4-completeness", "C.4 Validation: Completeness", "Completeness"),
    ("c4-compliance", "C.4 Validation: Compliance", "Compliance"),
    ("c4-consistency", "C.4 Validation: Consistency", "Consistency"),
    ("c4-traceability", "C.4 Validation: Traceability", "Traceability"),
    ("c4-correctness", "C.4 Validation: Correctness", "Correctness"),
    ("c4-functionality", "C.4 Validation: Functionality", "Functionality"),
    ("c4-performance", "C.4 Validation: Performance", "Performance"),
    ("c4-interfaces", "C.4 Validation: Interfaces", "Interfaces"),
    ("c4-maintainability", "C.4 Validation: Maintainability", "Maintainability"),
    ("c4-reliability", "C.4 Validation: Reliability", "Reliability"),
    ("c4-verifiability", "C.4 Validation: Verifiability/Testability", "Verifiability/Testability"),
    ("c4-data-usage", "C.4 Validation: Data Usage", "Data Usage"),
]
EXPECTED_APPC_ITEMS = 61

UNVERIFIABLE_TERMS = ["flexible", "easy", "sufficient", "safe", "ad hoc", "adequate", "accommodate",
                      "user-friendly", "usable", "when required", "if required", "appropriate", "fast", "portable",
                      "light-weight", "small", "large", "maximize", "minimize", "sufficient", "robust", "quickly",
                      "easily", "clearly"]
AMBIGUOUS_TERMS = ["as appropriate", "etc.", "and/or", "but not limited to"]
INDEFINITE_PRONOUNS = ["this", "these"]

METADATA = [  # Table 4.2-2 (verbatim function text)
    ("md-requirement-id", "Requirement ID", "Provides a unique numbering system for sorting and tracking."),
    ("md-rationale", "Rationale", "Provides additional information to help clarify the intent of the requirements "
                                  "at the time they were written."),
    ("md-traced-from", "Traced from", "Captures the bidirectional traceability between parent requirements and "
                                      "lower level (derived) requirements and the relationships between requirements."),
    ("md-owner", "Owner", "Person or group responsible for writing, managing, and/or approving changes to this "
                          "requirement."),
    ("md-verification-method", "Verification method", "Captures the method of verification (test, inspection, "
                                                       "analysis, demonstration) and should be determined as the "
                                                       "requirements are developed."),
    ("md-verification-lead", "Verification lead", "Person or group assigned responsibility for verifying the "
                                                  "requirement."),
    ("md-verification-level", "Verification level", "Specifies the level in the hierarchy at which the requirements "
                                                     "will be verified (e.g., system, subsystem, element)."),
]
VERIFICATION_METHODS = [  # "Methods of Verification" box, first sentence verbatim
    ("vm-analysis", "Analysis", "The use of mathematical modeling and analytical techniques to predict the "
                                "suitability of a design to stakeholder expectations based on calculated data or data "
                                "derived from lower system structure end product verifications."),
    ("vm-demonstration", "Demonstration", "Showing that the use of an end product achieves the individual specified "
                                          "requirement."),
    ("vm-inspection", "Inspection", "The visual examination of a realized end product."),
    ("vm-test", "Test", "The use of an end product to obtain detailed data needed to verify performance or provide "
                        "sufficient information to verify performance through further analysis."),
]
VALIDATION_STEPS = [  # 4.2.1.2.4 (numbered 1-6 in the handbook although the lead-in says "five steps")
    ("vs-1", "Are the Requirements Written Correctly?", "Identify and correct requirements \"shall\" statement "
                                                        "format errors and editorial errors."),
    ("vs-2", "Are the Requirements Technically Correct?", "A few trained reviewers from the technical team identify "
                                                          "and remove as many technical errors as possible before "
                                                          "having all the relevant stakeholders review the "
                                                          "requirements."),
    ("vs-3", "Do the Requirements Satisfy Stakeholders?", "All relevant stakeholder groups identify and remove defects."),
    ("vs-4", "Are the Requirements Feasible?", "All requirements should make technical sense and be possible to achieve."),
    ("vs-5", "Are the Requirements Verifiable?", "All requirements should be stated in a fashion and with enough "
                                                 "information that it will be possible to verify the requirement after "
                                                 "the end product is implemented."),
    ("vs-6", "Are the Requirements Redundant or Over-specified?", "All requirements should be unique (not redundant to "
                                                                  "other requirements) and necessary to meet the "
                                                                  "required functions, performance, or behaviors."),
]


def build_checklist(doc: Doc) -> dict:
    first = doc.find("Appendix C: How to Write a Good Requirement - Checklist", 240, 260)
    last = doc.find("Appendix D: Requirements Verification Matrix", first, first + 6)
    text, marks = doc.span(first, last)
    low = text.lower()
    positions, cursor = [], 0
    for iid, grp, anchor in APPC_SEQ:
        k = normalise(anchor).lower()
        pos = low.find(k, cursor)
        assert pos >= 0, f"Appendix C anchor not found in order: {anchor!r}"
        positions.append((pos, iid, grp, anchor))
        cursor = pos + len(k)
    groups = []
    for gid, title, anchor in APPC_GROUPS:
        gpos = low.find(normalise(anchor).lower())
        groups.append({"id": gid, "title": title, "parent": "appendix-c",
                       "citation": cit(page_at(marks, gpos), "Appendix C")})
    groups.insert(0, {"id": "appendix-c", "title": "Appendix C: How to Write a Good Requirement - Checklist",
                      "parent": None, "citation": cit(first, "Appendix C")})
    items = []
    for n, (pos, iid, grp, anchor) in enumerate(positions):
        if iid is None:
            continue
        end = positions[n + 1][0]
        body = text[pos:end].strip()
        sec = grp.split("-")[0].upper().replace("C", "C.")
        items.append({"id": iid, "group": grp, "text": body, "citation": cit(page_at(marks, pos), f"Appendix {sec}")})
    assert len(items) == EXPECTED_APPC_ITEMS, len(items)
    verif = next(i for i in items if i["id"] == "c4-verifiability-unverifiable-terms")["text"].lower()
    for term in UNVERIFIABLE_TERMS:
        assert term in verif, term
    clar = next(i for i in items if i["id"] == "c4-clarity-unambiguous")["text"].lower()
    for term in AMBIGUOUS_TERMS + INDEFINITE_PRONOUNS:
        assert term in clar, term

    t422 = doc.find("Table 4.2-2 Requirements Metadata", 60, 100)
    groups.append({"id": "metadata", "title": "Table 4.2-2 Requirements Metadata", "parent": None,
                   "citation": cit(t422, "4.2.1.2.3")})
    for iid, title, fn in METADATA:
        doc.require(t422, title, fn[:60])
        items.append({"id": iid, "group": "metadata", "title": title, "text": fn, "citation": cit(t422, "4.2 (Table 4.2-2)")})
    box = doc.find("Methods of Verification", 115, 130)
    groups.append({"id": "verification-methods", "title": "Methods of Verification", "parent": None,
                   "citation": cit(box, "5.3")})
    for iid, title, desc in VERIFICATION_METHODS:
        doc.require(box, f"{title}: {desc}")
        items.append({"id": iid, "group": "verification-methods", "title": title, "text": desc,
                      "citation": cit(box, "5.3 (Methods of Verification box)")})
    vstart = doc.find("4.2.1.2.4 Validate Technical Requirements", 60, 100)
    groups.append({"id": "validation-steps", "title": "Validate Technical Requirements (4.2.1.2.4)", "parent": None,
                   "citation": cit(vstart, "4.2.1.2.4")})
    for iid, title, desc in VALIDATION_STEPS:
        page = doc.find(f"{title} {desc[:50]}", vstart, vstart + 1)
        items.append({"id": iid, "group": "validation-steps", "title": title, "text": desc,
                      "citation": cit(page, "4.2.1.2.4")})
    single_shall = doc.find("complete sentences with a single \"shall\" per statement", 60, 100)
    self_derived = doc.find("identified as self-derived and concurrence on it sought", 150, 170)
    gold = doc.find("the requirement is \"gold plating\" and should be eliminated", 150, 170)
    bidir = doc.find("Bidirectional traceability: The ability to trace any given requirement", 150, 170)
    vcrm = doc.find("Table D-1 Requirements Verification Matrix", 250, 260)
    vcrm_only_shall = doc.find("Only \"shall\" requirements should be included in these matrices", 250, 260)
    return {
        "catalog_id": "nasa-requirements-checklist",
        "source_id": SOURCE_ID,
        "title": "NASA SE Handbook: How to Write a Good Requirement (Appendix C) and requirement metadata",
        "edition": EDITION,
        "description": ("Appendix C 'How to Write a Good Requirement - Checklist' (C.1 terms, C.2 editorial, C.3 "
                        "general goodness, C.4 requirements validation checklist), Table 4.2-2 requirements "
                        "metadata, the four verification methods and the requirements validation steps of "
                        "4.2.1.2.4. Drives `python -m agentlib nasa-se lint-requirements` and `trace`."),
        "extraction": {
            "method": ("pdftotext -layout; Appendix C items sliced verbatim between ordered anchors (footers "
                       "removed, whitespace/quotes normalised); other items located by anchor "
                       "(scripts/extract/nasa_se.py)"),
            "date": EXTRACTION_DATE,
            "fidelity": "verbatim-normalised-whitespace",
            "notes": ("Item ids are catalog-assigned (the handbook does not number checklist items). Checkbox "
                      "glyphs are not rendered. Verification-method texts are the first sentence of each "
                      "definition. The handbook says 'five steps' for requirements validation but lists six; all six "
                      "are kept. 'Unverifiable' and 'ambiguous' term lists in parameters are verbatim from C.4."),
            "pages_reviewed": "79-85, 121-122, 163-168, 249-255",
        },
        "groups": groups,
        "items": items,
        "parameters": {
            "term_usage": {"shall": "requirement", "will": "facts or declaration of purpose", "should": "goal",
                           "citation": cit(first, "C.1")},
            "unverifiable_terms": sorted(set(UNVERIFIABLE_TERMS)),
            "unverifiable_patterns_note": "C.4 also lists 'other \"ly\" words, other \"ize\" words'.",
            "unverifiable_terms_citation": cit(page_at(marks, low.find("are the requirements free of unverifiable")),
                                               "C.4 Verifiability/Testability"),
            "ambiguous_terms": AMBIGUOUS_TERMS,
            "indefinite_pronouns": INDEFINITE_PRONOUNS,
            "ambiguous_terms_citation": cit(page_at(marks, low.find("are the requirements clear and unambiguous")),
                                            "C.4 Clarity"),
            "verification_methods": ["Test", "Analysis", "Inspection", "Demonstration"],
            "single_shall_citation": cit(single_shall, "4.2.1.2.3"),
            "bidirectional_traceability_definition": {
                "text": ("The ability to trace any given requirement/expectation to its parent requirement/"
                         "expectation and to its allocated children requirements/expectations."),
                "citation": cit(bidir, "6.2"),
            },
            "self_derived": {
                "text": ("Each requirement should trace to a parent/source in a baselined document or be identified "
                         "as self-derived with concurrence sought from the next higher level; a requirement with no "
                         "parent that is not an acceptable self-derived requirement indicates flawed traceability or "
                         "'gold plating'."),
                "citation": cit(self_derived, "6.2.1.2.3"),
                "gold_plating_citation": cit(gold, "6.2.1.2.3"),
            },
            "verification_matrix": {
                "title": "Table D-1 Requirements Verification Matrix",
                "columns": ["Requirement No.", "Document", "Paragraph", "Shall Statement",
                            "Verification Success Criteria", "Verification Method", "Facility or Lab", "Phase",
                            "Acceptance Requirement?", "Preflight Acceptance?", "Performing Organization", "Results"],
                "note": "Only 'shall' requirements should be included in verification matrices.",
                "citation": cit(vcrm, "Appendix D"),
                "only_shall_citation": cit(vcrm_only_shall, "Appendix D"),
            },
        },
    }


def build_all() -> dict[str, dict]:
    verify_pdf()
    doc = Doc(pdf_pages())
    doc.require(doc.find("Table D-1 Requirements Verification Matrix", 250, 260), "Verification", "Performing")
    return {
        "nasa-se-processes": build_processes(doc),
        "nasa-se-lifecycle": build_lifecycle(doc),
        "nasa-requirements-checklist": build_checklist(doc),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="fail if committed catalogs differ")
    args = ap.parse_args(argv)
    cats = build_all()
    rc = 0
    for cid, data in cats.items():
        path = CATALOG_DIR / f"{cid}.json"
        rendered = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        n = len(data["items"])
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != rendered:
                print(f"{path.relative_to(ROOT)} is stale; rerun scripts/extract/nasa_se.py", file=sys.stderr)
                rc = 1
            else:
                print(f"{path.relative_to(ROOT)} up to date ({n} items)")
        else:
            path.write_text(rendered, encoding="utf-8")
            print(f"wrote {path.relative_to(ROOT)} ({n} items)")
    return rc


if __name__ == "__main__":
    sys.exit(main())
