"""Evaluation suite specification.

A suite lives at ``evals/<skill>/cases.yaml``::

    skill: green-book-appraisal
    description: What this suite measures.
    cases:
      - id: short-kebab-id
        prompt: |
          The task given to the model (the skill is loaded as system context).
        fixtures: [fixtures/costs.csv]      # optional, appended to the prompt
        golden: golden/short-kebab-id.md     # reference output; MUST pass
        negative: golden/short-kebab-id.bad.md  # optional; MUST fail >=1 check
        threshold: 1.0                       # fraction of checks required
        checks:
          - {type: contains, values: ["Net Present Social Value"]}
          - {type: regex, pattern: "3\\.5\\s*%"}

Supported check types are documented in :mod:`agentlib.evals.graders`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from agentlib.evals.graders import CHECK_TYPES


class SpecError(ValueError):
    pass


@dataclass
class Case:
    id: str
    prompt: str
    checks: list[dict]
    base: Path
    fixtures: list[str] = field(default_factory=list)
    golden: str | None = None
    negative: str | None = None
    threshold: float = 1.0

    def fixture_text(self) -> str:
        parts = []
        for f in self.fixtures:
            parts.append(f"\n\n--- {f} ---\n" + (self.base / f).read_text(encoding="utf-8"))
        return "".join(parts)

    def full_prompt(self) -> str:
        return self.prompt + self.fixture_text()


@dataclass
class Suite:
    skill: str
    description: str
    cases: list[Case]
    path: Path


def load_suite(path: Path) -> Suite:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise SpecError(f"invalid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise SpecError("suite must be a mapping")
    for key in ("skill", "description", "cases"):
        if key not in data:
            raise SpecError(f"missing '{key}'")
    if path.parent.name != data["skill"]:
        raise SpecError(f"suite directory '{path.parent.name}' must equal skill '{data['skill']}'")
    base = path.parent
    cases: list[Case] = []
    seen: set[str] = set()
    if not data["cases"]:
        raise SpecError("suite has no cases")
    for raw in data["cases"]:
        cid = raw.get("id")
        if not cid or cid in seen:
            raise SpecError(f"case id missing or duplicated: {cid!r}")
        seen.add(cid)
        if not raw.get("prompt"):
            raise SpecError(f"{cid}: missing prompt")
        checks = raw.get("checks") or []
        if not checks:
            raise SpecError(f"{cid}: at least one check is required")
        for chk in checks:
            ctype = chk.get("type")
            if ctype not in CHECK_TYPES:
                raise SpecError(f"{cid}: unknown check type {ctype!r}; known: {sorted(CHECK_TYPES)}")
            try:
                CHECK_TYPES[ctype].validate(chk)
            except (KeyError, TypeError, ValueError) as exc:
                raise SpecError(f"{cid}: invalid {ctype} check: {exc}") from exc
        for key in ("golden", "negative"):
            if raw.get(key) and not (base / raw[key]).is_file():
                raise SpecError(f"{cid}: {key} file not found: {raw[key]}")
        for fx in raw.get("fixtures", []):
            if not (base / fx).is_file():
                raise SpecError(f"{cid}: fixture not found: {fx}")
        if not raw.get("golden"):
            raise SpecError(f"{cid}: a golden reference output is required so graders are verified offline")
        threshold = float(raw.get("threshold", 1.0))
        if not 0 < threshold <= 1:
            raise SpecError(f"{cid}: threshold must be in (0, 1]")
        cases.append(Case(cid, raw["prompt"], checks, base, raw.get("fixtures", []), raw.get("golden"), raw.get("negative"), threshold))
    return Suite(data["skill"], data["description"], cases, path)
