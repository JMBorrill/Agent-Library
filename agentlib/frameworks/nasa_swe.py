"""NPR 7150.2D / NASA-STD-8739.8B deterministic tools (``python -m agentlib nasa-swe ...``).

Catalogs: ``catalog/npr-7150-2d.json`` (SWE requirements, Appendix C applicability,
Appendix D classes) and ``catalog/nasa-std-8739-8b.json`` (SA/SS tasks per SWE,
safety-critical criteria, IV&V requirements, hazard cause areas), both produced by
``scripts/extract/nasa_swe.py`` from the pinned PDFs.

Sub-commands
------------
``classify``       candidate software class from Appendix D answers (deterministic)
``matrix``         Requirements Mapping Matrix skeleton for a class (md | csv | json)
``check-matrix``   validate a filled-in matrix (ids, coverage, status, evidence, tailoring)
``sa-tasks``       software assurance / safety tasks mapped to SWEs (and IV&V requirements)
``sc-assess``      safety-critical software determination against NASA-STD-8739.8B 4.2 a-e
``hazard-causes``  Appendix A Table 2 software cause checklist for hazard analysis
``show``           one SWE (or IV&V / SASS item) with applicability and SA tasks

Everything here supports, but never replaces, the decisions of the accountable
NASA authorities (project manager, Engineering/SMA/CIO Technical Authorities).
"""
from __future__ import annotations

import csv
import io
import json
import re
import sys
from functools import lru_cache
from pathlib import Path

import yaml

from agentlib.paths import load_catalog

NPR_CATALOG = "npr-7150-2d"
STD_CATALOG = "nasa-std-8739-8b"
NPR_SRC = "nasa-software-requirements"
STD_SRC = "nasa-software-assurance"
CLASSES = "ABCDEF"
ENGINEERING_CLASSES = "ABCDE"

STATUSES = ("Compliant", "Partially Compliant", "Non-Compliant", "Planned", "Tailored", "Not Applicable")
STATUS_ALIASES = {
    "compliant": "Compliant", "complies": "Compliant", "met": "Compliant", "yes": "Compliant",
    "partially compliant": "Partially Compliant", "partial": "Partially Compliant", "partially met": "Partially Compliant",
    "non-compliant": "Non-Compliant", "non compliant": "Non-Compliant", "noncompliant": "Non-Compliant",
    "not compliant": "Non-Compliant", "not met": "Non-Compliant", "no": "Non-Compliant",
    "planned": "Planned", "in progress": "Planned", "open": "Planned",
    "tailored": "Tailored", "waived": "Tailored", "waiver": "Tailored", "relief": "Tailored", "deviation": "Tailored",
    "not applicable": "Not Applicable", "n/a": "Not Applicable", "na": "Not Applicable", "not-applicable": "Not Applicable",
}
NEEDS_EVIDENCE = {"Compliant", "Partially Compliant"}
NEEDS_RATIONALE = {"Tailored", "Not Applicable", "Non-Compliant", "Partially Compliant"}

DISCLAIMER = (
    "Decision support only. The project manager classifies software (SWE-020) and maintains the Requirements "
    "Mapping Matrix (SWE-125); software engineering and software assurance Technical Authorities must agree on the "
    "classification, and tailoring of 'X' requirements needs approval of the Authority named in Appendix C "
    "(NPR 7150.2D 2.2.5). This tool does not grant compliance, approval or relief."
)

SWE_RE = re.compile(r"\bSWE[- ]?(\d{1,3})([a-d])?\b", re.I)
IVV_RE = re.compile(r"\b4\.4\.2\.(\d{1,3})\b")


class NasaSweError(ValueError):
    """Invalid user input (unknown id, malformed file, bad answers)."""


# ------------------------------------------------------------------ catalog access
@lru_cache(maxsize=1)
def npr() -> dict:
    return load_catalog(NPR_CATALOG)


@lru_cache(maxsize=1)
def std() -> dict:
    return load_catalog(STD_CATALOG)


@lru_cache(maxsize=1)
def swe_index() -> dict[str, dict]:
    return {it["id"]: it for it in npr()["items"]}


def normalise_swe(raw: str) -> str:
    """``swe-33`` / ``SWE 033`` / ``33`` -> ``SWE-033``. Raises NasaSweError if it is not a SWE id."""
    s = str(raw).strip()
    m = re.fullmatch(r"(?:SWE[- ]?)?0*(\d{1,3})([a-d])?", s, re.I)
    if not m:
        raise NasaSweError(f"not a SWE identifier: {raw!r}")
    return f"SWE-{int(m.group(1)):03d}"


def get_requirement(swe: str) -> dict:
    sid = normalise_swe(swe)
    try:
        return swe_index()[sid]
    except KeyError:
        raise NasaSweError(f"{sid} is not a requirement in NPR 7150.2D") from None


def normalise_class(raw: str) -> str:
    c = str(raw).strip().upper().removeprefix("CLASS").strip()
    if c not in CLASSES or len(c) != 1:
        raise NasaSweError(f"software class must be one of A-F, got {raw!r}")
    return c


def is_applicable(item: dict, cls: str) -> bool:
    app = item.get("applicability")
    return bool(app and app.get(cls) == "X")


def applicable_requirements(cls: str) -> list[dict]:
    cls = normalise_class(cls)
    return [it for it in npr()["items"] if is_applicable(it, cls)]


def sa_task_sets(swe: str | None = None) -> list[dict]:
    rows = [it for it in std()["items"] if it.get("kind") == "sa-task-set"]
    if swe:
        sid = normalise_swe(swe)
        rows = [r for r in rows if r["swe"] == sid]
    return rows


def ivv_requirements() -> list[dict]:
    return [it for it in std()["items"] if it.get("kind") == "ivv-requirement"]


def cite(source: str, locator: str, page: int) -> str:
    """Library citation syntax checked by ``agentlib evidence``: ``[src locator, p. N]``."""
    return f"[{source} {locator}, p. {page}]"


# ------------------------------------------------------------------ classification
def classification_questions() -> list[dict]:
    """Yes/no questions derived from Appendix D (scopes, criteria, exclusions) plus the safety-critical flag."""
    qs: list[dict] = []
    for cls, d in npr()["parameters"]["classes"].items():
        for sc in d.get("scopes", []):
            qs.append({"id": sc["id"], "class": cls, "kind": "scope", "text": sc["text"], "pdf_page": sc["pdf_page"]})
        for c in d["criteria"]:
            q = {"id": c["id"], "class": cls, "kind": "criterion", "text": c["text"], "pdf_page": c["pdf_page"]}
            if c.get("requires_scope"):
                q["requires_scope"] = c["requires_scope"]
            qs.append(q)
        for x in d["exclusions"]:
            qs.append({"id": x["id"], "class": cls, "kind": "exclusion", "text": x["text"], "pdf_page": x["pdf_page"]})
    qs.append({"id": "safety_critical", "class": "*", "kind": "flag", "pdf_page": 85,
               "text": ("The software is safety-critical (NASA-STD-8739.8B 4.2 criteria; see `nasa-swe sc-assess`). "
                        "Class E software cannot be safety-critical (Appendix D, Class E a.3).")})
    return qs


def _truthy(v) -> bool:
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    s = str(v).strip().lower()
    if s in ("y", "yes", "true", "1", "x"):
        return True
    if s in ("n", "no", "false", "0", "", "unknown", "?"):
        return False
    raise NasaSweError(f"answer must be yes/no, got {v!r}")


def classify(answers: dict) -> dict:
    """Walk Appendix D deterministically. ``answers`` maps question ids to yes/no."""
    qs = {q["id"]: q for q in classification_questions()}
    unknown = sorted(k for k in answers if k not in qs)
    if unknown:
        raise NasaSweError(f"unknown question id(s): {unknown}; run `nasa-swe classify --list-questions`")
    yes = {k for k, v in answers.items() if _truthy(v)}
    classes = npr()["parameters"]["classes"]
    considered = {}
    for cls in CLASSES:
        d = classes[cls]
        met, blocked_by_scope = [], []
        for c in d["criteria"]:
            if c["id"] not in yes:
                continue
            scope = c.get("requires_scope")
            if scope and scope not in yes:
                blocked_by_scope.append(c["id"])
                continue
            met.append(c)
        excl = [x for x in d["exclusions"] if x["id"] in yes]
        considered[cls] = {
            "criteria_met": [c["id"] for c in met],
            "criteria_needing_scope": blocked_by_scope,
            "exclusions": [x["id"] for x in excl],
            "matches": bool(met) and not excl,
            "_met": met, "_excl": excl,
        }
    safety_critical = "safety_critical" in yes
    rationale: list[str] = []
    candidate = next((c for c in ENGINEERING_CLASSES if considered[c]["matches"]), None)
    if candidate is None and considered["F"]["matches"]:
        candidate = "F"
    if candidate and candidate != "F":
        higher_rule = npr()["parameters"]["classification_rules"][0]
        others = [c for c in ENGINEERING_CLASSES if considered[c]["matches"] and c != candidate]
        if others:
            rationale.append(f"Classes {', '.join([candidate] + others)} all appear to apply; the higher class is assigned "
                             f"({higher_rule['text']} {cite(NPR_SRC, 'Appendix D D.2', higher_rule['pdf_page'])}).")
    if safety_critical and candidate in (None, "E"):
        prev = candidate
        candidate = "D"
        rationale.append("Software is declared safety-critical: Class E software cannot be safety-critical and "
                         "safety-critical software has to be classified as Class D or higher "
                         f"{cite(NPR_SRC, 'Appendix D Class E', 85)}. "
                         + ("Candidate raised from E to D; " if prev == "E" else "")
                         + "review the Class A-D definitions to confirm whether a higher class applies.")
    if safety_critical and candidate == "F":
        rationale.append("Class F software was declared safety-critical: confirm the classification with the "
                         "Engineering and SMA Technical Authorities (Class F defects 'may affect mission objectives or "
                         f"system safety') {cite(NPR_SRC, 'Appendix D Class F', 86)}.")
    if candidate and candidate != "F" and considered["F"]["matches"]:
        rationale.append("Class F (business/IT infrastructure) criterion also answered yes: separate systems/subsystems "
                         "can carry different classes; classify each one separately "
                         f"{cite(NPR_SRC, 'Appendix D D.1', 79)}.")
    for cls in CLASSES:
        info = considered[cls]
        for x in info["_excl"]:
            rationale.append(f"Class {cls} excluded by {x['id']}: \"{x['text']}\" {cite(NPR_SRC, f'Appendix D Class {cls}', x['pdf_page'])}")
        if info["criteria_needing_scope"]:
            rationale.append(f"Class {cls} criteria {info['criteria_needing_scope']} answered yes but the class scope "
                             f"question was not; they were not counted.")
    matched = []
    if candidate:
        for c in considered[candidate]["_met"]:
            matched.append({**c, "class": candidate,
                            "citation": cite(NPR_SRC, f"Appendix D Class {candidate}", c["pdf_page"])})
    if candidate is None:
        rationale.append("No Appendix D definition matched the answers; insufficient information to propose a class.")
    applicable = len(applicable_requirements(candidate)) if candidate else 0
    for v in considered.values():
        v.pop("_met"), v.pop("_excl")
    return {
        "candidate_class": candidate,
        "class_title": classes[candidate]["title"] if candidate else None,
        "safety_critical": safety_critical,
        "matched_criteria": matched,
        "considered": considered,
        "rationale": rationale,
        "applicable_requirements": applicable,
        "disclaimer": ("Candidate classification only. The project manager classifies each system and subsystem "
                       "(SWE-020); software engineering and software assurance Technical Authorities must agree on the "
                       "classification (Note to 3.5.1), and the NASA Chief Engineer is the ultimate TA for "
                       "classification disputes (Appendix D, D.2)."),
    }


def render_classification(result: dict, fmt: str = "md") -> str:
    if fmt == "json":
        return json.dumps(result, indent=2)
    c = result["candidate_class"]
    lines = ["# Software classification (candidate)", ""]
    if c:
        lines.append(f"Candidate class: **Class {c}** - {result['class_title']}")
    else:
        lines.append("Candidate class: **undetermined**")
    lines.append(f"Safety-critical declared: {'yes' if result['safety_critical'] else 'no'}")
    if c:
        lines.append(f"Applicable ('X') requirements in Appendix C for Class {c}: {result['applicable_requirements']}")
    lines += ["", "## Matched Appendix D criteria", ""]
    if result["matched_criteria"]:
        for m in result["matched_criteria"]:
            lines.append(f"- {m['id']}: {m['text']} {m['citation']}")
    else:
        lines.append("- none")
    if result["rationale"]:
        lines += ["", "## Rationale and flags", ""] + [f"- {r}" for r in result["rationale"]]
    lines += ["", "## Authority", "", result["disclaimer"], ""]
    return "\n".join(lines)


# ------------------------------------------------------------------ safety-critical assessment
def safety_criteria() -> list[dict]:
    return [it for it in std()["items"] if it.get("kind") == "safety-critical-criterion"]


def sc_assess(criteria_met: list[str] | dict) -> dict:
    """NASA-STD-8739.8B 4.2: safety-critical if at least one of criteria a-e is met."""
    if isinstance(criteria_met, dict):
        met = {str(k).strip().lower() for k, v in criteria_met.items() if _truthy(v)}
        given = {str(k).strip().lower() for k in criteria_met}
    else:
        met = {str(k).strip().lower() for k in criteria_met}
        given = set(met)
    letters = {c["criterion"] for c in safety_criteria()}
    bad = sorted(given - letters)
    if bad:
        raise NasaSweError(f"criteria must be among a-e (NASA-STD-8739.8B 4.2), got {bad}")
    crit = [c for c in safety_criteria() if c["criterion"] in met]
    sc = bool(crit)
    follow = []
    if sc:
        for it in npr()["items"]:
            if it.get("condition") in ("safety-critical", "safety-or-mission-critical") or it["id"] in ("SWE-205", "SWE-192", "SWE-184"):
                follow.append({"id": it["id"], "section": it["section"], "statement": it["statement"],
                               "citation": cite(NPR_SRC, it["id"], it["citation"]["pdf_page"])})
    return {
        "safety_critical": sc,
        "criteria_met": [{"criterion": c["criterion"], "text": c["text"],
                          "citation": cite(STD_SRC, f"4.2 {c['criterion']}", c["citation"]["pdf_page"])} for c in crit],
        "rule": std()["parameters"]["safety_critical_definition"]["rule"],
        "note": std()["parameters"]["safety_critical_definition"]["note"],
        "follow_on_requirements": follow,
        "disclaimer": ("The determination is made by the project manager in conjunction with the SMA organization "
                       "(SWE-205) and must be traceable to the hazard analysis (NASA-STD-8739.8B 4.2 Note)."),
    }


def render_sc(result: dict, fmt: str = "md") -> str:
    if fmt == "json":
        return json.dumps(result, indent=2)
    lines = ["# Software safety-criticality assessment", "",
             f"Safety-critical determination: **{'Yes' if result['safety_critical'] else 'No'}**", "",
             f"Rule: {result['rule']} {cite(STD_SRC, '4.2', 15)}", "", "## Criteria met", ""]
    lines += [f"- 4.2 {c['criterion']}. {c['text']} {c['citation']}" for c in result["criteria_met"]] or ["- none"]
    if result["follow_on_requirements"]:
        lines += ["", "## Safety-critical requirements triggered (NPR 7150.2D)", ""]
        lines += [f"- {f['id']} ({f['section']}): {f['statement']} {f['citation']}" for f in result["follow_on_requirements"]]
    lines += ["", "## Notes", "", f"- {result['note']}", f"- {result['disclaimer']}", ""]
    return "\n".join(lines)


# ------------------------------------------------------------------ requirements mapping matrix
MATRIX_COLUMNS = ["swe_id", "section", "requirement", "authority", "applicability", "condition",
                  "status", "tailoring_rationale", "approval", "evidence", "sa_tasks"]
CONDITION_TEXT = {
    "safety-critical": "applies if the project has safety-critical software (SWE-205 determination)",
    "safety-or-mission-critical": "applies if the project has safety-critical or mission-critical software",
    "ivv": "applies if software IV&V is required/performed (SWE-141)",
    "project-category": "applies to Category 1 / Category 2 (Class A or B payload risk) projects per NPR 7120.5",
    "class-a-or-b": "CMMI-DEV rating: ML3 for Class A, ML2 for Class B (exceptions per requirement)",
}


def build_matrix(cls: str, safety_critical: bool = False, ivv: bool = False) -> list[dict]:
    cls = normalise_class(cls)
    sa_counts: dict[str, int] = {}
    for r in sa_task_sets():
        sa_counts[r["swe"]] = sa_counts.get(r["swe"], 0) + len(r["tasks"])
    rows = []
    for it in applicable_requirements(cls):
        cond = it.get("condition")
        note = CONDITION_TEXT.get(cond, "")
        if cond in ("safety-critical", "safety-or-mission-critical") and safety_critical:
            note = "applies: safety-critical software declared"
        if cond == "ivv" and ivv:
            note = "applies: software IV&V required/performed"
        auth = it["applicability"]["authority"]
        if cls == "F":
            auth = it["applicability"]["class_f_authority"] or auth
        stmt = it["statement"] + (" (see list items in NPR)" if it.get("list_items") else "")
        rows.append({
            "swe_id": it["id"], "section": it["section"], "requirement": stmt, "authority": auth,
            "applicability": "X", "condition": note, "status": "", "tailoring_rationale": "", "approval": "",
            "evidence": "", "sa_tasks": sa_counts.get(it["id"], 0),
            "pdf_page": it["citation"]["pdf_page"], "appendix_c_page": it["applicability"]["citation"]["pdf_page"],
        })
    return rows


def _md_cell(v) -> str:
    return str(v).replace("|", "\\|").replace("\n", " ")


def render_matrix(rows: list[dict], cls: str, fmt: str = "md", safety_critical: bool = False, ivv: bool = False) -> str:
    cls = normalise_class(cls)
    if fmt == "json":
        return json.dumps({"framework": "NPR 7150.2D", "catalog": NPR_CATALOG, "class": cls,
                           "safety_critical": safety_critical, "ivv": ivv, "allowed_status": list(STATUSES),
                           "rows": rows}, indent=2)
    if fmt == "csv":
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=MATRIX_COLUMNS + ["pdf_page", "appendix_c_page"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
        return buf.getvalue()
    if fmt != "md":
        raise NasaSweError(f"unknown format {fmt!r}")
    legend = npr()["parameters"]["matrix_legend"]
    lines = [
        f"# Requirements Mapping Matrix - NPR 7150.2D, Class {cls}", "",
        f"Software class: {cls}  ",
        f"Safety-critical software: {'yes' if safety_critical else 'no / not yet determined'}  ",
        f"Software IV&V: {'yes' if ivv else 'no / not yet determined'}  ",
        f"Applicable ('X') requirements: {len(rows)} {cite(NPR_SRC, 'Appendix C', 56)}", "",
        f"Legend: X = {legend['X']} Blank = {legend['blank']}  ",
        f"Allowed status values: {', '.join(STATUSES)}.", "",
        "| SWE | Section | Requirement | Authority | Condition | Status | Tailoring / waiver rationale | Approval | Evidence |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append("| " + " | ".join(_md_cell(r[k]) for k in ("swe_id", "section", "requirement", "authority",
                                                                   "condition", "status", "tailoring_rationale",
                                                                   "approval", "evidence")) + " |")
    lines += ["", f"_{DISCLAIMER}_", ""]
    return "\n".join(lines)


# ------------------------------------------------------------------ matrix checking
COLUMN_ALIASES = {
    "swe_id": ("swe id", "swe", "swe #", "swe no", "id", "requirement id", "req id", "swe_id"),
    "status": ("status", "compliance", "compliance status", "implementation status"),
    "evidence": ("evidence", "objective evidence", "artifacts", "artefacts", "evidence reference"),
    "tailoring_rationale": ("tailoring rationale", "tailoring / waiver rationale", "tailoring/waiver", "tailoring",
                            "tailoring / waiver", "rationale", "justification", "waiver", "tailoring waiver rationale"),
    "approval": ("approval", "approved by", "ta approval", "authority approval", "approvals"),
}


def _norm_header(h: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9#/ ]+", " ", str(h).lower())).strip()


def _map_columns(headers: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    normed = {h: _norm_header(h) for h in headers}
    for canon, aliases in COLUMN_ALIASES.items():
        al = [_norm_header(a) for a in aliases]
        for h, n in normed.items():
            if n in al and h not in mapping.values():
                mapping[canon] = h
                break
    return mapping


def _clean_cell(v) -> str:
    """Strip whitespace and surrounding Markdown emphasis/code markers."""
    s = "" if v is None else str(v).strip()
    return re.sub(r"^[*`_]+|[*`_]+$", "", s).strip()


def _rows_from_table(headers: list[str], records: list[dict]) -> list[dict]:
    mapping = _map_columns(headers)
    if "swe_id" not in mapping:
        raise NasaSweError(f"no SWE id column found in headers {headers}")
    out = []
    for rec in records:
        row = {canon: _clean_cell(rec.get(src, "")) for canon, src in mapping.items()}
        for k in ("status", "evidence", "tailoring_rationale", "approval"):
            row.setdefault(k, "")
        out.append(row)
    return out


def parse_matrix_text(text: str, fmt: str) -> tuple[str | None, list[dict]]:
    """Return (class or None, rows) from json | csv | md | yaml text."""
    cls = None
    if fmt in ("json", "yaml", "yml"):
        try:
            data = json.loads(text) if fmt == "json" else yaml.safe_load(text)
        except (json.JSONDecodeError, yaml.YAMLError) as exc:
            raise NasaSweError(f"cannot parse {fmt}: {exc}") from exc
        if isinstance(data, dict):
            cls = data.get("class") or data.get("software_class")
            records = data.get("rows") or data.get("requirements") or []
        elif isinstance(data, list):
            records = data
        else:
            raise NasaSweError("matrix file must be a list of rows or an object with 'rows'")
        if not all(isinstance(r, dict) for r in records):
            raise NasaSweError("every matrix row must be an object")
        headers = sorted({k for r in records for k in r})
        return (str(cls) if cls else None), _rows_from_table(headers, records)
    if fmt == "csv":
        lines = [ln for ln in text.splitlines() if not ln.lstrip().startswith("#")]
        for ln in text.splitlines():
            m = re.match(r"\s*#\s*(?:software\s+)?class\s*[:=]\s*([A-Fa-f])\b", ln)
            if m:
                cls = m.group(1).upper()
        reader = csv.DictReader(io.StringIO("\n".join(lines)))
        if not reader.fieldnames:
            raise NasaSweError("CSV has no header row")
        return cls, _rows_from_table(list(reader.fieldnames), list(reader))
    if fmt == "md":
        m = re.search(r"^\s*(?:software\s+)?class\s*[:=]\s*\**\s*(?:class\s+)?([A-F])\b", text, re.I | re.M)
        if m:
            cls = m.group(1).upper()
        tables = _md_tables(text)
        for headers, records in tables:
            if "swe_id" in _map_columns(headers):
                return cls, _rows_from_table(headers, records)
        raise NasaSweError("no Markdown table with a SWE id column found")
    raise NasaSweError(f"unsupported matrix format {fmt!r} (use json, csv, md or yaml)")


def _split_md_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    return [c.replace("\\|", "|").strip() for c in re.split(r"(?<!\\)\|", s)]


def _md_tables(text: str) -> list[tuple[list[str], list[dict]]]:
    lines = text.splitlines()
    tables = []
    i = 0
    while i < len(lines) - 1:
        if lines[i].strip().startswith("|") and re.match(r"^\s*\|?\s*:?-{2,}", lines[i + 1]):
            headers = _split_md_row(lines[i])
            j = i + 2
            records = []
            while j < len(lines) and lines[j].strip().startswith("|"):
                cells = _split_md_row(lines[j])
                records.append({h: (cells[k] if k < len(cells) else "") for k, h in enumerate(headers)})
                j += 1
            tables.append((headers, records))
            i = j
        else:
            i += 1
    return tables


def load_matrix(path: Path) -> tuple[str | None, list[dict]]:
    path = Path(path)
    if not path.is_file():
        raise NasaSweError(f"file not found: {path}")
    ext = path.suffix.lower().lstrip(".")
    fmt = {"markdown": "md", "yml": "yaml"}.get(ext, ext)
    return parse_matrix_text(path.read_text(encoding="utf-8"), fmt)


def normalise_status(raw: str) -> str | None:
    s = re.sub(r"\s+", " ", str(raw or "").strip().lower())
    if not s:
        return None
    if s in STATUS_ALIASES:
        return STATUS_ALIASES[s]
    for st in STATUSES:
        if s == st.lower():
            return st
    return "INVALID"


def check_matrix(rows: list[dict], cls: str | None) -> dict:
    """Validate a filled-in Requirements Mapping Matrix. Returns findings and summary statistics."""
    findings: list[dict] = []

    def add(level: str, swe: str, msg: str) -> None:
        findings.append({"level": level, "swe": swe, "message": msg})

    if cls:
        cls = normalise_class(cls)
    else:
        add("warning", "-", "software class unknown (pass --class or include 'class'): coverage of applicable "
                            "requirements was not checked")
    index = swe_index()
    seen: dict[str, int] = {}
    statuses: dict[str, int] = {s: 0 for s in STATUSES}
    with_evidence = 0
    valid_rows = 0
    for n, row in enumerate(rows, 1):
        raw_id = row.get("swe_id", "")
        try:
            sid = normalise_swe(raw_id)
        except NasaSweError:
            add("error", str(raw_id) or f"row {n}", f"row {n}: '{raw_id}' is not a SWE identifier")
            continue
        if sid not in index:
            add("error", sid, f"unknown requirement id {sid}: not in NPR 7150.2D")
            continue
        seen[sid] = seen.get(sid, 0) + 1
        if seen[sid] == 2:
            add("error", sid, f"{sid} appears more than once")
        item = index[sid]
        if item.get("applicability") is None:
            add("warning", sid, f"{sid} is a Chapter 2 institutional requirement; Chapter 2 requirements are not part "
                                "of the Appendix C Requirements Mapping Matrix (NPR 7150.2D 1.3.1)")
        elif cls and not is_applicable(item, cls):
            add("info", sid, f"{sid} is blank (optional / not invoked) for Class {cls} in Appendix C")
        valid_rows += 1
        st = normalise_status(row.get("status", ""))
        evidence = (row.get("evidence") or "").strip()
        rationale = (row.get("tailoring_rationale") or "").strip()
        approval = (row.get("approval") or "").strip()
        if st is None:
            add("error", sid, f"{sid}: missing status (allowed: {', '.join(STATUSES)})")
            continue
        if st == "INVALID":
            add("error", sid, f"{sid}: invalid status '{row.get('status')}' (allowed: {', '.join(STATUSES)})")
            continue
        statuses[st] += 1
        if evidence:
            with_evidence += 1
        if st in NEEDS_EVIDENCE and not evidence:
            add("error", sid, f"{sid}: status '{st}' but no evidence recorded")
        if st in NEEDS_RATIONALE and not rationale:
            add("error", sid, f"{sid}: status '{st}' needs a tailoring/waiver rationale with risk evaluation "
                              "(NPR 7150.2D 2.2.5 Note; SWE-125 Note)")
        if st == "Tailored" and item.get("applicability"):
            authority = item["applicability"]["authority"]
            if not approval:
                add("warning", sid, f"{sid}: tailored but no approval recorded; relief from an 'X' requirement needs "
                                    f"the Appendix C Authority ({authority}) approval (NPR 7150.2D 2.2.5)")
            elif authority.startswith("HQ") and not re.search(r"\b(HQ|OCE|OSMA|OCIO|OCHMO)\b", approval):
                add("warning", sid, f"{sid}: Authority is {authority}; tailoring needs NASA HQ approval "
                                    "(NPR 7150.2D 2.1.8.2 b Note)")
            if item["section"].startswith("3.11.") and approval and not re.search(r"SAISO|CISO", approval, re.I):
                add("warning", sid, f"{sid}: cybersecurity (3.11) relief needs SAISO or Center CISO agreement "
                                    "(NPR 7150.2D 2.2.6)")
    missing: list[str] = []
    if cls:
        missing = [it["id"] for it in applicable_requirements(cls) if it["id"] not in seen]
        for sid in missing:
            add("error", sid, f"{sid} is marked 'X' for Class {cls} in Appendix C but is missing from the matrix")
    applicable_n = len(applicable_requirements(cls)) if cls else None
    addressed = sum(statuses.values())
    summary = {
        "class": cls,
        "rows": len(rows),
        "valid_rows": valid_rows,
        "applicable_requirements": applicable_n,
        "missing_applicable": len(missing),
        "status_counts": statuses,
        "rows_with_evidence": with_evidence,
        "evidence_coverage_pct": round(100 * with_evidence / addressed, 1) if addressed else 0.0,
        "compliant_pct_of_applicable": (round(100 * statuses["Compliant"] / applicable_n, 1) if applicable_n else None),
        "errors": sum(f["level"] == "error" for f in findings),
        "warnings": sum(f["level"] == "warning" for f in findings),
        "infos": sum(f["level"] == "info" for f in findings),
    }
    return {"summary": summary, "findings": findings, "disclaimer": DISCLAIMER}


def render_check(report: dict, fmt: str = "md") -> str:
    if fmt == "json":
        return json.dumps(report, indent=2)
    s = report["summary"]
    lines = ["# Requirements Mapping Matrix check", "",
             f"Class: {s['class'] or 'unknown'} | rows: {s['rows']} | applicable: {s['applicable_requirements']} | "
             f"missing applicable: {s['missing_applicable']}",
             f"Errors: {s['errors']} | warnings: {s['warnings']} | info: {s['infos']}",
             f"Evidence coverage: {s['evidence_coverage_pct']}% of rows with a status | Compliant: "
             f"{s['compliant_pct_of_applicable']}% of applicable", "",
             "| Status | Count |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in s["status_counts"].items()]
    lines += ["", "## Findings", ""]
    if not report["findings"]:
        lines.append("- none")
    for f in report["findings"]:
        lines.append(f"- {f['level'].upper()} {f['swe']}: {f['message']}")
    lines += ["", f"_{report['disclaimer']}_", ""]
    return "\n".join(lines)


# ------------------------------------------------------------------ rendering helpers
def render_sa_tasks(rows: list[dict], fmt: str = "md", safety_only: bool = False) -> str:
    if fmt == "json":
        return json.dumps(rows, indent=2)
    lines = ["# NASA-STD-8739.8B software assurance and software safety tasks", ""]
    for r in rows:
        npr_item = swe_index().get(r["swe"], {})
        label = r["swe"] + (r["swe_part"] or "")
        lines.append(f"## {label} ({r['npr_section']}) {cite(STD_SRC, 'Table 1 ' + label, r['citation']['pdf_page'])}")
        if npr_item:
            lines.append(f"NPR 7150.2D: {npr_item['statement']}")
        lines.append("")
        for t in r["tasks"]:
            if safety_only and t["n"] not in r["safety_related_tasks"]:
                continue
            flag = " [safety]" if t["n"] in r["safety_related_tasks"] else ""
            lines.append(f"{t['n']}. {t['text']}{flag}")
        lines.append("")
    return "\n".join(lines)


def render_ivv(fmt: str = "md") -> str:
    rows = ivv_requirements()
    if fmt == "json":
        return json.dumps(rows, indent=2)
    lines = ["# NASA-STD-8739.8B IV&V requirements (4.4.2)", ""]
    for r in rows:
        lines.append(f"- {r['id']} ({r['actor']}): {r['text']} {cite(STD_SRC, r['id'], r['citation']['pdf_page'])}")
    return "\n".join(lines) + "\n"


def show(ident: str, fmt: str = "md") -> str:
    ident = ident.strip()
    std_items = {it["id"]: it for it in std()["items"]}
    if ident in std_items:
        it = std_items[ident]
        if fmt == "json":
            return json.dumps(it, indent=2)
        out = [f"# {it['id']} (NASA-STD-8739.8B)", "", it["text"], "",
               f"Source: {cite(STD_SRC, it['id'], it['citation']['pdf_page'])}"]
        if it.get("notes"):
            out += ["", it["notes"]]
        return "\n".join(out) + "\n"
    item = get_requirement(ident)
    sas = sa_task_sets(item["id"])
    if fmt == "json":
        return json.dumps({"requirement": item, "sa_tasks": sas}, indent=2)
    out = [f"# {item['id']} - NPR 7150.2D {item['section']}", "", item["text"], "",
           f"Actor: {item['actor']}", f"Source: {cite(NPR_SRC, item['id'], item['citation']['pdf_page'])}"
           + (f" (pages {', '.join(map(str, item['pages']))})" if len(item["pages"]) > 1 else "")]
    app = item.get("applicability")
    if app:
        cls = " ".join(f"{c}:{app[c] or '-'}" for c in CLASSES)
        out.append(f"Appendix C applicability: {cls} | Authority: {app['authority']}"
                   f" | Class F Authority: {app['class_f_authority'] or '-'} "
                   f"{cite(NPR_SRC, 'Appendix C', app['citation']['pdf_page'])}")
    else:
        out.append(f"Appendix C applicability: none - {item.get('applicability_note', '')}")
    if item.get("condition"):
        out.append(f"Condition: {CONDITION_TEXT.get(item['condition'], item['condition'])}")
    if item.get("traceability_table"):
        out += ["", "Table 1 (bi-directional traceability by class):"]
        out += [f"- {r['trace']}: {', '.join(r['classes'])}" for r in item["traceability_table"]["rows"]]
    if item.get("notes"):
        out += ["", "Notes: " + item["notes"]]
    if sas:
        out += ["", "Software assurance / safety tasks (NASA-STD-8739.8B Table 1):"]
        for r in sas:
            for t in r["tasks"]:
                out.append(f"- {r['swe']}{r['swe_part'] or ''}.{t['n']}: {t['text']} "
                           f"{cite(STD_SRC, 'Table 1', r['citation']['pdf_page'])}")
    return "\n".join(out) + "\n"


def hazard_causes(area: str | None = None) -> list[dict]:
    rows = [it for it in std()["items"] if it.get("kind") == "hazard-cause-area"]
    if area:
        rows = [r for r in rows if area.lower() in r["title"].lower()]
    return rows


def render_hazard_causes(rows: list[dict], fmt: str = "md") -> str:
    if fmt == "json":
        return json.dumps(rows, indent=2)
    lines = ["# Software cause checklist for hazard analysis (NASA-STD-8739.8B Appendix A, Table 2)", ""]
    for r in rows:
        lines += [f"## {r['title']} {cite(STD_SRC, 'Table 2', r['citation']['pdf_page'])}", ""]
        lines += [f"- [ ] {c}" for c in r["causes"]]
        lines.append("")
    return "\n".join(lines)


# ------------------------------------------------------------------ graders (evals)
def _all_swe_mentions(output: str) -> list[str]:
    return [f"SWE-{int(m.group(1)):03d}" for m in SWE_RE.finditer(output)]


def grade_swe_ids_valid(output: str, check: dict) -> tuple[bool, str]:
    """All SWE ids mentioned exist in NPR 7150.2D; at least ``min`` distinct ids; optional ``required`` list."""
    ids = set(_all_swe_mentions(output))
    bad = sorted(i for i in ids if i not in swe_index())
    need = int(check.get("min", 1))
    required = {normalise_swe(r) for r in check.get("required", [])}
    missing = sorted(required - ids)
    ok = not bad and len(ids) >= need and not missing
    return ok, f"{len(ids)} distinct SWE ids (need {need}); unknown: {bad}; missing required: {missing}"


CANDIDATE_RE = re.compile(r"candidate\s+(?:software\s+)?class(?:ification)?\s*(?:is|:|=|-)?\s*\**\s*(?:class\s+)?([A-F])\b", re.I)


def grade_candidate_class(output: str, check: dict) -> tuple[bool, str]:
    """The first 'Candidate class: X' statement equals ``expected``."""
    m = CANDIDATE_RE.search(output)
    if not m:
        return False, "no 'Candidate class: <A-F>' statement found"
    got = m.group(1).upper()
    exp = normalise_class(check["expected"])
    return got == exp, f"candidate class {got} (expected {exp})"


def grade_matrix_coverage(output: str, check: dict) -> tuple[bool, str]:
    """A Markdown table lists the applicable SWEs for ``class`` (or the ``ids`` given) with valid statuses.

    ``min_fraction`` (default 1.0) of the required ids must appear in table rows; ``forbid`` ids must not.
    Status cells, when filled, must be allowed values.
    """
    req = [normalise_swe(i) for i in check.get("ids", [])] or [it["id"] for it in applicable_requirements(check["class"])]
    rows_ids: set[str] = set()
    bad_status: list[str] = []
    for headers, records in _md_tables(output):
        mapping = _map_columns(headers)
        if "swe_id" not in mapping:
            continue
        for rec in records:
            m = SWE_RE.search(rec.get(mapping["swe_id"], ""))
            if not m:
                continue
            rows_ids.add(f"SWE-{int(m.group(1)):03d}")
            if "status" in mapping:
                st = normalise_status(_clean_cell(rec.get(mapping["status"], "")))
                if st == "INVALID":
                    bad_status.append(rec.get(mapping["status"], ""))
    got = [i for i in req if i in rows_ids]
    frac = len(got) / len(req) if req else 0.0
    need = float(check.get("min_fraction", 1.0))
    forbid = [normalise_swe(i) for i in check.get("forbid", [])]
    forbidden = [i for i in forbid if i in rows_ids]
    unknown = sorted(i for i in rows_ids if i not in swe_index())
    ok = frac >= need and not forbidden and not unknown and not bad_status
    return ok, (f"{len(got)}/{len(req)} required SWE rows ({frac:.0%}, need {need:.0%}); forbidden present: "
                f"{forbidden}; unknown: {unknown}; invalid status values: {bad_status[:5]}")


SC_RE = re.compile(r"safety[- ]critical(?:ity)?(?:\s+software)?\s+determination\s*[:\-]?\s*\**\s*(yes|no)\b", re.I)


def grade_safety_critical_determination(output: str, check: dict) -> tuple[bool, str]:
    """'Safety-critical determination: Yes/No' equals ``expected``; ``criteria`` letters (4.2 a-e) are cited."""
    m = SC_RE.search(output)
    if not m:
        return False, "no 'Safety-critical determination: Yes|No' statement"
    got = m.group(1).lower() == "yes"
    exp = _truthy(check["expected"])
    cited = {c.lower() for c in re.findall(r"4\.2\s*\(?([a-e])\b", output)}
    need = {c.lower() for c in check.get("criteria", [])}
    missing = sorted(need - cited)
    return got == exp and not missing, f"determination {'yes' if got else 'no'} (expected {'yes' if exp else 'no'}); criteria cited {sorted(cited)}; missing {missing}"


def grade_ivv_refs_valid(output: str, check: dict) -> tuple[bool, str]:
    """Every 4.4.2.N reference exists (1..49); at least ``min`` distinct references."""
    refs = {int(n) for n in IVV_RE.findall(output)}
    valid = {int(r["id"].rsplit(".", 1)[1]) for r in ivv_requirements()}
    bad = sorted(r for r in refs if r not in valid)
    need = int(check.get("min", 1))
    return not bad and len(refs) >= need, f"{len(refs)} IV&V refs (need {need}); invalid: {['4.4.2.%d' % b for b in bad]}"


CITE_RE = re.compile(r"\[(nasa-software-requirements|nasa-software-assurance)\s+([^\],\[]+?),\s*p\.\s*(\d+)\]")


def grade_page_citations(output: str, check: dict) -> tuple[bool, str]:
    """Library citations of SWE / Table 1 / 4.4.2.N / 4.2 items point at the right PDF page (+-``tolerance``)."""
    tol = int(check.get("tolerance", 0))
    std_items = {it["id"]: it for it in std()["items"]}
    checked, wrong = 0, []
    for src, loc, page in CITE_RE.findall(output):
        page = int(page)
        allowed: set[int] = set()
        m = SWE_RE.search(loc)
        if src == NPR_SRC and m:
            it = swe_index().get(f"SWE-{int(m.group(1)):03d}")
            if it is None:
                wrong.append(f"{loc}: unknown")
                continue
            allowed = set(it["pages"]) | ({it["applicability"]["citation"]["pdf_page"]} if it.get("applicability") else set())
        elif src == STD_SRC and m:
            allowed = {p for r in sa_task_sets(f"SWE-{int(m.group(1)):03d}") for p in r["pages"]}
        elif src == STD_SRC and IVV_RE.search(loc):
            it = std_items.get(IVV_RE.search(loc).group(0))
            allowed = {it["citation"]["pdf_page"]} if it else set()
        elif src == STD_SRC and re.match(r"4\.2\b", loc.strip()):
            allowed = {15, 16}
        else:
            continue
        checked += 1
        if not any(abs(page - a) <= tol for a in allowed):
            wrong.append(f"{src} {loc} p.{page} (expected {sorted(allowed)})")
    need = int(check.get("min", 1))
    return not wrong and checked >= need, f"{checked} checkable citations (need {need}); wrong: {wrong[:5]}"


def grade_check_matrix_fixture(output: str, check: dict) -> tuple[bool, str]:
    """Output reports every error the tool finds in fixture ``fixture`` (paths relative to the eval suite)."""
    from agentlib.paths import repo_root

    path = repo_root() / check["fixture"]
    cls, rows = load_matrix(path)
    report = check_matrix(rows, check.get("class") or cls)
    expected = sorted({f["swe"] for f in report["findings"] if f["level"] == "error"} - {"-"})
    # missing applicable rows can be summarised as a count; individual ids for the rest must appear
    named = [s for s in expected if not any(f["swe"] == s and "missing from the matrix" in f["message"]
                                            for f in report["findings"])]
    missing_named = [s for s in named if s not in output and s.replace("SWE-", "SWE ") not in output]
    n_missing = report["summary"]["missing_applicable"]
    count_ok = n_missing == 0 or re.search(rf"\b{n_missing}\b", output) is not None
    return not missing_named and count_ok, (f"tool errors on {named}; not mentioned: {missing_named}; "
                                            f"missing-applicable count {n_missing} mentioned: {count_ok}")


# ------------------------------------------------------------------ CLI
def _emit(text: str, output: str | None) -> None:
    if output:
        Path(output).write_text(text, encoding="utf-8")
        print(f"wrote {output}", file=sys.stderr)
    else:
        sys.stdout.write(text if text.endswith("\n") else text + "\n")


def _load_answers(path: str) -> dict:
    p = Path(path)
    if not p.is_file():
        raise NasaSweError(f"answers file not found: {path}")
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise NasaSweError("answers file must be a mapping of question id -> yes/no")
    if "answers" in data and isinstance(data["answers"], dict):
        extra = {k: v for k, v in data.items() if k != "answers"}
        data = {**data["answers"], **extra}
    return data


def _cmd_classify(args) -> int:
    if args.list_questions:
        qs = classification_questions()
        if args.format == "json":
            print(json.dumps(qs, indent=2))
            return 0
        for q in qs:
            scope = f" [requires {q['requires_scope']}]" if q.get("requires_scope") else ""
            print(f"{q['id']:16} {q['kind']:9} p.{q['pdf_page']:<3} {q['text']}{scope}")
        return 0
    answers: dict = _load_answers(args.answers) if args.answers else {}
    for qid in args.yes or []:
        answers[qid] = True
    for qid in args.no or []:
        answers[qid] = False
    if args.safety_critical:
        answers["safety_critical"] = True
    if not answers:
        raise NasaSweError("no answers given: use --answers FILE, --yes ID (repeatable) or --list-questions")
    _emit(render_classification(classify(answers), args.format), args.output)
    return 0


def _cmd_matrix(args) -> int:
    rows = build_matrix(args.cls, args.safety_critical, args.ivv)
    _emit(render_matrix(rows, args.cls, args.format, args.safety_critical, args.ivv), args.output)
    return 0


def _cmd_check_matrix(args) -> int:
    cls, rows = load_matrix(Path(args.file))
    report = check_matrix(rows, args.cls or cls)
    _emit(render_check(report, args.format), args.output)
    return 1 if report["summary"]["errors"] else 0


def _cmd_sa_tasks(args) -> int:
    if args.ivv:
        _emit(render_ivv(args.format), args.output)
        return 0
    rows = sa_task_sets(args.swe)
    if args.swe and not rows:
        get_requirement(args.swe)  # raises if unknown
        raise NasaSweError(f"{normalise_swe(args.swe)} has no row in NASA-STD-8739.8B Table 1 "
                           "(Chapter 2 requirements are not mapped)")
    if args.cls:
        app = {it["id"] for it in applicable_requirements(args.cls)}
        rows = [r for r in rows if r["swe"] in app]
    if args.safety_only:
        rows = [r for r in rows if r["safety_related_tasks"]]
    _emit(render_sa_tasks(rows, args.format, args.safety_only), args.output)
    return 0


def _cmd_sc_assess(args) -> int:
    crit: list[str] | dict
    if args.answers:
        crit = _load_answers(args.answers)
    else:
        crit = [c.strip() for c in (args.criteria or "").split(",") if c.strip()]
    _emit(render_sc(sc_assess(crit), args.format), args.output)
    return 0


def _cmd_hazards(args) -> int:
    rows = hazard_causes(args.area)
    if not rows:
        raise NasaSweError(f"no hazard cause area matches {args.area!r}")
    _emit(render_hazard_causes(rows, args.format), args.output)
    return 0


def _cmd_show(args) -> int:
    _emit(show(args.id, args.format), args.output)
    return 0


def _wrap(fn):
    def run(args) -> int:
        try:
            return fn(args)
        except NasaSweError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    return run


def register(sub) -> None:
    p = sub.add_parser("nasa-swe", help="NPR 7150.2D / NASA-STD-8739.8B: classification, compliance matrix, SA tasks")
    ss = p.add_subparsers(dest="nasa_cmd", required=True)

    c = ss.add_parser("classify", help="candidate software class from Appendix D answers")
    c.add_argument("--answers", help="YAML mapping of question id -> yes/no (see --list-questions)")
    c.add_argument("--yes", action="append", metavar="ID", help="answer yes to a question id (repeatable)")
    c.add_argument("--no", action="append", metavar="ID", help="answer no to a question id (repeatable)")
    c.add_argument("--safety-critical", action="store_true", help="the software is safety-critical")
    c.add_argument("--list-questions", action="store_true", help="list question ids from Appendix D")
    c.add_argument("--format", choices=["md", "json"], default="md")
    c.add_argument("-o", "--output")
    c.set_defaults(func=_wrap(_cmd_classify))

    m = ss.add_parser("matrix", help="Requirements Mapping Matrix skeleton for a software class")
    m.add_argument("--class", dest="cls", required=True, help="software class A-F")
    m.add_argument("--safety-critical", action="store_true", help="project has safety-critical software")
    m.add_argument("--ivv", action="store_true", help="software IV&V is required/performed")
    m.add_argument("--format", choices=["md", "csv", "json"], default="md")
    m.add_argument("-o", "--output")
    m.set_defaults(func=_wrap(_cmd_matrix))

    k = ss.add_parser("check-matrix", help="validate a filled-in matrix (.csv, .json, .md, .yaml)")
    k.add_argument("file")
    k.add_argument("--class", dest="cls", help="software class A-F (overrides the file)")
    k.add_argument("--format", choices=["md", "json"], default="md")
    k.add_argument("-o", "--output")
    k.set_defaults(func=_wrap(_cmd_check_matrix))

    s = ss.add_parser("sa-tasks", help="software assurance / safety tasks mapped to SWE requirements")
    s.add_argument("--swe", help="only this requirement, e.g. SWE-134")
    s.add_argument("--class", dest="cls", help="only requirements applicable ('X') to this class")
    s.add_argument("--safety-only", action="store_true", help="only tasks that mention safety/hazards")
    s.add_argument("--ivv", action="store_true", help="list the IV&V requirements (4.4.2.x) instead")
    s.add_argument("--format", choices=["md", "json"], default="md")
    s.add_argument("-o", "--output")
    s.set_defaults(func=_wrap(_cmd_sa_tasks))

    a = ss.add_parser("sc-assess", help="safety-critical determination against NASA-STD-8739.8B 4.2 a-e")
    a.add_argument("--criteria", help="comma-separated criteria met, e.g. 'a,b' (empty = none)")
    a.add_argument("--answers", help="YAML mapping a..e -> yes/no")
    a.add_argument("--format", choices=["md", "json"], default="md")
    a.add_argument("-o", "--output")
    a.set_defaults(func=_wrap(_cmd_sc_assess))

    h = ss.add_parser("hazard-causes", help="Appendix A Table 2 software cause checklist")
    h.add_argument("--area", help="filter by cause area (substring)")
    h.add_argument("--format", choices=["md", "json"], default="md")
    h.add_argument("-o", "--output")
    h.set_defaults(func=_wrap(_cmd_hazards))

    w = ss.add_parser("show", help="show one SWE (or 4.4.2.x / SASS-01) with applicability and SA tasks")
    w.add_argument("id")
    w.add_argument("--format", choices=["md", "json"], default="md")
    w.add_argument("-o", "--output")
    w.set_defaults(func=_wrap(_cmd_show))
