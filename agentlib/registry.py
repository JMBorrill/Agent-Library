"""Build ``registry.json``: a deterministic index of every library component.

The registry is generated, never hand-edited. CI fails when it is stale.
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from agentlib import frontmatter
from agentlib.paths import repo_root


def _first_line(text: str) -> str:
    return " ".join(str(text).split())


def build_registry(root: Path | None = None) -> dict:
    root = root or repo_root()
    reg: dict = {"schema_version": 1, "skills": [], "agents": [], "commands": [], "workflows": [], "catalogs": [], "eval_suites": []}
    for md in sorted((root / "skills").glob("*/SKILL.md")):
        meta, _ = frontmatter.load(md)
        m = meta.get("metadata", {})
        reg["skills"].append({
            "name": meta["name"],
            "path": str(md.parent.relative_to(root)),
            "description": _first_line(meta["description"]),
            "category": m.get("category"),
            "version": m.get("version"),
            "maturity": m.get("maturity"),
            "sources": m.get("sources", []),
            "catalogs": m.get("catalogs", []),
            "tools": m.get("tools", []),
            "has_eval_suite": (root / "evals" / meta["name"] / "cases.yaml").is_file(),
        })
    for md in sorted((root / "agents").glob("*.md")):
        meta, _ = frontmatter.load(md)
        reg["agents"].append({
            "name": meta["name"],
            "path": str(md.relative_to(root)),
            "description": _first_line(meta["description"]),
            "model": meta.get("model", "inherit"),
        })
    for md in sorted((root / "commands").glob("*.md")):
        meta, _ = frontmatter.load(md)
        reg["commands"].append({"name": md.stem, "path": str(md.relative_to(root)), "description": _first_line(meta["description"])})
    for wf in sorted((root / "workflows").glob("*.yaml")):
        data = yaml.safe_load(wf.read_text(encoding="utf-8"))
        reg["workflows"].append({
            "id": data["id"],
            "path": str(wf.relative_to(root)),
            "title": data["title"],
            "version": data["version"],
            "stages": [s["id"] for s in data["stages"]],
        })
    for cat in sorted((root / "catalog").glob("*.json")):
        data = json.loads(cat.read_text(encoding="utf-8"))
        reg["catalogs"].append({
            "id": data["catalog_id"],
            "path": str(cat.relative_to(root)),
            "source_id": data["source_id"],
            "edition": data["edition"],
            "items": len(data["items"]),
            "fidelity": data["extraction"]["fidelity"],
        })
    for suite in sorted((root / "evals").glob("*/cases.yaml")):
        data = yaml.safe_load(suite.read_text(encoding="utf-8"))
        reg["eval_suites"].append({"skill": data.get("skill"), "path": str(suite.relative_to(root)), "cases": len(data.get("cases", []))})
    return reg


def write_registry(root: Path | None = None) -> Path:
    root = root or repo_root()
    path = root / "registry.json"
    path.write_text(json.dumps(build_registry(root), indent=2) + "\n", encoding="utf-8")
    return path
