#!/usr/bin/env python3
"""Check a shaped pitch (Markdown) and, optionally, a scope list.

Pitch checks: the five ingredients are present and non-empty (Problem, Appetite, Solution, Rabbit
holes, No-gos); the appetite states an explicit, bounded time budget no larger than the team's
configured maximum; the appetite comes before the solution; the solution describes elements
(breadboard / fat-marker sketch / places and connections); each rabbit hole carries a resolution or
decision; no-gos are listed; the problem links to evidence; vague and unbounded wording is flagged.

Scope list checks (--scopes): every scope has tasks and at least one must-have; nice-to-haves are
marked with a leading "~"; scope names are unique and describe a slice of the feature, not a layer.

Usage:
  pitch_check.py PITCH.md [--max-appetite-weeks 6] [--scopes SCOPES.md] [--strict] [--json]
  pitch_check.py --scopes SCOPES.md [--json]
Exit codes: 0 no errors (warnings allowed unless --strict), 1 errors, 2 unreadable input / bad usage.

Scope: a structural and wording check. Whether the problem matters, the appetite is right or the
solution is sound is a judgement for the people placing the bet.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SECTIONS = {
    "problem": ["problem"],
    "appetite": ["appetite"],
    "solution": ["solution"],
    "rabbit_holes": ["rabbit holes", "rabbit-holes", "risks and rabbit holes"],
    "no_gos": ["no-gos", "no gos", "nogos", "no-go", "out of bounds"],
}
VAGUE = ["intuitive", "seamless", "seamlessly", "easy", "easily", "simple", "user-friendly",
         "user friendly", "better", "improve", "improved", "enhance", "enhanced", "optimise",
         "optimize", "robust", "smart", "powerful", "modern", "best-in-class", "world-class",
         "delightful", "streamline", "streamlined", "flexible", "as needed"]
UNBOUNDED = ["and more", "etc", "and so on", "everything", "all the things", "any and all",
             "fully featured", "full-featured", "whatever is needed", "as many as", "end-to-end platform"]
UNBOUNDED_APPETITE = ["as long as it takes", "until done", "until it's done", "ongoing", "open-ended",
                      "tbd", "tbc", "unknown", "however long"]
ELEMENT_WORDS = re.compile(r"\b(breadboard|fat[- ]marker|sketch|elements?|places?|affordances?|"
                           r"connections?|flow|screen|step)\b", re.I)
RESOLUTION = re.compile(r"(->|→|\bresolution\s*:|\bdecision\s*:|\bdecided\b|\bpatch\s*:|"
                        r"\bwe will\b|\bout of scope\b|\bno-go\b|\bmitigat)", re.I)
EVIDENCE = re.compile(r"(\[[^\]]+\]\([^)]+\)|\b[A-Z][A-Z0-9]*-EV-\d+\b|\bEV-\d+\b|https?://\S+)")
TIME = re.compile(r"(\d+(?:\.\d+)?)\s*(working\s+days?|days?|weeks?|wks?|months?)\b", re.I)
BULLET = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.*\S)\s*$")
LAYER_NAMES = {"frontend", "front end", "backend", "back end", "database", "api", "ui", "misc",
               "miscellaneous", "other", "bugs", "polish", "testing", "qa", "design"}


def _f(rid: str, severity: str, rule: str, message: str) -> dict:
    return {"id": rid, "severity": severity, "rule": rule, "message": message}


def _term(text: str, term: str) -> bool:
    return re.search(rf"(?<![\w-]){re.escape(term)}(?![\w-])", text, re.I) is not None


def parse_sections(text: str) -> tuple[dict[str, str], list[str]]:
    """Map canonical section key -> body text; also return the order of keys found."""
    found: dict[str, str] = {}
    order: list[str] = []
    current = None
    buf: list[str] = []
    in_code = False

    def flush():
        if current is not None:
            found[current] = found.get(current, "") + "\n".join(buf).strip()

    for line in text.splitlines():
        if line.startswith("```"):
            in_code = not in_code
        m = None if in_code else re.match(r"^#{1,3}\s+(.+?)\s*#*\s*$", line)
        if m:
            flush()
            buf = []
            title = re.sub(r"^\d+[.)]\s*", "", m.group(1)).strip().lower()
            current = None
            for key, names in SECTIONS.items():
                if title in names or any(title.startswith(n) for n in names):
                    current = key
                    if key not in order:
                        order.append(key)
                    break
            continue
        if current is not None:
            buf.append(line)
    flush()
    return found, order


def bullets(body: str) -> list[str]:
    return [m.group(1) for line in body.splitlines() if (m := BULLET.match(line))]


def appetite_weeks(body: str) -> list[float]:
    out = []
    for num, unit in TIME.findall(body):
        n = float(num)
        u = unit.lower()
        if "day" in u:
            out.append(n / 5.0)  # working days
        elif u.startswith("month"):
            out.append(n * 4.0)
        else:
            out.append(n)
    return out


def check_pitch(text: str, max_weeks: float = 6.0) -> tuple[list[dict], dict]:
    findings: list[dict] = []
    if not text.strip():
        return [_f("pitch", "error", "empty-document", "pitch is empty")], {}
    sec, order = parse_sections(text)
    for key in SECTIONS:
        if key not in sec:
            findings.append(_f(key, "error", "missing-section", f"no '{SECTIONS[key][0].title()}' section"))
        elif not sec[key].strip():
            findings.append(_f(key, "error", "empty-section", f"'{SECTIONS[key][0].title()}' section is empty"))
    if "appetite" in order and "solution" in order and order.index("appetite") > order.index("solution"):
        findings.append(_f("appetite", "warning", "appetite-after-solution",
                           "appetite should be set before the solution is described"))
    # appetite
    weeks: list[float] = []
    app = sec.get("appetite", "")
    if app.strip():
        unb = [t for t in UNBOUNDED_APPETITE if _term(app, t)]
        weeks = appetite_weeks(app)
        if unb:
            findings.append(_f("appetite", "error", "appetite-unbounded", f"unbounded appetite wording {unb}"))
        if not weeks:
            findings.append(_f("appetite", "error", "appetite-no-time-budget",
                               "no explicit time budget (e.g. '2 weeks', '6 weeks', '10 working days')"))
        else:
            if len(set(weeks)) > 1:
                findings.append(_f("appetite", "warning", "appetite-ambiguous",
                                   f"several time budgets found {sorted(set(weeks))} weeks; state one"))
            if max(weeks) > max_weeks:
                findings.append(_f("appetite", "error", "appetite-exceeds-cycle",
                                   f"appetite {max(weeks):g} weeks exceeds the configured maximum of {max_weeks:g} weeks; split or re-shape"))
            if max(weeks) <= 0:
                findings.append(_f("appetite", "error", "appetite-no-time-budget", "time budget must be > 0"))
    # problem evidence
    prob = sec.get("problem", "")
    if prob.strip() and not EVIDENCE.search(prob):
        findings.append(_f("problem", "warning", "problem-without-evidence",
                           "problem does not link evidence (evidence ID such as DWS-EV-001, or a link)"))
    # solution
    sol = sec.get("solution", "")
    if sol.strip():
        if not ELEMENT_WORDS.search(sol):
            findings.append(_f("solution", "warning", "solution-no-elements",
                               "solution does not describe elements (places, affordances, connections, breadboard or fat-marker sketch)"))
        if len(sol.split()) < 30:
            findings.append(_f("solution", "warning", "solution-thin", "solution under 30 words — too abstract to bet on"))
        if not prob.strip():
            findings.append(_f("solution", "error", "solution-without-problem", "solution given without a problem statement"))
    # rabbit holes
    rh = sec.get("rabbit_holes", "")
    if "rabbit_holes" in sec:
        items = bullets(rh)
        if not items and rh.strip():
            findings.append(_f("rabbit_holes", "warning", "rabbit-holes-not-listed", "write rabbit holes as a bullet list"))
        if not rh.strip() or re.fullmatch(r"\W*(none|n/?a|no risks?)\W*", rh.strip(), re.I):
            findings.append(_f("rabbit_holes", "warning", "no-rabbit-holes",
                               "no rabbit holes identified — unusual for shaped work; look again"))
        for i, item in enumerate(items, 1):
            if not RESOLUTION.search(item):
                findings.append(_f(f"rabbit_holes[{i}]", "error", "rabbit-hole-unresolved",
                                   f"no resolution or decision: '{item[:60]}' (add '-> <resolution>' or 'Decision: ...')"))
    # no-gos
    ng = sec.get("no_gos", "")
    if ng.strip() and not bullets(ng):
        findings.append(_f("no_gos", "error", "no-gos-empty", "list at least one explicit no-go as a bullet"))
    # wording
    for key, body in sec.items():
        vague = sorted({t for t in VAGUE if _term(body, t)})
        if vague:
            findings.append(_f(key, "warning", "vague-term", f"vague words {vague}: say what changes for whom"))
        unbounded = sorted({t for t in UNBOUNDED if _term(body, t)})
        if unbounded:
            sev = "error" if key in ("solution", "appetite") else "warning"
            findings.append(_f(key, sev, "unbounded-scope", f"open-ended scope wording {unbounded}"))
    summary = {"sections_found": order, "appetite_weeks": max(weeks) if weeks else None,
               "max_appetite_weeks": max_weeks,
               "rabbit_holes": len(bullets(rh)), "no_gos": len(bullets(ng))}
    return findings, summary


def check_scopes(text: str) -> tuple[list[dict], dict]:
    findings: list[dict] = []
    scopes: dict[str, dict] = {}
    order: list[str] = []
    current = None
    for line in text.splitlines():
        m = re.match(r"^#{2,3}\s+(?:scope\s*:\s*)?(.+?)\s*$", line, re.I)
        if m:
            current = m.group(1).strip()
            if current.lower() in ("scopes", "scope list", "scope map"):
                current = None
                continue
            if current in scopes:
                findings.append(_f(current, "error", "duplicate-scope", "scope name used more than once"))
            else:
                scopes[current] = {"must": 0, "nice": 0}
                order.append(current)
            continue
        b = BULLET.match(line)
        if b and current is not None:
            task = re.sub(r"^\[[ xX]\]\s*", "", b.group(1)).strip()
            key = "nice" if task.startswith("~") else "must"
            scopes[current][key] += 1
    if not scopes:
        findings.append(_f("scopes", "error", "no-scopes", "no scopes found (use '## Scope: <name>' headings with task bullets)"))
    for name in order:
        c = scopes[name]
        if c["must"] + c["nice"] == 0:
            findings.append(_f(name, "error", "scope-empty", "scope has no tasks"))
        elif c["must"] == 0:
            findings.append(_f(name, "error", "scope-no-must-have", "every task is a nice-to-have (~); the scope cannot be finished or cut cleanly"))
        if name.lower() in LAYER_NAMES:
            findings.append(_f(name, "warning", "scope-is-layer", "scope named after a layer or bucket; name a slice of the feature that can be finished on its own"))
    total_must = sum(s["must"] for s in scopes.values())
    total_nice = sum(s["nice"] for s in scopes.values())
    if total_must + total_nice and total_nice > total_must:
        findings.append(_f("scopes", "warning", "too-many-nice-to-haves", f"{total_nice} nice-to-haves vs {total_must} must-haves"))
    return findings, {"scopes": len(scopes), "must_haves": total_must, "nice_to_haves": total_nice}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Check a shaped pitch and/or scope list.")
    ap.add_argument("pitch", type=Path, nargs="?")
    ap.add_argument("--scopes", type=Path)
    ap.add_argument("--max-appetite-weeks", type=float, default=6.0,
                    help="team's largest single bet in weeks (default 6; set to your own cadence)")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if not args.pitch and not args.scopes:
        print("give a pitch file and/or --scopes", file=sys.stderr)
        return 2
    if args.max_appetite_weeks <= 0:
        print("--max-appetite-weeks must be > 0", file=sys.stderr)
        return 2
    findings: list[dict] = []
    summary: dict = {}
    try:
        if args.pitch:
            f, s = check_pitch(args.pitch.read_text(encoding="utf-8"), args.max_appetite_weeks)
            findings += f
            summary["pitch"] = s
        if args.scopes:
            f, s = check_scopes(args.scopes.read_text(encoding="utf-8"))
            findings += f
            summary["scopes"] = s
    except (OSError, UnicodeDecodeError) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 2
    summary["errors"] = sum(1 for f in findings if f["severity"] == "error")
    summary["warnings"] = sum(1 for f in findings if f["severity"] == "warning")
    failed = summary["errors"] > 0 or (args.strict and summary["warnings"] > 0)
    out = {"findings": findings, "summary": summary, "passed": not failed}
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        for f in findings:
            print(f"{f['severity'].upper():8} {f['id']:<18} {f['rule']:<26} {f['message']}")
        print(f"\n{'FAIL' if failed else 'PASS'}: {summary}")
        print("Scope: structure and wording check only; the bet itself is a human judgement.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
