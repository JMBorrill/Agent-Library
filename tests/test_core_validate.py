"""Tests for the core validators using small synthetic libraries."""
import json
import shutil
from pathlib import Path

import pytest

from agentlib import frontmatter
from agentlib.validate import (check_agents, check_catalogs, check_commands, check_skills,
                               check_workflows, validate_all)

SKILL = """---
name: demo-skill
description: Demonstrates the skill contract for validator tests. Use when testing the validator.
metadata:
  version: 1.0.0
  category: meta
  maturity: draft
  sources: [nasa-se]
---
# Demo
## When to use
x
## Workflow
1. [ref](references/guide.md)
## Outputs
x
## Sources
- nasa-se, Rev 2, p. 1
## Limitations
x
"""

AGENT = """---
name: demo-agent
description: A demonstration agent used by the validator tests; delegate here when testing the validator.
tools: Read, Grep
model: inherit
---
You are a demo agent. Use skills/demo-skill/ for everything. """ + "Lorem ipsum dolor sit amet. " * 10


@pytest.fixture
def lib(tmp_path, root):
    (tmp_path / "schemas").mkdir()
    for s in (root / "schemas").glob("*.json"):
        shutil.copy(s, tmp_path / "schemas" / s.name)
    (tmp_path / "sources").mkdir()
    shutil.copy(root / "sources" / "pdf-manifest.json", tmp_path / "sources" / "pdf-manifest.json")
    sd = tmp_path / "skills" / "demo-skill"
    (sd / "references").mkdir(parents=True)
    (sd / "SKILL.md").write_text(SKILL)
    (sd / "references" / "guide.md").write_text("# guide\n")
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "demo-agent.md").write_text(AGENT)
    for d in ("commands", "workflows", "catalog", "evals"):
        (tmp_path / d).mkdir()
    return tmp_path


def errors(issues):
    return [i for i in issues if i.level == "error"]


def test_frontmatter_split():
    meta, body = frontmatter.split("---\na: 1\n---\nbody\n")
    assert meta == {"a": 1} and body == "body\n"
    with pytest.raises(frontmatter.FrontMatterError):
        frontmatter.split("no front matter")
    with pytest.raises(frontmatter.FrontMatterError):
        frontmatter.split("---\na: 1\n")


def test_valid_skill_and_agent(lib):
    assert errors(check_skills(lib)) == []
    assert errors(check_agents(lib)) == []


def test_skill_name_mismatch_and_missing_section(lib):
    p = lib / "skills" / "demo-skill" / "SKILL.md"
    p.write_text(SKILL.replace("name: demo-skill", "name: other").replace("## Limitations\nx\n", ""))
    msgs = " ".join(str(i) for i in errors(check_skills(lib)))
    assert "must equal directory" in msgs
    assert "Limitations" in msgs


def test_skill_unknown_source_and_uncited(lib):
    p = lib / "skills" / "demo-skill" / "SKILL.md"
    p.write_text(SKILL.replace("sources: [nasa-se]", "sources: [nasa-se, made-up]"))
    msgs = " ".join(str(i) for i in errors(check_skills(lib)))
    assert "unknown source id 'made-up'" in msgs
    assert "not cited" in msgs


def test_skill_broken_link(lib):
    (lib / "skills" / "demo-skill" / "references" / "guide.md").unlink()
    assert any("broken relative link" in i.message for i in errors(check_skills(lib)))


def test_skill_unknown_frontmatter_key(lib):
    p = lib / "skills" / "demo-skill" / "SKILL.md"
    p.write_text(SKILL.replace("metadata:", "colour: blue\nmetadata:"))
    assert errors(check_skills(lib))


def test_agent_unknown_skill_reference(lib):
    p = lib / "agents" / "demo-agent.md"
    p.write_text(AGENT.replace("skills/demo-skill/", "skills/ghost/"))
    assert any("ghost" in i.message for i in errors(check_agents(lib)))


def test_command_unknown_workflow(lib):
    (lib / "commands" / "go.md").write_text("---\ndescription: Run the demo workflow end to end.\n---\nFollow workflows/nope.yaml\n")
    assert any("nope" in i.message for i in errors(check_commands(lib)))


def _wf(**over):
    wf = {
        "id": "demo", "title": "Demo", "version": "1.0.0",
        "description": "A demonstration workflow for validator tests.",
        "inputs": [{"name": "brief", "description": "input"}],
        "outputs": [{"name": "report", "description": "out"}],
        "stages": [
            {"id": "a", "title": "A", "agent": "demo-agent", "skills": ["demo-skill"], "consumes": ["brief"],
             "produces": ["draft"], "gate": {"criteria": ["ok"], "decision": "human"}},
            {"id": "b", "title": "B", "agent": "demo-agent", "skills": [], "depends_on": ["a"], "consumes": ["draft"],
             "produces": ["report"], "gate": {"criteria": ["ok"], "decision": "automated"}},
        ],
    }
    wf.update(over)
    return wf


def test_workflow_valid_and_broken(lib):
    import yaml

    path = lib / "workflows" / "demo.yaml"
    path.write_text(yaml.safe_dump(_wf()))
    assert errors(check_workflows(lib)) == []
    bad = _wf()
    bad["stages"][1]["consumes"] = ["missing-artefact"]
    bad["stages"][0]["agent"] = "ghost"
    bad["stages"][1]["depends_on"] = ["zzz"]
    path.write_text(yaml.safe_dump(bad))
    msgs = " ".join(i.message for i in errors(check_workflows(lib)))
    assert "unknown agent" in msgs and "missing-artefact" in msgs and "zzz" in msgs


def test_catalog_page_range(lib):
    cat = {
        "catalog_id": "demo", "source_id": "nist-ssdf", "title": "t", "edition": "e",
        "extraction": {"method": "m", "date": "2026-10-13", "fidelity": "structural"},
        "items": [{"id": "X", "text": "abc", "citation": {"pdf_page": 999}},
                  {"id": "X", "text": "abc", "citation": {"pdf_page": 1}}],
    }
    (lib / "catalog" / "demo.json").write_text(json.dumps(cat))
    msgs = " ".join(i.message for i in errors(check_catalogs(lib)))
    assert "outside" in msgs and "duplicate" in msgs


def test_repository_validates(root):
    """The real library must be free of validation errors."""
    issues = errors(validate_all(root))
    assert issues == [], "\n".join(map(str, issues))


def test_source_citation_is_token_matched(lib):
    p = lib / "skills" / "demo-skill" / "SKILL.md"
    p.write_text(SKILL.replace("- nasa-se, Rev 2, p. 1", "- nasa-se-design, Rev 2, p. 1"))
    assert any("not cited" in i.message for i in errors(check_skills(lib)))


def test_headings_in_code_fences_do_not_count(lib):
    p = lib / "skills" / "demo-skill" / "SKILL.md"
    p.write_text(SKILL.replace("## Limitations\nx\n", "```md\n## Limitations\n```\n"))
    assert any("Limitations" in i.message for i in errors(check_skills(lib)))
