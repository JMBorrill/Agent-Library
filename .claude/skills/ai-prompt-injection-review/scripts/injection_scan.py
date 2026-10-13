#!/usr/bin/env python3
"""Heuristic screen for prompt-injection / jailbreak patterns in untrusted content.

Rules (rule id -> severity):
  instruction-override (high)   "ignore/disregard/forget previous instructions", "new instructions:"
  role-reassignment (medium)    "you are now", "act as", developer/DAN mode, fake system/assistant turns
  prompt-exfiltration (high)    requests to reveal the system prompt, hidden instructions, keys
  hidden-text (high)            zero-width / bidi-control / Unicode tag characters, HTML comments or
                                CSS-hidden text that contain instruction-like words
  exfiltration-url (high)       markdown images or links whose URL carries a query string, or
                                instructions to send/append data to a URL
  tool-coercion (high)          instructions to call tools, run commands, change records, tool-call JSON
  encoded-payload (medium/high) base64 runs >= --min-b64 chars that decode to text (high if the
                                decoded text itself matches a rule)
  data-egress-request (medium)  requests to send/forward/export data to an email address
  concealment (medium)          "do not tell the user/underwriter/anyone"
  addressed-to-ai (low)         text addressing an AI assistant/model directly
  authority-bypass (medium)     a third party's authority claimed as already given ("the owner has
                                already okayed this", "as lead underwriter I have cleared it") AND, in
                                the same document, a verification bypass ("no need to check", "can skip")
  bulk-personal-data-request (medium)  a send/text/email/export request for every/each/all clients'
                                (customers', contacts'...) names, addresses, phone numbers, emails...
  Each social-engineering signal alone is at most "review"; both together reach "flag".
Verdict per document: flag (any high, or score >= 4), review (score >= 2), clean.

Input: a text file (one document), or JSONL (--jsonl) with {"id", "text", optional "label":
"malicious"|"benign"}; labelled corpora get detection / false-positive rates in the summary.

Usage:
  injection_scan.py doc.txt [--json]
  injection_scan.py corpus.jsonl --jsonl [--min-b64 40] [--json]
Exit codes: 0 nothing flagged, 1 at least one document flagged, 2 unreadable input.

Scope: a SCREENING HEURISTIC with known false negatives (paraphrased, translated, image-borne
or novel attacks) and false positives (security training material). A clean result is not
evidence that content is safe; enforce tool policy (tool_policy_check.py) regardless.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import json
import re
import sys
import unicodedata
from pathlib import Path

WEIGHTS = {"high": 4, "medium": 2, "low": 1}
INSTR_WORDS = r"(?:ignore|disregard|forget|override|instruction|assistant|system prompt|you must|do not tell|send|forward|email|reply|approve|delete|transfer|execute|call|tool)"

PATTERNS: list[tuple[str, str, re.Pattern]] = [
    ("instruction-override", "high", re.compile(
        r"\b(?:ignore|disregard|forget|override|bypass|skip)\b[^.\n]{0,40}\b(?:previous|prior|above|earlier|all|any|your|the|system|safety)\b[^.\n]{0,30}\b(?:instructions?|prompts?|rules|guidelines|directives|polic(?:y|ies)|guardrails)\b", re.I)),
    ("instruction-override", "high", re.compile(r"(?:^|\n)\s*(?:new|updated|revised|real) (?:instructions?|task|rules)\s*:", re.I)),
    ("role-reassignment", "medium", re.compile(
        r"\b(?:you are now|from now on,? you (?:are|will)|pretend (?:to be|you are)|act as (?:an?|the) (?!applicant|broker)|roleplay as|developer mode|DAN mode|jailbreak(?:en)? mode|do anything now)\b", re.I)),
    ("role-reassignment", "medium", re.compile(r"(?:^|\n)\s*(?:###\s*)?(?:system|assistant)\s*:\s*\S|<\|?(?:im_start|system)\|?>", re.I)),
    ("prompt-exfiltration", "high", re.compile(
        r"\b(?:reveal|print|repeat|show|output|leak|tell me)\b[^.\n]{0,30}\b(?:system prompt|hidden instructions|initial instructions|your instructions|api keys?|secrets?|credentials|access tokens?)\b", re.I)),
    ("tool-coercion", "high", re.compile(
        r"\b(?:call|invoke|use|run|trigger|execute)\b[^.\n]{0,25}\b(?:tool|function|plugin|command|shell|script|api)\b", re.I)),
    ("data-egress-request", "medium", re.compile(
        r"\b(?:send|forward|e-?mail|export|upload|post)\b[^.\n]{0,60}\b(?:to|at)\s+[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", re.I)),
    ("tool-coercion", "high", re.compile(
        r"\b(?:mark|set|change|update)\b[^.\n]{0,40}\b(?:as|to)\s+(?:approved|accepted|verified|paid|closed|priority)\b[^.\n]{0,40}\b(?:without|do not|don't|no need)\b", re.I)),
    ("tool-coercion", "high", re.compile(r"\{\s*\"(?:tool|function|name)\"\s*:\s*\"[a-z_]+\"", re.I)),
    ("exfiltration-url", "high", re.compile(r"!\[[^\]]*\]\(\s*https?://[^)\s]*\?[^)\s]*=", re.I)),
    ("exfiltration-url", "high", re.compile(
        r"\b(?:append|add|include|encode|put)\b[^.\n]{0,60}\b(?:to|in|into)\b[^.\n]{0,20}\b(?:url|link|query string|image|webhook)\b", re.I)),
    ("exfiltration-url", "high", re.compile(r"https?://[^\s)]*\?[^\s)]*=\{?\{?[^\s)]*(?:\}\}|%7B|\{)", re.I)),
    ("concealment", "medium", re.compile(
        r"\b(?:do not|don't|never|without)\s+(?:tell(?:ing)?|inform(?:ing)?|mention(?:ing)?|alert(?:ing)?|notify(?:ing)?|reveal(?:ing)?)\s+(?:this\s+to\s+)?(?:the\s+)?(?:user|underwriter|customer|human|reviewer|anyone|operator|broker)", re.I)),
    ("addressed-to-ai", "low", re.compile(
        r"\b(?:(?:dear|hey|attention|note to(?: the)?)\s+(?:ai|llm|assistant|chatbot|copilot|model)|(?:ai|llm) (?:assistant|agent|model)s?(?: reading this)?\s*[:,])", re.I)),
]
AUTHORITY_CLAIM = re.compile(
    r"\b(?:owner|manager|boss|director|supervisor|admin(?:istrator)?|underwriter|compliance|management|"
    r"partner|head of \w+|team lead)\b[^.\n]{0,40}?\b(?:okayed|ok'?d|approved|authori[sz]ed|signed (?:this |it )?off|"
    r"cleared|agreed)\b", re.I)
VERIFICATION_BYPASS = re.compile(
    r"\b(?:no need to|(?:do not|don'?t) need to|needn'?t|without)\s+(?:double-)?(?:check|confirm|verify|ask)(?:ing)?\b"
    r"|\b(?:can|should|just|please)\s+skip\b", re.I)
BULK_PERSONAL_DATA = re.compile(
    r"\b(?:send|text|e-?mail|forward|share|export|list|give)\b[^.\n]{0,100}?"
    r"\b(?:each|every|all(?: of)?(?: the| your| our)?)\s+(?:clients?|customers?|owners?|contacts?|applicants?|"
    r"patients?|members?|users?)(?:'s|s'|\u2019s)?\b[^.\n]{0,40}?"
    r"\b(?:names?|address(?:es)?|phone|mobile|numbers?|e-?mails?|dates? of birth|DOB|details|records?)\b", re.I)
INVISIBLE = re.compile("[​-‏‪-‮⁠-⁤⁦-⁩﻿]")
TAG_CHARS = re.compile("[\U000e0000-\U000e007f]")
HTML_COMMENT = re.compile(r"<!--(.*?)-->", re.S)
CSS_HIDDEN = re.compile(
    r"<[^>]+style\s*=\s*\"[^\"]*(?:display\s*:\s*none|font-size\s*:\s*0|color\s*:\s*(?:#fff(?:fff)?|white)|opacity\s*:\s*0)[^\"]*\"[^>]*>(.*?)</", re.I | re.S)
INSTR_RE = re.compile(INSTR_WORDS, re.I)
B64_RUN = re.compile(r"(?<![A-Za-z0-9+/=])[A-Za-z0-9+/]{16,}={0,2}(?![A-Za-z0-9+/=])")


def _hit(rule: str, severity: str, evidence: str) -> dict:
    ev = evidence.replace("\n", " ")
    return {"rule": rule, "severity": severity, "evidence": ev[:120]}


def _pattern_hits(text: str) -> list[dict]:
    hits = []
    for rule, sev, pat in PATTERNS:
        m = pat.search(text)
        if m:
            hits.append(_hit(rule, sev, m.group(0)))
    return hits


def scan_text(text: str, min_b64: int = 40, _depth: int = 0) -> dict:
    """Return {"verdict", "score", "hits"} for one document."""
    hits: list[dict] = []
    if INVISIBLE.search(text):
        n = len(INVISIBLE.findall(text))
        hits.append(_hit("hidden-text", "high", f"{n} zero-width/bidi control character(s)"))
    if TAG_CHARS.search(text):
        decoded = "".join(chr(ord(c) - 0xE0000) for c in TAG_CHARS.findall(text))
        hits.append(_hit("hidden-text", "high", f"Unicode tag characters encoding: {decoded[:60]!r}"))
    for body in HTML_COMMENT.findall(text) + CSS_HIDDEN.findall(text):
        if INSTR_RE.search(body):
            hits.append(_hit("hidden-text", "high", f"hidden markup containing instructions: {body.strip()[:80]}"))
            break
    # normalise: strip invisibles and tag chars, NFKC fold look-alikes, before pattern matching
    visible = unicodedata.normalize("NFKC", TAG_CHARS.sub("", INVISIBLE.sub("", text)))
    hits.extend(_pattern_hits(visible))
    claim, bypass = AUTHORITY_CLAIM.search(visible), VERIFICATION_BYPASS.search(visible)
    if claim and bypass:
        hits.append(_hit("authority-bypass", "medium", f"{claim.group(0)} ... {bypass.group(0)}"))
    bulk = BULK_PERSONAL_DATA.search(visible)
    if bulk:
        hits.append(_hit("bulk-personal-data-request", "medium", bulk.group(0)))
    if _depth == 0:
        for m in B64_RUN.finditer(visible):
            run = m.group(0)
            if len(run) < min_b64:
                continue
            try:
                raw = base64.b64decode(run + "=" * (-len(run) % 4), validate=True)
                decoded = raw.decode("utf-8")
            except (binascii.Error, UnicodeDecodeError, ValueError):
                continue
            printable = sum(ch.isprintable() or ch.isspace() for ch in decoded) / max(1, len(decoded))
            if printable < 0.9:
                continue
            inner = scan_text(decoded, min_b64, _depth + 1)
            sev = "high" if inner["hits"] else "medium"
            hits.append(_hit("encoded-payload", sev, f"base64 ({len(run)} chars) decodes to: {decoded[:60]!r}"))
    # de-duplicate by (rule, severity)
    seen, uniq = set(), []
    for h in hits:
        key = (h["rule"], h["severity"])
        if key not in seen:
            seen.add(key)
            uniq.append(h)
    score = sum(WEIGHTS[h["severity"]] for h in uniq)
    verdict = "flag" if any(h["severity"] == "high" for h in uniq) or score >= 4 else "review" if score >= 2 else "clean"
    return {"verdict": verdict, "score": score, "hits": uniq}


def read_docs(path: Path, jsonl: bool) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    if not jsonl:
        return [{"id": path.name, "text": text}]
    docs = []
    for n, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"line {n}: invalid JSON ({exc.msg})") from None
        if not isinstance(obj, dict) or not isinstance(obj.get("text"), str):
            raise ValueError(f"line {n}: need an object with string 'text'")
        if obj.get("label") not in (None, "malicious", "benign"):
            raise ValueError(f"line {n}: label must be malicious|benign")
        obj.setdefault("id", f"line-{n}")
        docs.append(obj)
    return docs


def scan_docs(docs: list[dict], min_b64: int = 40) -> dict:
    results = []
    for d in docs:
        r = scan_text(d["text"], min_b64)
        results.append({"id": str(d["id"]), "label": d.get("label"), **r})
    summary = {"documents": len(results),
               "flag": sum(r["verdict"] == "flag" for r in results),
               "review": sum(r["verdict"] == "review" for r in results),
               "clean": sum(r["verdict"] == "clean" for r in results)}
    mal = [r for r in results if r["label"] == "malicious"]
    ben = [r for r in results if r["label"] == "benign"]
    if mal or ben:
        detected = [r for r in mal if r["verdict"] in ("flag", "review")]
        fps = [r for r in ben if r["verdict"] == "flag"]
        summary["labelled"] = {
            "malicious": len(mal), "benign": len(ben),
            "detected": len(detected),
            "detection_rate": round(len(detected) / len(mal), 4) if mal else None,
            "false_negatives": [r["id"] for r in mal if r not in detected],
            "false_positives_flagged": [r["id"] for r in fps],
            "false_positive_rate": round(len(fps) / len(ben), 4) if ben else None,
            "benign_sent_to_review": [r["id"] for r in ben if r["verdict"] == "review"],
            "note": "detection counts flag or review; false positives count flag only",
        }
    findings = [{"id": r["id"], "severity": "error" if r["verdict"] == "flag" else "warning",
                 "rule": h["rule"], "message": h["evidence"]}
                for r in results if r["verdict"] != "clean" for h in r["hits"]]
    return {"documents": results, "summary": summary, "findings": findings, "passed": summary["flag"] == 0}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Heuristic prompt-injection screen for untrusted content.")
    ap.add_argument("path", type=Path)
    ap.add_argument("--jsonl", action="store_true", help="input is JSONL of {id, text, label?}")
    ap.add_argument("--min-b64", type=int, default=40, help="minimum base64 run length to decode (default 40)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if args.min_b64 < 8:
        print("--min-b64 must be >= 8", file=sys.stderr)
        return 2
    try:
        docs = read_docs(args.path, args.jsonl)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 2
    report = scan_docs(docs, args.min_b64)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        for r in report["documents"]:
            label = f" [{r['label']}]" if r["label"] else ""
            print(f"{r['verdict'].upper():6} score={r['score']:<3} {r['id']}{label}")
            for h in r["hits"]:
                print(f"         {h['severity']:<6} {h['rule']:<20} {h['evidence']}")
        print(f"\nSummary: {report['summary']}")
        print("Scope: screening heuristic with known false negatives; a clean result is not proof of safety.")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
