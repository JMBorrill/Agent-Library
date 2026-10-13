"""Library content must itself meet the evidence standard it enforces."""
import pytest

from agentlib.frameworks import evidence


def _docs(root):
    return sorted(list((root / "skills").rglob("*.md")) + list((root / "agents").glob("*.md"))
                  + list((root / "commands").glob("*.md")) + list((root / "templates").glob("*.md")))


def test_no_citation_or_identifier_errors_in_library_content(root):
    problems = []
    for path in _docs(root):
        for f in evidence.check_document(path.read_text(encoding="utf-8"), root):
            if f.level == "error":
                problems.append(f"{path.relative_to(root)}:{f.line}: {f.message}")
    assert not problems, "\n".join(problems)


def test_every_skill_states_limitations_about_professional_judgement(root):
    for skill in sorted((root / "skills").glob("*/SKILL.md")):
        text = skill.read_text(encoding="utf-8").lower()
        limitations = text.split("## limitations", 1)[-1]
        assert any(w in limitations for w in ("judgement", "judgment", "approval", "assurance")), skill


@pytest.mark.parametrize("sub", ["references", "templates"])
def test_framework_skills_ship_references_and_templates(root, sub):
    for skill in sorted((root / "skills").glob("*/SKILL.md")):
        if skill.parent.name == "framework-selector" and sub == "templates":
            continue
        assert any((skill.parent / sub).glob("*.md")), f"{skill.parent.name} has no {sub}/"
