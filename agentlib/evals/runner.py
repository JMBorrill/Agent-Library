"""Run evaluation suites.

Modes
-----
offline (default, used in CI)
    For every case: the golden output must reach the case threshold and the
    negative output (if any) must fall below it. This proves each check is
    satisfiable *and* discriminating without calling a model.

live
    Load the skill (SKILL.md plus its references) as the system prompt, send
    each case prompt to the Claude Messages API, grade the response and write
    a JSON report. Requires ``ANTHROPIC_API_KEY``. Model defaults to
    ``AGENTLIB_EVAL_MODEL`` or ``claude-sonnet-5-5``.

grade
    Grade an arbitrary output file against one case (useful for manual or
    third-party runs).
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path

from agentlib.evals.graders import CheckResult, grade
from agentlib.evals.spec import Case, Suite, load_suite
from agentlib.paths import repo_root

DEFAULT_MODEL = "claude-sonnet-5-5"
MAX_REFERENCE_CHARS = 120_000


@dataclass
class CaseResult:
    skill: str
    case: str
    mode: str
    passed: bool
    score: float
    threshold: float
    checks: list[dict] = field(default_factory=list)
    note: str = ""


def score(results: list[CheckResult]) -> float:
    return sum(r.passed for r in results) / len(results) if results else 0.0


def discover_suites(root: Path | None = None, skills: list[str] | None = None) -> list[Suite]:
    root = root or repo_root()
    suites = [load_suite(p) for p in sorted((root / "evals").glob("*/cases.yaml"))]
    if skills:
        suites = [s for s in suites if s.skill in skills]
    return suites


def run_offline(suite: Suite) -> list[CaseResult]:
    out = []
    for case in suite.cases:
        golden = (case.base / case.golden).read_text(encoding="utf-8")
        g = grade(golden, case.checks)
        gs = score(g)
        out.append(CaseResult(suite.skill, case.id, "golden", gs >= case.threshold, gs, case.threshold,
                              [asdict(r) for r in g], "golden output must pass"))
        if case.negative:
            bad = (case.base / case.negative).read_text(encoding="utf-8")
            b = grade(bad, case.checks)
            bs = score(b)
            out.append(CaseResult(suite.skill, case.id, "negative", bs < case.threshold, bs, case.threshold,
                                  [asdict(r) for r in b], "negative output must fail"))
    return out


def skill_system_prompt(root: Path, skill: str) -> str:
    sdir = root / "skills" / skill
    parts = [(sdir / "SKILL.md").read_text(encoding="utf-8")]
    budget = MAX_REFERENCE_CHARS
    for ref in sorted((sdir / "references").glob("*.md")) if (sdir / "references").is_dir() else []:
        text = ref.read_text(encoding="utf-8")
        if len(text) > budget:
            break
        parts.append(f"\n\n<reference path=\"references/{ref.name}\">\n{text}\n</reference>")
        budget -= len(text)
    return "You are operating with the following Agent Skill loaded.\n\n" + "".join(parts)


def call_claude(system: str, prompt: str, model: str, max_tokens: int = 8000) -> str:
    """Call the Messages API. Uses the ``anthropic`` SDK when installed, else HTTPS."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set; live evals need API access")
    try:
        import anthropic  # type: ignore

        client = anthropic.Anthropic()
        msg = client.messages.create(model=model, max_tokens=max_tokens, system=system,
                                     messages=[{"role": "user", "content": prompt}])
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    except ImportError:
        pass
    body = json.dumps({"model": model, "max_tokens": max_tokens, "system": system,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, headers={
        "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as resp:  # noqa: S310 - fixed https URL
        data = json.loads(resp.read())
    return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")


def run_live(suite: Suite, root: Path, model: str, out_dir: Path) -> list[CaseResult]:
    system = skill_system_prompt(root, suite.skill)
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for case in suite.cases:
        started = time.time()
        try:
            text = call_claude(system, case.full_prompt(), model)
        except Exception as exc:  # report, keep going
            results.append(CaseResult(suite.skill, case.id, "live", False, 0.0, case.threshold, [], f"API error: {exc}"))
            continue
        (out_dir / f"{suite.skill}__{case.id}.md").write_text(text, encoding="utf-8")
        g = grade(text, case.checks)
        s = score(g)
        results.append(CaseResult(suite.skill, case.id, "live", s >= case.threshold, s, case.threshold,
                                  [asdict(r) for r in g], f"model={model} seconds={time.time() - started:.1f}"))
    return results


def grade_file(case: Case, output_path: Path) -> CaseResult:
    text = output_path.read_text(encoding="utf-8")
    g = grade(text, case.checks)
    s = score(g)
    return CaseResult("", case.id, "grade", s >= case.threshold, s, case.threshold, [asdict(r) for r in g])


def summarise(results: list[CaseResult]) -> str:
    lines = []
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        lines.append(f"{status} {r.skill}/{r.case} [{r.mode}] score={r.score:.2f} threshold={r.threshold:.2f}")
        if not r.passed:
            for c in r.checks:
                marker = "ok " if c["passed"] else "BAD"
                lines.append(f"    {marker} {c['type']}: {c['detail']}")
            if r.note:
                lines.append(f"    note: {r.note}")
    passed = sum(r.passed for r in results)
    lines.append(f"\n{passed}/{len(results)} evaluation results passed")
    return "\n".join(lines)
