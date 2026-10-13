"""Structural validation for every component in the library.

Each ``check_*`` function returns a list of :class:`Issue`. ``validate_all``
runs every check. Errors fail CI; warnings are reported but do not fail
unless ``--strict`` is used.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import jsonschema
import yaml

from agentlib import frontmatter
from agentlib.paths import repo_root

# Sections every SKILL.md body must contain (level-2 headings, case-insensitive
# prefix match so "## Workflow" and "## Workflow (step by step)" both pass).
REQUIRED_SKILL_SECTIONS = ("When to use", "Workflow", "Outputs", "Sources", "Limitations")
MAX_SKILL_BODY_LINES = 500  # Anthropic guidance: keep SKILL.md lean, push detail to references/
KNOWN_TOOLS = {
    "Read", "Write", "Edit", "MultiEdit", "Glob", "Grep", "Bash", "WebFetch", "WebSearch",
    "Task", "Agent", "TodoWrite", "NotebookEdit", "Skill",
}
LINK_RE = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")


@dataclass(frozen=True)
class Issue:
    level: str  # "error" | "warning"
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.level.upper()}: {self.path}: {self.message}"


def _schema(root: Path, name: str) -> dict:
    return json.loads((root / "schemas" / name).read_text(encoding="utf-8"))


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def known_source_ids(root: Path) -> set[str]:
    """Source IDs declared in ``sources/pdf-manifest.json`` (bundled, linked and aliases)."""
    manifest = json.loads((root / "sources" / "pdf-manifest.json").read_text(encoding="utf-8"))
    ids = {s["id"] for s in manifest.get("sources", [])}
    ids |= {s["id"] for s in manifest.get("linked_sources", [])}
    ids |= set(manifest.get("framework_aliases", {}))
    return ids


def bundled_page_counts(root: Path) -> dict[str, int]:
    manifest = json.loads((root / "sources" / "pdf-manifest.json").read_text(encoding="utf-8"))
    return {s["id"]: s["pages"] for s in manifest.get("sources", [])}


def _schema_errors(schema: dict, data: object, rel: str, what: str) -> list[Issue]:
    validator = jsonschema.Draft202012Validator(schema)
    out = []
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        loc = "/".join(str(p) for p in err.path) or "<root>"
        out.append(Issue("error", rel, f"{what} {loc}: {err.message}"))
    return out


def _check_links(root: Path, md_path: Path, body: str) -> list[Issue]:
    issues = []
    for target in LINK_RE.findall(body):
        if re.match(r"^[a-z]+:", target):  # http:, https:, mailto:
            continue
        resolved = (md_path.parent / target).resolve()
        if not resolved.exists():
            issues.append(Issue("error", _rel(root, md_path), f"broken relative link: {target}"))
    return issues


FENCE_RE = re.compile(r"^(```|~~~).*?^\1[^\n]*$", re.M | re.S)


def _strip_fences(body: str) -> str:
    """Remove fenced code blocks so headings inside examples do not count."""
    return FENCE_RE.sub("", body)


def _sections(body: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"^##\s+(.+)$", _strip_fences(body), re.M)]


# ---------------------------------------------------------------- skills
def check_skills(root: Path) -> list[Issue]:
    issues: list[Issue] = []
    schema = _schema(root, "skill-frontmatter.schema.json")
    sources = known_source_ids(root)
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        return [Issue("error", "skills", "skills/ directory missing")]
    for skill_dir in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
        md = skill_dir / "SKILL.md"
        rel = _rel(root, md)
        if not md.is_file():
            issues.append(Issue("error", _rel(root, skill_dir), "missing SKILL.md"))
            continue
        try:
            meta, body = frontmatter.load(md)
        except frontmatter.FrontMatterError as exc:
            issues.append(Issue("error", rel, str(exc)))
            continue
        issues += _schema_errors(schema, meta, rel, "front matter")
        if meta.get("name") != skill_dir.name:
            issues.append(Issue("error", rel, f"name '{meta.get('name')}' must equal directory '{skill_dir.name}'"))
        md_meta = meta.get("metadata") or {}
        for sid in md_meta.get("sources", []):
            if sid not in sources:
                issues.append(Issue("error", rel, f"unknown source id '{sid}' (see sources/pdf-manifest.json)"))
        for cat in md_meta.get("catalogs", []):
            if not (root / "catalog" / f"{cat}.json").is_file():
                issues.append(Issue("error", rel, f"declared catalog '{cat}' not found in catalog/"))
        present = [s.lower() for s in _sections(body)]
        for req in REQUIRED_SKILL_SECTIONS:
            if not any(s.startswith(req.lower()) for s in present):
                issues.append(Issue("error", rel, f"missing required section '## {req}'"))
        n_lines = body.count("\n")
        if n_lines > MAX_SKILL_BODY_LINES:
            issues.append(Issue("warning", rel, f"body has {n_lines} lines (> {MAX_SKILL_BODY_LINES}); move detail to references/"))
        sources_section = _section_text(_strip_fences(body), "Sources")
        for sid in md_meta.get("sources", []):
            # token match: citing "nist-ai-playbook" must not count as citing "nist-ai"
            if not re.search(rf"(?<![\w-]){re.escape(sid)}(?![\w-])", sources_section):
                issues.append(Issue("error", rel, f"source '{sid}' declared in metadata but not cited in '## Sources'"))
        issues += _check_links(root, md, body)
        for extra in skill_dir.rglob("*.md"):
            if extra.name != "SKILL.md":
                issues += _check_links(root, extra, extra.read_text(encoding="utf-8"))
        desc = meta.get("description", "")
        if isinstance(desc, str) and "use when" not in desc.lower() and "use for" not in desc.lower():
            issues.append(Issue("warning", rel, "description should say when to use the skill ('Use when ...')"))
    return issues


def _section_text(body: str, title: str) -> str:
    m = re.search(rf"^##\s+{re.escape(title)}.*?$(.*?)(?=^##\s|\Z)", body, re.M | re.S | re.I)
    return m.group(1) if m else ""


# ---------------------------------------------------------------- agents & commands
def _tool_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [t.strip() for t in value.split(",") if t.strip()]
    return list(value)


def check_agents(root: Path) -> list[Issue]:
    issues: list[Issue] = []
    schema = _schema(root, "agent-frontmatter.schema.json")
    skills = {p.name for p in (root / "skills").iterdir() if p.is_dir()} if (root / "skills").is_dir() else set()
    for md in sorted((root / "agents").glob("*.md")):
        rel = _rel(root, md)
        try:
            meta, body = frontmatter.load(md)
        except frontmatter.FrontMatterError as exc:
            issues.append(Issue("error", rel, str(exc)))
            continue
        issues += _schema_errors(schema, meta, rel, "front matter")
        if meta.get("name") != md.stem:
            issues.append(Issue("error", rel, f"name '{meta.get('name')}' must equal file stem '{md.stem}'"))
        for tool in _tool_list(meta.get("tools")):
            base = tool.split("(")[0]
            if base not in KNOWN_TOOLS and not base.startswith("mcp__"):
                issues.append(Issue("warning", rel, f"unrecognised tool '{tool}'"))
        for skill in _tool_list(meta.get("skills")):
            if skill not in skills:
                issues.append(Issue("error", rel, f"references unknown skill '{skill}'"))
        for ref in re.findall(r"skills/([a-z0-9-]+)/", body):
            if ref not in skills:
                issues.append(Issue("error", rel, f"body references unknown skill path skills/{ref}/"))
        if len(body.strip()) < 200:
            issues.append(Issue("error", rel, "agent system prompt body is too short (< 200 chars)"))
        issues += _check_links(root, md, body)
    return issues


def check_commands(root: Path) -> list[Issue]:
    issues: list[Issue] = []
    schema = _schema(root, "command-frontmatter.schema.json")
    workflows = {p.stem for p in (root / "workflows").glob("*.yaml")}
    for md in sorted((root / "commands").glob("*.md")):
        rel = _rel(root, md)
        try:
            meta, body = frontmatter.load(md)
        except frontmatter.FrontMatterError as exc:
            issues.append(Issue("error", rel, str(exc)))
            continue
        issues += _schema_errors(schema, meta, rel, "front matter")
        for ref in re.findall(r"workflows/([a-z0-9-]+)\.yaml", body):
            if ref not in workflows:
                issues.append(Issue("error", rel, f"references unknown workflow workflows/{ref}.yaml"))
        issues += _check_links(root, md, body)
    return issues


# ---------------------------------------------------------------- workflows
def check_workflows(root: Path) -> list[Issue]:
    issues: list[Issue] = []
    schema = _schema(root, "workflow.schema.json")
    agents = {p.stem for p in (root / "agents").glob("*.md")}
    skills = {p.name for p in (root / "skills").iterdir() if p.is_dir()} if (root / "skills").is_dir() else set()
    sources = known_source_ids(root)
    for wf_path in sorted((root / "workflows").glob("*.yaml")):
        rel = _rel(root, wf_path)
        try:
            wf = yaml.safe_load(wf_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            issues.append(Issue("error", rel, f"invalid YAML: {exc}"))
            continue
        schema_issues = _schema_errors(schema, wf, rel, "workflow")
        issues += schema_issues
        if schema_issues:
            continue
        if wf["id"] != wf_path.stem:
            issues.append(Issue("error", rel, f"id '{wf['id']}' must equal file stem"))
        for sid in wf.get("sources", []):
            if sid not in sources:
                issues.append(Issue("error", rel, f"unknown source id '{sid}'"))
        for io in wf.get("inputs", []) + wf.get("outputs", []):
            if io.get("template") and not (root / io["template"]).is_file():
                issues.append(Issue("error", rel, f"template not found: {io['template']}"))
        seen: set[str] = set()
        produced: set[str] = {i["name"] for i in wf.get("inputs", [])}
        for stage in wf["stages"]:
            sid = stage["id"]
            if sid in seen:
                issues.append(Issue("error", rel, f"duplicate stage id '{sid}'"))
            if stage["agent"] not in agents:
                issues.append(Issue("error", rel, f"stage '{sid}': unknown agent '{stage['agent']}'"))
            for sk in stage["skills"]:
                if sk not in skills:
                    issues.append(Issue("error", rel, f"stage '{sid}': unknown skill '{sk}'"))
            for dep in stage.get("depends_on", []):
                if dep not in seen:
                    issues.append(Issue("error", rel, f"stage '{sid}': depends_on '{dep}' is not an earlier stage"))
            for artefact in stage.get("consumes", []):
                if artefact not in produced:
                    issues.append(Issue("error", rel, f"stage '{sid}': consumes '{artefact}' which no input or earlier stage produces"))
            produced |= set(stage["produces"])
            seen.add(sid)
        for out in wf.get("outputs", []):
            if out["name"] not in produced:
                issues.append(Issue("error", rel, f"workflow output '{out['name']}' is never produced by a stage"))
    return issues


# ---------------------------------------------------------------- catalogs
def check_catalogs(root: Path) -> list[Issue]:
    issues: list[Issue] = []
    schema = _schema(root, "catalog.schema.json")
    pages = bundled_page_counts(root)
    for path in sorted((root / "catalog").glob("*.json")):
        rel = _rel(root, path)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            issues.append(Issue("error", rel, f"invalid JSON: {exc}"))
            continue
        schema_issues = _schema_errors(schema, data, rel, "catalog")
        issues += schema_issues
        if schema_issues:
            continue
        if data["catalog_id"] != path.stem:
            issues.append(Issue("error", rel, "catalog_id must equal file stem"))
        src = data["source_id"]
        if src not in pages:
            issues.append(Issue("error", rel, f"source_id '{src}' is not a bundled PDF in the manifest"))
            continue
        max_page = pages[src]
        ids = set()
        group_ids = {g["id"] for g in data.get("groups", [])}
        for entry in data.get("groups", []) + data["items"]:
            cit = entry.get("citation")
            if cit and not 1 <= cit["pdf_page"] <= max_page:
                issues.append(Issue("error", rel, f"{entry['id']}: pdf_page {cit['pdf_page']} outside 1..{max_page}"))
        for item in data["items"]:
            if item["id"] in ids:
                issues.append(Issue("error", rel, f"duplicate item id '{item['id']}'"))
            ids.add(item["id"])
            if group_ids and item.get("group") and item["group"] not in group_ids:
                issues.append(Issue("error", rel, f"{item['id']}: unknown group '{item['group']}'"))
    return issues


# ---------------------------------------------------------------- evals
def check_evals(root: Path) -> list[Issue]:
    issues: list[Issue] = []
    from agentlib.evals.spec import load_suite, SpecError  # local import avoids cycle

    skills = {p.name for p in (root / "skills").iterdir() if p.is_dir()} if (root / "skills").is_dir() else set()
    evals_dir = root / "evals"
    covered = set()
    for suite_path in sorted(evals_dir.glob("*/cases.yaml")):
        rel = _rel(root, suite_path)
        try:
            suite = load_suite(suite_path)
        except SpecError as exc:
            issues.append(Issue("error", rel, str(exc)))
            continue
        if suite.skill not in skills:
            issues.append(Issue("error", rel, f"suite targets unknown skill '{suite.skill}'"))
        covered.add(suite.skill)
    for skill in sorted(skills - covered):
        issues.append(Issue("warning", f"skills/{skill}", "no evaluation suite in evals/<skill>/cases.yaml"))
    return issues


# ---------------------------------------------------------------- plugin manifest
def check_plugin(root: Path) -> list[Issue]:
    issues: list[Issue] = []
    plugin = root / ".claude-plugin" / "plugin.json"
    market = root / ".claude-plugin" / "marketplace.json"
    for p in (plugin, market):
        if not p.is_file():
            issues.append(Issue("error", _rel(root, p), "missing"))
    if issues:
        return issues
    try:
        data = json.loads(plugin.read_text(encoding="utf-8"))
        mk = json.loads(market.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [Issue("error", ".claude-plugin", f"invalid JSON: {exc}")]
    if not re.match(r"^[a-z0-9-]+$", data.get("name", "")):
        issues.append(Issue("error", _rel(root, plugin), "plugin name must be kebab-case"))
    names = [p.get("name") for p in mk.get("plugins", [])]
    if data.get("name") not in names:
        issues.append(Issue("error", _rel(root, market), "marketplace does not list the plugin"))
    for p in mk.get("plugins", []):
        if p.get("name") == data.get("name") and p.get("version") != data.get("version"):
            issues.append(Issue("error", _rel(root, market), "marketplace plugin version differs from plugin.json"))
    return issues


# ---------------------------------------------------------------- registry
def check_registry(root: Path) -> list[Issue]:
    from agentlib.registry import build_registry

    path = root / "registry.json"
    if not path.is_file():
        return [Issue("error", "registry.json", "missing; run `python -m agentlib registry --write`")]
    current = json.loads(path.read_text(encoding="utf-8"))
    if current != build_registry(root):
        return [Issue("error", "registry.json", "out of date; run `python -m agentlib registry --write`")]
    return []


CHECKS = {
    "skills": check_skills,
    "agents": check_agents,
    "commands": check_commands,
    "workflows": check_workflows,
    "catalogs": check_catalogs,
    "evals": check_evals,
    "plugin": check_plugin,
    "registry": check_registry,
}


def validate_all(root: Path | None = None, only: Iterable[str] | None = None) -> list[Issue]:
    root = root or repo_root()
    issues: list[Issue] = []
    for name, fn in CHECKS.items():
        if only and name not in only:
            continue
        issues += fn(root)
    return issues
