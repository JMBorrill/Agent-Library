"""Install library components into another repository.

Skills go to ``<target>/.claude/skills/<name>/``, agents to
``<target>/.claude/agents/``, commands to ``<target>/.claude/commands/``.
Workflows, templates and catalogs go under ``<target>/.agent-library/`` so the
installed skills can reference them. A lock file records the library version
and SHA-256 of every installed file so upgrades never silently clobber local
edits (files that differ are skipped unless ``force``).
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path

from agentlib import __version__, frontmatter
from agentlib.paths import repo_root

LOCK_NAME = ".agent-library.lock.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _skill_deps(root: Path, skill: str) -> set[str]:
    """Skills referenced by another skill's SKILL.md (``skills/<name>/`` or ``../<name>/``)."""
    text = (root / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
    refs = set(re.findall(r"(?:skills/|\.\./)([a-z0-9-]+)/", text))
    return {r for r in refs if (root / "skills" / r / "SKILL.md").is_file()} - {skill}


def resolve_skills(root: Path, requested: list[str] | None) -> list[str]:
    all_skills = sorted(p.parent.name for p in (root / "skills").glob("*/SKILL.md"))
    if not requested:
        return all_skills
    unknown = set(requested) - set(all_skills)
    if unknown:
        raise SystemExit(f"unknown skill(s): {sorted(unknown)}")
    todo, done = list(requested), set()
    while todo:
        s = todo.pop()
        if s in done:
            continue
        done.add(s)
        todo += sorted(_skill_deps(root, s) - done)
    return sorted(done)


def _plan(root: Path, target: Path, components: list[str], skills: list[str]) -> list[tuple[Path, Path]]:
    pairs: list[tuple[Path, Path]] = []
    if "skills" in components:
        for s in skills:
            for f in sorted((root / "skills" / s).rglob("*")):
                if f.is_file() and "__pycache__" not in f.parts:
                    pairs.append((f, target / ".claude" / "skills" / s / f.relative_to(root / "skills" / s)))
    if "agents" in components:
        for f in sorted((root / "agents").glob("*.md")):
            meta, _ = frontmatter.load(f)
            pairs.append((f, target / ".claude" / "agents" / f.name))
    if "commands" in components:
        for f in sorted((root / "commands").glob("*.md")):
            pairs.append((f, target / ".claude" / "commands" / f.name))
    for comp, sub in (("workflows", "workflows"), ("templates", "templates"), ("catalog", "catalog")):
        if comp in components and (root / sub).is_dir():
            for f in sorted((root / sub).rglob("*")):
                if f.is_file():
                    pairs.append((f, target / ".agent-library" / sub / f.relative_to(root / sub)))
    return pairs


def install(target: Path, components: list[str], skills: list[str] | None = None,
            dry_run: bool = False, force: bool = False, root: Path | None = None) -> str:
    root = root or repo_root()
    target = target.resolve()
    if not target.is_dir():
        raise SystemExit(f"target {target} is not a directory")
    if target == root.resolve():
        raise SystemExit("refusing to install the library into itself")
    chosen = resolve_skills(root, skills)
    lock_path = target / LOCK_NAME
    lock = json.loads(lock_path.read_text()) if lock_path.is_file() else {"files": {}}
    written, skipped, unchanged = [], [], []
    for src, dst in _plan(root, target, components, chosen):
        rel = str(dst.relative_to(target))
        if dst.exists():
            if _sha(dst) == _sha(src):
                unchanged.append(rel)
                lock["files"][rel] = _sha(src)
                continue
            locally_edited = lock["files"].get(rel) != _sha(dst)
            if locally_edited and not force:
                skipped.append(rel)
                continue
        if not dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        lock["files"][rel] = _sha(src)
        written.append(rel)
    lock.update({"library": "JMBorrill/Agent-Library", "version": __version__, "skills": chosen, "components": components})
    if not dry_run:
        lock_path.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [f"{'Would install' if dry_run else 'Installed'} into {target}",
             f"  skills: {', '.join(chosen)}",
             f"  written: {len(written)}  unchanged: {len(unchanged)}  skipped (locally modified): {len(skipped)}"]
    lines += [f"    skipped {s} (use --force to overwrite)" for s in skipped]
    return "\n".join(lines)
