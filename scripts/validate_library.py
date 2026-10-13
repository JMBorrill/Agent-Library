#!/usr/bin/env python3
"""Validate the library's structure: skills, agents, packs, sources, crosswalks.

A PASS means the library is *structurally* consistent (metadata, references, mappings).
It says nothing about the engineering, legal or financial correctness of any content.

Usage: python3 scripts/validate_library.py [--json] [--root PATH]
Exit: 0 no errors, 1 errors found, 2 cannot run.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agentlib import frontmatter  # noqa: E402

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SPEC_SKILL_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
REQUIRED_SKILL_METADATA = ("pack", "version", "sources")
SKILL_SECTIONS = [
    "Purpose", "When to use", "Inputs", "Procedure", "Decision criteria", "Outputs",
    "Validation", "Examples", "Escalation and stop conditions", "References",
]
AGENT_KEYS = {
    "name", "description", "tools", "disallowedTools", "model", "permissionMode", "maxTurns",
    "skills", "mcpServers", "hooks", "memory", "background", "effort", "isolation", "color",
    "initialPrompt", "omitClaudeMd",
}
AGENT_SECTIONS = [
    "Responsibility", "Skills", "Boundaries", "Collaboration and handoff",
    "Evidence and reporting", "Human approval required",
]
KNOWN_TOOLS = {
    "Read", "Write", "Edit", "Glob", "Grep", "Bash", "WebFetch", "WebSearch", "Agent",
    "NotebookEdit", "TodoWrite", "Skill", "TaskCreate", "TaskUpdate", "TaskList", "TaskGet",
}
AGENT_COLORS = {"red", "blue", "green", "yellow", "purple", "orange", "pink", "cyan"}
ACCESS_STATUSES = {"VERIFIED", "PARTIALLY_VERIFIED", "INACCESSIBLE", "UNVERIFIED"}
REGISTRY_FIELDS = (
    "id", "title", "version", "url", "scope", "pack", "access_status", "licence",
    "normative_status", "last_checked", "review_by", "audit",
)
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
LINK_RE = re.compile(r"\]\(([^)#\s]+)\)|`((?:references|scripts|assets)/[^`\s]+)`")


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.stats: dict[str, int] = {}

    def err(self, where: str, msg: str) -> None:
        self.errors.append(f"{where}: {msg}")

    def warn(self, where: str, msg: str) -> None:
        self.warnings.append(f"{where}: {msg}")


def _headings(body: str) -> list[str]:
    out, in_code = [], False
    for line in body.splitlines():
        if line.startswith("```"):
            in_code = not in_code
        elif not in_code and line.startswith("## "):
            out.append(line[3:].strip())
    return out


def _check_sections(where: str, body: str, required: list[str], rep: Report) -> None:
    found = _headings(body)
    missing = [s for s in required if s not in found]
    if missing:
        rep.err(where, f"missing required sections: {', '.join(missing)}")
        return
    order = [found.index(s) for s in required]
    if order != sorted(order):
        rep.err(where, "required sections are out of order (see docs/CONVENTIONS.md)")


def _section_text(body: str, heading: str) -> str:
    m = re.search(rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)", body, re.M | re.S)
    return m.group(1) if m else ""


def _stdlib_check(path: Path, rep: Report, where: str) -> None:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        rep.err(where, f"{path.name} does not compile: {exc}")
        return
    local = {p.stem for p in path.parent.glob("*.py")}
    allowed = set(sys.stdlib_module_names) | local | {"__future__"}
    has_main = False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "main":
            has_main = True
        mods = []
        if isinstance(node, ast.Import):
            mods = [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            mods = [node.module.split(".")[0]]
        for m in mods:
            if m not in allowed:
                rep.err(where, f"{path.name} imports non-stdlib module '{m}' (skills must be self-contained)")
    if not path.name.startswith("_") and not has_main:
        rep.err(where, f"{path.name} has no main() entry point")


def load_registry(root: Path, rep: Report) -> dict[str, dict]:
    path = root / "sources" / "registry.json"
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        rep.err("sources/registry.json", f"unreadable: {exc}")
        return {}
    out: dict[str, dict] = {}
    for row in rows:
        sid = row.get("id", "<missing id>")
        where = f"sources/registry.json[{sid}]"
        for f in REGISTRY_FIELDS:
            if f not in row or row[f] in ("", None):
                rep.err(where, f"missing field '{f}'")
        if sid in out:
            rep.err(where, "duplicate source id")
        if not str(row.get("url", "")).startswith("https://"):
            rep.err(where, "url must be https")
        if row.get("access_status") not in ACCESS_STATUSES:
            rep.err(where, f"access_status must be one of {sorted(ACCESS_STATUSES)}")
        for dkey in ("last_checked", "review_by"):
            if row.get(dkey) and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(row[dkey])):
                rep.err(where, f"{dkey} must be YYYY-MM-DD")
        audit = row.get("audit")
        if audit and not (root / audit).is_file():
            rep.err(where, f"audit file not found: {audit}")
        out[sid] = row
    rep.stats["sources"] = len(out)
    return out


def load_packs(root: Path, rep: Report) -> dict:
    path = root / "packs" / "packs.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        rep.err("packs/packs.json", f"unreadable: {exc}")
        return {}
    return data.get("packs", {})


def check_skills(root: Path, registry: dict, packs: dict, rep: Report) -> dict[str, dict]:
    skills: dict[str, dict] = {}
    sdir = root / ".claude" / "skills"
    for skill_md in sorted(sdir.glob("*/SKILL.md")):
        d = skill_md.parent
        where = f"skill {d.name}"
        text = skill_md.read_text(encoding="utf-8")
        try:
            fm, body = frontmatter.load(text)
        except frontmatter.FrontmatterError as exc:
            rep.err(where, f"frontmatter: {exc}")
            continue
        unknown = set(fm) - SPEC_SKILL_KEYS
        if unknown:
            rep.err(where, f"non-spec frontmatter keys {sorted(unknown)} (breaks portability)")
        name = fm.get("name", "")
        if not isinstance(name, str) or not NAME_RE.fullmatch(name) or len(name) > 64:
            rep.err(where, f"invalid name {name!r}")
        if name != d.name:
            rep.err(where, f"name {name!r} must equal directory name")
        desc = fm.get("description")
        if not isinstance(desc, str) or not desc.strip():
            rep.err(where, "description missing")
        elif len(desc) > 1024:
            rep.err(where, f"description too long ({len(desc)} > 1024)")
        elif len(desc) < 80:
            rep.warn(where, "description is very short; include what + when + trigger keywords")
        comp = fm.get("compatibility")
        if comp is not None and (not isinstance(comp, str) or not 1 <= len(comp) <= 500):
            rep.err(where, "compatibility must be 1-500 characters")
        if "allowed-tools" in fm and not isinstance(fm["allowed-tools"], str):
            rep.err(where, "allowed-tools must be a space-separated string")
        meta = fm.get("metadata", {})
        if not isinstance(meta, dict):
            rep.err(where, "metadata must be a mapping of strings")
            meta = {}
        for k in REQUIRED_SKILL_METADATA:
            if k not in meta:
                rep.err(where, f"metadata.{k} missing")
        if meta.get("version") and not SEMVER.fullmatch(meta["version"]):
            rep.err(where, "metadata.version must be semver X.Y.Z")
        srcs = meta.get("sources", "").split()
        for s in srcs:
            if s not in registry:
                rep.err(where, f"metadata.sources references unknown source '{s}'")
        pack = meta.get("pack")
        if pack and pack not in packs:
            rep.err(where, f"metadata.pack '{pack}' not defined in packs/packs.json")
        elif pack and name not in packs[pack].get("skills", []):
            rep.err(where, f"skill not listed in its pack '{pack}'")
        nlines = text.count("\n") + 1
        if nlines >= 500:
            rep.err(where, f"SKILL.md has {nlines} lines (spec recommends < 500)")
        _check_sections(where, body, SKILL_SECTIONS, rep)
        for m in LINK_RE.finditer(body):
            target = m.group(1) or m.group(2)
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            target = target.rstrip(".,;:")
            if "*" in target or "<" in target:
                continue
            if not (d / target).exists():
                rep.err(where, f"referenced file does not exist: {target}")
        for py in sorted((d / "scripts").glob("*.py")) if (d / "scripts").is_dir() else []:
            _stdlib_check(py, rep, where)
        for sub in d.rglob("*"):
            if sub.is_file() and sub.relative_to(d).parts[0] not in ("SKILL.md", "scripts", "references", "assets"):
                rep.warn(where, f"file outside conventional folders: {sub.relative_to(d)}")
        skills[name] = {"dir": d, "meta": meta, "frontmatter": fm}
    rep.stats["skills"] = len(skills)
    return skills


def check_agents(root: Path, skills: dict, rep: Report) -> dict[str, dict]:
    agents: dict[str, dict] = {}
    for path in sorted((root / ".claude" / "agents").glob("*.md")):
        where = f"agent {path.stem}"
        try:
            fm, body = frontmatter.load(path.read_text(encoding="utf-8"))
        except frontmatter.FrontmatterError as exc:
            rep.err(where, f"frontmatter: {exc}")
            continue
        unknown = set(fm) - AGENT_KEYS
        if unknown:
            rep.err(where, f"unsupported frontmatter keys {sorted(unknown)}")
        name = fm.get("name")
        if not isinstance(name, str) or not name or ":" in name:
            rep.err(where, "name missing or contains ':'")
            continue
        if name != path.stem:
            rep.err(where, "name should equal the file name for maintainability")
        if name in agents:
            rep.err(where, "duplicate agent name")
        if not isinstance(fm.get("description"), str) or len(fm.get("description", "")) < 40:
            rep.err(where, "description missing or too short to route delegation")
        tools_raw = fm.get("tools")
        if tools_raw is None:
            rep.err(where, "tools must be an explicit allowlist (omitting it inherits every tool)")
            tools: list[str] = []
        else:
            tools = tools_raw if isinstance(tools_raw, list) else [t.strip() for t in tools_raw.split(",")]
        for t in tools:
            base = t.split("(", 1)[0]
            if base not in KNOWN_TOOLS and not base.startswith("mcp__"):
                rep.err(where, f"unknown tool '{t}'")
        if name.endswith("-reviewer") and {"Write", "Edit", "NotebookEdit"} & {t.split("(")[0] for t in tools}:
            rep.err(where, "reviewer agents must not have Write/Edit (separation of duties)")
        if fm.get("color") and fm["color"] not in AGENT_COLORS:
            rep.err(where, f"color must be one of {sorted(AGENT_COLORS)}")
        preload = fm.get("skills", [])
        if isinstance(preload, str):
            preload = [preload]
        if len(preload) > 3:
            rep.warn(where, f"preloads {len(preload)} skills; full text of each enters context")
        refs = set(preload)
        for s in preload:
            if s not in skills:
                rep.err(where, f"preloaded skill '{s}' does not exist")
        _check_sections(where, body, AGENT_SECTIONS, rep)
        for s in re.findall(r"`([a-z0-9]+(?:-[a-z0-9]+)*)`", _section_text(body, "Skills")):
            refs.add(s)
            if s not in skills:
                rep.err(where, f"Skills section references unknown skill '{s}'")
        if not refs:
            rep.err(where, "agent references no skills")
        agents[name] = {"skills": sorted(refs), "tools": tools}
    rep.stats["agents"] = len(agents)
    return agents


def check_packs(packs: dict, skills: dict, agents: dict, rep: Report) -> None:
    seen_skills: set[str] = set()
    seen_agents: set[str] = set()
    for pname, p in packs.items():
        where = f"pack {pname}"
        if not NAME_RE.fullmatch(pname):
            rep.err(where, "invalid pack name")
        for k in ("title", "description", "skills", "agents", "sources"):
            if k not in p:
                rep.err(where, f"missing '{k}'")
        for s in p.get("skills", []):
            if s not in skills:
                rep.err(where, f"unknown skill '{s}'")
            seen_skills.add(s)
        for a in p.get("agents", []):
            if a not in agents:
                rep.err(where, f"unknown agent '{a}'")
            seen_agents.add(a)
    for s in sorted(set(skills) - seen_skills):
        rep.err(f"skill {s}", "not included in any pack")
    for a in sorted(set(agents) - seen_agents):
        rep.err(f"agent {a}", "not included in any pack")
    rep.stats["packs"] = len(packs)


def check_nasa_map(root: Path, registry: dict, skills: dict, rep: Report) -> None:
    where = "sources/nasa-17-processes.json"
    try:
        data = json.loads((root / where).read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        rep.err(where, f"unreadable: {exc}")
        return
    procs = data.get("processes", [])
    if len(procs) != 17:
        rep.err(where, f"expected 17 processes, found {len(procs)}")
    groups = {"System design": 4, "Product realization": 5, "Technical management": 8}
    for g, n in groups.items():
        c = sum(1 for p in procs if p.get("group") == g)
        if c != n:
            rep.err(where, f"group '{g}' should have {n} processes, found {c}")
    for i, p in enumerate(procs, 1):
        pid = p.get("id")
        if pid != f"SE-{i:02d}":
            rep.err(where, f"non-consecutive id {pid}")
        if p.get("source_id") not in registry:
            rep.err(where, f"{pid}: unknown source {p.get('source_id')}")
        sk = p.get("skill_ids", [])
        if not sk:
            rep.err(where, f"{pid}: no skills mapped (orphan process)")
        for s in sk:
            if s not in skills:
                rep.err(where, f"{pid}: mapped skill '{s}' does not exist")
        for t in p.get("tests", []):
            if not (root / t).is_file():
                rep.err(where, f"{pid}: test file not found {t}")
        if not p.get("artifacts"):
            rep.err(where, f"{pid}: no artifacts mapped")


def check_crosswalks(root: Path, registry: dict, skills: dict, agents: dict, rep: Report) -> None:
    cdir = root / "docs" / "crosswalks"
    for sid in registry:
        path = cdir / f"{sid}.json"
        where = f"docs/crosswalks/{sid}.json"
        if not path.is_file():
            rep.err(where, "missing crosswalk for registered source")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            rep.err(where, f"unreadable: {exc}")
            continue
        if data.get("source_id") != sid:
            rep.err(where, "source_id mismatch")
        rows = data.get("rows", [])
        if not rows and data.get("status") != "BLOCKED_SOURCE":
            rep.err(where, "no rows and not marked BLOCKED_SOURCE")
        for r in rows:
            el = r.get("source_element", "?")
            for s in r.get("skills", []):
                if s not in skills:
                    rep.err(where, f"[{el}] unknown skill '{s}'")
            for a in r.get("agents", []):
                if a not in agents:
                    rep.err(where, f"[{el}] unknown agent '{a}'")
            for t in r.get("tests", []):
                if not (root / t).is_file():
                    rep.err(where, f"[{el}] test file not found: {t}")
            if r.get("source_verification") not in ("verified", "partially_verified", "unverified"):
                rep.err(where, f"[{el}] source_verification must be verified|partially_verified|unverified")


def run(root: Path) -> Report:
    rep = Report()
    registry = load_registry(root, rep)
    packs = load_packs(root, rep)
    skills = check_skills(root, registry, packs, rep)
    agents = check_agents(root, skills, rep)
    check_packs(packs, skills, agents, rep)
    check_nasa_map(root, registry, skills, rep)
    check_crosswalks(root, registry, skills, agents, rep)
    return rep


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--filter", action="append", default=[],
                    help="only report findings whose location contains this text (repeatable)")
    args = ap.parse_args(argv)
    if not (args.root / ".claude" / "skills").is_dir():
        print(f"cannot find .claude/skills under {args.root}", file=sys.stderr)
        return 2
    rep = run(args.root)
    if args.filter:
        keep = lambda m: any(f in m.split(":", 1)[0] for f in args.filter)  # noqa: E731
        rep.errors = [e for e in rep.errors if keep(e)]
        rep.warnings = [w for w in rep.warnings if keep(w)]
    if args.json:
        print(json.dumps({"errors": rep.errors, "warnings": rep.warnings, "stats": rep.stats}, indent=2))
    else:
        for w in rep.warnings:
            print(f"WARN  {w}")
        for e in rep.errors:
            print(f"ERROR {e}")
        status = "FAIL" if rep.errors else "PASS"
        stats = ", ".join(f"{v} {k}" for k, v in rep.stats.items())
        print(f"{status}: {stats}; {len(rep.errors)} errors, {len(rep.warnings)} warnings.")
        print("Scope: structural consistency only — not evidence of engineering, legal or financial correctness.")
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
