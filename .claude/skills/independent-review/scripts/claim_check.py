#!/usr/bin/env python3
"""Flag overclaimed assurance and unsupported evidence claims in Markdown/text artifacts.

Detects, per line:
  assurance-claim       "approved", "certified", "compliant", "qualified", "production-ready",
                        "safe to operate", "passes NASA", "meets all requirements", "guaranteed", ...
                        unless the line negates/conditions it ("not", "pending", "requires", "only ... can")
                        or cites a sign-off record ("[signoff: <name>, YYYY-MM-DD]").
  absolute-claim        "zero risk", "100% safe/accurate", "no risk", "cannot fail", "fully secure"
  unsupported-research  "interviews/users/customers showed|said|confirmed ..." or long quotes without
                        an [evidence: ...] tag
  unverified-citation   "NASA ...§", "MCOB 11.6", "ASVS 1.2.3", "GOVERN 1.1" style precise references
                        on a line without "(unverified)", "verified" or a source audit pointer (warning)

Code blocks are skipped. Usage: claim_check.py PATH [PATH ...] [--json]
Exit: 0 no errors, 1 errors, 2 no readable files.
Scope: a language screen. It cannot tell whether a claim is true; reviewers must open the evidence.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ASSURANCE = re.compile(
    r"\b(approved|certified|certification granted|accredited|compliant|in compliance|fully compliant|"
    r"qualified for flight|flight[- ]qualified|(?:is|are|was|been|now) qualified|production[- ]ready|ready for production|"
    r"safe to (?:operate|launch|deploy|use|fly)|is safe|are safe|passes nasa|nasa[- ]approved|"
    r"fca[- ](?:approved|compliant)|meets all requirements|signed off|guaranteed?|loan approved|credit approved)\b",
    re.I)
ABSOLUTE = re.compile(r"\b(zero risk|no risk|risk[- ]free(?! (?:rate|return|asset|bond))|100\s?% (?:safe|accurate|secure|reliable)|cannot fail|"
                      r"fully secure|completely secure|never fails)\b", re.I)
RESEARCH = re.compile(r"\b(interviews?|users?|customers?|participants?|stakeholders?|operators?)\s+"
                      r"(showed|show|said|say|told us|confirmed|love|loved|want|wanted|asked for)\b", re.I)
QUOTE = re.compile(r"[\"“][^\"”]{25,}[\"”]")
PRECISE_REF = re.compile(r"(§\s?\d+(?:\.\d+)+|\bMCOB\s?\d+(?:\.\d+)*|\bPRIN\s?2A|\bASVS[- ]?(?:v?5\.0\.0-)?\d+\.\d+\.\d+|"
                         r"\b(?:GOVERN|MAP|MEASURE|MANAGE)\s\d+\.\d+|\bPW\.\d|\bPO\.\d|\bRV\.\d|\bPS\.\d)")
NEGATION = re.compile(r"\b(not|never|no|cannot|can't|isn't|aren't|without|pending|until|unless|requires?|"
                      r"required|must|only (?:an?|the)?\s*\w*\s*(?:human|owner|authority|person)|"
                      r"do not|does not|did not|prohibited|claim|claims|recommend|recommendation|"
                      r"if|whether|would|should|awaiting|to be|tbd|nobody|none)\b", re.I)
SIGNOFF = re.compile(r"\[signoff:\s*[^,\]]+,\s*\d{4}-\d{2}-\d{2}\]", re.I)
EVIDENCE = re.compile(r"\[evidence:\s*[^\]]+\]", re.I)
VERIFY_MARK = re.compile(r"\(unverified|unverified\)|verified|sources/audits/|secondary", re.I)
SUFFIXES = {".md", ".txt", ".markdown", ".rst"}


def _f(loc, sev, rule, msg):
    return {"id": loc, "severity": sev, "rule": rule, "message": msg}


def scan_text(text: str, name: str = "-") -> list[dict]:
    out, in_code = [], False
    for i, line in enumerate(text.splitlines(), 1):
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code or line.strip().startswith("|---"):
            continue
        loc = f"{name}:{i}"
        clean = re.sub(r"`[^`]*`", "", line)
        m = ASSURANCE.search(clean)
        if m and not NEGATION.search(clean) and not SIGNOFF.search(clean):
            out.append(_f(loc, "error", "assurance-claim",
                          f"'{m.group(0)}' asserted without a sign-off record [signoff: name, date] — "
                          "rephrase as a recommendation or cite the human decision"))
        m = ABSOLUTE.search(clean)
        if m and not NEGATION.search(clean.replace(m.group(0), "")):
            out.append(_f(loc, "error", "absolute-claim", f"absolute claim '{m.group(0)}'"))
        if (RESEARCH.search(clean) or QUOTE.search(clean)) and not EVIDENCE.search(clean):
            neg = NEGATION.search(clean)
            if not (neg and neg.group(0).lower() in {"never", "not", "no", "do not", "does not", "did not", "without"}):
                out.append(_f(loc, "error", "unsupported-research",
                              "research claim or quotation without [evidence: ...] — never invent interviews or quotes"))
        if PRECISE_REF.search(clean) and not VERIFY_MARK.search(clean):
            out.append(_f(loc, "warning", "unverified-citation",
                          "precise source reference without a verification marker — mark '(unverified)' or cite the audit"))
    return out


def collect(paths: list[Path]) -> list[Path]:
    files = []
    for p in paths:
        if p.is_dir():
            files += sorted(x for x in p.rglob("*") if x.suffix.lower() in SUFFIXES and x.is_file())
        elif p.is_file():
            files.append(p)
    return files


def main(argv=None):
    ap = argparse.ArgumentParser(description="Screen artifacts for overclaimed assurance.")
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    files = collect(a.paths)
    if not files:
        print("no readable .md/.txt files found", file=sys.stderr)
        return 2
    findings = []
    for f in files:
        try:
            findings += scan_text(f.read_text(encoding="utf-8"), str(f))
        except (OSError, UnicodeDecodeError) as exc:
            findings.append(_f(str(f), "warning", "unreadable", str(exc)))
    sev = Counter(x["severity"] for x in findings)
    res = {"findings": findings, "summary": {"files": len(files), "errors": sev.get("error", 0),
                                            "warnings": sev.get("warning", 0)}}
    res["passed"] = res["summary"]["errors"] == 0
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        for x in findings:
            print(f"{x['severity'].upper():8} {x['id']:<48} {x['rule']:<22} {x['message']}")
        print(f"\n{'PASS' if res['passed'] else 'FAIL'}: {res['summary']}")
        print("Scope: language screen only; it cannot establish whether any claim is true.")
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
