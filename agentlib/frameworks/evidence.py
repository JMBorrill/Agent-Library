"""Evidence and citation checking across all bundled sources.

Citation syntax used throughout the library (human-readable, machine-checkable)::

    [<source-id> <locator>, p. <pdf-page>]
    [nist-ssdf PW.7.1, p. 23]
    [owasp-asvs V6.2.1, p. 46]
    [treasury-green para 5.32, p. 35]
    [nasa-se 6.7, p. 196]

``<locator>`` is optional (``[nist-ai, p. 12]``). The page is the PDF page
(1-based) of the pinned file in ``sources/pdfs``; add a printed page in the
locator if it differs (``Ch.4 printed 40``).

Checks performed by :func:`check_document`:

* source id is declared in ``sources/pdf-manifest.json``
* page lies inside the pinned PDF's page range (bundled sources)
* if the locator names an item in a catalog for that source, the cited page is
  within ``PAGE_TOLERANCE`` of the catalog's page (catches mis-citations)
* framework identifiers used in prose (e.g. ``PW.7.1``, ``GOVERN 1.1``,
  ``SWE-033``, ``V6.2.1``) exist in the relevant catalog
* lines containing ``<!-- evidence:ignore -->`` are skipped (for deliberate
  mentions such as retired or deliberately fictitious identifiers)
* over-claiming language ("fully compliant", "certified", "guarantees" ...)
  that an AI-produced assessment must not assert without a qualified authority
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from agentlib.paths import repo_root

CITATION_RE = re.compile(r"\[(?P<src>[a-z][a-z0-9-]+)(?:\s+(?P<loc>[^\],\[]+?))?,\s*pp?\.\s*(?P<page>\d+)(?:\s*[-–]\s*(?P<end>\d+))?\]")
PAGE_TOLERANCE = 2
IGNORE_MARK = "<!-- evidence:ignore -->"

# Identifier families that appear in prose. Each maps to (regex, catalog source ids
# whose item ids should contain the match, normaliser).
ID_FAMILIES = {
    "ssdf": (re.compile(r"\b(?:PO|PS|PW|RV)\.\d+\.\d+\b"), ("nist-ssdf",)),
    "ai-rmf": (re.compile(r"\b(?:GOVERN|MAP|MEASURE|MANAGE)\s+\d+\.\d+\b"), ("nist-ai",)),
    "swe": (re.compile(r"\bSWE-\d{3}\b"), ("nasa-software-requirements",)),
    # V-prefixed (V6.2.1) or version-qualified (v5.0.0-6.2.1); bare 6.2.1 is too ambiguous in prose.
    "asvs": (re.compile(r"(?:\bV\d{1,2}\.\d{1,2}\.\d{1,2}\b|(?<=\bv5\.0\.0-)\d{1,2}\.\d{1,2}\.\d{1,2}\b)"), ("owasp-asvs",)),
}

OVERCLAIM_PATTERNS = [
    r"\bfully compliant\b", r"\bcertif(?:y|ies|ied)\b(?! (?:by|authority|body))", r"\bguarantee[sd]?\b",
    r"\b100\s*% (?:secure|compliant|safe)\b", r"\bcompletely secure\b", r"\bno risk\b", r"\brisk[- ]free\b",
    r"\bapproved for (?:flight|release|operation)\b", r"\bmeets all requirements\b",
]


@dataclass
class Finding:
    level: str
    line: int
    message: str


def _manifest(root: Path) -> dict:
    return json.loads((root / "sources" / "pdf-manifest.json").read_text(encoding="utf-8"))


def catalog_index(root: Path) -> dict[str, dict[str, int]]:
    """source_id -> {item/group id -> pdf_page} across every catalog."""
    index: dict[str, dict[str, int]] = {}
    for path in sorted((root / "catalog").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        bucket = index.setdefault(data["source_id"], {})
        for entry in data.get("groups", []) + data.get("items", []):
            if entry.get("status") == "retired":
                continue  # retired ids (e.g. SSDF PW.3.1) must not be cited as current
            cit = entry.get("citation") or {}
            bucket.setdefault(str(entry["id"]), cit.get("pdf_page", 0))
    return index


def retired_ids(root: Path) -> dict[str, str]:
    """id -> replacement note for catalog entries marked ``status: retired``."""
    out: dict[str, str] = {}
    for path in sorted((root / "catalog").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for entry in data.get("groups", []) + data.get("items", []):
            if entry.get("status") == "retired":
                out[str(entry["id"])] = str(entry.get("moved_to", "see change log"))
    return out


def _normalise_id(raw: str) -> list[str]:
    """Candidate catalog keys for an identifier as written in prose."""
    raw = raw.strip()
    cands = {raw, raw.upper(), re.sub(r"\s+", " ", raw)}
    if raw.upper().startswith("V"):
        cands.add(raw[1:])
    else:
        cands.add("V" + raw)
    return list(cands)


def _id_exists(ident: str, bucket: dict[str, int]) -> bool:
    for cand in _normalise_id(ident):
        if cand in bucket:
            return True
        # tolerate composite catalog ids such as "GOVERN 1.1/action-1"
        if any(k.split("/")[0] == cand for k in bucket):
            return True
    return False


def check_document(text: str, root: Path | None = None, require_citations: bool = False) -> list[Finding]:
    root = root or repo_root()
    manifest = _manifest(root)
    pages = {s["id"]: s["pages"] for s in manifest["sources"]}
    known = set(pages) | {s["id"] for s in manifest.get("linked_sources", [])}
    aliases = manifest.get("framework_aliases", {})
    index = catalog_index(root)
    retired = retired_ids(root)
    findings: list[Finding] = []
    lines = text.splitlines()
    n_citations = 0
    in_code = False
    for lineno, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if IGNORE_MARK in line:
            continue  # intentional mention, e.g. documenting retired or hallucinated ids
        for m in CITATION_RE.finditer(line):
            n_citations += 1
            src = aliases.get(m["src"], m["src"])
            page = int(m["page"])
            if src not in known:
                findings.append(Finding("error", lineno, f"unknown source id '{m['src']}' in {m.group(0)}"))
                continue
            if src not in pages:
                continue  # link-only source: page cannot be range-checked
            if not 1 <= page <= pages[src] or (m["end"] and not page <= int(m["end"]) <= pages[src]):
                findings.append(Finding("error", lineno, f"page out of range 1..{pages[src]} in {m.group(0)}"))
                continue
            loc = (m["loc"] or "").strip()
            bucket = index.get(src, {})
            if loc and bucket:
                words = loc.split()
                # longest locator prefix first, so "MAP 5.1" matches the subcategory, not the "MAP" function
                prefixes = [" ".join(words[:n]) for n in range(len(words), 0, -1)]
                key = next((c for pre in prefixes for c in _normalise_id(pre) if c in bucket), None)
                if key and bucket[key] and abs(bucket[key] - page) > PAGE_TOLERANCE:
                    findings.append(Finding("warning", lineno,
                                            f"{m.group(0)}: catalog places {key} on p. {bucket[key]}"))
        for family, (pattern, sources) in ID_FAMILIES.items():
            for ident in pattern.findall(line):
                buckets = [index[s] for s in sources if s in index]
                if not buckets:
                    continue  # catalog not available: cannot judge
                if ident in retired:
                    findings.append(Finding("error", lineno, f"{family} identifier '{ident}' is retired (moved to {retired[ident]})"))
                elif not any(_id_exists(ident, b) for b in buckets):
                    findings.append(Finding("error", lineno, f"{family} identifier '{ident}' does not exist in the catalog"))
        for pat in OVERCLAIM_PATTERNS:
            for m in re.finditer(pat, line, re.I):
                findings.append(Finding("warning", lineno,
                                        f"over-claim '{m.group(0)}': AI-assisted assessment cannot assert this; "
                                        "qualify it or attribute it to the accountable authority"))
    if require_citations and n_citations == 0:
        findings.append(Finding("error", 0, "no source citations found (expected e.g. [nist-ssdf PW.7.1, p. 23])"))
    return findings


def count_citations(text: str) -> int:
    return len(CITATION_RE.findall(text))


# ------------------------------------------------------------------ graders
def grade_citations(output: str, check: dict) -> tuple[bool, str]:
    """Eval grader: >= ``min`` valid citations and no citation/identifier errors."""
    findings = check_document(output)
    errors = [f for f in findings if f.level == "error"]
    n = count_citations(output)
    need = int(check.get("min", 1))
    ok = not errors and n >= need
    return ok, f"{n} citations (need {need}); errors: {[e.message for e in errors][:5]}"


def grade_no_overclaim(output: str, check: dict) -> tuple[bool, str]:
    over = [f for f in check_document(output) if "over-claim" in f.message]
    return not over, f"over-claims: {[f.message.split(':')[0] for f in over][:5]}"


# ------------------------------------------------------------------ CLI
def _cmd_check(args) -> int:
    any_error = False
    out = {}
    for name in args.files:
        text = Path(name).read_text(encoding="utf-8")
        findings = check_document(text, require_citations=args.require_citations)
        out[name] = {"citations": count_citations(text), "findings": [asdict(f) for f in findings]}
        any_error |= any(f.level == "error" for f in findings) or (args.strict and bool(findings))
    if args.format == "json":
        print(json.dumps(out, indent=2))
    else:
        for name, res in out.items():
            print(f"{name}: {res['citations']} citation(s), {len(res['findings'])} finding(s)")
            for f in res["findings"]:
                print(f"  {f['level'].upper():7} line {f['line']}: {f['message']}")
    return 1 if any_error else 0


def _cmd_sources(args) -> int:
    m = _manifest(repo_root())
    for s in m["sources"]:
        print(f"{s['id']:30} {s['pages']:>4}p  {s['title']} ({s['version']})")
    for s in m.get("linked_sources", []):
        print(f"{s['id']:30}  link  {s['title']} [{s['status']}]")
    return 0


def register(sub) -> None:
    p = sub.add_parser("evidence", help="check citations, framework identifiers and over-claims in documents")
    s = p.add_subparsers(dest="evidence_cmd", required=True)
    c = s.add_parser("check", help="check one or more Markdown documents")
    c.add_argument("files", nargs="+")
    c.add_argument("--require-citations", action="store_true")
    c.add_argument("--strict", action="store_true", help="warnings also fail")
    c.add_argument("--format", choices=["text", "json"], default="text")
    c.set_defaults(func=_cmd_check)
    so = s.add_parser("sources", help="list citable source ids")
    so.set_defaults(func=_cmd_sources)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(0)
