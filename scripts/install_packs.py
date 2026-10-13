#!/usr/bin/env python3
"""Install selected skill packs, skills and agents from this library into another project — safely.

Defaults to a DRY RUN that prints the plan. Nothing is written without --apply.
* Resolves packs -> skills/agents and agents -> the skills they reference (dependencies are added
  and reported).
* Per item: CREATE (absent), SKIP (identical content already present) or CONFLICT (differs).
* Any CONFLICT aborts --apply unless --overwrite is given; overwritten items are first copied to
  <target>/.agent-library-backup/<UTC timestamp>/.
* Never modifies settings.json, CLAUDE.md, AGENTS.md or anything outside the chosen skill/agent dirs,
  except the install manifest <target>/.claude/agent-library.lock.json.
* No network access, no global (~/.claude) installs.

Usage examples:
  install_packs.py --target ../myproj --packs systems-engineering            # dry run
  install_packs.py --target ../myproj --skills se-requirements --apply
  install_packs.py --target ../myproj --packs ai-governance --no-agents --skills-dir .agents/skills --apply
  install_packs.py --list
Exit: 0 success / plan without conflicts, 1 conflicts (or refused), 2 usage errors.
"""
from __future__ import annotations

import argparse
import filecmp
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agentlib import AGENTS_DIR, ROOT, SKILLS_DIR, frontmatter  # noqa: E402

PROTECTED = {"settings.json", "settings.local.json", "CLAUDE.md", "AGENTS.md"}
MANIFEST = Path(".claude") / "agent-library.lock.json"


def load_packs() -> dict:
    return json.loads((ROOT / "packs" / "packs.json").read_text(encoding="utf-8"))["packs"]


def agent_skills(name: str) -> list[str]:
    import re
    fm, body = frontmatter.load((AGENTS_DIR / f"{name}.md").read_text(encoding="utf-8"))
    m = re.search(r"^## Skills\s*$(.*?)(?=^## |\Z)", body, re.M | re.S)
    refs = set(fm.get("skills", [])) | set(re.findall(r"`([a-z0-9]+(?:-[a-z0-9]+)*)`", m.group(1) if m else ""))
    return sorted(s for s in refs if (SKILLS_DIR / s / "SKILL.md").is_file())


def resolve(packs: list[str], skills: list[str], agents: list[str], include_agents: bool) -> tuple[list[str], list[str], list[str], list[str]]:
    catalog = load_packs()
    errors, notes = [], []
    sk, ag = list(dict.fromkeys(skills)), list(dict.fromkeys(agents))
    for p in packs:
        if p not in catalog:
            errors.append(f"unknown pack '{p}' (see --list)")
            continue
        sk += [s for s in catalog[p]["skills"] if s not in sk]
        if include_agents:
            ag += [a for a in catalog[p]["agents"] if a not in ag]
        for req in catalog[p].get("requires", []):
            if req not in packs:
                notes.append(f"pack '{p}' supplements '{req}', which is not selected")
    for s in sk:
        if not (SKILLS_DIR / s / "SKILL.md").is_file():
            errors.append(f"unknown skill '{s}'")
    if not include_agents and ag:
        notes.append("--no-agents: ignoring requested agents")
        ag = []
    for a in ag:
        if not (AGENTS_DIR / f"{a}.md").is_file():
            errors.append(f"unknown agent '{a}'")
            continue
        for dep in agent_skills(a):
            if dep not in sk:
                sk.append(dep)
                notes.append(f"added skill '{dep}' required by agent '{a}'")
    sk = [s for s in sk if (SKILLS_DIR / s / "SKILL.md").is_file()]
    return sk, ag, errors, notes


def tree_hash(path: Path) -> str:
    h = hashlib.sha256()
    files = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    for f in files:
        rel = f.name if path.is_file() else f.relative_to(path).as_posix()
        h.update(rel.encode())
        h.update(hashlib.sha256(f.read_bytes()).digest())
    return h.hexdigest()


def same_tree(a: Path, b: Path) -> bool:
    if a.is_file() or b.is_file():
        return a.is_file() and b.is_file() and filecmp.cmp(a, b, shallow=False)
    return tree_hash(a) == tree_hash(b)


def plan(target: Path, skills: list[str], agents: list[str], skills_dir: str, agents_dir: str) -> list[dict]:
    items = []
    for s in skills:
        src, dst = SKILLS_DIR / s, target / skills_dir / s
        items.append({"kind": "skill", "name": s, "src": src, "dst": dst,
                      "action": "CREATE" if not dst.exists() else "SKIP" if same_tree(src, dst) else "CONFLICT"})
    for a in agents:
        src, dst = AGENTS_DIR / f"{a}.md", target / agents_dir / f"{a}.md"
        items.append({"kind": "agent", "name": a, "src": src, "dst": dst,
                      "action": "CREATE" if not dst.exists() else "SKIP" if same_tree(src, dst) else "CONFLICT"})
    return items


def library_version() -> str:
    v = ROOT / "VERSION"
    return v.read_text(encoding="utf-8").strip() if v.is_file() else "unversioned"


def apply(target: Path, items: list[dict], overwrite: bool) -> list[str]:
    log = []
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = target / ".agent-library-backup" / stamp
    for it in items:
        if it["dst"].name in PROTECTED:
            raise RuntimeError(f"refusing to write protected file {it['dst']}")
        if it["action"] == "SKIP":
            continue
        if it["action"] == "CONFLICT":
            if not overwrite:
                raise RuntimeError("conflicts present; re-run with --overwrite to replace (backups are made)")
            bdst = backup_root / it["dst"].relative_to(target)
            bdst.parent.mkdir(parents=True, exist_ok=True)
            if it["dst"].is_dir():
                shutil.copytree(it["dst"], bdst)
                shutil.rmtree(it["dst"])
            else:
                shutil.copy2(it["dst"], bdst)
            log.append(f"backed up {it['dst'].relative_to(target)} -> {bdst.relative_to(target)}")
        it["dst"].parent.mkdir(parents=True, exist_ok=True)
        if it["src"].is_dir():
            shutil.copytree(it["src"], it["dst"], ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            shutil.copy2(it["src"], it["dst"])
        log.append(f"{'replaced' if it['action'] == 'CONFLICT' else 'created'} {it['dst'].relative_to(target)}")
    mpath = target / MANIFEST
    manifest = json.loads(mpath.read_text(encoding="utf-8")) if mpath.is_file() else {"installed": {}}
    for it in items:
        manifest["installed"][f"{it['kind']}:{it['name']}"] = {
            "path": it["dst"].relative_to(target).as_posix(), "sha256": tree_hash(it["dst"]),
            "library_version": library_version()}
    manifest["source_library"] = "agent-library"
    manifest["updated_utc"] = stamp
    mpath.parent.mkdir(parents=True, exist_ok=True)
    mpath.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    log.append(f"manifest {MANIFEST.as_posix()} updated")
    return log


def main(argv=None):
    ap = argparse.ArgumentParser(description="Safely install library packs/skills/agents into a project.")
    ap.add_argument("--target", type=Path)
    ap.add_argument("--packs", default="")
    ap.add_argument("--skills", default="")
    ap.add_argument("--agents", default="")
    ap.add_argument("--all", action="store_true", help="every pack")
    ap.add_argument("--no-agents", action="store_true", help="skills only (for non-Claude Agent Skills tools)")
    ap.add_argument("--skills-dir", default=".claude/skills")
    ap.add_argument("--agents-dir", default=".claude/agents")
    ap.add_argument("--apply", action="store_true", help="write files (default is a dry run)")
    ap.add_argument("--overwrite", action="store_true", help="replace conflicting items after backing them up")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.list:
        for name, p in load_packs().items():
            print(f"{name:<22} {len(p['skills']):>2} skills  agents: {', '.join(p['agents'])}\n    {p['description']}")
        return 0
    if not a.target:
        print("--target is required (or use --list)", file=sys.stderr)
        return 2
    target = a.target.resolve()
    if target == ROOT:
        print("refusing to install the library into itself", file=sys.stderr)
        return 2
    if not target.is_dir():
        print(f"target directory does not exist: {target}", file=sys.stderr)
        return 2
    for d in (a.skills_dir, a.agents_dir):
        if Path(d).is_absolute() or ".." in Path(d).parts:
            print(f"--skills-dir/--agents-dir must be relative paths inside the target: {d}", file=sys.stderr)
            return 2
    split = lambda s: [x.strip() for x in s.split(",") if x.strip()]  # noqa: E731
    packs = list(load_packs()) if a.all else split(a.packs)
    skills, agents, errors, notes = resolve(packs, split(a.skills), split(a.agents), not a.no_agents)
    if errors:
        for e in errors:
            print(f"ERROR {e}", file=sys.stderr)
        return 2
    if not skills and not agents:
        print("nothing selected: use --packs, --skills, --agents or --all", file=sys.stderr)
        return 2
    items = plan(target, skills, agents, a.skills_dir, a.agents_dir)
    conflicts = [i for i in items if i["action"] == "CONFLICT"]
    report = {"target": str(target), "dry_run": not a.apply, "notes": notes,
              "items": [{"kind": i["kind"], "name": i["name"], "action": i["action"],
                         "path": i["dst"].relative_to(target).as_posix()} for i in items]}
    log = []
    if a.apply:
        if conflicts and not a.overwrite:
            report["refused"] = "conflicts present; nothing written. Re-run with --overwrite (backups are made) or resolve manually."
        else:
            try:
                log = apply(target, items, a.overwrite)
            except (OSError, RuntimeError) as exc:
                print(f"ERROR {exc}", file=sys.stderr)
                return 1
    report["log"] = log
    if a.json:
        print(json.dumps(report, indent=2))
    else:
        for n in notes:
            print(f"NOTE  {n}")
        for i in report["items"]:
            print(f"{i['action']:<9} {i['kind']:<6} {i['path']}")
        for line in log:
            print(f"DONE  {line}")
        if report.get("refused"):
            print(f"REFUSED {report['refused']}")
        elif not a.apply:
            print(f"\nDry run: {len(items)} items, {len(conflicts)} conflicts. Nothing written; add --apply to install.")
    return 1 if conflicts and not (a.apply and a.overwrite) else 0


if __name__ == "__main__":
    sys.exit(main())
