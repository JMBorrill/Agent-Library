#!/usr/bin/env python3
"""Heuristic security screen for Python / JavaScript / TypeScript / SQL files.

Each rule is a small, explainable pattern for a representative failure, mapped to an OWASP ASVS
5.0.0 chapter or section by title (requirement-level IDs are not claimed):

  SC001 hardcoded-secret            V13.3 Secret Management
  SC002 sql-string-building         V1.2  Injection Prevention
  SC003 missing-tenant-filter       V8    Authorization (chapter)
  SC004 debug-mode-enabled          V13.4 Unintended Information Leakage
  SC005 weak-password-hash          V11.4 Hashing and Hash-based Functions
  SC006 insecure-deserialization    V1.5  Safe Deserialization
  SC007 tls-verification-disabled   V12   Secure Communication (chapter)
  SC008 cors-wildcard-credentials   V3.5  Browser Origin Separation
  SC009 jwt-verification-disabled   V9.1  Token source and integrity

Suppress a reviewed false positive on its line with: static-checks: ignore[SC00N] <reason>

Usage:
  static_checks.py PATH [PATH ...] [--tenant-tables t1,t2] [--tenant-column tenant_id]
                   [--config cfg.json] [--json]
Exit codes: 0 no findings, 1 findings, 2 unreadable input.

Scope: a heuristic screen, not a SAST tool and not security assurance. It misses most
vulnerabilities (no data-flow analysis) and can raise false positives.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".sql"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
RULES = {
    "SC001": ("hardcoded-secret", "V13.3", "Secret Management"),
    "SC002": ("sql-string-building", "V1.2", "Injection Prevention"),
    "SC003": ("missing-tenant-filter", "V8", "Authorization"),
    "SC004": ("debug-mode-enabled", "V13.4", "Unintended Information Leakage"),
    "SC005": ("weak-password-hash", "V11.4", "Hashing and Hash-based Functions"),
    "SC006": ("insecure-deserialization", "V1.5", "Safe Deserialization"),
    "SC007": ("tls-verification-disabled", "V12", "Secure Communication"),
    "SC008": ("cors-wildcard-credentials", "V3.5", "Browser Origin Separation"),
    "SC009": ("jwt-verification-disabled", "V9.1", "Token source and integrity"),
}
SECRET_RX = [
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bsk-[A-Za-z0-9-]{8,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"""(?i)\b(?:password|passwd|secret(?:_key)?|api[_-]?key|access[_-]?token|auth[_-]?token|"""
               r"""client[_-]?secret|private[_-]?key)\b["']?\s*[:=]\s*["']([^"'\s]{6,})["']"""),
]
PLACEHOLDER = re.compile(r"(?i)(os\.environ|getenv|process\.env|<[^>]+>|\$\{|changeme|example|placeholder|xxxxx)")
SQL_KW = re.compile(r"(?i)\b(select\s.+?\sfrom|insert\s+into|update\s+\w+\s+set|delete\s+from)\b")
SQL_BUILD = [
    re.compile(r"""\b[fF][rR]?(["']).*\{[^}]+\}"""),         # Python f-string with interpolation
    re.compile(r"""["']\s*%\s*[\w(]"""),                       # "..." % value
    re.compile(r"""["']\s*\.format\s*\("""),                   # "...".format(
    re.compile(r"""["']\s*\+\s*[\w(]|[\w)]\s*\+\s*["']"""),    # string concatenation
    re.compile(r"""`[^`]*\$\{[^}]+\}"""),                       # JS template literal
]
DEBUG_RX = [
    re.compile(r"^\s*DEBUG\s*=\s*True\b"),
    re.compile(r"\.run\([^)]*\bdebug\s*=\s*True"),
    re.compile(r"\bapp\.debug\s*=\s*True"),
    re.compile(r"""FLASK_DEBUG["']?\s*[]=:,]\s*["']?(1|true)""", re.I),
    re.compile(r"""NODE_ENV\s*=\s*["']development["']"""),
]
WEAK_HASH = re.compile(r"""(?i)(hashlib\.(md5|sha1)\s*\(|hashlib\.new\(\s*["'](md5|sha1)["']|createHash\(\s*["'](md5|sha1)["']|"""
                       r"""\b(md5|sha1)\s*\()""")
PASSWORD_WORD = re.compile(r"(?i)pass(word|wd|phrase)?|pwd")
DESER_RX = [
    re.compile(r"\b(c?[pP]ickle|dill|marshal|shelve)\.loads?\s*\("),
    re.compile(r"\byaml\.unsafe_load\s*\("),
    re.compile(r"\bunserialize\s*\("),
]
YAML_LOAD = re.compile(r"\byaml\.load(_all)?\s*\(")
YAML_SAFE = re.compile(r"Loader\s*=\s*(yaml\.)?C?SafeLoader")
TLS_RX = [
    re.compile(r"\bverify\s*=\s*False\b"),
    re.compile(r"\brejectUnauthorized\s*:\s*false\b"),
    re.compile(r"""NODE_TLS_REJECT_UNAUTHORIZED["']?\s*[]=:]\s*["']?0"""),
    re.compile(r"\bssl\._create_unverified_context\b"),
    re.compile(r"\bCERT_NONE\b"),
    re.compile(r"\bcheck_hostname\s*=\s*False\b"),
]
CORS_ORIGIN = re.compile(r"""(?i)(origins?\s*[=:]\s*(\[\s*)?["']\*["']|access-control-allow-origin["']?\s*[,:]\s*["']\*["']|"""
                         r"""\borigin\s*:\s*true\b)""")
CORS_CREDS = re.compile(r"""(?i)(supports_credentials\s*=\s*True|credentials\s*:\s*true|"""
                        r"""access-control-allow-credentials["']?\s*[,:]\s*["']true["'])""")
JWT_RX = [
    re.compile(r"""(?i)algorithms?\s*[=:]\s*\[?[^\]\n]*["']none["']"""),
    re.compile(r"""(?i)["']alg["']\s*:\s*["']none["']"""),
    re.compile(r"""["']verify_signature["']\s*:\s*False"""),
    re.compile(r"""jwt\.decode\([^)]*\bverify\s*=\s*False"""),
]
SUPPRESS = re.compile(r"static-checks:\s*ignore\[(SC\d{3})\]\s*(.*)")
COMMENT = re.compile(r"^\s*(#|//|--|\*|/\*)")
STRING_LIT = re.compile(r"(\"\"\"|'''|`)(.*?)\1|\"([^\"\n]*)\"|'([^'\n]*)'", re.S)


def _mask(text: str) -> str:
    out = text
    for rx in SECRET_RX:
        out = rx.sub(lambda m: m.group(0)[:4] + "***", out)
    return out.strip()[:160]


def _f(path: str, line: int, code: str, message: str, snippet: str) -> dict:
    rule, ref, title = RULES[code]
    level = "section" if "." in ref else "chapter"
    return {"id": f"{path}:{line}", "severity": "error", "rule": rule, "rule_id": code,
            "asvs_ref": f"ASVS v5.0.0 {ref} {title}", "asvs_mapping": level,
            "message": message, "file": path, "line": line, "snippet": _mask(snippet)}


def sql_snippets(path: str, text: str) -> list[tuple[int, str]]:
    if path.endswith(".sql"):
        out, start = [], 0
        for stmt in text.split(";"):
            m = SQL_KW.search(stmt)
            if m:
                out.append((text.count("\n", 0, start + m.start()) + 1, stmt))
            start += len(stmt) + 1
        return out
    out = []
    for m in STRING_LIT.finditer(text):
        body = m.group(2) or m.group(3) or m.group(4) or ""
        if SQL_KW.search(body.replace("\n", " ")):
            out.append((text.count("\n", 0, m.start()) + 1, body))
    return out


def tenant_findings(path: str, text: str, tables: set[str], column: str) -> list[tuple[int, str, str]]:
    out = []
    col = re.compile(rf"\b{re.escape(column)}\b", re.I)
    for line, sql in sql_snippets(path, text):
        flat = " ".join(sql.split())
        names = {t.lower() for t in re.findall(r"(?i)\b(?:from|join|update|into)\s+([A-Za-z_][\w.]*)", flat)}
        names = {n.split(".")[-1] for n in names}
        hit = sorted(names & tables)
        if not hit:
            continue
        ins = re.search(r"(?i)insert\s+into\s+\w+\s*\(([^)]*)\)", flat)
        if ins and not col.search(ins.group(1)):
            out.append((line, f"INSERT into tenant-scoped table {hit} without {column} column", flat))
        elif not ins and not col.search(flat):
            out.append((line, f"query on tenant-scoped table(s) {hit} has no {column} filter", flat))
    return out


def scan_text(path: str, text: str, tables: set[str] | None = None, column: str = "tenant_id") -> list[dict]:
    lines = text.splitlines()
    raw: list[dict] = []
    for i, line in enumerate(lines, 1):
        is_comment = bool(COMMENT.match(line))
        for rx in SECRET_RX:
            if rx.search(line) and not PLACEHOLDER.search(line):
                raw.append(_f(path, i, "SC001", "possible hard-coded secret; load from a secret manager or environment "
                              "(value masked; rotate if real)", line))
                break
        if is_comment:
            continue
        if SQL_KW.search(line) and any(rx.search(line) for rx in SQL_BUILD):
            raw.append(_f(path, i, "SC002", "SQL built from string formatting/concatenation; use parameterised "
                          "queries", line))
        if any(rx.search(line) for rx in DEBUG_RX):
            raw.append(_f(path, i, "SC004", "debug mode enabled; never ship debug settings to production", line))
        if WEAK_HASH.search(line):
            window = " ".join(lines[max(0, i - 4):i + 3])
            if PASSWORD_WORD.search(window):
                raw.append(_f(path, i, "SC005", "MD5/SHA-1 used near password handling; use a password hashing "
                              "function such as Argon2id, scrypt, bcrypt or PBKDF2", line))
        if any(rx.search(line) for rx in DESER_RX) or (YAML_LOAD.search(line) and not YAML_SAFE.search(line)):
            raw.append(_f(path, i, "SC006", "unsafe deserialisation of possibly untrusted data; use JSON or "
                          "yaml.safe_load", line))
        if "jwt" not in line.lower() and any(rx.search(line) for rx in TLS_RX):
            raw.append(_f(path, i, "SC007", "TLS certificate/hostname verification disabled", line))
        if CORS_ORIGIN.search(line):
            near = lines[max(0, i - 9):i + 8]
            if any(CORS_CREDS.search(x) for x in near):
                raw.append(_f(path, i, "SC008", "CORS allows any origin together with credentials", line))
        if any(rx.search(line) for rx in JWT_RX):
            raw.append(_f(path, i, "SC009", "JWT accepted with 'none' algorithm or signature verification disabled",
                          line))
    if tables:
        for ln, msg, snippet in tenant_findings(path, text, tables, column):
            raw.append(_f(path, ln, "SC003", msg, snippet))
    out = []
    for f in raw:
        src = lines[f["line"] - 1] if 0 < f["line"] <= len(lines) else ""
        m = SUPPRESS.search(src)
        if m and m.group(1) == f["rule_id"]:
            reason = m.group(2).strip()
            if reason:
                out.append({**f, "severity": "info", "rule": "suppressed",
                            "message": f"{f['rule_id']} suppressed: {reason}"})
                continue
            f["message"] += " (suppression ignored: no reason given)"
        out.append(f)
    return out


def iter_files(paths: list[Path]) -> list[Path]:
    files = []
    for p in paths:
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            files += [q for q in sorted(p.rglob("*")) if q.is_file() and q.suffix in EXTENSIONS
                      and not set(q.parts) & SKIP_DIRS]
        else:
            raise OSError(f"{p} does not exist")
    return files


def scan(paths: list[Path], tables: set[str] | None = None, column: str = "tenant_id", base: Path | None = None) -> dict:
    findings: list[dict] = []
    files = iter_files(paths)
    for f in files:
        try:
            rel = f.resolve().relative_to((base or Path.cwd()).resolve()).as_posix()
        except ValueError:
            rel = f.as_posix()
        findings += scan_text(rel, f.read_text(encoding="utf-8", errors="replace"), tables, column)
    if not tables:
        findings.append({"id": "-", "severity": "info", "rule": "tenant-check-inactive",
                         "message": "SC003 inactive: pass --tenant-tables (and --tenant-column) to check tenant filters"})
    by_rule: dict[str, int] = {}
    for f in findings:
        if f["severity"] == "error":
            by_rule[f["rule"]] = by_rule.get(f["rule"], 0) + 1
    summary = {"files_scanned": len(files), "by_rule": by_rule,
               "errors": sum(by_rule.values()), "warnings": 0,
               "info": sum(1 for f in findings if f["severity"] == "info")}
    return {"findings": findings, "summary": summary,
            "rules": {k: {"rule": v[0], "asvs_ref": f"ASVS v5.0.0 {v[1]} {v[2]}"} for k, v in RULES.items()}}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Heuristic security screen (not a SAST tool).")
    ap.add_argument("paths", type=Path, nargs="+")
    ap.add_argument("--tenant-tables", help="comma-separated tenant-scoped table names")
    ap.add_argument("--tenant-column", default=None)
    ap.add_argument("--config", type=Path, help='JSON: {"tenant_tables": [...], "tenant_column": "tenant_id"}')
    ap.add_argument("--base", type=Path, help="report paths relative to this directory")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        cfg = json.loads(args.config.read_text(encoding="utf-8")) if args.config else {}
        tables = {t.strip().lower() for t in (args.tenant_tables.split(",") if args.tenant_tables
                                               else cfg.get("tenant_tables", [])) if t.strip()}
        column = args.tenant_column or cfg.get("tenant_column", "tenant_id")
        result = scan(args.paths, tables, column, args.base)
    except (OSError, UnicodeDecodeError, ValueError, AttributeError) as exc:
        print(f"cannot scan: {exc}", file=sys.stderr)
        return 2
    failed = result["summary"]["errors"] > 0
    result["passed"] = not failed
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for f in result["findings"]:
            ref = f" [{f['rule_id']} {f['asvs_ref']}]" if "rule_id" in f else ""
            print(f"{f['severity'].upper():8} {f['id']:<40} {f['rule']:<27} {f['message']}{ref}")
        print(f"\n{'FAIL' if failed else 'PASS'}: {result['summary']}")
        print("Scope: heuristic screen only - not a SAST tool, not a penetration test, not security assurance.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
