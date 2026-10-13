"""OWASP Application Security Verification Standard (ASVS) 5.0.0 tools.

Deterministic helpers over ``catalog/owasp-asvs-5.json`` (extracted by
``scripts/extract/asvs.py`` from the pinned PDF, source id ``owasp-asvs``).
ASVS content: Copyright (c) 2008-2025 The OWASP Foundation, CC BY-SA 4.0.

CLI (``python -m agentlib asvs ...``)::

    asvs chapters [--sections] [--format md|json]
    asvs show <id> [--format md|json]
    asvs search <text...> [--level N] [--chapters V1 V6.2] [--format md|json]
    asvs checklist --level N [--chapters ...] [--format md|csv|yaml|json] [-o FILE]
    asvs check-assessment <file> --level N [--chapters ...] [--strict] [--format md|json]
    asvs map-findings <file> [--top K] [--min-score S] [--format md|json]

Identifiers follow the document: ``<chapter>.<section>.<requirement>`` (e.g.
``1.2.5``; PDF p. 16). ``V1.2.5`` and the version-qualified ``v5.0.0-1.2.5``
are accepted on input; identifiers qualified with another version are
rejected. Levels are cumulative (PDF pp. 13-14): a level-N scope contains every
requirement whose level is <= N.

Exit codes: 0 ok; 1 assessment invalid/incomplete (or has failures with
``--strict``); 2 usage or input error.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import re
import sys
from functools import lru_cache
from pathlib import Path

import yaml

from agentlib.paths import load_catalog

CATALOG_ID = "owasp-asvs-5"
VERSION = "5.0.0"
STATUSES = ("pass", "fail", "not-applicable", "not-verified")
STATUS_ALIASES = {
    "passed": "pass", "ok": "pass", "compliant": "pass",
    "failed": "fail", "non-compliant": "fail",
    "n/a": "not-applicable", "na": "not-applicable", "not applicable": "not-applicable",
    "not_applicable": "not-applicable",
    "not verified": "not-verified", "not_verified": "not-verified", "untested": "not-verified",
}
FINDING_KEYS = ("finding_ref", "finding", "findings", "finding_id", "issue", "ticket")
JUSTIFICATION_KEYS = ("justification", "rationale", "reason", "na_justification")


class AsvsError(ValueError):
    """Bad identifier, filter or input file."""


# --------------------------------------------------------------------------- catalog access
@lru_cache(maxsize=1)
def catalog() -> dict:
    return load_catalog(CATALOG_ID)


def requirements() -> list[dict]:
    return catalog()["items"]


@lru_cache(maxsize=1)
def _index() -> dict[str, dict]:
    return {r["id"]: r for r in requirements()}


@lru_cache(maxsize=1)
def _groups() -> dict[str, dict]:
    return {g["id"]: g for g in catalog()["groups"]}


def chapters() -> list[dict]:
    return [g for g in catalog()["groups"] if g.get("kind") == "chapter"]


def sections(chapter: str | None = None) -> list[dict]:
    return [g for g in catalog()["groups"] if g.get("kind") == "section" and (chapter is None or g["parent"] == chapter)]


def sort_key(rid: str) -> tuple[int, ...]:
    return tuple(int(p) for p in rid.split("."))


_ID_RE = re.compile(r"^(?:v(?P<ver>\d+\.\d+\.\d+)-)?v?(?P<id>\d+\.\d+\.\d+)$", re.I)


def normalize_id(raw: str) -> str:
    """Return the canonical ``c.s.r`` id or raise :class:`AsvsError`.

    Accepts ``1.2.5``, ``V1.2.5`` and ``v5.0.0-1.2.5``. Does not check existence.
    """
    s = str(raw).strip()
    s = re.sub(r"^(?:owasp[\s-]*)?asvs[\s:-]*", "", s, flags=re.I)
    m = _ID_RE.match(s)
    if not m:
        raise AsvsError(f"not an ASVS requirement identifier: {raw!r}")
    if m.group("ver") and m.group("ver") != VERSION:
        raise AsvsError(f"{raw!r} refers to ASVS {m.group('ver')}; this catalog is ASVS {VERSION}")
    return ".".join(str(int(p)) for p in m.group("id").split("."))


def get(raw: str) -> dict:
    rid = normalize_id(raw)
    try:
        return _index()[rid]
    except KeyError:
        raise AsvsError(f"unknown ASVS {VERSION} requirement: {rid}") from None


def exists(raw: str) -> bool:
    try:
        get(raw)
        return True
    except AsvsError:
        return False


def normalize_scope(tokens: list[str] | None) -> list[str]:
    """Normalise chapter/section filters: ``V1``, ``1``, ``v6.2``, ``6.2`` -> ``V1``, ``V6.2``."""
    out = []
    for tok in tokens or []:
        for part in re.split(r"[,\s]+", str(tok).strip()):
            if not part:
                continue
            m = re.match(r"^v?(\d+)(?:\.(\d+))?$", part, re.I)
            if not m:
                raise AsvsError(f"not a chapter/section reference: {part!r} (use e.g. V1 or V6.2)")
            gid = f"V{int(m.group(1))}" + (f".{int(m.group(2))}" if m.group(2) else "")
            if gid not in _groups():
                raise AsvsError(f"unknown ASVS {VERSION} chapter/section: {gid}")
            if gid not in out:
                out.append(gid)
    return out


def _in_scope(req: dict, scope: list[str]) -> bool:
    return not scope or req["chapter"] in scope or req["group"] in scope


def select(level: int = 3, scope: list[str] | None = None) -> list[dict]:
    """All requirements at or below ``level`` (levels are cumulative) within ``scope``."""
    if level not in (1, 2, 3):
        raise AsvsError("level must be 1, 2 or 3")
    scope = normalize_scope(scope)
    return [r for r in requirements() if r["level"] <= level and _in_scope(r, scope)]


def search(text: str, level: int = 3, scope: list[str] | None = None) -> list[dict]:
    """Requirements whose text, section or chapter title contains every term (case-insensitive)."""
    terms = [t.lower() for t in re.findall(r"\S+", text)]
    if not terms:
        raise AsvsError("empty search")
    groups = _groups()
    out = []
    for r in select(level, scope):
        hay = " ".join([r["id"], r["text"], groups[r["group"]]["title"], groups[r["chapter"]]["title"]]).lower()
        if all(t in hay for t in terms):
            out.append(r)
    return out


# --------------------------------------------------------------------------- checklist
CHECKLIST_COLUMNS = ("id", "chapter", "section", "level", "requirement", "status", "evidence", "finding_ref", "justification")


def checklist_rows(level: int, scope: list[str] | None = None) -> list[dict]:
    groups = _groups()
    return [{
        "id": r["id"],
        "chapter": f"{r['chapter']} {groups[r['chapter']]['title']}",
        "section": f"{r['group']} {groups[r['group']]['title']}",
        "level": r["level"],
        "requirement": r["text"],
        "status": "not-verified",
        "evidence": "",
        "finding_ref": "",
        "justification": "",
        "pdf_page": r["citation"]["pdf_page"],
    } for r in select(level, scope)]


def render_checklist(level: int, scope: list[str] | None, fmt: str) -> str:
    scope = normalize_scope(scope)
    rows = checklist_rows(level, scope)
    meta = {
        "standard": f"OWASP ASVS {VERSION}",
        "target_level": level,
        "scope": scope or "all chapters",
        "requirement_count": len(rows),
        "note": "Levels are cumulative: all requirements at or below the target level are in scope.",
        "statuses": list(STATUSES),
        "license": "ASVS content (c) The OWASP Foundation, CC BY-SA 4.0",
    }
    if fmt == "json":
        return json.dumps({**meta, "results": rows}, indent=2, ensure_ascii=False) + "\n"
    if fmt == "yaml":
        return yaml.safe_dump({**meta, "results": rows}, sort_keys=False, allow_unicode=True, width=120)
    if fmt == "csv":
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=list(CHECKLIST_COLUMNS) + ["pdf_page"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
        return buf.getvalue()
    # markdown
    lines = [f"# OWASP ASVS {VERSION} verification checklist - Level {level}", "",
             f"Scope: {', '.join(scope) if scope else 'all chapters (V1-V17)'}. "
             f"{len(rows)} requirements (levels are cumulative: L1..L{level}).",
             f"Statuses: {', '.join(STATUSES)}. A `fail` needs a finding reference; "
             "`not-applicable` needs a justification.", ""]
    current = None
    for r in rows:
        if r["chapter"] != current:
            current = r["chapter"]
            lines += ["", f"## {current}", "", "| ID | L | Requirement | Status | Evidence / finding |",
                      "|---|---|---|---|---|"]
        text = r["requirement"].replace("|", "\\|")
        lines.append(f"| {r['id']} | {r['level']} | {text} | not-verified | |")
    lines += ["", f"Source: OWASP ASVS {VERSION} (May 2025), The OWASP Foundation, CC BY-SA 4.0."]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- assessment validation
def load_structured(path: Path) -> object:
    """Load JSON, YAML or CSV (CSV -> list of dicts)."""
    if not path.is_file():
        raise AsvsError(f"file not found: {path}")
    text = path.read_text(encoding="utf-8-sig")
    suffix = path.suffix.lower()
    try:
        if suffix == ".csv":
            return list(csv.DictReader(io.StringIO(text)))
        if suffix == ".json":
            return json.loads(text)
        return yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError, csv.Error) as exc:
        raise AsvsError(f"cannot parse {path}: {exc}") from exc


def _first(entry: dict, keys: tuple[str, ...]) -> str:
    for k in keys:
        v = entry.get(k)
        if v not in (None, "", []):
            return ", ".join(map(str, v)) if isinstance(v, list) else str(v).strip()
    return ""


def _entries(data: object) -> tuple[list[dict], dict]:
    if isinstance(data, list):
        return data, {}
    if isinstance(data, dict):
        for key in ("results", "requirements", "assessment", "items"):
            if isinstance(data.get(key), list):
                return data[key], data
        # mapping form {id: status} or {id: {status: ...}}
        if data and all(re.match(r"^v?[\d.]+(-[\d.]+)?$", str(k), re.I) for k in data):
            out = []
            for k, v in data.items():
                out.append({"id": k, **v} if isinstance(v, dict) else {"id": k, "status": v})
            return out, {}
    raise AsvsError("assessment must be a list of results or a mapping with a 'results' list")


def check_assessment(data: object, level: int | None = None, scope: list[str] | None = None) -> dict:
    """Validate a filled assessment and compute per-chapter compliance.

    ``level``/``scope`` default to the file's ``level``/``target_level`` and
    ``scope``/``chapters`` keys. Returns a report dict; ``report['valid']`` is
    False when there are errors, ``report['complete']`` is False when any
    in-scope requirement is missing or ``not-verified``.
    """
    entries, meta = _entries(data)
    if level is None:
        level = meta.get("target_level", meta.get("level"))
    try:
        level = int(level)
    except (TypeError, ValueError):
        raise AsvsError("target level not given (use --level or a 'level' key)") from None
    if scope is None:
        raw_scope = meta.get("chapters", meta.get("scope"))
        scope = raw_scope if isinstance(raw_scope, list) else []
    scope = normalize_scope(scope)
    in_scope = {r["id"]: r for r in select(level, scope)}

    errors: list[dict] = []
    warnings: list[dict] = []
    seen: dict[str, dict] = {}
    for n, e in enumerate(entries, start=1):
        if not isinstance(e, dict):
            errors.append({"entry": n, "id": None, "problem": "entry is not a mapping"})
            continue
        raw_id = e.get("id") or e.get("requirement_id") or e.get("asvs_id")
        if not raw_id:
            errors.append({"entry": n, "id": None, "problem": "missing id"})
            continue
        try:
            rid = get(str(raw_id))["id"]
        except AsvsError as exc:
            errors.append({"entry": n, "id": str(raw_id), "problem": f"unknown id: {exc}"})
            continue
        if rid in seen:
            errors.append({"entry": n, "id": rid, "problem": "duplicate entry"})
            continue
        status_raw = str(e.get("status", "")).strip().lower()
        status = STATUS_ALIASES.get(status_raw, status_raw)
        rec = {"id": rid, "status": status, "finding_ref": _first(e, FINDING_KEYS),
               "justification": _first(e, JUSTIFICATION_KEYS), "evidence": _first(e, ("evidence", "notes"))}
        seen[rid] = rec
        if status not in STATUSES:
            errors.append({"entry": n, "id": rid, "problem": f"invalid status {e.get('status')!r}; use one of {', '.join(STATUSES)}"})
            continue
        if status == "fail" and not rec["finding_ref"]:
            errors.append({"entry": n, "id": rid, "problem": "status 'fail' without a finding reference"})
        if status == "not-applicable" and not rec["justification"]:
            errors.append({"entry": n, "id": rid, "problem": "status 'not-applicable' without a justification"})
        if rid not in in_scope:
            req = _index()[rid]
            why = (f"level {req['level']} is above target level {level} (recommendation only)"
                   if req["level"] > level else "outside the declared chapter scope")
            warnings.append({"entry": n, "id": rid, "problem": f"not in scope: {why}; excluded from compliance"})

    missing = sorted((rid for rid in in_scope if rid not in seen), key=sort_key)
    for rid in missing:
        errors.append({"entry": None, "id": rid, "problem": "in-scope requirement has no result"})

    groups = _groups()
    per_chapter: dict[str, dict] = {}
    for rid, req in in_scope.items():
        ch = per_chapter.setdefault(req["chapter"], {"chapter": req["chapter"], "title": groups[req["chapter"]]["title"],
                                                     "in_scope": 0, "pass": 0, "fail": 0, "not-applicable": 0,
                                                     "not-verified": 0, "missing": 0, "invalid": 0})
        ch["in_scope"] += 1
        rec = seen.get(rid)
        if rec is None:
            ch["missing"] += 1
        elif rec["status"] in STATUSES:
            ch[rec["status"]] += 1
        else:
            ch["invalid"] += 1

    def pct(c: dict) -> float | None:
        applicable = c["in_scope"] - c["not-applicable"]
        return round(100.0 * c["pass"] / applicable, 1) if applicable else None

    chapters_out = sorted(per_chapter.values(), key=lambda c: int(c["chapter"][1:]))
    for c in chapters_out:
        c["compliance_pct"] = pct(c)
    totals = {k: sum(c[k] for c in chapters_out) for k in ("in_scope", "pass", "fail", "not-applicable", "not-verified", "missing", "invalid")}
    totals["compliance_pct"] = pct(totals)
    failures = [{"id": rid, "level": in_scope[rid]["level"], "finding_ref": seen[rid]["finding_ref"],
                 "requirement": in_scope[rid]["text"]}
                for rid in sorted(in_scope, key=sort_key) if seen.get(rid, {}).get("status") == "fail"]
    not_verified = sorted((rid for rid in in_scope if seen.get(rid, {}).get("status") == "not-verified"), key=sort_key)
    complete = not missing and not not_verified and totals["invalid"] == 0
    valid = not errors
    return {
        "standard": f"OWASP ASVS {VERSION}",
        "target_level": level,
        "scope": scope or ["V1-V17 (all)"],
        "valid": valid,
        "complete": complete,
        "compliant": valid and complete and totals["fail"] == 0,
        "totals": totals,
        "chapters": chapters_out,
        "failures": failures,
        "not_verified": not_verified,
        "missing": missing,
        "errors": errors,
        "warnings": warnings,
        "compliance_definition": "pass / (in-scope - not-applicable) x 100; missing, invalid and not-verified count as not passed",
    }


def render_assessment(rep: dict) -> str:
    t = rep["totals"]
    verdict = ("COMPLIANT" if rep["compliant"] else
               "INVALID" if not rep["valid"] else "INCOMPLETE" if not rep["complete"] else "NOT COMPLIANT (failures)")
    lines = [f"# ASVS {VERSION} assessment check - Level {rep['target_level']}", "",
             f"- Scope: {', '.join(rep['scope'])}",
             f"- Verdict: **{verdict}** (valid={rep['valid']}, complete={rep['complete']})",
             f"- In scope: {t['in_scope']} | pass {t['pass']} | fail {t['fail']} | N/A {t['not-applicable']} | "
             f"not-verified {t['not-verified']} | missing {t['missing']} | invalid {t['invalid']}",
             f"- Compliance: {_fmt_pct(t['compliance_pct'])} ({rep['compliance_definition']})", "",
             "## Per-chapter results", "",
             "| Chapter | In scope | Pass | Fail | N/A | Not verified | Missing | Compliance |",
             "|---|---|---|---|---|---|---|---|"]
    for c in rep["chapters"]:
        lines.append(f"| {c['chapter']} {c['title']} | {c['in_scope']} | {c['pass']} | {c['fail']} | "
                     f"{c['not-applicable']} | {c['not-verified']} | {c['missing']} | {_fmt_pct(c['compliance_pct'])} |")
    lines += ["", "## Failures", ""]
    lines += [f"- {f['id']} (L{f['level']}) - finding {f['finding_ref'] or 'MISSING'}: {f['requirement']}" for f in rep["failures"]] or ["- none"]
    lines += ["", "## Errors", ""]
    lines += [f"- {e['id'] or 'entry ' + str(e['entry'])}: {e['problem']}" for e in rep["errors"]] or ["- none"]
    if rep["warnings"]:
        lines += ["", "## Warnings", ""] + [f"- {w['id']}: {w['problem']}" for w in rep["warnings"]]
    return "\n".join(lines) + "\n"


def _fmt_pct(v: float | None) -> str:
    return "n/a" if v is None else f"{v:.1f}%"


# --------------------------------------------------------------------------- finding mapping
# Keyword index: tokens from each requirement's text (weight 1.0), its section
# title (weight 1.5) and chapter title (weight 0.5), weighted by inverse document
# frequency over the 345 requirements (text BM25 length-normalised, plus a
# bonus for query bigrams found verbatim). Query expansion uses SYNONYMS below. The
# CWE_SECTION_HINTS table is authored by this library (ASVS 5.0 deliberately
# dropped CWE mappings, PDF p. 23) and only adds a fixed bonus to requirements in
# the hinted sections; it is a heuristic, not an official mapping.
STOPWORDS = set("""a an and are as at be been by can could do does for from has have if in into is it its may
must no not of on or other such than that the their them then there these this those to use used uses using
verify was were when where which while who will with within without e.g i.e application applications ensure
ensures only all any each also should being based example""".split())
FIELD_WEIGHTS = {"text": 1.0, "section": 1.5, "chapter": 0.5}
CWE_BONUS = 5.0
BIGRAM_MIN_IDF = 2.0
SYNONYMS = {
    "xss": "cross site scripting output encoding html",
    "sqli": "sql injection database parameterized queries",
    "sql": "sql database parameterized queries injection",
    "csrf": "csrf cross-origin cors sensitive functionality cookie samesite",
    "xsrf": "csrf cross-origin cors",
    "ssrf": "server-side request forgery ssrf",
    "httponly": "cookie httponly attribute",
    "xxe": "xml parsers external entities",
    "idor": "authorization data-specific access object permissions",
    "bola": "authorization data-specific access object permissions",
    "bfla": "authorization function-level access permissions",
    "jwt": "self-contained tokens token signature algorithms",
    "mfa": "multi-factor authentication",
    "2fa": "multi-factor authentication",
    "otp": "one-time multi-factor authentication",
    "brute": "brute force credential stuffing anti-automation",
    "bruteforce": "brute force credential stuffing anti-automation",
    "enumeration": "valid users deduced failed authentication error messages",
    "clickjacking": "frame-ancestors content-security-policy",
    "hsts": "strict-transport-security hsts",
    "tls": "tls certificates encrypted",
    "ssl": "tls certificates",
    "rce": "command injection code execution eval deserialization",
    "deserialization": "deserialization untrusted object types",
    "traversal": "file paths path user-submitted filenames",
    "upload": "file upload accepts extension content",
    "redirect": "redirect url hostname domain",
    "cors": "cors access-control-allow-origin origin",
    "secrets": "secrets management key vault",
    "hardcoded": "secrets management key vault source code",
    "logging": "log logs logging security events",
    "logout": "session termination logout",
    "session": "session tokens timeout termination",
    "rate": "anti-automation excessive calls",
    "dos": "availability resource-demanding anti-automation",
    "debug": "debug modes production information leakage",
    "stacktrace": "stack trace error handling",
    "verbose": "error messages information leakage",
    "password": "password passwords",
    "hash": "hash hashing password storage key derivation",
    "md5": "approved hash functions",
    "sha1": "approved hash functions",
    "ecb": "block modes cipher",
    "dependency": "components third-party dependencies remediation",
    "outdated": "components update remediation",
    "cve": "components update remediation",
    "cookie": "cookie secure httponly samesite",
    "prototype": "prototype pollution",
    "race": "concurrency race condition",
    "toctou": "concurrency race condition",
    "oauth": "oauth authorization server client",
    "oidc": "oidc openid provider id token",
    "pii": "sensitive data personal",
}
CWE_SECTION_HINTS: dict[int, tuple[str, ...]] = {
    20: ("V2.2",), 22: ("V5.3",), 23: ("V5.3",), 77: ("V1.2",), 78: ("V1.2",), 79: ("V1.2", "V1.3", "V3.2"),
    89: ("V1.2",), 90: ("V1.2",), 94: ("V1.3",), 95: ("V1.3",), 117: ("V16.4",), 200: ("V13.4", "V14.2"),
    209: ("V16.5", "V13.4"), 284: ("V8.2", "V8.3"), 285: ("V8.2", "V8.3"), 287: ("V6.3",), 295: ("V12.3", "V12.1"),
    307: ("V6.3",), 311: ("V14.2", "V12.1"), 312: ("V14.2",), 319: ("V12.1", "V12.2"), 326: ("V11.3",),
    327: ("V11.3", "V11.2"), 330: ("V11.5",), 338: ("V11.5",), 345: ("V3.6",), 346: ("V3.4", "V3.5"),
    347: ("V9.1",), 352: ("V3.5", "V3.3"), 359: ("V14.2",), 362: ("V15.4",), 367: ("V15.4",), 384: ("V7.2",),
    400: ("V15.2", "V2.4"), 434: ("V5.2",), 489: ("V13.4",), 502: ("V1.5",), 521: ("V6.2",), 525: ("V14.3",),
    532: ("V16.2",), 548: ("V13.4",), 601: ("V3.7",), 611: ("V1.5",), 613: ("V7.3", "V7.4"), 614: ("V3.3",),
    639: ("V8.2",), 643: ("V1.2",), 770: ("V2.4", "V15.2"), 778: ("V16.3",), 798: ("V13.3",), 799: ("V2.4",),
    829: ("V3.6", "V15.2"), 840: ("V2.3",), 841: ("V2.3",), 862: ("V8.2", "V8.3"), 863: ("V8.2", "V8.3"),
    915: ("V15.3",), 916: ("V11.4",), 918: ("V1.3",), 942: ("V3.4",), 1004: ("V3.3",), 1021: ("V3.4",),
    1035: ("V15.2",), 1104: ("V15.2",), 1236: ("V1.2",), 1275: ("V3.3",), 1321: ("V15.3",), 1336: ("V1.3",),
}


def tokenize(text: str) -> list[str]:
    """Lower-case word tokens, hyphenated words split, stopwords/numbers dropped, light suffix stemming."""
    toks = re.findall(r"[a-z0-9]+", text.lower())
    return [_stem(t) for t in toks if t not in STOPWORDS and len(t) > 1 and not t.isdigit()]


def _stem(t: str) -> str:
    for suf in ("ation", "ing", "ies", "es", "ed", "s"):
        if t.endswith(suf) and len(t) - len(suf) >= 4:
            return t[: -len(suf)] + ("y" if suf == "ies" else "")
    return t


@lru_cache(maxsize=1)
def keyword_index() -> dict:
    """Per-requirement token sets for text/section/chapter, token sequence, IDF and text lengths."""
    groups = _groups()
    docs = {}
    df: dict[str, int] = {}
    for r in requirements():
        seq = tokenize(r["text"])
        fields = {"text": set(seq), "section": set(tokenize(groups[r["group"]]["title"])),
                  "chapter": set(tokenize(groups[r["chapter"]]["title"]))}
        docs[r["id"]] = {**fields, "bigrams": set(zip(seq, seq[1:])), "length": len(seq)}
        for tok in set().union(*fields.values()):
            df[tok] = df.get(tok, 0) + 1
    n = len(docs)
    idf = {t: math.log((n + 1) / (c + 0.5)) for t, c in df.items()}
    avglen = sum(d["length"] for d in docs.values()) / n
    return {"docs": docs, "idf": idf, "avglen": avglen}


def _finding_text(f: dict) -> str:
    return " ".join(str(f.get(k, "")) for k in ("title", "name", "description", "summary", "category", "tags"))


def _cwes(f: dict) -> list[int]:
    raw = f.get("cwe") or f.get("cwes") or f.get("cwe_id") or []
    raw = raw if isinstance(raw, list) else [raw]
    out = []
    for v in raw:
        m = re.search(r"(\d+)", str(v))
        if m:
            out.append(int(m.group(1)))
    return out


def map_finding(finding: dict, top: int = 5, min_score: float = 1.0, level: int = 3) -> list[dict]:
    """Rank requirements for one finding (deterministic; ties broken by requirement id).

    score = sum over matched query terms of IDF x field weight, where the
    requirement-text contribution is BM25 length-normalised (k1=1.2, b=0.75),
    + IDF of both tokens for each query bigram found verbatim in the text
    (only when both tokens have IDF >= BIGRAM_MIN_IDF),
    + CWE_BONUS when the finding's CWE hints at the requirement's section.
    """
    idx = keyword_index()
    raw = _finding_text(finding)
    seq = tokenize(raw)
    expanded = list(seq)
    for w in re.findall(r"[a-z0-9]+", raw.lower()):
        if w in SYNONYMS:
            expanded += tokenize(SYNONYMS[w])
    q = set(expanded)
    q_bigrams = set(zip(seq, seq[1:]))
    hinted = {s for c in _cwes(finding) for s in CWE_SECTION_HINTS.get(c, ())}
    k1, b = 1.2, 0.75
    scored = []
    for r in requirements():
        if r["level"] > level:
            continue
        d = idx["docs"][r["id"]]
        norm = (k1 + 1) / (1 + k1 * (1 - b + b * d["length"] / idx["avglen"]))
        score = 0.0
        matched = set()
        for fname, weight in FIELD_WEIGHTS.items():
            hits = q & d[fname]
            factor = weight * (norm if fname == "text" else 1.0)
            score += factor * sum(idx["idf"].get(t, 0.0) for t in hits)
            matched |= hits
        for bg in q_bigrams & d["bigrams"]:
            a, c = idx["idf"].get(bg[0], 0.0), idx["idf"].get(bg[1], 0.0)
            if min(a, c) >= BIGRAM_MIN_IDF:  # ignore bigrams of common words ("user input")
                score += a + c
        if r["group"] in hinted:
            score += CWE_BONUS
        if score >= min_score and matched:
            scored.append({"id": r["id"], "score": round(score, 3), "level": r["level"], "section": r["group"],
                           "matched_terms": sorted(matched), "cwe_hint": r["group"] in hinted,
                           "requirement": r["text"]})
    scored.sort(key=lambda c: (-c["score"], sort_key(c["id"])))
    return scored[:top]


def map_findings(data: object, top: int = 5, min_score: float = 1.0, level: int = 3) -> list[dict]:
    if isinstance(data, dict):
        data = data.get("findings", data.get("results"))
    if not isinstance(data, list):
        raise AsvsError("findings file must be a list of findings or a mapping with a 'findings' list")
    out = []
    for n, f in enumerate(data, start=1):
        if not isinstance(f, dict) or not _finding_text(f).strip():
            raise AsvsError(f"finding {n} needs at least a title or description")
        out.append({"finding": str(f.get("id") or f.get("title") or n), "title": str(f.get("title", "")),
                    "cwe": _cwes(f), "candidates": map_finding(f, top, min_score, level)})
    return out


def render_mapping(results: list[dict]) -> str:
    lines = [f"# Suggested ASVS {VERSION} requirement candidates", "",
             "> SUGGESTIONS ONLY - generated by a deterministic keyword index (requirement text, section and "
             "chapter titles; optional library-authored CWE hints). A verifier must confirm each mapping "
             "against the requirement text before using it in a report.", ""]
    for r in results:
        cwe = f" (CWE {', '.join(map(str, r['cwe']))})" if r["cwe"] else ""
        lines += [f"## {r['finding']}: {r['title']}{cwe}".rstrip(": "), "",
                  "| Rank | Candidate | Score | Level | Matched terms | Requirement |", "|---|---|---|---|---|---|"]
        if not r["candidates"]:
            lines.append("| - | none above threshold | | | | |")
        for i, c in enumerate(r["candidates"], start=1):
            hint = " +CWE" if c["cwe_hint"] else ""
            text = c["requirement"][:160].replace("|", "\\|") + ("..." if len(c["requirement"]) > 160 else "")
            lines.append(f"| {i} | {c['id']} | {c['score']}{hint} | {c['level']} | {', '.join(c['matched_terms'][:8])} | {text} |")
        lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------- graders (evals)
# An ASVS id in prose: c.s.r not embedded in a longer dotted number. Section 0 never
# exists, so version strings such as 5.0.0 / 4.0.3 are skipped.
_PROSE_ID = re.compile(r"(?<![\d.])(?:v5\.0\.0-|V)?(\d{1,2})\.(\d{1,2})\.(\d{1,2})(?![\d.]\d)")


def ids_in(output: str) -> list[str]:
    found = []
    for m in _PROSE_ID.finditer(output):
        if m.group(2) == "0":
            continue
        rid = f"{int(m.group(1))}.{int(m.group(2))}.{int(m.group(3))}"
        if rid not in found:
            found.append(rid)
    return found


def grade_ids_exist(output: str, check: dict) -> tuple[bool, str]:
    """Every ASVS-looking id in the output exists in 5.0.0; at least ``min`` (default 1) ids cited.

    Optional ``require``: list of ids that must be cited.
    """
    ids = ids_in(output)
    unknown = [i for i in ids if i not in _index()]
    need = int(check.get("min", 1))
    missing = [normalize_id(r) for r in check.get("require", []) if normalize_id(r) not in ids]
    ok = not unknown and len(ids) - len(unknown) >= need and not missing
    return ok, f"{len(ids)} ids cited; unknown: {unknown}; required missing: {missing}"


def grade_level_appropriate(output: str, check: dict) -> tuple[bool, str]:
    """All cited ids are at or below ``check['level']`` (e.g. an L1 checklist cites no L2/L3 ids)."""
    level = int(check["level"])
    ids = [i for i in ids_in(output) if i in _index()]
    above = [i for i in ids if _index()[i]["level"] > level]
    return (not above and bool(ids)), f"{len(ids)} known ids; above L{level}: {above}"


_INLINE_LEVEL = re.compile(r"(?<![\d.])(?:v5\.0\.0-|V)?(\d{1,2}\.\d{1,2}\.\d{1,2})(?![\d.]\d)\s*[\(\[,:-]?\s*\(?(?:L|Level\s*)([123])\b", re.I)


def claimed_levels(output: str) -> list[tuple[str, int]]:
    """(id, level) claims from inline '1.2.5 (L1)' text and Markdown tables with an ID and Level column."""
    claims = [(normalize_id(m.group(1)), int(m.group(2))) for m in _INLINE_LEVEL.finditer(output)]
    header = None
    for line in output.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            header = None
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if header is None:
            low = [c.lower() for c in cells]
            lv = next((i for i, c in enumerate(low) if c in ("l", "level", "lvl", "asvs level")), None)
            idc = next((i for i, c in enumerate(low) if c in ("id", "#", "requirement id", "asvs id", "req", "asvs")), None)
            header = (idc, lv) if lv is not None and idc is not None else (None, None)
            continue
        idc, lv = header
        if idc is None or set(s) <= set("|-: "):
            continue
        if max(idc, lv) < len(cells):
            m = re.match(r"^(?:v5\.0\.0-|V)?(\d+\.\d+\.\d+)$", cells[idc])
            lm = re.match(r"^L?([123])$", cells[lv], re.I)
            if m and lm:
                claims.append((m.group(1), int(lm.group(1))))
    return claims


def grade_levels_claimed(output: str, check: dict) -> tuple[bool, str]:
    """Every level the output attributes to a requirement matches the catalog (min ``min`` claims)."""
    claims = claimed_levels(output)
    wrong = [(i, lv, _index()[i]["level"]) for i, lv in claims if i in _index() and _index()[i]["level"] != lv]
    unknown = [i for i, _ in claims if i not in _index()]
    need = int(check.get("min", 1))
    ok = not wrong and not unknown and len(claims) >= need
    return ok, f"{len(claims)} level claims; wrong (id, claimed, actual): {wrong}; unknown: {unknown}"


def grade_chapters_exist(output: str, check: dict) -> tuple[bool, str]:
    """Every 'V<n>' / 'V<n>.<m>' chapter or section reference exists in ASVS 5.0.0."""
    refs = set(re.findall(r"(?<![\w.])V(\d{1,2}(?:\.\d{1,2})?)(?![\d.]*\d)\b", output))
    unknown = sorted(f"V{r}" for r in refs if f"V{r}" not in _groups())
    return not unknown, f"{len(refs)} chapter/section refs; unknown: {unknown}"


def grade_json_assessment(output: str, check: dict) -> tuple[bool, str]:
    """The first ```json block is an assessment that passes check-assessment validation (``valid``)."""
    m = re.search(r"```json\s*\n(.*?)```", output, re.S)
    if not m:
        return False, "no ```json block"
    rep = check_assessment(json.loads(m.group(1)), check.get("level"), check.get("chapters"))
    if check.get("require_complete") and not rep["complete"]:
        return False, f"incomplete: missing {rep['missing'][:5]} not-verified {rep['not_verified'][:5]}"
    return rep["valid"], f"valid={rep['valid']} errors={[e['problem'] + ' ' + str(e['id']) for e in rep['errors'][:5]]}"


# --------------------------------------------------------------------------- CLI
def _emit(text: str, out: str | None) -> None:
    if out:
        Path(out).write_text(text, encoding="utf-8")
        print(f"wrote {out}", file=sys.stderr)
    else:
        sys.stdout.write(text)


def _req_md(r: dict) -> str:
    g = _groups()
    c = r["citation"]
    return (f"{r['id']} (v{VERSION}-{r['id']}) - Level {r['level']}\n"
            f"{r['chapter']} {g[r['chapter']]['title']} > {r['group']} {g[r['group']]['title']}\n"
            f"PDF page {c['pdf_page']} (printed {c['printed_page']})\n\n{r['text']}\n")


def _cmd_chapters(args) -> int:
    rows = []
    for ch in chapters():
        reqs = [r for r in requirements() if r["chapter"] == ch["id"]]
        row = {"id": ch["id"], "title": ch["title"], "pdf_page": ch["citation"]["pdf_page"],
               "requirements": len(reqs), **{f"L{lv}": sum(r["level"] == lv for r in reqs) for lv in (1, 2, 3)}}
        if args.sections:
            row["sections"] = [{"id": s["id"], "title": s["title"], "requirements": s["requirement_count"]} for s in sections(ch["id"])]
        rows.append(row)
    if args.format == "json":
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return 0
    print(f"| Chapter | Title | Reqs | L1 | L2 | L3 | PDF p. |\n|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['id']} | {r['title']} | {r['requirements']} | {r['L1']} | {r['L2']} | {r['L3']} | {r['pdf_page']} |")
        for s in r.get("sections", []):
            print(f"|  | {s['id']} {s['title']} | {s['requirements']} | | | | |")
    total = len(requirements())
    print(f"\nTotal: {total} requirements in {len(rows)} chapters (OWASP ASVS {VERSION}).")
    return 0


def _cmd_show(args) -> int:
    reqs = [get(i) for i in args.ids]
    if args.format == "json":
        print(json.dumps(reqs if len(reqs) > 1 else reqs[0], indent=2, ensure_ascii=False))
    else:
        print("\n".join(_req_md(r) for r in reqs), end="")
    return 0


def _cmd_search(args) -> int:
    hits = search(" ".join(args.text), args.level, args.chapters)
    if args.format == "json":
        print(json.dumps(hits, indent=2, ensure_ascii=False))
    else:
        for r in hits:
            print(f"{r['id']:8} L{r['level']}  {r['text']}")
        print(f"\n{len(hits)} match(es).")
    return 0


def _cmd_checklist(args) -> int:
    _emit(render_checklist(args.level, args.chapters, args.format), args.output)
    return 0


def _cmd_check(args) -> int:
    rep = check_assessment(load_structured(Path(args.file)), args.level, args.chapters)
    _emit(json.dumps(rep, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else render_assessment(rep), args.output)
    if not rep["valid"] or not rep["complete"]:
        return 1
    if args.strict and rep["totals"]["fail"]:
        return 1
    return 0


def _cmd_map(args) -> int:
    res = map_findings(load_structured(Path(args.file)), args.top, args.min_score, args.level)
    if args.format == "json":
        payload = {"note": "Suggestions only; confirm each candidate against the requirement text.",
                   "standard": f"OWASP ASVS {VERSION}", "results": res}
        _emit(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", args.output)
    else:
        _emit(render_mapping(res), args.output)
    return 0


def _wrap(fn):
    def run(args) -> int:
        try:
            return fn(args)
        except AsvsError as exc:
            print(f"asvs: error: {exc}", file=sys.stderr)
            return 2
    return run


def register(subparsers) -> None:
    p = subparsers.add_parser("asvs", help=f"OWASP ASVS {VERSION} checklists, assessment checks and finding mapping",
                              description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="asvs_command", required=True)

    def level_arg(sp, required=False, default=None):
        sp.add_argument("--level", type=int, choices=(1, 2, 3), required=required, default=default,
                        help="target ASVS level (cumulative)")

    def chapters_arg(sp):
        sp.add_argument("--chapters", nargs="+", metavar="V#", help="restrict to chapters/sections, e.g. V1 V6 V8.2")

    c = sub.add_parser("chapters", help="list chapters (and sections) with requirement counts")
    c.add_argument("--sections", action="store_true")
    c.add_argument("--format", choices=("md", "json"), default="md")
    c.set_defaults(func=_wrap(_cmd_chapters))

    s = sub.add_parser("show", help="show one or more requirements by id (1.2.5, V1.2.5, v5.0.0-1.2.5)")
    s.add_argument("ids", nargs="+")
    s.add_argument("--format", choices=("md", "json"), default="md")
    s.set_defaults(func=_wrap(_cmd_show))

    se = sub.add_parser("search", help="find requirements containing all the given terms")
    se.add_argument("text", nargs="+")
    level_arg(se, default=3)
    chapters_arg(se)
    se.add_argument("--format", choices=("md", "json"), default="md")
    se.set_defaults(func=_wrap(_cmd_search))

    cl = sub.add_parser("checklist", help="verification checklist of all requirements at or below a level")
    level_arg(cl, required=True)
    chapters_arg(cl)
    cl.add_argument("--format", choices=("md", "csv", "yaml", "json"), default="md")
    cl.add_argument("-o", "--output")
    cl.set_defaults(func=_wrap(_cmd_checklist))

    ca = sub.add_parser("check-assessment", help="validate a filled assessment (JSON/YAML/CSV) and compute compliance")
    ca.add_argument("file")
    level_arg(ca)
    chapters_arg(ca)
    ca.add_argument("--strict", action="store_true", help="also exit 1 when any requirement fails")
    ca.add_argument("--format", choices=("md", "json"), default="md")
    ca.add_argument("-o", "--output")
    ca.set_defaults(func=_wrap(_cmd_check))

    mf = sub.add_parser("map-findings", help="suggest candidate ASVS requirements for security findings")
    mf.add_argument("file")
    mf.add_argument("--top", type=int, default=5)
    mf.add_argument("--min-score", type=float, default=1.0)
    level_arg(mf, default=3)
    mf.add_argument("--format", choices=("md", "json"), default="md")
    mf.add_argument("-o", "--output")
    mf.set_defaults(func=_wrap(_cmd_map))
