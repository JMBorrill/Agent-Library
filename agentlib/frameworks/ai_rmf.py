"""NIST AI Risk Management Framework (AI RMF 1.0) + Playbook tools.

Deterministic helpers over ``catalog/nist-ai-rmf.json`` (NIST AI 100-1 Core:
4 functions, 19 categories, 72 subcategories, 7 trustworthy-AI
characteristics) and ``catalog/nist-ai-rmf-playbook.json`` (Playbook suggested
actions and transparency & documentation questions).

CLI: ``python -m agentlib ai-rmf <sub-command>``

* ``list [--function MAP]``                       list subcategories
* ``show <id>``                                   subcategory + Playbook actions/questions
* ``characteristics``                             the 7 trustworthy-AI characteristics
* ``profile-template [--functions ...] [--format md|csv|yaml]``
* ``check-profile <file> [--functions ...]``      validate a filled current/target profile + gap analysis
* ``register-template [--format md|csv|yaml]``
* ``check-register <file>``                       validate an AI risk register
* ``scan <file>``                                 subcategory ids referenced in a document (coverage)

Grader functions (``grade_*``) are usable as ``python`` checks in eval suites.

Conventions that are NOT taken from NIST (the AI RMF prescribes no scales):
implementation status levels, the 1-5 likelihood/impact scales and the
likelihood x impact rating bands. They are library conventions, documented in
``docs/frameworks/ai_rmf.md``. The Playbook (GOVERN 1.3 "About", PDF p. 9)
describes risk as approximately impact x likelihood placed on a qualitative or
quantitative scale, which is what the register checker implements.
"""
from __future__ import annotations

import csv
import io
import json
import re
import sys
from collections import Counter, OrderedDict
from functools import lru_cache
from pathlib import Path
from typing import Iterable

import yaml

from agentlib.paths import load_catalog

CORE_ID = "nist-ai-rmf"
PLAYBOOK_ID = "nist-ai-rmf-playbook"
FUNCTIONS = ("GOVERN", "MAP", "MEASURE", "MANAGE")
FUNCTION_ABBREV = {"GV": "GOVERN", "MP": "MAP", "MS": "MEASURE", "MG": "MANAGE"}

# Subcategory ids in free text: "GOVERN 1.1", "MAP-2.3", "Measure 2.11", "GV-1.1", "MS 2.7"
ID_IN_TEXT_RE = re.compile(r"\b(GOVERN|MAP|MEASURE|MANAGE|GV|MP|MS|MG)[ \-]?(\d{1,2})\.(\d{1,2})\b", re.I)
ID_EXACT_RE = re.compile(r"^\s*(GOVERN|MAP|MEASURE|MANAGE|GV|MP|MS|MG)[ \-_]?(\d{1,2})\.(\d{1,2})\s*$", re.I)

# ------------------------------------------------------------------ statuses
# Library convention for profile status (ordered).
STATUS_LEVELS: "OrderedDict[str, int]" = OrderedDict([
    ("not-implemented", 0),
    ("partially-implemented", 1),
    ("largely-implemented", 2),
    ("implemented", 3),
])
NOT_APPLICABLE = "not-applicable"
STATUS_ALIASES = {
    "none": "not-implemented", "no": "not-implemented", "not implemented": "not-implemented",
    "not started": "not-implemented", "not-started": "not-implemented", "0": "not-implemented",
    "partial": "partially-implemented", "partially implemented": "partially-implemented",
    "in progress": "partially-implemented", "in-progress": "partially-implemented", "1": "partially-implemented",
    "largely": "largely-implemented", "largely implemented": "largely-implemented", "2": "largely-implemented",
    "yes": "implemented", "full": "implemented", "fully implemented": "implemented", "3": "implemented",
    "n/a": NOT_APPLICABLE, "na": NOT_APPLICABLE, "not applicable": NOT_APPLICABLE,
}
PRIORITIES = ("high", "medium", "low")

# ------------------------------------------------------------------ register scales
LIKELIHOOD_WORDS = {"rare": 1, "unlikely": 2, "possible": 3, "likely": 4, "almost certain": 5, "almost-certain": 5,
                    "very low": 1, "low": 2, "medium": 3, "moderate": 3, "high": 4, "very high": 5}
IMPACT_WORDS = {"negligible": 1, "minor": 2, "moderate": 3, "major": 4, "severe": 5, "critical": 5,
                "very low": 1, "low": 2, "medium": 3, "high": 4, "very high": 5}
RATING_LEVELS = OrderedDict([("low", 1), ("medium", 2), ("high", 3), ("critical", 4)])
RATING_ALIASES = {"very high": "critical", "very-high": "critical", "extreme": "critical", "med": "medium",
                  "moderate": "medium", "green": "low", "amber": "medium", "red": "high"}
# score = likelihood (1-5) x impact (1-5) -> band (library convention)
SCORE_BANDS = ((4, "low"), (9, "medium"), (16, "high"), (25, "critical"))
TREATMENTS = ("mitigate", "transfer", "avoid", "accept")
TREATMENT_ALIASES = {"mitigating": "mitigate", "mitigation": "mitigate", "reduce": "mitigate",
                     "transferring": "transfer", "share": "transfer", "avoiding": "avoid", "terminate": "avoid",
                     "accepting": "accept", "acceptance": "accept", "tolerate": "accept", "retain": "accept"}

# Register field aliases (normalised header -> canonical field)
REGISTER_FIELDS = OrderedDict([
    ("id", ["id", "risk_id", "ref", "risk_ref"]),
    ("description", ["description", "risk_description", "risk", "title"]),
    ("stakeholders", ["affected_stakeholders", "stakeholders", "affected_parties", "impacted_stakeholders"]),
    ("characteristics", ["trustworthiness_characteristics", "trustworthiness_characteristic", "characteristics",
                         "characteristic", "trustworthy_characteristics"]),
    ("likelihood", ["likelihood", "inherent_likelihood"]),
    ("impact", ["impact", "inherent_impact", "severity"]),
    ("inherent_rating", ["inherent_rating", "inherent", "inherent_risk"]),
    ("residual_rating", ["residual_rating", "residual", "residual_risk"]),
    ("treatment", ["treatment", "response", "risk_response"]),
    ("owner", ["owner", "risk_owner"]),
    ("subcategories", ["linked_subcategories", "subcategories", "ai_rmf_subcategories", "ai_rmf", "subcategory"]),
])
OPTIONAL_REGISTER_FIELDS = OrderedDict([
    ("residual_likelihood", ["residual_likelihood"]),
    ("residual_impact", ["residual_impact"]),
    ("controls", ["controls", "treatment_actions", "mitigations", "actions"]),
    ("residual_justification", ["residual_justification", "justification"]),
    ("escalated_to", ["escalated_to", "escalation"]),
    ("accepted_by", ["accepted_by", "acceptance_signoff", "acceptance_sign_off", "risk_acceptance", "sign_off",
                     "signoff"]),
    ("review_date", ["review_date", "next_review"]),
])
REQUIRED_REGISTER_FIELDS = tuple(REGISTER_FIELDS)

CHARACTERISTIC_ALIASES = {
    "valid-reliable": ["valid and reliable", "valid & reliable", "valid-reliable", "valid", "reliable", "validity",
                       "reliability", "accuracy", "robustness"],
    "safe": ["safe", "safety"],
    "secure-resilient": ["secure and resilient", "secure & resilient", "secure-resilient", "secure", "security",
                         "resilient", "resilience"],
    "accountable-transparent": ["accountable and transparent", "accountable & transparent",
                                "accountable-transparent", "accountable", "accountability", "transparent",
                                "transparency"],
    "explainable-interpretable": ["explainable and interpretable", "explainable & interpretable",
                                  "explainable-interpretable", "explainable", "explainability", "interpretable",
                                  "interpretability"],
    "privacy-enhanced": ["privacy-enhanced", "privacy enhanced", "privacy"],
    "fair-bias-managed": ["fair with harmful bias managed", "fair – with harmful bias managed",
                          "fair - with harmful bias managed", "fair-bias-managed", "fair", "fairness",
                          "harmful bias", "bias"],
}
# phrases used to detect characteristic coverage in prose (graders)
CHARACTERISTIC_PROSE = {
    "valid-reliable": [r"valid(?:ity)?\s*(?:and|&)\s*reliab"],
    "safe": [r"\bsafe\b", r"\bsafety\b"],
    "secure-resilient": [r"secur(?:e|ity)\s*(?:and|&)\s*resilien"],
    "accountable-transparent": [r"accountab(?:le|ility)\s*(?:and|&)\s*transparen"],
    "explainable-interpretable": [r"explainab(?:le|ility)\s*(?:and|&)\s*interpretab"],
    "privacy-enhanced": [r"privacy[\s-]*enhanced"],
    "fair-bias-managed": [r"fair(?:ness)?\b[^.\n]{0,20}harmful bias"],
}


class AIRMFError(ValueError):
    """Input error (bad file, unknown format)."""


# ------------------------------------------------------------------ catalog access
@lru_cache(maxsize=1)
def core() -> dict:
    return load_catalog(CORE_ID)


@lru_cache(maxsize=1)
def playbook() -> dict:
    return load_catalog(PLAYBOOK_ID)


def subcategories(functions: Iterable[str] | None = None) -> list[dict]:
    fns = {normalise_function(f) for f in functions} if functions else set(FUNCTIONS)
    return [i for i in core()["items"] if i["function"] in fns]


@lru_cache(maxsize=1)
def subcategory_index() -> dict[str, dict]:
    return {i["id"]: i for i in core()["items"]}


@lru_cache(maxsize=1)
def group_index() -> dict[str, dict]:
    return {g["id"]: g for g in core()["groups"]}


def trustworthy_characteristics() -> list[dict]:
    return core()["parameters"]["trustworthy_characteristics"]


def normalise_function(name: str) -> str:
    up = str(name).strip().upper()
    up = FUNCTION_ABBREV.get(up, up)
    if up not in FUNCTIONS:
        raise AIRMFError(f"unknown AI RMF function '{name}' (expected one of {', '.join(FUNCTIONS)})")
    return up


def normalise_id(raw: str) -> str | None:
    """Canonicalise a subcategory id ('gv-1.1' -> 'GOVERN 1.1'); None if not id-shaped."""
    m = ID_EXACT_RE.match(str(raw))
    if not m:
        return None
    fn = m.group(1).upper()
    fn = FUNCTION_ABBREV.get(fn, fn)
    return f"{fn} {int(m.group(2))}.{int(m.group(3))}"


def is_valid_id(sid: str) -> bool:
    return sid in subcategory_index()


def find_ids(text: str) -> list[str]:
    """All subcategory-shaped ids in ``text`` (canonical form, in order, may include invalid ones)."""
    out = []
    for m in ID_IN_TEXT_RE.finditer(text):
        fn = m.group(1).upper()
        fn = FUNCTION_ABBREV.get(fn, fn)
        out.append(f"{fn} {int(m.group(2))}.{int(m.group(3))}")
    return out


def normalise_characteristic(raw: str) -> str | None:
    key = re.sub(r"\s+", " ", str(raw).strip().lower())
    for cid, aliases in CHARACTERISTIC_ALIASES.items():
        if key == cid or key in aliases:
            return cid
    # tolerate decorations such as "Fair (harmful bias managed)" or "Privacy-enhanced AI":
    # match the longest alias contained as a whole phrase
    best = None
    for cid, aliases in CHARACTERISTIC_ALIASES.items():
        for a in aliases:
            if re.search(rf"(?<![a-z]){re.escape(a)}(?![a-z])", key) and (best is None or len(a) > best[1]):
                best = (cid, len(a))
    return best[0] if best else None


def playbook_entries(sid: str) -> dict:
    items = [i for i in playbook()["items"] if i["subcategory"] == sid]
    return {
        "actions": [i for i in items if i["kind"] == "suggested-action"],
        "questions": [i for i in items if i["kind"] == "documentation-question"],
        "meta": playbook()["parameters"]["subcategories"].get(sid, {}),
    }


# ------------------------------------------------------------------ show / list
def show(sid: str, include_questions: bool = True) -> str:
    canon = normalise_id(sid)
    if not canon or canon not in subcategory_index():
        raise AIRMFError(f"unknown subcategory '{sid}'")
    item = subcategory_index()[canon]
    cat = group_index()[item["group"]]
    pb = playbook_entries(canon)
    cit = item["citation"]
    lines = [f"# {canon}", "",
             f"**Function:** {item['function']}  ",
             f"**Category:** {cat['id']} - {cat['title']}  ",
             f"**Source:** NIST AI 100-1 (AI RMF 1.0), {cit['section']}, PDF p. {cit['pdf_page']} "
             f"(printed p. {cit['printed_page']})", "",
             "## Outcome (verbatim)", "", f"> {item['text']}", ""]
    meta = pb["meta"]
    if meta:
        lines += [f"## Playbook suggested actions (Playbook PDF p. {meta['pdf_page']}+)", ""]
        lead = next((a.get("lead_in") for a in pb["actions"] if a.get("lead_in")), None)
        if lead:
            lines += [f"_{lead}_", ""]
        for a in pb["actions"]:
            lines.append(f"- `{a['id']}` (p. {a['citation']['pdf_page']}) {a['text']}")
            for s in a.get("sub_actions", []):
                lines.append(f"    - {s}")
        if include_questions and pb["questions"]:
            lines += ["", "## Playbook transparency & documentation questions", ""]
            for q in pb["questions"]:
                lines.append(f"- `{q['id']}` (p. {q['citation']['pdf_page']}) {q['text']}")
    lines += ["", "_Playbook actions are voluntary suggestions, not requirements._"]
    return "\n".join(lines) + "\n"


def list_subcategories(functions: Iterable[str] | None = None) -> list[dict]:
    return [{"id": i["id"], "category": i["group"], "pdf_page": i["citation"]["pdf_page"], "text": i["text"]}
            for i in subcategories(functions)]


# ------------------------------------------------------------------ generic table I/O
def _norm_header(h: str) -> str:
    h = str(h).strip().lower()
    h = re.sub(r"[^a-z0-9]+", "_", h).strip("_")
    return h


def parse_md_tables(text: str) -> list[list[dict]]:
    """Parse every pipe table in Markdown text into a list of row dicts (normalised headers)."""
    tables: list[list[dict]] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines) - 1:
        line, sep = lines[i].strip(), lines[i + 1].strip()
        if line.startswith("|") and re.match(r"^\|?\s*:?-{3,}", sep):
            headers = [_norm_header(c) for c in _split_row(line)]
            rows = []
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                cells = _split_row(lines[j].strip())
                cells += [""] * (len(headers) - len(cells))
                rows.append({h: c.strip() for h, c in zip(headers, cells)})
                j += 1
            tables.append(rows)
            i = j
        else:
            i += 1
    return tables


def _split_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line)]


def load_rows(path: Path, list_key: str) -> tuple[list[dict], dict]:
    """Load rows from YAML/JSON (list or mapping with ``list_key``), CSV or Markdown table.

    Returns (rows, metadata)."""
    path = Path(path)
    if not path.is_file():
        raise AIRMFError(f"file not found: {path}")
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix in (".yaml", ".yml", ".json"):
        try:
            data = json.loads(text) if suffix == ".json" else yaml.safe_load(text)
        except (yaml.YAMLError, json.JSONDecodeError) as exc:
            raise AIRMFError(f"cannot parse {path.name}: {exc}") from exc
        meta: dict = {}
        if isinstance(data, dict):
            meta = {k: v for k, v in data.items() if k != list_key}
            data = data.get(list_key)
        if not isinstance(data, list):
            raise AIRMFError(f"{path.name}: expected a list or a mapping with a '{list_key}' list")
        rows = []
        for n, r in enumerate(data, 1):
            if not isinstance(r, dict):
                raise AIRMFError(f"{path.name}: entry {n} is not a mapping")
            rows.append({_norm_header(k): v for k, v in r.items()})
        return rows, meta
    if suffix == ".csv":
        reader = csv.DictReader(io.StringIO(text))
        return [{_norm_header(k): (v or "").strip() for k, v in r.items() if k is not None} for r in reader], {}
    if suffix in (".md", ".markdown"):
        tables = parse_md_tables(text)
        if not tables:
            raise AIRMFError(f"{path.name}: no Markdown table found")
        return max(tables, key=len), {}
    raise AIRMFError(f"unsupported file type '{suffix}' (use .yaml, .yml, .json, .csv or .md)")


def _as_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v).strip() for v in value if str(v).strip()]
    return [p.strip() for p in re.split(r"[;|,\n]", str(value)) if p.strip()]


def _blank(value) -> bool:
    if value is None:
        return True
    if isinstance(value, (list, tuple, dict)):
        return len(value) == 0
    return str(value).strip() in ("", "-", "—", "tbd", "TBD", "?")


def _pick(row: dict, aliases: list[str]):
    for a in aliases:
        if a in row and not _blank(row[a]):
            return row[a]
    for a in aliases:
        if a in row:
            return row[a]
    return None


# ------------------------------------------------------------------ profiles
PROFILE_COLUMNS = ["function", "category", "subcategory", "outcome", "current_status", "target_status",
                   "priority", "owner", "evidence", "notes"]


def profile_template(functions: Iterable[str] | None = None, fmt: str = "md", system: str = "<AI system / scope>") -> str:
    subs = subcategories(functions)
    fns = sorted({s["function"] for s in subs}, key=FUNCTIONS.index)
    statuses = list(STATUS_LEVELS) + [NOT_APPLICABLE]
    if fmt == "yaml":
        doc = {
            "profile": {
                "system": system,
                "type": "current-and-target",
                "functions": fns,
                "date": "<YYYY-MM-DD>",
                "prepared_by": "<name/role>",
                "status_values": statuses,
                "priority_values": list(PRIORITIES),
                "source": "NIST AI 100-1 AI RMF 1.0, Tables 1-4 (PDF pp. 27-38); profiles: Section 6 (PDF p. 38)",
            },
            "subcategories": [
                {"id": s["id"], "outcome": s["text"], "current_status": "", "target_status": "", "priority": "",
                 "owner": "", "evidence": "", "notes": ""} for s in subs
            ],
        }
        return yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120)
    if fmt == "csv":
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        w.writerow(PROFILE_COLUMNS)
        for s in subs:
            w.writerow([s["function"], s["group"], s["id"], s["text"], "", "", "", "", "", ""])
        return buf.getvalue()
    if fmt != "md":
        raise AIRMFError(f"unknown format '{fmt}' (md, csv, yaml)")
    out = [f"# AI RMF current / target profile - {system}", "",
           "Source: NIST AI 100-1 (AI RMF 1.0) Tables 1-4, PDF pp. 27-38; temporal profiles per Section 6, PDF p. 38.",
           f"Status values: {', '.join(statuses)}. Priority: {', '.join(PRIORITIES)}.",
           "Evidence is required where current status is `implemented`. "
           "Validate with `python -m agentlib ai-rmf check-profile <file>`.", ""]
    for fn in fns:
        out += [f"## {fn}", "", "| Subcategory | Outcome | Current status | Target status | Priority | Owner | Evidence | Notes |",
                "|---|---|---|---|---|---|---|---|"]
        for s in subs:
            if s["function"] == fn:
                out.append(f"| {s['id']} | {s['text'].replace('|', '/')} |  |  |  |  |  |  |")
        out.append("")
    return "\n".join(out)


def _norm_status(value) -> str | None:
    if _blank(value):
        return None
    v = re.sub(r"\s+", " ", str(value).strip().lower())
    v = STATUS_ALIASES.get(v, v)
    v = v.replace(" ", "-")
    if v in STATUS_LEVELS or v == NOT_APPLICABLE:
        return v
    return "INVALID:" + str(value)


def check_profile(rows: list[dict], functions: Iterable[str] | None = None) -> dict:
    """Validate a filled current/target profile and compute a gap analysis.

    Returns a report dict with ``errors``, ``warnings``, ``gaps`` and ``summary``."""
    errors: list[str] = []
    warnings: list[str] = []
    scope = [normalise_function(f) for f in functions] if functions else list(FUNCTIONS)
    expected = [s["id"] for s in subcategories(scope)]
    seen: dict[str, dict] = {}
    for n, row in enumerate(rows, 1):
        raw_id = _pick(row, ["subcategory", "id", "subcategory_id"])
        if _blank(raw_id):
            errors.append(f"row {n}: missing subcategory id")
            continue
        sid = normalise_id(str(raw_id))
        if not sid or sid not in subcategory_index():
            errors.append(f"row {n}: unknown subcategory id '{raw_id}' (not in AI RMF 1.0 Tables 1-4)")
            continue
        if sid in seen:
            errors.append(f"{sid}: duplicate row")
            continue
        if sid.split()[0] not in scope:
            warnings.append(f"{sid}: outside declared scope ({', '.join(scope)}); ignored")
            continue
        cur = _norm_status(_pick(row, ["current_status", "current"]))
        tgt = _norm_status(_pick(row, ["target_status", "target"]))
        rec = {"id": sid, "current": cur, "target": tgt,
               "priority": str(_pick(row, ["priority"]) or "").strip().lower(),
               "owner": _pick(row, ["owner"]), "evidence": _pick(row, ["evidence"]), "notes": _pick(row, ["notes"])}
        for label, val in (("current", cur), ("target", tgt)):
            if val is None:
                errors.append(f"{sid}: {label} status missing")
            elif val.startswith("INVALID:"):
                errors.append(f"{sid}: invalid {label} status '{val[8:]}' "
                              f"(allowed: {', '.join(list(STATUS_LEVELS) + [NOT_APPLICABLE])})")
        if rec["priority"] and rec["priority"] not in PRIORITIES:
            errors.append(f"{sid}: invalid priority '{rec['priority']}' (allowed: {', '.join(PRIORITIES)})")
        if cur == "implemented" and _blank(rec["evidence"]):
            errors.append(f"{sid}: current status 'implemented' but no evidence recorded")
        elif cur == "largely-implemented" and _blank(rec["evidence"]):
            warnings.append(f"{sid}: 'largely-implemented' without evidence")
        if NOT_APPLICABLE in (cur, tgt) and _blank(rec["notes"]):
            warnings.append(f"{sid}: not-applicable without a justification in notes")
        seen[sid] = rec
    missing = [s for s in expected if s not in seen]
    for sid in missing:
        errors.append(f"{sid}: missing from profile (in scope {', '.join(scope)})")

    gaps = []
    for sid, rec in seen.items():
        cur, tgt = rec["current"], rec["target"]
        if cur in STATUS_LEVELS and tgt in STATUS_LEVELS:
            delta = STATUS_LEVELS[tgt] - STATUS_LEVELS[cur]
            if delta > 0:
                gaps.append({"id": sid, "current": cur, "target": tgt, "size": delta,
                             "priority": rec["priority"] or "unset", "owner": rec["owner"] or ""})
                if _blank(rec["owner"]):
                    warnings.append(f"{sid}: gap (target > current) has no owner")
                if not rec["priority"]:
                    warnings.append(f"{sid}: gap (target > current) has no priority")
            elif delta < 0:
                warnings.append(f"{sid}: target '{tgt}' is below current '{cur}' - confirm intent")
    prio_rank = {"high": 0, "medium": 1, "low": 2, "unset": 3}
    gaps.sort(key=lambda g: (prio_rank.get(g["priority"], 3), -g["size"], _sort_key(g["id"])))

    summary = {"by_function": OrderedDict(), "by_category": OrderedDict()}
    for sid in expected:
        if sid not in seen:
            continue
        rec = seen[sid]
        item = subcategory_index()[sid]
        for key, bucket in ((item["function"], "by_function"), (item["group"], "by_category")):
            s = summary[bucket].setdefault(key, {"subcategories": 0, "implemented": 0, "not_applicable": 0,
                                                  "gaps": 0, "high_priority_gaps": 0})
            s["subcategories"] += 1
            if rec["current"] == "implemented":
                s["implemented"] += 1
            if NOT_APPLICABLE in (rec["current"], rec["target"]):
                s["not_applicable"] += 1
    for g in gaps:
        item = subcategory_index()[g["id"]]
        for key, bucket in ((item["function"], "by_function"), (item["group"], "by_category")):
            summary[bucket][key]["gaps"] += 1
            if g["priority"] == "high":
                summary[bucket][key]["high_priority_gaps"] += 1
    return {"scope": scope, "rows": len(rows), "assessed": len(seen), "missing": missing,
            "errors": errors, "warnings": warnings, "gaps": gaps, "summary": summary, "ok": not errors}


def _sort_key(sid: str):
    fn, num = sid.split()
    a, b = num.split(".")
    return (FUNCTIONS.index(fn), int(a), int(b))


def format_profile_report(rep: dict) -> str:
    out = ["# AI RMF profile check", "",
           f"Scope: {', '.join(rep['scope'])} | rows: {rep['rows']} | assessed: {rep['assessed']} | "
           f"errors: {len(rep['errors'])} | warnings: {len(rep['warnings'])} | gaps: {len(rep['gaps'])}", ""]
    out += ["## Gap summary by function", "", "| Function | Subcategories | Implemented | Gaps | High-priority gaps | N/A |",
            "|---|---|---|---|---|---|"]
    for fn, s in rep["summary"]["by_function"].items():
        out.append(f"| {fn} | {s['subcategories']} | {s['implemented']} | {s['gaps']} | {s['high_priority_gaps']} | {s['not_applicable']} |")
    out += ["", "## Gap summary by category", "", "| Category | Subcategories | Implemented | Gaps | High-priority gaps |",
            "|---|---|---|---|---|"]
    for c, s in rep["summary"]["by_category"].items():
        out.append(f"| {c} | {s['subcategories']} | {s['implemented']} | {s['gaps']} | {s['high_priority_gaps']} |")
    out += ["", "## Gaps (target > current), highest priority first", ""]
    if rep["gaps"]:
        out += ["| Subcategory | Current | Target | Size | Priority | Owner |", "|---|---|---|---|---|---|"]
        for g in rep["gaps"]:
            out.append(f"| {g['id']} | {g['current']} | {g['target']} | {g['size']} | {g['priority']} | {g['owner']} |")
    else:
        out.append("No gaps.")
    for title, key in (("Errors", "errors"), ("Warnings", "warnings")):
        if rep[key]:
            out += ["", f"## {title}", ""] + [f"- {m}" for m in rep[key]]
    out += ["", "Result: " + ("PASS" if rep["ok"] else "FAIL")]
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------ risk register
REGISTER_COLUMNS = ["id", "description", "affected_stakeholders", "trustworthiness_characteristics", "likelihood",
                    "impact", "inherent_rating", "treatment", "controls", "residual_likelihood", "residual_impact",
                    "residual_rating", "residual_justification", "owner", "escalated_to", "accepted_by",
                    "linked_subcategories", "review_date"]


def register_template(fmt: str = "md") -> str:
    example = {
        "id": "R-001",
        "description": "<risk event, cause and consequence>",
        "affected_stakeholders": "<e.g. applicants; operators>",
        "trustworthiness_characteristics": "<e.g. fair-bias-managed; accountable-transparent>",
        "likelihood": "<1-5>", "impact": "<1-5>", "inherent_rating": "<low|medium|high|critical>",
        "treatment": "<mitigate|transfer|avoid|accept>", "controls": "<controls / actions>",
        "residual_likelihood": "<1-5>", "residual_impact": "<1-5>", "residual_rating": "<low|medium|high|critical>",
        "residual_justification": "<required if residual > inherent>", "owner": "<named role>",
        "escalated_to": "<required for high/critical residual unless accepted>",
        "accepted_by": "<name, role, date - required for accept or high/critical residual>",
        "linked_subcategories": "<e.g. MAP 5.1; MEASURE 2.11; MANAGE 1.3>", "review_date": "<YYYY-MM-DD>",
    }
    if fmt == "yaml":
        doc = {"register": {"system": "<AI system>", "scales": {
            "likelihood": "1 rare - 5 almost certain", "impact": "1 negligible - 5 severe",
            "rating_bands": "L x I: 1-4 low, 5-9 medium, 10-16 high, 20-25 critical (library convention)"}},
            "risks": [{k: example[k] for k in REGISTER_COLUMNS}]}
        return yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120)
    if fmt == "csv":
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        w.writerow(REGISTER_COLUMNS)
        w.writerow([example[k] for k in REGISTER_COLUMNS])
        return buf.getvalue()
    if fmt != "md":
        raise AIRMFError(f"unknown format '{fmt}' (md, csv, yaml)")
    head = "| " + " | ".join(c.replace("_", " ").title() for c in REGISTER_COLUMNS) + " |"
    sep = "|" + "---|" * len(REGISTER_COLUMNS)
    row = "| " + " | ".join(example[k] for k in REGISTER_COLUMNS) + " |"
    return "\n".join(["# AI risk register", "",
                      "Scales (library convention; AI RMF prescribes none): likelihood 1-5, impact 1-5, "
                      "rating bands on L x I: 1-4 low, 5-9 medium, 10-16 high, 20-25 critical.",
                      "Treatment options per AI RMF MANAGE 1.3 (PDF p. 37): mitigate, transfer, avoid, accept.",
                      "", head, sep, row, ""])


def _scale(value, words: dict) -> int | None:
    if _blank(value):
        return None
    v = str(value).strip().lower()
    if re.fullmatch(r"[1-5]", v):
        return int(v)
    return words.get(v)


def _rating(value) -> str | None:
    if _blank(value):
        return None
    v = str(value).strip().lower()
    m = re.match(r"^(\d{1,2})(?:\s*\((.*)\))?$", v)
    if m:
        return score_band(int(m.group(1)))
    m = re.match(r"^([a-z -]+?)(?:\s*\(\d+\))?$", v)
    if m:
        v = m.group(1).strip()
    v = RATING_ALIASES.get(v, v)
    return v if v in RATING_LEVELS else "INVALID:" + str(value)


def score_band(score: int) -> str:
    if not 1 <= score <= 25:
        return f"INVALID:{score}"
    for upper, band in SCORE_BANDS:
        if score <= upper:
            return band
    return "critical"


def _treatment(value) -> str | None:
    if _blank(value):
        return None
    v = str(value).strip().lower()
    first = re.split(r"[\s(:;,/-]", v)[0]
    for cand in (v, first):
        cand = TREATMENT_ALIASES.get(cand, cand)
        if cand in TREATMENTS:
            return cand
    return "INVALID:" + str(value)


def _canon_register_row(row: dict) -> dict:
    out = {}
    for field, aliases in list(REGISTER_FIELDS.items()) + list(OPTIONAL_REGISTER_FIELDS.items()):
        out[field] = _pick(row, aliases)
    return out


def check_register(rows: list[dict]) -> dict:
    """Validate an AI risk register. Returns report with errors, warnings and summary."""
    errors: list[str] = []
    warnings: list[str] = []
    risks = []
    ids_seen: set[str] = set()
    if not rows:
        errors.append("register is empty")
    for n, raw in enumerate(rows, 1):
        r = _canon_register_row(raw)
        rid = str(r["id"]).strip() if not _blank(r["id"]) else f"row {n}"
        if rid in ids_seen:
            errors.append(f"{rid}: duplicate risk id")
        ids_seen.add(rid)
        missing = [f for f in REQUIRED_REGISTER_FIELDS if _blank(r[f])]
        for f in missing:
            errors.append(f"{rid}: missing required field '{f}'")
        # characteristics
        chars = []
        for c in _as_list(r["characteristics"]):
            cid = normalise_characteristic(c)
            if cid is None:
                errors.append(f"{rid}: unknown trustworthiness characteristic '{c}'")
            else:
                chars.append(cid)
        # subcategories
        subs = []
        for s in _as_list(r["subcategories"]):
            sid = normalise_id(s)
            if not sid or sid not in subcategory_index():
                errors.append(f"{rid}: invalid AI RMF subcategory id '{s}'")
            else:
                subs.append(sid)
        # scales and ratings
        lik = _scale(r["likelihood"], LIKELIHOOD_WORDS)
        imp = _scale(r["impact"], IMPACT_WORDS)
        if not _blank(r["likelihood"]) and lik is None:
            errors.append(f"{rid}: likelihood '{r['likelihood']}' not on the 1-5 scale")
        if not _blank(r["impact"]) and imp is None:
            errors.append(f"{rid}: impact '{r['impact']}' not on the 1-5 scale")
        inh = _rating(r["inherent_rating"])
        res = _rating(r["residual_rating"])
        for label, val in (("inherent_rating", inh), ("residual_rating", res)):
            if val and val.startswith("INVALID:"):
                errors.append(f"{rid}: invalid {label} '{val[8:]}' (low, medium, high, critical or a 1-25 score)")
        inh = inh if inh in RATING_LEVELS else None
        res = res if res in RATING_LEVELS else None
        if lik and imp and inh:
            computed = score_band(lik * imp)
            if computed != inh:
                warnings.append(f"{rid}: inherent rating '{inh}' differs from likelihood x impact = {lik * imp} "
                                f"('{computed}' on the library matrix) - confirm the organisation's matrix")
        rl = _scale(r["residual_likelihood"], LIKELIHOOD_WORDS)
        ri = _scale(r["residual_impact"], IMPACT_WORDS)
        if rl and ri and res and score_band(rl * ri) != res:
            warnings.append(f"{rid}: residual rating '{res}' differs from residual L x I = {rl * ri}")
        if inh and res and RATING_LEVELS[res] > RATING_LEVELS[inh] and _blank(r["residual_justification"]):
            errors.append(f"{rid}: residual rating '{res}' exceeds inherent '{inh}' without residual_justification")
        treat = _treatment(r["treatment"])
        if treat and treat.startswith("INVALID:"):
            errors.append(f"{rid}: invalid treatment '{treat[8:]}' (mitigate, transfer, avoid, accept - MANAGE 1.3)")
            treat = None
        if treat == "accept" and _blank(r["accepted_by"]):
            errors.append(f"{rid}: treatment 'accept' requires an acceptance sign-off (accepted_by)")
        if res in ("high", "critical") and _blank(r["escalated_to"]) and _blank(r["accepted_by"]):
            errors.append(f"{rid}: residual rating '{res}' requires escalation (escalated_to) or "
                          f"acceptance sign-off (accepted_by)")
        if treat in ("mitigate", "transfer") and _blank(r["controls"]):
            warnings.append(f"{rid}: treatment '{treat}' but no controls/actions recorded")
        if treat == "mitigate" and inh and res and inh == res and _blank(r["residual_justification"]):
            warnings.append(f"{rid}: 'mitigate' did not reduce the rating ({inh}) - check controls")
        if subs and not any(s.startswith(("MANAGE", "MEASURE")) for s in subs):
            warnings.append(f"{rid}: no MEASURE or MANAGE subcategory linked (how is it measured/treated?)")
        if _blank(r["review_date"]):
            warnings.append(f"{rid}: no review date")
        risks.append({"id": rid, "characteristics": chars, "subcategories": subs, "inherent": inh,
                      "residual": res, "treatment": treat, "owner": r["owner"]})
    summary = {
        "risks": len(risks),
        "by_residual": dict(Counter(r["residual"] or "unrated" for r in risks)),
        "by_treatment": dict(Counter(r["treatment"] or "none" for r in risks)),
        "by_characteristic": dict(Counter(c for r in risks for c in r["characteristics"])),
        "functions_linked": sorted({s.split()[0] for r in risks for s in r["subcategories"]}, key=FUNCTIONS.index),
        "characteristics_not_covered": [c["id"] for c in trustworthy_characteristics()
                                        if c["id"] not in {x for r in risks for x in r["characteristics"]}],
    }
    return {"errors": errors, "warnings": warnings, "summary": summary, "risks": risks, "ok": not errors}


def format_register_report(rep: dict) -> str:
    s = rep["summary"]
    out = ["# AI risk register check", "",
           f"Risks: {s['risks']} | errors: {len(rep['errors'])} | warnings: {len(rep['warnings'])}", "",
           f"- Residual ratings: {s['by_residual']}",
           f"- Treatments: {s['by_treatment']}",
           f"- Characteristics: {s['by_characteristic']}",
           f"- Characteristics with no risk recorded: {', '.join(s['characteristics_not_covered']) or 'none'}",
           f"- AI RMF functions linked: {', '.join(s['functions_linked']) or 'none'}"]
    for title, key in (("Errors", "errors"), ("Warnings", "warnings")):
        if rep[key]:
            out += ["", f"## {title}", ""] + [f"- {m}" for m in rep[key]]
    out += ["", "Result: " + ("PASS" if rep["ok"] else "FAIL")]
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------ scanning / coverage
def scan_text(text: str) -> dict:
    ids = find_ids(text)
    valid = [i for i in dict.fromkeys(ids) if i in subcategory_index()]
    invalid = [i for i in dict.fromkeys(ids) if i not in subcategory_index()]
    by_fn = {fn: sorted({i for i in valid if i.startswith(fn + " ")}, key=_sort_key) for fn in FUNCTIONS}
    chars = [cid for cid, pats in CHARACTERISTIC_PROSE.items() if any(re.search(p, text, re.I) for p in pats)]
    return {"valid": valid, "invalid": invalid, "by_function": by_fn,
            "functions_covered": [fn for fn in FUNCTIONS if by_fn[fn]], "characteristics": chars}


# ------------------------------------------------------------------ graders
def grade_valid_subcategory_ids(output: str, check: dict) -> tuple[bool, str]:
    """Every subcategory-shaped id is a real AI RMF 1.0 subcategory; at least ``min`` (default 1) distinct."""
    rep = scan_text(output)
    need = int(check.get("min", 1))
    if rep["invalid"]:
        return False, f"invalid/invented subcategory ids: {rep['invalid']}"
    if len(rep["valid"]) < need:
        return False, f"{len(rep['valid'])} valid subcategory ids (need {need})"
    return True, f"{len(rep['valid'])} valid subcategory ids, none invalid"


def grade_function_coverage(output: str, check: dict) -> tuple[bool, str]:
    """At least ``min_per_function`` (default 1) valid subcategory ids from each of ``functions`` (default all 4)."""
    rep = scan_text(output)
    fns = [normalise_function(f) for f in check.get("functions", FUNCTIONS)]
    need = int(check.get("min_per_function", 1))
    short = {fn: len(rep["by_function"][fn]) for fn in fns if len(rep["by_function"][fn]) < need}
    if short:
        return False, f"functions below {need} subcategory reference(s): {short}"
    return True, f"covers {', '.join(fns)} (>= {need} each)"


def grade_trustworthy_characteristics(output: str, check: dict) -> tuple[bool, str]:
    """Names at least ``min`` (default 7) trustworthy characteristics, and all of ``required`` (ids) if given."""
    rep = scan_text(output)
    found = set(rep["characteristics"])
    need = int(check.get("min", 7))
    req = [normalise_characteristic(r) or r for r in check.get("required", [])]
    missing_req = [r for r in req if r not in found]
    if missing_req:
        return False, f"required characteristics not discussed: {missing_req}"
    if len(found) < need:
        return False, f"{len(found)} characteristics named (need {need}): {sorted(found)}"
    return True, f"{len(found)} characteristics named"


def grade_register_table(output: str, check: dict) -> tuple[bool, str]:
    """The largest Markdown table that looks like a risk register passes ``check_register`` (no errors).

    ``min_risks`` (default 1) sets the minimum number of rows."""
    candidates = [t for t in parse_md_tables(output)
                  if t and any(a in t[0] for a in REGISTER_FIELDS["treatment"])]
    if not candidates:
        return False, "no risk register table (with a treatment column) found"
    rows = max(candidates, key=len)
    rep = check_register(rows)
    need = int(check.get("min_risks", 1))
    if len(rows) < need:
        return False, f"{len(rows)} risks in register (need {need})"
    if rep["errors"]:
        return False, f"register errors: {rep['errors'][:5]}"
    return True, f"register with {len(rows)} risks passes check_register"


def grade_profile_table(output: str, check: dict) -> tuple[bool, str]:
    """Markdown profile table(s) with subcategory/current/target columns: valid ids and statuses,
    evidence for 'implemented'. ``functions`` restricts the completeness check; ``require_complete``
    (default false) requires every in-scope subcategory."""
    rows: list[dict] = []
    for t in parse_md_tables(output):
        if t and any(k in t[0] for k in ("current_status", "current")) and any(
                k in t[0] for k in ("subcategory", "id")):
            rows += t
    if not rows:
        return False, "no profile table (subcategory + current status columns) found"
    rep = check_profile(rows, check.get("functions"))
    errs = rep["errors"]
    if not check.get("require_complete", False):
        errs = [e for e in errs if "missing from profile" not in e]
    if errs:
        return False, f"profile errors: {errs[:5]}"
    need = int(check.get("min_gaps", 0))
    if len(rep["gaps"]) < need:
        return False, f"{len(rep['gaps'])} gaps identified (need {need})"
    return True, f"profile table valid ({rep['assessed']} rows, {len(rep['gaps'])} gaps)"


# ------------------------------------------------------------------ CLI
def _write(text: str, output: str | None) -> None:
    if output:
        Path(output).write_text(text, encoding="utf-8")
        print(f"wrote {output}")
    else:
        sys.stdout.write(text)


def _cmd(args) -> int:
    try:
        return _dispatch(args)
    except AIRMFError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _dispatch(args) -> int:
    act = args.ai_rmf_cmd
    if act == "list":
        rows = list_subcategories(args.function)
        if args.format == "json":
            print(json.dumps(rows, indent=2, ensure_ascii=False))
        else:
            for r in rows:
                text = r["text"] if args.full else (r["text"][:110] + ("..." if len(r["text"]) > 110 else ""))
                print(f"{r['id']:<13} p.{r['pdf_page']:<3} {text}")
            print(f"{len(rows)} subcategories")
        return 0
    if act == "show":
        sid = normalise_id(args.id)
        if args.format == "json":
            if not sid or sid not in subcategory_index():
                raise AIRMFError(f"unknown subcategory '{args.id}'")
            pb = playbook_entries(sid)
            print(json.dumps({"subcategory": subcategory_index()[sid], "category": group_index()[sid.rsplit('.', 1)[0]],
                              "playbook": {"actions": pb["actions"], "questions": pb["questions"],
                                           "statement": pb["meta"].get("statement")}}, indent=2, ensure_ascii=False))
        else:
            sys.stdout.write(show(args.id, include_questions=not args.no_questions))
        return 0
    if act == "characteristics":
        for c in trustworthy_characteristics():
            print(f"{c['id']:<26} {c['section']} {c['name']} (PDF p. {c['citation']['pdf_page']}): {c['summary']}")
        return 0
    if act == "profile-template":
        _write(profile_template(args.functions, args.format, args.system), args.output)
        return 0
    if act == "register-template":
        _write(register_template(args.format), args.output)
        return 0
    if act == "check-profile":
        rows, meta = load_rows(Path(args.file), "subcategories")
        fns = args.functions or ((meta.get("profile") or {}).get("functions") if isinstance(meta.get("profile"), dict) else None)
        rep = check_profile(rows, fns)
        _write(json.dumps(rep, indent=2) + "\n" if args.json else format_profile_report(rep), args.output)
        return 0 if rep["ok"] else 1
    if act == "check-register":
        rows, _ = load_rows(Path(args.file), "risks")
        rep = check_register(rows)
        _write(json.dumps(rep, indent=2) + "\n" if args.json else format_register_report(rep), args.output)
        return 0 if rep["ok"] else 1
    if act == "scan":
        p = Path(args.file)
        if not p.is_file():
            raise AIRMFError(f"file not found: {p}")
        rep = scan_text(p.read_text(encoding="utf-8"))
        if args.json:
            print(json.dumps(rep, indent=2))
        else:
            for fn in FUNCTIONS:
                print(f"{fn:<8} {len(rep['by_function'][fn]):>2}/{len(subcategories([fn]))}  {', '.join(rep['by_function'][fn])}")
            print(f"characteristics named: {', '.join(rep['characteristics']) or 'none'}")
            if rep["invalid"]:
                print(f"INVALID ids (not in AI RMF 1.0): {', '.join(rep['invalid'])}")
        return 1 if rep["invalid"] else 0
    raise AIRMFError(f"unknown sub-command {act}")


def register(subparsers) -> None:
    p = subparsers.add_parser("ai-rmf", help="NIST AI RMF 1.0 + Playbook: profiles, risk registers, lookups")
    sub = p.add_subparsers(dest="ai_rmf_cmd", required=True)

    ls = sub.add_parser("list", help="list subcategories")
    ls.add_argument("--function", action="append", choices=list(FUNCTIONS), help="repeatable")
    ls.add_argument("--format", choices=["text", "json"], default="text")
    ls.add_argument("--full", action="store_true", help="do not truncate outcome text")

    sh = sub.add_parser("show", help="show a subcategory with Playbook suggested actions")
    sh.add_argument("id", help="e.g. 'GOVERN 1.1', 'MAP-5.1', 'MS 2.11'")
    sh.add_argument("--format", choices=["md", "json"], default="md")
    sh.add_argument("--no-questions", action="store_true", help="omit transparency & documentation questions")

    sub.add_parser("characteristics", help="list the 7 trustworthy-AI characteristics")

    pt = sub.add_parser("profile-template", help="generate a current/target profile worksheet")
    pt.add_argument("--functions", nargs="+", type=str.upper, choices=list(FUNCTIONS))
    pt.add_argument("--format", choices=["md", "csv", "yaml"], default="md")
    pt.add_argument("--system", default="<AI system / scope>")
    pt.add_argument("--output", "-o")

    cp = sub.add_parser("check-profile", help="validate a filled profile and report gaps")
    cp.add_argument("file")
    cp.add_argument("--functions", nargs="+", type=str.upper, choices=list(FUNCTIONS),
                    help="scope (default: profile.functions in YAML, else all four)")
    cp.add_argument("--json", action="store_true")
    cp.add_argument("--output", "-o")

    rt = sub.add_parser("register-template", help="generate an AI risk register template")
    rt.add_argument("--format", choices=["md", "csv", "yaml"], default="md")
    rt.add_argument("--output", "-o")

    cr = sub.add_parser("check-register", help="validate an AI risk register (YAML/CSV/MD)")
    cr.add_argument("file")
    cr.add_argument("--json", action="store_true")
    cr.add_argument("--output", "-o")

    sc = sub.add_parser("scan", help="report AI RMF subcategory ids referenced in a document")
    sc.add_argument("file")
    sc.add_argument("--json", action="store_true")

    p.set_defaults(func=_cmd)
