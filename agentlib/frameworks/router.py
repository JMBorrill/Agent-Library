"""Deterministic skill router: ``python -m agentlib route "<problem description>"``.

Scores each skill by weighted keyword hits from a curated signal table plus
token overlap with the skill's own description. The result is a suggestion
for the ``framework-selector`` skill, not a decision.
"""
from __future__ import annotations

import json
import re

from agentlib import frontmatter
from agentlib.paths import repo_root

# skill -> (weight, phrases). Phrases are matched as whole words/phrases, lower-case.
SIGNALS: dict[str, list[tuple[float, list[str]]]] = {
    "nasa-systems-engineering": [
        (3, ["systems engineering", "conops", "concept of operations", "life cycle review", "lifecycle review",
             "pdr", "cdr", "srr", "mdr", "key decision point", "semp", "trade study", "technology readiness", "trl"]),
        (1.5, ["architecture", "mission", "spacecraft", "interfaces", "integration", "subsystem", "stakeholder expectations"]),
    ],
    "requirements-engineering": [
        (3, ["requirement", "requirements", "shall statement", "traceability", "verification matrix", "vcrm"]),
        (1, ["acceptance criteria", "specification", "validation"]),
    ],
    "nasa-software-engineering": [
        (3, ["npr 7150", "7150.2", "software class", "software classification", "swe-", "compliance matrix"]),
        (1.5, ["flight software", "software development plan", "nasa software", "software management plan"]),
    ],
    "nasa-software-assurance": [
        (3, ["software assurance", "software safety", "8739.8", "iv&v", "safety-critical software", "safety critical software"]),
        (1.5, ["hazard analysis", "independent verification", "assurance audit", "nonconformance"]),
    ],
    "nist-ssdf": [
        (3, ["ssdf", "800-218", "secure software development", "secure sdlc", "sbom", "software supply chain",
             "attestation", "vulnerability disclosure", "provenance"]),
        (1.5, ["ci/cd", "pipeline", "code signing", "dependency", "dependencies", "secret scanning", "sast", "sca"]),
    ],
    "owasp-asvs": [
        (3, ["asvs", "application security verification", "penetration test", "pentest", "web application security",
             "api security", "owasp"]),
        (1.5, ["security review", "security testing", "threat model", "authentication", "session", "access control", "injection", "xss", "csrf", "tls", "oauth", "jwt",
               "web app", "api", "security requirements"]),
    ],
    "nist-ai-rmf": [
        (3, ["ai rmf", "ai risk", "artificial intelligence", "machine learning", "model card", "llm", "genai",
             "generative ai", "trustworthy ai", "algorithmic", "ai system"]),
        (1.5, ["bias", "fairness", "explainability", "hallucination", "model", "training data", "ai governance"]),
    ],
    "green-book-appraisal": [
        (3, ["green book", "business case", "cost-benefit", "cost benefit", "value for money", "npv", "npsv",
             "bcr", "options appraisal", "appraisal", "hm treasury", "five case"]),
        (1.5, ["public spending", "investment", "discount rate", "optimism bias", "benefits realisation", "funding"]),
    ],
    "evidence-and-citation": [
        (2, ["citation", "cite", "evidence", "audit trail", "traceable claims", "assurance case"]),
        (0.5, ["report", "assessment", "review"]),
    ],
}
STOP = set("a an and the of for to in on with by or is are be this that it as at from we our need needs".split())


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9][a-z0-9.+&/-]*", text.lower()) if t not in STOP and len(t) > 2}


def _phrase_hit(phrase: str, text: str) -> bool:
    """Whole-word match. Phrases ending in punctuation ("swe-") or a version number ("7150.2")
    may be followed by more characters ("swe-033", "7150.2d")."""
    tail = "" if not phrase[-1].isalpha() else r"(?![a-z0-9])"
    return re.search(r"(?<![a-z0-9])" + re.escape(phrase) + tail, text) is not None


def route(problem: str, top: int = 5) -> list[dict]:
    text = " " + problem.lower() + " "
    words = _tokens(problem)
    root = repo_root()
    results = []
    for md in sorted((root / "skills").glob("*/SKILL.md")):
        meta, _ = frontmatter.load(md)
        name = meta["name"]
        if name == "framework-selector":
            continue
        score, hits = 0.0, []
        for weight, phrases in SIGNALS.get(name, []):
            for ph in phrases:
                if _phrase_hit(ph, text):
                    score += weight
                    hits.append(ph)
        overlap = words & _tokens(meta["description"])
        score += 0.25 * len(overlap)
        if score > 0:
            results.append({"skill": name, "score": round(score, 2), "signals": hits,
                            "description_overlap": sorted(overlap)[:8]})
    results.sort(key=lambda r: (-r["score"], r["skill"]))
    return results[:top]


def _cmd_route(args) -> int:
    res = route(" ".join(args.problem), args.top)
    if args.format == "json":
        print(json.dumps(res, indent=2))
    elif not res:
        print("No skill matched; describe the deliverable, life-cycle stage and consequences of failure.")
    else:
        print("Suggested skills (deterministic keyword routing; confirm with the framework-selector skill):")
        for r in res:
            print(f"  {r['score']:6.2f}  {r['skill']:28} signals: {', '.join(r['signals']) or '-'}")
    return 0


def register(sub) -> None:
    p = sub.add_parser("route", help="suggest skills for a problem description")
    p.add_argument("problem", nargs="+")
    p.add_argument("--top", type=int, default=5)
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.set_defaults(func=_cmd_route)
