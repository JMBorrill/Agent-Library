"""NIST SP 800-218 Secure Software Development Framework (SSDF) 1.1 tools.

Deterministic helpers over ``catalog/nist-ssdf.json`` (extracted from the pinned
PDF by ``scripts/extract/ssdf.py``):

* ``ssdf list [--group PW] [--all]``              practices and tasks
* ``ssdf show <id>``                               a group, practice or task with examples/references
* ``ssdf assessment-template [--format md|csv|yaml]`` gap-assessment worksheet for every active task
* ``ssdf check-assessment <file>``                 validate + score a filled worksheet, prioritised gaps
* ``ssdf evidence-matrix <file>``                  attestation-style evidence matrix (Markdown)
* ``ssdf map-pipeline <file>``                     which tasks a CI/CD pipeline description supports
* ``ssdf pipeline-controls``                       the documented control vocabulary and mapping rules

Important caveats encoded in the outputs:

* SSDF practices are "not prioritized" and "not ... a checklist" (SP 800-218 p.12, printed p.3).
  Any prioritisation here is a transparent tool heuristic, not NIST guidance.
* A pipeline control *supporting* a task is not evidence that the task is implemented
  (support != compliance). Mapping rules cite the notional implementation example they rely on
  (``basis: example``) or are marked ``interpretive``.

Grader functions (``grade_*``) are provided for evaluation suites.
"""
from __future__ import annotations

import csv
import io
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from functools import lru_cache
from pathlib import Path

import yaml

from agentlib.paths import load_catalog, repo_root

CATALOG_ID = "nist-ssdf"
STATUSES = ("implemented", "partial", "planned", "not-implemented", "not-applicable")
STATUS_ALIASES = {
    "n/a": "not-applicable", "na": "not-applicable", "not applicable": "not-applicable",
    "not implemented": "not-implemented", "not_implemented": "not-implemented",
    "partially implemented": "partial", "partially-implemented": "partial",
    "not_applicable": "not-applicable", "done": "implemented",
}
STATUS_CREDIT = {"implemented": 1.0, "partial": 0.5, "planned": 0.0, "not-implemented": 0.0}
TEMPLATE_COLUMNS = ["group", "practice", "id", "task", "status", "evidence", "owner", "target_date",
                    "justification", "notes"]
TASK_ID_RE = re.compile(r"\b(PO|PS|PW|RV)\.(\d{1,2})\.(\d{1,2})\b")
PRACTICE_ID_RE = re.compile(r"\b(PO|PS|PW|RV)\.(\d{1,2})\b(?!\.\d)")
DISCLAIMER = (
    "Self-assessment aid generated from NIST SP 800-218 (SSDF v1.1). It supports, but does not replace, "
    "qualified professional judgement, independent assessment or a formal attestation."
)


# --------------------------------------------------------------------------- catalog access
@lru_cache(maxsize=1)
def _catalog_cached(root: str) -> dict:
    return load_catalog(CATALOG_ID, Path(root))


def catalog() -> dict:
    return _catalog_cached(str(repo_root()))


def items_by_id() -> dict[str, dict]:
    return {i["id"]: i for i in catalog()["items"]}


def groups() -> list[dict]:
    return catalog()["groups"]


def practices(active_only: bool = True) -> list[dict]:
    return [i for i in catalog()["items"] if i["kind"] == "practice" and (i["status"] == "active" or not active_only)]


def tasks(active_only: bool = True, group: str | None = None) -> list[dict]:
    out = [i for i in catalog()["items"] if i["kind"] == "task" and (i["status"] == "active" or not active_only)]
    if group:
        out = [t for t in out if t["group"] == group.upper()]
    return out


def active_task_ids() -> list[str]:
    return [t["id"] for t in tasks()]


def eo_mapping() -> dict:
    return catalog()["parameters"]["eo14028_4e_mapping"]["mapping"]


@lru_cache(maxsize=1)
def _eo_by_task_cached(root: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for sub, ids in eo_mapping().items():
        if isinstance(ids, list):
            for tid in ids:
                out.setdefault(tid, []).append(sub)
    return out


def eo_subsections(task_id: str) -> list[str]:
    """EO 14028 Section 4e subsections that Appendix A Table 2 maps to this task (excludes 4e(ix),
    which the table maps to 'All practices and tasks consistent with a risk-based approach')."""
    return _eo_by_task_cached(str(repo_root())).get(task_id, [])


def page_ref(item: dict) -> str:
    c = item["citation"]
    return f"PDF p.{c['pdf_page']} (printed p.{c.get('printed_page', '?')})"


class SSDFError(ValueError):
    """Input error reported to the CLI user."""


def get(item_id: str) -> dict:
    key = item_id.strip().upper()
    by = items_by_id()
    if key in by:
        return by[key]
    for g in groups():
        if g["id"] == key:
            return {**g, "kind": "group"}
    raise SSDFError(f"unknown SSDF id '{item_id}' (expected a group like PW, a practice like PW.4 or a task like PW.4.1)")


# --------------------------------------------------------------------------- show / list
def render_item(item: dict) -> str:
    lines: list[str] = []
    if item["kind"] == "group":
        lines.append(f"# {item['id']} - {item['title']}")
        lines.append("")
        lines.append(item["text"])
        lines.append("")
        lines.append(f"Source: NIST SP 800-218 Section 2, {page_ref(item)}")
        lines.append("")
        lines.append("Practices:")
        for p in practices():
            if p["group"] == item["id"]:
                n = sum(1 for t in tasks() if t["practice"] == p["id"])
                lines.append(f"- {p['id']} {p['title']} ({n} task{'' if n == 1 else 's'})")
        return "\n".join(lines)
    if item["kind"] == "practice":
        lines.append(f"# {item['id']} - {item['title']}")
        lines.append("")
        lines.append(item["text"])
        if item["status"] != "active":
            lines.append("")
            lines.append(f"Status: RETIRED identifier in SSDF 1.1 (moved to {', '.join(item.get('moved_to', []))}).")
        lines.append("")
        lines.append(f"Source: NIST SP 800-218 Table 1, {page_ref(item)}")
        ts = [t for t in tasks(active_only=False) if t["practice"] == item["id"]]
        if ts:
            lines.append("")
            lines.append("Tasks:")
            for t in ts:
                flag = " [retired]" if t["status"] != "active" else ""
                lines.append(f"- {t['id']}{flag}: {t['text']}")
        return "\n".join(lines)
    # task
    p = items_by_id()[item["practice"]]
    lines.append(f"# {item['id']} ({p['id']} {p['title']})")
    lines.append("")
    lines.append(item["text"])
    if item["status"] != "active":
        lines.append("")
        lines.append(f"Status: RETIRED identifier in SSDF 1.1 - see {', '.join(item.get('moved_to', []))}.")
    lines.append("")
    cont = ""
    if item.get("pdf_pages"):
        cont = f"; row continues to PDF p.{max(item['pdf_pages'])}"
    lines.append(f"Source: NIST SP 800-218 Table 1, {page_ref(item)}{cont}")
    if item.get("examples"):
        lines.append("")
        lines.append("Notional implementation examples (not required; not exhaustive):")
        for n, ex in enumerate(item["examples"], 1):
            lines.append(f"  {n}. {ex}")
    if item.get("references"):
        lines.append("")
        lines.append("Informative references:")
        for r in item["references"]:
            lines.append(f"  - {r['ref']}: {r['text']}")
    eo = eo_subsections(item["id"])
    if eo:
        lines.append("")
        lines.append(f"EO 14028 Section 4e subsections mapped in Appendix A Table 2 (PDF p.33): {', '.join(eo)}")
    return "\n".join(lines)


def list_items(group: str | None = None, include_retired: bool = False) -> list[dict]:
    if group and group.upper() not in {g["id"] for g in groups()}:
        raise SSDFError(f"unknown group '{group}' (use PO, PS, PW or RV)")
    out = []
    for i in catalog()["items"]:
        if group and i["group"] != group.upper():
            continue
        if i["status"] != "active" and not include_retired:
            continue
        out.append(i)
    return out


# --------------------------------------------------------------------------- assessment template
def template_rows() -> list[dict]:
    rows = []
    for t in tasks():
        rows.append({"group": t["group"], "practice": t["practice"], "id": t["id"], "task": t["text"],
                     "status": "", "evidence": "", "owner": "", "target_date": "", "justification": "", "notes": ""})
    return rows


def _md_cell(value) -> str:
    if isinstance(value, list):
        value = "; ".join(str(v) for v in value)
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")


def assessment_template(fmt: str = "md") -> str:
    rows = template_rows()
    if fmt == "csv":
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=TEMPLATE_COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
        return buf.getvalue()
    if fmt == "yaml":
        doc = {
            "assessment": {"organisation": "", "scope": "", "assessor": "", "date": "",
                           "framework": "NIST SP 800-218 SSDF v1.1",
                           "status_values": list(STATUSES)},
            "tasks": [{"id": r["id"], "practice": r["practice"], "task": r["task"], "status": "", "evidence": [],
                       "owner": "", "target_date": "", "justification": "", "notes": ""} for r in rows],
        }
        header = ("# SSDF v1.1 gap assessment worksheet (NIST SP 800-218, Table 1, PDF pp.14-28).\n"
                  "# status: implemented | partial | planned | not-implemented | not-applicable\n"
                  "# implemented/partial need evidence; not-applicable needs a justification;\n"
                  "# planned should have an owner and target_date (YYYY-MM-DD).\n"
                  "# Validate with: python -m agentlib ssdf check-assessment <this file>\n")
        return header + yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=1000)
    if fmt != "md":
        raise SSDFError(f"unknown format '{fmt}' (md, csv or yaml)")
    out = ["# SSDF v1.1 gap assessment worksheet", "",
           "Source: NIST SP 800-218, Secure Software Development Framework (SSDF) Version 1.1, Table 1 "
           "(PDF pp.14-28). 42 tasks in 19 practices.", "",
           "| Field | Value |", "|---|---|", "| Organisation | |", "| Scope (products / teams) | |",
           "| Assessor | |", "| Date | |", "",
           "Status values: `implemented`, `partial`, `planned`, `not-implemented`, `not-applicable`. "
           "Implemented/partial rows need evidence; not-applicable rows need a justification; planned rows "
           "should name an owner and a target date (YYYY-MM-DD).", ""]
    cur = None
    for r in rows:
        if r["group"] != cur:
            cur = r["group"]
            g = next(g for g in groups() if g["id"] == cur)
            out += ["", f"## {g['id']} - {g['title']}", "",
                    "| " + " | ".join(TEMPLATE_COLUMNS[1:]) + " |",
                    "|" + "---|" * (len(TEMPLATE_COLUMNS) - 1)]
        out.append("| " + " | ".join(_md_cell(r[c]) for c in TEMPLATE_COLUMNS[1:]) + " |")
    out += ["", DISCLAIMER, ""]
    return "\n".join(out)


# --------------------------------------------------------------------------- assessment loading
def _norm_key(k: str) -> str:
    k = str(k).strip().lower().replace(" ", "_").replace("-", "_")
    return {"task_id": "id", "ssdf_id": "id", "task_text": "task", "target": "target_date",
            "due": "target_date", "due_date": "target_date", "justification_for_n/a": "justification",
            "rationale": "justification"}.get(k, k)


def _parse_md_tables(text: str) -> list[dict]:
    rows: list[dict] = []
    header: list[str] | None = None
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            header = None
            continue
        cells = [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", s.strip("|"))]
        if header is None:
            keys = [_norm_key(c) for c in cells]
            if "id" in keys and "status" in keys:
                header = keys
            continue
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        rows.append(dict(zip(header, cells)))
    return rows


def load_assessment(path: str | Path) -> tuple[dict, list[dict]]:
    """Load a filled worksheet (YAML, JSON, CSV or Markdown table). Returns (metadata, rows)."""
    p = Path(path)
    if not p.is_file():
        raise SSDFError(f"assessment file not found: {p}")
    text = p.read_text(encoding="utf-8")
    suffix = p.suffix.lower()
    meta: dict = {}
    if suffix in (".yaml", ".yml", ".json"):
        try:
            data = json.loads(text) if suffix == ".json" else yaml.safe_load(text)
        except (yaml.YAMLError, json.JSONDecodeError) as exc:
            raise SSDFError(f"cannot parse {p.name}: {exc}") from exc
        if isinstance(data, list):
            raw = data
        elif isinstance(data, dict):
            meta = data.get("assessment") or {}
            raw = data.get("tasks")
            if raw is None:
                raise SSDFError(f"{p.name}: expected a 'tasks' list")
        else:
            raise SSDFError(f"{p.name}: expected a mapping with 'tasks' or a list of rows")
        if not isinstance(raw, list) or not all(isinstance(r, dict) for r in raw):
            raise SSDFError(f"{p.name}: 'tasks' must be a list of mappings")
    elif suffix == ".csv":
        raw = list(csv.DictReader(io.StringIO(text)))
    elif suffix in (".md", ".markdown"):
        raw = _parse_md_tables(text)
        if not raw:
            raise SSDFError(f"{p.name}: no Markdown table with 'id' and 'status' columns found")
    else:
        raise SSDFError(f"unsupported assessment format '{suffix}' (use .yaml, .json, .csv or .md)")
    rows = []
    for r in raw:
        row = {_norm_key(k): v for k, v in r.items() if k is not None}
        rows.append(row)
    return meta if isinstance(meta, dict) else {}, rows


def _evidence_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    s = str(value).strip()
    if not s or s.lower() in {"-", "none", "n/a", "tbd", "todo"}:
        return []
    return [x.strip() for x in re.split(r";|\n", s) if x.strip()]


def normalise_status(value) -> str:
    s = str(value or "").strip().lower()
    s = STATUS_ALIASES.get(s, s).replace("_", "-").replace(" ", "-")
    return s


# --------------------------------------------------------------------------- assessment checking
@dataclass
class Finding:
    level: str  # error | warning
    id: str
    message: str


@dataclass
class AssessmentResult:
    meta: dict
    rows: dict[str, dict]
    findings: list[Finding] = field(default_factory=list)
    scores: dict = field(default_factory=dict)
    gaps: list[dict] = field(default_factory=list)

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "error"]

    def to_dict(self) -> dict:
        return {"meta": self.meta, "valid": not self.errors,
                "findings": [f.__dict__ for f in self.findings], "scores": self.scores, "gaps": self.gaps}


def _pct(num: float, den: int) -> float | None:
    return round(100.0 * num / den, 1) if den else None


def check_assessment(meta: dict, raw_rows: list[dict], today: date | None = None) -> AssessmentResult:
    by = items_by_id()
    active = active_task_ids()
    res = AssessmentResult(meta=meta, rows={})
    seen: set[str] = set()
    for n, r in enumerate(raw_rows, 1):
        rid = str(r.get("id") or "").strip().upper()
        if not rid:
            res.findings.append(Finding("error", f"row {n}", "row has no task id"))
            continue
        if rid not in by or by[rid]["kind"] != "task":
            res.findings.append(Finding("error", rid, "unknown SSDF v1.1 task id"))
            continue
        if by[rid]["status"] != "active":
            res.findings.append(Finding("error", rid, f"retired identifier in SSDF v1.1; assess "
                                                     f"{', '.join(by[rid].get('moved_to', []))} instead"))
            continue
        if rid in seen:
            res.findings.append(Finding("error", rid, "duplicate row for this task"))
            continue
        seen.add(rid)
        status = normalise_status(r.get("status"))
        evidence = _evidence_list(r.get("evidence"))
        row = {"id": rid, "status": status, "evidence": evidence,
               "owner": str(r.get("owner") or "").strip(),
               "target_date": str(r.get("target_date") or "").strip(),
               "justification": str(r.get("justification") or "").strip(),
               "notes": str(r.get("notes") or "").strip()}
        if not status:
            res.findings.append(Finding("error", rid, "status is empty (task not assessed)"))
            row["status"] = "unassessed"
        elif status not in STATUSES:
            res.findings.append(Finding("error", rid, f"invalid status '{r.get('status')}' (allowed: {', '.join(STATUSES)})"))
            row["status"] = "unassessed"
        st = row["status"]
        if st == "implemented" and not evidence:
            res.findings.append(Finding("error", rid, "status 'implemented' without evidence"))
        if st == "partial" and not evidence:
            res.findings.append(Finding("warning", rid, "status 'partial' without evidence of what is in place"))
        if st == "not-applicable" and not row["justification"]:
            res.findings.append(Finding("error", rid, "status 'not-applicable' without justification"))
        if st in ("planned", "not-implemented", "partial"):
            if st == "planned" and not row["owner"]:
                res.findings.append(Finding("warning", rid, "planned without an owner"))
            if st == "planned" and not row["target_date"]:
                res.findings.append(Finding("warning", rid, "planned without a target_date"))
        # conservative scoring: unevidenced claims and unjustified exclusions earn no credit
        row["score_status"] = st
        if st == "implemented" and not evidence:
            row["score_status"] = "unevidenced"
        if st == "not-applicable" and not row["justification"]:
            row["score_status"] = "unassessed"
        if row["target_date"]:
            try:
                d = date.fromisoformat(row["target_date"])
                if today and d < today and st in ("planned", "partial", "not-implemented"):
                    res.findings.append(Finding("warning", rid, f"target_date {d} is in the past"))
            except ValueError:
                res.findings.append(Finding("warning", rid, f"target_date '{row['target_date']}' is not YYYY-MM-DD"))
        res.rows[rid] = row
    for tid in active:
        if tid not in res.rows:
            res.findings.append(Finding("error", tid, "task missing from assessment"))
            res.rows[tid] = {"id": tid, "status": "unassessed", "score_status": "unassessed", "evidence": [],
                             "owner": "", "target_date": "", "justification": "", "notes": ""}
    res.scores = score(res.rows)
    res.gaps = prioritise_gaps(res.rows)
    order = {t: n for n, t in enumerate(active)}
    res.findings.sort(key=lambda f: (0 if f.level == "error" else 1, order.get(f.id, 999), f.id))
    return res


def _score_bucket(rows: list[dict]) -> dict:
    counts = {s: 0 for s in STATUSES + ("unevidenced", "unassessed")}
    for r in rows:
        counts[r["score_status"]] = counts.get(r["score_status"], 0) + 1
    applicable = len(rows) - counts["not-applicable"]
    credit = sum(STATUS_CREDIT.get(r["score_status"], 0.0) for r in rows)
    return {"tasks": len(rows), "applicable": applicable, "counts": counts,
            "coverage_pct": _pct(credit, applicable), "implemented_pct": _pct(counts["implemented"], applicable)}


def score(rows: dict[str, dict]) -> dict:
    """Coverage % = (implemented + 0.5 x partial) / applicable tasks. Unassessed counts as 0."""
    all_rows = [rows[t] for t in active_task_ids()]
    out = {"method": "coverage = (implemented + 0.5*partial) / (tasks - not-applicable); unassessed/invalid "
                     "rows, implemented-without-evidence and not-applicable-without-justification score 0",
           "overall": _score_bucket(all_rows), "groups": {}, "practices": {}}
    for g in groups():
        out["groups"][g["id"]] = _score_bucket([rows[t["id"]] for t in tasks(group=g["id"])])
    for p in practices():
        out["practices"][p["id"]] = _score_bucket([rows[t["id"]] for t in tasks() if t["practice"] == p["id"]])
    return out


STATUS_WEIGHT = {"unassessed": 3, "not-implemented": 3, "unevidenced": 2, "planned": 2, "partial": 1}


def prioritise_gaps(rows: dict[str, dict]) -> list[dict]:
    """Order gaps with a transparent heuristic (SSDF itself does not prioritise practices, p.12):
    1) status severity (unassessed/not-implemented > planned > partial);
    2) number of EO 14028 Section 4e subsections mapped to the task in Appendix A Table 2;
    3) document order.
    Tier: High = unassessed/not-implemented and EO-mapped; Medium = other unassessed/not-implemented,
    or planned lacking owner/target date, or implemented without evidence; Low = partial, or planned with
    owner and target date. Statuses here are scoring statuses (see ``check_assessment``)."""
    by = items_by_id()
    order = {t: n for n, t in enumerate(active_task_ids())}
    gaps = []
    for tid, r in rows.items():
        st = r["score_status"]
        if st not in STATUS_WEIGHT:
            continue
        eo = eo_subsections(tid)
        if st in ("unassessed", "not-implemented"):
            tier = "High" if eo else "Medium"
        elif st == "unevidenced":
            tier = "Medium"
        elif st == "planned":
            tier = "Low" if (r["owner"] and r["target_date"]) else "Medium"
        else:
            tier = "Low"
        gaps.append({"id": tid, "practice": by[tid]["practice"], "status": st, "tier": tier,
                     "eo14028_4e": eo, "owner": r["owner"], "target_date": r["target_date"],
                     "task": by[tid]["text"], "pdf_page": by[tid]["citation"]["pdf_page"]})
    tier_rank = {"High": 0, "Medium": 1, "Low": 2}
    gaps.sort(key=lambda g: (tier_rank[g["tier"]], -STATUS_WEIGHT[g["status"]], -len(g["eo14028_4e"]), order[g["id"]]))
    for n, g in enumerate(gaps, 1):
        g["rank"] = n
    return gaps


def _fmt_pct(v) -> str:
    return "n/a" if v is None else f"{v:.1f}%"


def _short(text: str, n: int = 110) -> str:
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def render_check(res: AssessmentResult, max_gaps: int = 50) -> str:
    sc = res.scores
    out = ["# SSDF v1.1 assessment check", ""]
    if res.meta:
        who = ", ".join(f"{k}: {v}" for k, v in res.meta.items() if v and k in ("organisation", "scope", "assessor", "date"))
        if who:
            out += [who, ""]
    errs = res.errors
    warns = [f for f in res.findings if f.level == "warning"]
    out.append(f"Validation: {'PASS' if not errs else 'FAIL'} - {len(errs)} error(s), {len(warns)} warning(s).")
    o = sc["overall"]
    out += ["", "## Overall", "",
            f"- Coverage: {_fmt_pct(o['coverage_pct'])} ({sc['method']})",
            f"- Fully implemented: {_fmt_pct(o['implemented_pct'])} of {o['applicable']} applicable tasks "
            f"({o['tasks']} assessed tasks, {o['counts']['not-applicable']} not applicable)",
            "- Counts: " + ", ".join(f"{k} {v}" for k, v in o["counts"].items() if v), "",
            "## By practice group", "", "| Group | Applicable | Implemented | Partial | Planned | Not implemented | Unevidenced | Unassessed | Coverage |",
            "|---|---|---|---|---|---|---|---|---|"]
    for g in groups():
        b = sc["groups"][g["id"]]
        c = b["counts"]
        out.append(f"| {g['id']} {g['title']} | {b['applicable']} | {c['implemented']} | {c['partial']} | {c['planned']} | "
                   f"{c['not-implemented']} | {c['unevidenced']} | {c['unassessed']} | {_fmt_pct(b['coverage_pct'])} |")
    out += ["", "## By practice", "", "| Practice | Tasks | Applicable | Coverage |", "|---|---|---|---|"]
    by = items_by_id()
    for pid, b in sc["practices"].items():
        out.append(f"| {pid} {by[pid]['title']} | {b['tasks']} | {b['applicable']} | {_fmt_pct(b['coverage_pct'])} |")
    if res.findings:
        out += ["", "## Findings", "", "| Level | Id | Issue |", "|---|---|---|"]
        for f in res.findings:
            out.append(f"| {f.level} | {f.id} | {_md_cell(f.message)} |")
    out += ["", "## Prioritised gaps", "",
            "Tool heuristic, not NIST guidance (SSDF practices are not prioritised; PDF p.12): status severity, "
            "then number of EO 14028 Section 4e subsections mapped in Appendix A Table 2 (PDF p.33).", ""]
    if res.gaps:
        out += ["| Rank | Tier | Task | Status | EO 14028 4e | Owner | Target | Task text |", "|---|---|---|---|---|---|---|---|"]
        for g in res.gaps[:max_gaps]:
            out.append(f"| {g['rank']} | {g['tier']} | {g['id']} | {g['status']} | {', '.join(g['eo14028_4e']) or '-'} | "
                       f"{g['owner'] or '-'} | {g['target_date'] or '-'} | {_md_cell(_short(g['task']))} |")
        if len(res.gaps) > max_gaps:
            out.append(f"\n({len(res.gaps) - max_gaps} more gaps not shown)")
    else:
        out.append("No gaps: every applicable task is recorded as implemented.")
    out += ["", DISCLAIMER, ""]
    return "\n".join(out)


# --------------------------------------------------------------------------- evidence matrix
def evidence_matrix(res: AssessmentResult, full_text: bool = False) -> str:
    by = items_by_id()
    m = res.meta or {}
    out = ["# SSDF v1.1 evidence matrix", "",
           "| Field | Value |", "|---|---|",
           f"| Organisation | {_md_cell(m.get('organisation', ''))} |",
           f"| Scope | {_md_cell(m.get('scope', ''))} |",
           f"| Assessor | {_md_cell(m.get('assessor', ''))} |",
           f"| Assessment date | {_md_cell(m.get('date', ''))} |",
           "| Framework | NIST SP 800-218, SSDF Version 1.1 (February 2022), Table 1 (PDF pp.14-28) |",
           f"| Basis | Self-assessment worksheet; validation {'passed' if not res.errors else 'FAILED - see open issues'} |",
           f"| Overall coverage | {_fmt_pct(res.scores['overall']['coverage_pct'])} |", "",
           "This matrix records what the producer states and the evidence it points to. It is attestation-style "
           "(task-by-task statement plus evidence references), not an attestation form, certification or "
           "independent verification. EO 14028 column: Section 4e subsections that SSDF Appendix A Table 2 "
           "(PDF p.33) maps to each task; 4e(ix) applies to all tasks.", ""]
    for g in groups():
        out += [f"## {g['id']} - {g['title']}", "",
                "| Task | Requirement | Status | Evidence | Owner | EO 14028 4e | Justification / notes | Source |",
                "|---|---|---|---|---|---|---|---|"]
        for t in tasks(group=g["id"]):
            r = res.rows[t["id"]]
            text = t["text"] if full_text else _short(t["text"], 140)
            ev = "; ".join(r["evidence"]) or ("**none**" if r["status"] in ("implemented", "partial") else "-")
            note = r["justification"] or r["notes"]
            if r["status"] in ("planned", "partial", "not-implemented") and r["target_date"]:
                note = (note + "; " if note else "") + f"target {r['target_date']}"
            out.append(f"| {t['id']} | {_md_cell(text)} | {r['status']} | {_md_cell(ev)} | {_md_cell(r['owner'] or '-')} | "
                       f"{', '.join(eo_subsections(t['id'])) or '-'} | {_md_cell(note or '-')} | p.{t['citation']['pdf_page']} |")
        out.append("")
    if res.findings:
        out += ["## Open validation issues", ""]
        out += [f"- {f.level}: {f.id}: {f.message}" for f in res.findings]
        out.append("")
    out += [DISCLAIMER, ""]
    return "\n".join(out)


# --------------------------------------------------------------------------- pipeline mapping
@dataclass(frozen=True)
class Rule:
    control: str
    aliases: tuple[str, ...]
    description: str
    # task id -> (basis, note). basis: "example" (an SSDF notional example names this kind of control)
    # or "interpretive" (reasonable reading, not named in the SSDF text).
    tasks: dict
    scheduled_tasks: dict = field(default_factory=dict)  # added when the step has scheduled: true
    blocking_tasks: dict = field(default_factory=dict)   # added when the step has blocking: true


_GATE = {"PO.4.2": ("example", "PO.4.2 Ex.3: automate decision-making utilizing the criteria")}

PIPELINE_RULES: tuple[Rule, ...] = (
    Rule("sast", ("static-analysis", "code-scanning", "codeql", "semgrep", "sonarqube", "sonarcloud", "bandit", "gosec", "checkmarx", "fortify"),
         "Static application security testing on source code",
         {"PW.7.2": ("example", "PW.7.2 Ex.4/Ex.6: static analysis tool / automated tools as code is checked in")},
         {"RV.1.2": ("example", "RV.1.2 Ex.1: automated code analysis on a regular or continuous basis for all supported releases")},
         _GATE),
    Rule("secret-scanning", ("secrets-scanning", "gitleaks", "trufflehog", "detect-secrets", "push-protection"),
         "Detects credentials committed to source",
         {"PW.7.2": ("interpretive", "hard-coded secrets treated as an unsafe practice found by automated tools (cf. PW.7.2 Ex.6); not named in SSDF")},
         {}, _GATE),
    Rule("code-review", ("peer-review", "required-reviews", "pull-request-review", "codeowners", "merge-request-approval"),
         "Mandatory human review of changes before merge",
         {"PW.7.2": ("example", "PW.7.2 Ex.1/Ex.3: peer review of code using peer reviewing tools"),
          "PS.1.1": ("example", "PS.1.1 Ex.4: code owner reviews and approves all changes by others")}),
    Rule("branch-protection", ("protected-branches", "repo-access-control", "least-privilege-repo", "scm-access-control"),
         "Repository access control and protected branches",
         {"PS.1.1": ("example", "PS.1.1 Ex.1/Ex.2: code in a repository with restricted access; version control with accountability")}),
    Rule("commit-signing", ("signed-commits", "gpg-commits", "gitsign"), "Signed commits enforced",
         {"PS.1.1": ("example", "PS.1.1 Ex.3: use commit signing for code repositories")}),
    Rule("sca", ("dependency-scanning", "software-composition-analysis", "dependabot", "renovate-vuln", "snyk", "osv-scanner", "npm-audit", "pip-audit", "owasp-dependency-check", "trivy-fs"),
         "Known-vulnerability detection in third-party components",
         {"PW.4.4": ("example", "PW.4.4 Ex.1/Ex.2: automatic detection of known vulnerabilities in software components"),
          "PW.4.1": ("example", "PW.4.1 Ex.3: source composition analysis as provenance information for components")},
         {"RV.1.1": ("example", "RV.1.1 Ex.3: automatically review software composition data to identify new vulnerabilities")},
         _GATE),
    Rule("container-scanning", ("image-scanning", "trivy-image", "grype", "clair"), "Vulnerability scanning of container images",
         {"PW.4.4": ("example", "PW.4.4 Ex.2: automatic detection of known vulnerabilities in software components")},
         {"RV.1.1": ("example", "RV.1.1 Ex.3: automatically review composition data for new vulnerabilities")},
         _GATE),
    Rule("sbom", ("sbom-generation", "syft", "cyclonedx", "spdx"), "Software bill of materials generated for each release",
         {"PS.3.2": ("example", "PS.3.2 task text: provenance data for all components, e.g. in an SBOM"),
          "PW.4.1": ("example", "PW.4.1 Ex.3: obtain provenance information (e.g., SBOM) for each component")}),
    Rule("provenance", ("slsa", "build-provenance", "in-toto", "attestations"), "Signed build provenance / attestations",
         {"PS.3.2": ("example", "PS.3.2 Ex.3: protect integrity of provenance data and let recipients verify it"),
          "PS.3.1": ("example", "PS.3.1 Ex.2: store and protect provenance data, e.g. by signing it")}),
    Rule("signing", ("artifact-signing", "code-signing", "cosign", "sigstore", "authenticode", "gpg-sign"), "Release artifacts are signed",
         {"PS.1.1": ("example", "PS.1.1 Ex.5: code signing to help protect integrity of executables"),
          "PS.2.1": ("example", "PS.2.1 Ex.2: code signing that consumers can validate (only if signatures/keys are published to acquirers)")}),
    Rule("checksums", ("hashes", "release-hashes", "sha256sums"), "Cryptographic hashes published for release files",
         {"PS.2.1": ("example", "PS.2.1 Ex.1: post cryptographic hashes for release files on a well-secured website"),
          "PS.1.1": ("example", "PS.1.1 Ex.6: cryptographic hashes to protect file integrity")}),
    Rule("dependency-pinning", ("lockfile", "pinned-dependencies", "version-pinning"), "Dependencies pinned to exact versions",
         {"PW.4.1": ("interpretive", "pinning supports maintaining approved component versions (cf. PW.4.1 Ex.5); not named in SSDF")}),
    Rule("dependency-integrity", ("hash-pinning", "dependency-signature-verification", "verified-dependencies", "require-hashes"),
         "Integrity of fetched components verified (hashes/signatures)",
         {"PW.4.4": ("example", "PW.4.4 Ex.6: confirm integrity of components through digital signatures or other mechanisms")}),
    Rule("private-registry", ("artifact-proxy", "vetted-repository", "internal-mirror", "curated-registry"),
         "Components consumed only from a sanctioned repository",
         {"PW.4.1": ("example", "PW.4.1 Ex.4: repositories hosting sanctioned and vetted open-source components")}),
    Rule("dast", ("dynamic-analysis", "zap", "burp", "dynamic-scanning"), "Dynamic testing of the running application",
         {"PW.8.2": ("example", "PW.8.2 Ex.2: dynamic vulnerability testing in the automated test suite")},
         {"RV.1.2": ("example", "RV.1.2 Ex.1: automated testing on a regular or continuous basis")}, _GATE),
    Rule("fuzzing", ("fuzz-testing", "oss-fuzz", "libfuzzer", "afl"), "Fuzz testing of input handling",
         {"PW.8.2": ("example", "PW.8.2 Ex.5: fuzz testing tools")},
         {"RV.1.2": ("example", "RV.1.2 Ex.1: automated testing on a regular or continuous basis")}),
    Rule("penetration-test", ("pentest", "pen-test"), "Penetration testing",
         {"PW.8.2": ("example", "PW.8.2 Ex.6: penetration testing for high-risk scenarios")}),
    Rule("security-tests", ("security-unit-tests", "security-regression-tests", "security-functional-tests"),
         "Functional/regression tests of security features and past vulnerabilities",
         {"PW.8.2": ("example", "PW.8.2 Ex.1/Ex.3: functional testing of security features; tests for previously reported vulnerabilities")}),
    Rule("compiler-hardening", ("hardening-flags", "warnings-as-errors", "clean-build", "pie-aslr"), "Secure compiler/build tool configuration",
         {"PW.6.2": ("example", "PW.6.2 Ex.1/Ex.2/Ex.4: compiler warnings, clean build, randomisation features")}),
    Rule("toolchain-updates", ("up-to-date-build-tools", "toolchain-patching"), "Compiler/interpreter/build tools kept current",
         {"PW.6.1": ("example", "PW.6.1 Ex.1: up-to-date versions of compiler, interpreter and build tools")}),
    Rule("isolated-build", ("hermetic-build", "ephemeral-runners", "dedicated-build-environment"), "Builds in a dedicated, controlled environment",
         {"PW.6.2": ("example", "PW.6.2 Ex.3: all builds in a dedicated, highly controlled build environment")}),
    Rule("reproducible-builds", ("reproducible-build", "deterministic-builds"), "Reproducible builds",
         {"PO.3.2": ("example", "PO.3.2 Ex.4: technologies and processes for reproducible builds")}),
    Rule("pipeline-as-code", ("pipelines-as-code", "ci-as-code"), "Pipeline defined as version-controlled code",
         {"PO.3.2": ("example", "PO.3.2 Ex.3: code-based configuration for toolchains (pipelines-as-code)")}),
    Rule("ci-hardening", ("pinned-actions", "least-privilege-ci-tokens", "tool-integrity-verification", "runner-hardening"),
         "Security of the CI/CD toolchain itself",
         {"PO.3.2": ("example", "PO.3.2 Ex.6/Ex.7: monitor tools; verify integrity and provenance of each tool")}),
    Rule("security-gate", ("policy-as-code", "quality-gate", "release-gate", "opa", "conftest"), "Automated pass/fail on security criteria",
         {"PO.4.2": ("example", "PO.4.2 Ex.3: automate decision-making utilizing the criteria"),
          "PO.4.1": ("interpretive", "a gate implies criteria exist (PO.4.1 Ex.3); the criteria themselves need separate evidence")}),
    Rule("artifact-retention", ("audit-trail", "scan-results-retention", "evidence-store", "ci-logs-retention"),
         "Tool results and logs retained as artifacts",
         {"PO.3.3": ("example", "PO.3.3 Ex.1/Ex.3: audit trail from tooling; retention policies for artifact data"),
          "PO.4.2": ("example", "PO.4.2 Ex.1/Ex.4: toolchain gathers information; protected from alteration (if immutable)")}),
    Rule("release-archive", ("immutable-artifact-repository", "release-retention"), "Releases archived with restricted read-only access",
         {"PS.3.1": ("example", "PS.3.1 Ex.1: store release files in repositories with read-only access")}),
    Rule("findings-tracking", ("issue-tracking", "vulnerability-tracking", "defectdojo"), "Findings recorded and triaged in a tracker",
         {"RV.2.1": ("example", "RV.2.1 Ex.1: use issue tracking software to record each vulnerability"),
          "PW.7.2": ("interpretive", "PW.7.2 task text requires recording and triaging discovered issues")}),
    Rule("vulnerability-monitoring", ("dependency-track", "continuous-monitoring", "vuln-feed-monitoring"),
         "Ongoing monitoring of released components for new vulnerabilities",
         {"RV.1.1": ("example", "RV.1.1 Ex.1/Ex.3: monitor vulnerability sources; review composition data for new vulnerabilities")}),
    Rule("vulnerability-disclosure", ("vdp", "security-txt", "bug-bounty", "psirt"), "Public vulnerability disclosure / reporting channel",
         {"RV.1.3": ("example", "RV.1.3 Ex.1/Ex.2: vulnerability disclosure program; PSIRT"),
          "RV.1.1": ("interpretive", "a reporting channel helps gather reports from acquirers and users")}),
    Rule("security-advisories", ("advisories", "csaf", "vex"), "Security advisories published to acquirers",
         {"RV.2.2": ("example", "RV.2.2 Ex.3: develop and release security advisories")}),
    Rule("automated-updates", ("trusted-update-delivery", "signed-updates"), "Remediations delivered by an automated, trusted mechanism",
         {"RV.2.2": ("example", "RV.2.2 Ex.4: deliver remediations via an automated and trusted delivery mechanism")}),
    Rule("linting", ("linter", "formatter", "eslint", "pylint", "ruff"), "Linters/formatters",
         {"PW.5.1": ("example", "PW.5.1 Ex.7: linters and formatters to standardise code style (supports, not secure coding itself)")}),
    Rule("secure-coding-ide", ("ide-security-plugin", "pre-commit-security-hooks"), "Developer tooling encouraging secure coding",
         {"PW.5.1": ("example", "PW.5.1 Ex.5: development environments with automated secure-coding features")}),
    Rule("secure-config-tests", ("default-settings-tests", "secure-defaults-check"), "Tests that default settings are secure",
         {"PW.9.1": ("example", "PW.9.1 Ex.1: test that settings, including defaults, work as expected"),
          "PW.9.2": ("example", "PW.9.2 Ex.1: verify the approved configuration is in place")}),
    Rule("threat-modeling", ("threat-model", "risk-modeling"), "Threat/risk modelling as part of the workflow",
         {"PW.1.1": ("example", "PW.1.1 task text: threat modeling, attack modeling, attack surface mapping")}),
    Rule("design-review", ("security-design-review", "architecture-review"), "Security review of designs",
         {"PW.2.1": ("example", "PW.2.1 Ex.1-3: review design against requirements and risk models")}),
    Rule("mfa", ("sso-mfa", "multi-factor-authentication", "conditional-access"), "MFA on SCM/CI/build environments",
         {"PO.5.1": ("example", "PO.5.1 Ex.1: multi-factor, risk-based authentication for each environment"),
          "PO.5.2": ("example", "PO.5.2 Ex.5: MFA for development endpoints and resources (only if enforced there)")}),
    Rule("environment-separation", ("network-segmentation", "separate-environments"), "Development/build/production environments separated",
         {"PO.5.1": ("example", "PO.5.1 Ex.2: network segmentation and access controls separating environments")}),
    Rule("security-training", ("secure-coding-training", "role-based-training"), "Role-based secure development training",
         {"PO.2.2": ("example", "PO.2.2 task text: role-based training")}),
)

# Tasks that are primarily organisational/process decisions; a pipeline rarely evidences them on its own.
ORGANISATIONAL_TASKS = frozenset({
    "PO.1.1", "PO.1.2", "PO.1.3", "PO.2.1", "PO.2.2", "PO.2.3", "PO.3.1", "PO.4.1", "PO.5.2",
    "PW.1.2", "PW.1.3", "PW.4.2", "PW.7.1", "PW.8.1", "RV.1.3", "RV.2.2", "RV.3.1", "RV.3.2", "RV.3.4",
})


def _rule_index() -> dict[str, Rule]:
    idx: dict[str, Rule] = {}
    for r in PIPELINE_RULES:
        for name in (r.control,) + r.aliases:
            idx[_norm_control(name)] = r
    return idx


def _norm_control(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(name).strip().lower()).strip("-")


def _truthy(v) -> bool:
    return v is True or str(v).strip().lower() in {"true", "yes", "1", "on"}


def load_pipeline(path: str | Path) -> dict:
    p = Path(path)
    if not p.is_file():
        raise SSDFError(f"pipeline file not found: {p}")
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise SSDFError(f"cannot parse {p.name}: {exc}") from exc
    if not isinstance(data, dict):
        raise SSDFError(f"{p.name}: expected a mapping (see `ssdf pipeline-controls`)")
    return data


def map_pipeline(data: dict) -> dict:
    """Map a pipeline description to SSDF tasks.

    Accepted shapes: ``{pipeline: {name, steps|controls: [...]}}`` or top-level ``steps``/``controls``.
    Each step is a string (control type) or a mapping with ``type`` (or ``control``/``kind``) and
    optional ``name``, ``tool``, ``enabled`` (default true), ``blocking``, ``scheduled``.
    """
    pipe = data.get("pipeline", data) if isinstance(data, dict) else {}
    if not isinstance(pipe, dict):
        raise SSDFError("'pipeline' must be a mapping")
    steps = pipe.get("steps") or pipe.get("controls") or []
    if not isinstance(steps, list) or not steps:
        raise SSDFError("pipeline has no 'steps' (or 'controls') list")
    idx = _rule_index()
    support: dict[str, list[dict]] = {}
    unmapped, disabled, recognised = [], [], []
    for n, s in enumerate(steps, 1):
        if isinstance(s, str):
            s = {"type": s}
        if not isinstance(s, dict):
            raise SSDFError(f"step {n} must be a string or a mapping")
        ctype = s.get("type") or s.get("control") or s.get("kind") or s.get("tool")
        name = str(s.get("name") or s.get("tool") or ctype or f"step {n}")
        if not ctype:
            unmapped.append({"step": name, "reason": "no 'type'"})
            continue
        if "enabled" in s and not _truthy(s.get("enabled")):
            disabled.append(name)
            continue
        rule = idx.get(_norm_control(ctype)) or (idx.get(_norm_control(s["tool"])) if s.get("tool") else None)
        if rule is None:
            unmapped.append({"step": name, "reason": f"control type '{ctype}' has no SSDF mapping rule"})
            continue
        recognised.append({"step": name, "control": rule.control, "blocking": _truthy(s.get("blocking")),
                           "scheduled": _truthy(s.get("scheduled"))})
        mapped = dict(rule.tasks)
        if _truthy(s.get("scheduled")):
            mapped.update(rule.scheduled_tasks)
        if _truthy(s.get("blocking")):
            mapped.update(rule.blocking_tasks)
        for tid, (basis, note) in mapped.items():
            support.setdefault(tid, []).append({"step": name, "control": rule.control, "basis": basis, "note": note})
    by = items_by_id()
    result_tasks = []
    for t in tasks():
        sup = support.get(t["id"], [])
        bases = {x["basis"] for x in sup}
        level = "supported" if "example" in bases else ("interpretive-support" if sup else "no-supporting-control")
        result_tasks.append({"id": t["id"], "practice": t["practice"], "group": t["group"], "support": level,
                             "organisational": t["id"] in ORGANISATIONAL_TASKS, "controls": sup,
                             "pdf_page": t["citation"]["pdf_page"], "task": t["text"]})
    counts = {k: sum(1 for r in result_tasks if r["support"] == k)
              for k in ("supported", "interpretive-support", "no-supporting-control")}
    return {"pipeline": str(pipe.get("name") or "unnamed pipeline"), "recognised_steps": recognised,
            "unmapped_steps": unmapped, "disabled_steps": disabled, "counts": counts, "tasks": result_tasks,
            "note": "Support != compliance: a mapped control can contribute evidence for a task, but whether the task "
                    "is implemented depends on scope, configuration, enforcement and the organisation's own criteria."}


def render_pipeline(res: dict) -> str:
    by = items_by_id()
    c = res["counts"]
    out = [f"# SSDF v1.1 pipeline mapping: {res['pipeline']}", "", f"> {res['note']}", "",
           f"- Tasks with an example-based supporting control: {c['supported']} of 42",
           f"- Tasks with interpretive support only: {c['interpretive-support']}",
           f"- Tasks with no supporting control in this pipeline: {c['no-supporting-control']}", ""]
    if res["unmapped_steps"]:
        out += ["Unmapped steps (no rule; not credited): " + "; ".join(f"{u['step']} ({u['reason']})" for u in res["unmapped_steps"]), ""]
    if res["disabled_steps"]:
        out += ["Disabled steps (ignored): " + ", ".join(res["disabled_steps"]), ""]
    out += ["## Tasks with supporting controls", "", "| Task | Support | Controls (basis) | Source |", "|---|---|---|---|"]
    for t in res["tasks"]:
        if t["support"] != "no-supporting-control":
            ctrls = "; ".join(f"{x['step']} [{x['control']}] ({x['basis']}: {x['note']})" for x in t["controls"])
            out.append(f"| {t['id']} | {t['support']} | {_md_cell(ctrls)} | p.{t['pdf_page']} |")
    out += ["", "## Tasks with no supporting control", "",
            "Organisational tasks are normally evidenced by policy/process records rather than pipeline steps.", "",
            "| Task | Practice | Organisational | Task text | Source |", "|---|---|---|---|---|"]
    for t in res["tasks"]:
        if t["support"] == "no-supporting-control":
            out.append(f"| {t['id']} | {t['practice']} {by[t['practice']]['title']} | {'yes' if t['organisational'] else 'no'} | "
                       f"{_md_cell(_short(t['task']))} | p.{t['pdf_page']} |")
    out += ["", DISCLAIMER, ""]
    return "\n".join(out)


def render_rules() -> str:
    out = ["# SSDF pipeline control vocabulary and mapping rules", "",
           "basis 'example' = an SSDF v1.1 notional implementation example or task text names this kind of control; "
           "'interpretive' = reasonable reading not named in SSDF. `scheduled: true` and `blocking: true` on a step add "
           "the listed extra tasks. Support != compliance.", "",
           "| Control | Aliases | Tasks (basis) | If scheduled | If blocking |", "|---|---|---|---|---|"]
    for r in PIPELINE_RULES:
        fmt = lambda d: "; ".join(f"{k} ({v[0]})" for k, v in d.items()) or "-"
        out.append(f"| {r.control} | {', '.join(r.aliases)} | {fmt(r.tasks)} | {fmt(r.scheduled_tasks)} | {fmt(r.blocking_tasks)} |")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- CLI
def _emit(text: str, out: str | None) -> None:
    if out:
        Path(out).write_text(text, encoding="utf-8")
        print(f"wrote {out}")
    else:
        sys.stdout.write(text if text.endswith("\n") else text + "\n")


def _cmd(args) -> int:
    try:
        return _dispatch(args)
    except SSDFError as exc:
        print(f"ssdf: error: {exc}", file=sys.stderr)
        return 2


def _dispatch(args) -> int:
    cmd = args.ssdf_command
    if cmd == "list":
        items = list_items(args.group, args.all)
        if args.format == "json":
            _emit(json.dumps([{k: i.get(k) for k in ("id", "kind", "title", "text", "status", "citation")} for i in items],
                             indent=2, ensure_ascii=False), args.out)
        else:
            lines = []
            for i in items:
                flag = " [retired]" if i["status"] != "active" else ""
                if i["kind"] == "practice":
                    lines.append(f"{i['id']:7} {i['title']}{flag}  (p.{i['citation']['pdf_page']})")
                else:
                    lines.append(f"  {i['id']:7} {_short(i['text'], 100)}{flag}")
            _emit("\n".join(lines), args.out)
        return 0
    if cmd == "show":
        item = get(args.id)
        if args.format == "json":
            _emit(json.dumps(item, indent=2, ensure_ascii=False), None)
        else:
            _emit(render_item(item), None)
        return 0
    if cmd == "assessment-template":
        _emit(assessment_template(args.format), args.out)
        return 0
    if cmd in ("check-assessment", "evidence-matrix"):
        meta, rows = load_assessment(args.file)
        today = date.fromisoformat(args.today) if getattr(args, "today", None) else date.today()
        res = check_assessment(meta, rows, today=today)
        if cmd == "evidence-matrix":
            _emit(evidence_matrix(res, full_text=args.full_text), args.out)
            return 0
        if args.format == "json":
            _emit(json.dumps(res.to_dict(), indent=2, ensure_ascii=False), args.out)
        else:
            _emit(render_check(res, args.max_gaps), args.out)
        return 1 if res.errors else 0
    if cmd == "map-pipeline":
        res = map_pipeline(load_pipeline(args.file))
        _emit(json.dumps(res, indent=2, ensure_ascii=False) if args.format == "json" else render_pipeline(res), args.out)
        return 0
    if cmd == "pipeline-controls":
        _emit(render_rules(), None)
        return 0
    raise SSDFError(f"unknown command {cmd}")  # pragma: no cover


def register(subparsers) -> None:
    p = subparsers.add_parser("ssdf", help="NIST SP 800-218 SSDF v1.1: catalog, gap assessment, evidence matrix, pipeline mapping",
                              description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="ssdf_command", required=True)

    s = sub.add_parser("list", help="list practices and tasks")
    s.add_argument("--group", help="PO, PS, PW or RV")
    s.add_argument("--all", action="store_true", help="include retired identifiers")
    s.add_argument("--format", choices=["text", "json"], default="text")
    s.add_argument("--out")

    s = sub.add_parser("show", help="show a group, practice or task (with examples and references)")
    s.add_argument("id")
    s.add_argument("--format", choices=["text", "json"], default="text")

    s = sub.add_parser("assessment-template", help="gap-assessment worksheet for all 42 tasks")
    s.add_argument("--format", choices=["md", "csv", "yaml"], default="md")
    s.add_argument("--out")

    s = sub.add_parser("check-assessment", help="validate and score a filled worksheet (exit 1 on errors)")
    s.add_argument("file")
    s.add_argument("--format", choices=["md", "json"], default="md")
    s.add_argument("--max-gaps", type=int, default=50)
    s.add_argument("--today", help="reference date YYYY-MM-DD for overdue checks (default: today)")
    s.add_argument("--out")

    s = sub.add_parser("evidence-matrix", help="attestation-style evidence matrix (Markdown) from a worksheet")
    s.add_argument("file")
    s.add_argument("--full-text", action="store_true", help="do not abbreviate task text")
    s.add_argument("--today")
    s.add_argument("--out")

    s = sub.add_parser("map-pipeline", help="which SSDF tasks a CI/CD pipeline description supports")
    s.add_argument("file")
    s.add_argument("--format", choices=["md", "json"], default="md")
    s.add_argument("--out")

    sub.add_parser("pipeline-controls", help="print the pipeline control vocabulary and mapping rules")
    p.set_defaults(func=_cmd)


# --------------------------------------------------------------------------- graders
_OVERCLAIM_RE = re.compile(
    r"(ssdf[- ]compliant|fully compliant|complies (?:fully )?with (?:the )?ssdf|ssdf[- ]certified|certif(?:y|ies|ied) "
    r"(?:that )?(?:\w+ ){0,4}(?:ssdf|sp 800-218)|(?:meets|satisfies) all (?:of the )?ssdf|compliance with (?:the )?ssdf is (?:achieved|demonstrated|confirmed))",
    re.I)
_NEGATION_RE = re.compile(r"\b(not|no|never|cannot|can't|isn't|doesn't|does not|do not|without|neither|nor|avoid)\b", re.I)


def _resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else repo_root() / p


def grade_ids_valid(output: str, check: dict) -> tuple[bool, str]:
    """Every SSDF task id (XX.n.n) in the output exists in SSDF v1.1. Retired ids fail unless
    ``allow_retired: true`` and the output says they are retired/moved. ``min`` = minimum distinct valid ids."""
    by = items_by_id()
    found = {".".join(m) for m in TASK_ID_RE.findall(output)}
    unknown = sorted(i for i in found if i not in by)
    retired = sorted(i for i in found if i in by and by[i]["status"] != "active")
    valid = sorted(i for i in found if i in by and by[i]["status"] == "active")
    problems = []
    if unknown:
        problems.append(f"unknown ids {unknown}")
    if retired and not (check.get("allow_retired") and re.search(r"retired|moved|formerly", output, re.I)):
        problems.append(f"retired ids used as current {retired}")
    need = int(check.get("min", 1))
    if len(valid) < need:
        problems.append(f"only {len(valid)} valid task ids (need {need})")
    return (not problems, "; ".join(problems) or f"{len(valid)} valid task ids, none invented")


def grade_practice_ids_valid(output: str, check: dict) -> tuple[bool, str]:
    """Every practice id (XX.n, not followed by .n) is an SSDF v1.1 practice; ``min`` distinct required."""
    by = items_by_id()
    found = {".".join(m) for m in PRACTICE_ID_RE.findall(output)}
    unknown = sorted(i for i in found if i not in by)
    retired = sorted(i for i in found if i in by and by[i]["status"] != "active")
    valid = [i for i in found if i in by and by[i]["status"] == "active"]
    problems = []
    if unknown:
        problems.append(f"unknown practice ids {unknown}")
    if retired and not re.search(r"retired|moved|merged", output, re.I):
        problems.append(f"retired practice ids used as current {retired}")
    if len(valid) < int(check.get("min", 1)):
        problems.append(f"only {len(valid)} valid practice ids")
    return (not problems, "; ".join(problems) or f"{len(valid)} valid practice ids")


def grade_no_overclaim(output: str, check: dict) -> tuple[bool, str]:
    """Fails if the output claims SSDF compliance/certification (unless the sentence negates it)."""
    hits = []
    for sent in re.split(r"(?<=[.!?])\s+|\n", output):
        for m in _OVERCLAIM_RE.finditer(sent):
            if not _NEGATION_RE.search(sent[: m.start()] + " " + sent[m.end(): m.end() + 40]):
                hits.append(m.group(0))
    return (not hits, f"overclaims: {hits}" if hits else "no unqualified compliance/certification claims")


def grade_page_citations(output: str, check: dict) -> tuple[bool, str]:
    """Citations written as '<task id> ... p.<N>' / '(p. N)' within the same line segment must match the
    catalog's PDF page for that task (or a continuation page). ``min`` = minimum number of correct citations."""
    by = items_by_id()
    pat = re.compile(r"\b((?:PO|PS|PW|RV)\.\d+\.\d+)\b[^\n|]{0,60}?\bp(?:age|p)?\.?\s*(\d{1,2})\b", re.I)
    good, bad = [], []
    for tid, page in pat.findall(output):
        it = by.get(tid.upper())
        if not it:
            bad.append(f"{tid}:p.{page} (unknown id)")
            continue
        pages = set(it.get("pdf_pages", [])) | {it["citation"]["pdf_page"]}
        (good if int(page) in pages else bad).append(f"{tid}:p.{page}")
    need = int(check.get("min", 1))
    ok = not bad and len(good) >= need
    return ok, f"correct {len(good)} (need {need}); wrong {bad}" if bad or len(good) < need else f"{len(good)} correct page citations"


def grade_assessment_numbers(output: str, check: dict) -> tuple[bool, str]:
    """Output must state the overall coverage % that ``check-assessment`` computes for ``fixture``
    (formatted with one decimal, e.g. 47.6%) and mention every High-tier gap id."""
    meta, rows = load_assessment(_resolve(check["fixture"]))
    res = check_assessment(meta, rows, today=date.fromisoformat(check.get("today", "2026-10-13")))
    cov = res.scores["overall"]["coverage_pct"]
    problems = []
    if cov is not None and not re.search(rf"{re.escape(f'{cov:.1f}')}\s*%", output):
        problems.append(f"overall coverage {cov:.1f}% not stated")
    if check.get("require_high_gaps", True):
        missing = [g["id"] for g in res.gaps if g["tier"] == "High" and g["id"] not in output]
        if missing:
            problems.append(f"High-tier gaps not mentioned: {missing}")
    if check.get("require_errors", True):
        err_ids = sorted({f.id for f in res.errors if TASK_ID_RE.fullmatch(f.id)})
        missing = [i for i in err_ids if i not in output]
        if missing:
            problems.append(f"validation errors not reported for: {missing}")
    return (not problems, "; ".join(problems) or f"coverage {cov}% and gaps/errors reported")


def grade_pipeline_gaps(output: str, check: dict) -> tuple[bool, str]:
    """For the pipeline ``fixture``: the output must name at least ``min_fraction`` (default 0.8) of the
    non-organisational tasks that have no supporting control, and must not present any of those tasks
    as covered on the same line (e.g. 'PW.8.2 ... supported')."""
    res = map_pipeline(load_pipeline(_resolve(check["fixture"])))
    gaps = [t["id"] for t in res["tasks"] if t["support"] == "no-supporting-control" and not t["organisational"]]
    named = [g for g in gaps if g in output]
    frac = float(check.get("min_fraction", 0.8))
    problems = []
    if gaps and len(named) < frac * len(gaps):
        problems.append(f"named {len(named)}/{len(gaps)} unsupported technical tasks: missing {[g for g in gaps if g not in named]}")
    for line in output.splitlines():
        for g in gaps:
            if g in line and re.search(r"\b(covered|supported|satisfied|implemented|compliant)\b", line, re.I) \
                    and not re.search(r"\b(no|not|none|without|missing|gap|unsupported)\b", line, re.I):
                problems.append(f"{g} presented as covered: {line.strip()[:80]}")
    return (not problems, "; ".join(problems) or f"{len(named)}/{len(gaps)} unsupported tasks flagged")
