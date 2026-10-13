"""Tests for the library's own quality gates (validator, frontmatter parser, manifests)."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers import ROOT

sys.path.insert(0, str(ROOT / "scripts"))
import validate_library  # noqa: E402
from agentlib import frontmatter  # noqa: E402

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None


def copy_library(dst: Path) -> None:
    for rel in (".claude", "sources", "packs", "docs/crosswalks", "tests"):
        src = ROOT / rel
        shutil.copytree(src, dst / rel, ignore=shutil.ignore_patterns("__pycache__"))


class FrontmatterParserTests(unittest.TestCase):
    def test_rejects_unsupported_constructs(self):
        bad = ["description: |\n  multi\n", "name: a\nname: b\n", "\tname: x\n", "key: a: b\n", "x: 'unterminated\n"]
        for fm in bad:
            with self.assertRaises(frontmatter.FrontmatterError, msg=fm):
                frontmatter.parse(fm)

    def test_requires_leading_delimiter(self):
        with self.assertRaises(frontmatter.FrontmatterError):
            frontmatter.split("\n---\nname: x\n---\n")

    def test_parses_lists_maps_and_quotes(self):
        d = frontmatter.parse('name: x\nskills:\n  - a\n  - b\nmetadata:\n  version: "1.0.0"\ndescription: "a: b"\n')
        self.assertEqual(d, {"name": "x", "skills": ["a", "b"], "metadata": {"version": "1.0.0"}, "description": "a: b"})

    @unittest.skipIf(yaml is None, "PyYAML not installed")
    def test_parity_with_pyyaml_on_every_library_file(self):
        files = list((ROOT / ".claude/skills").glob("*/SKILL.md")) + list((ROOT / ".claude/agents").glob("*.md"))
        self.assertGreater(len(files), 40)
        for f in files:
            fm_text, _ = frontmatter.split(f.read_text(encoding="utf-8"))
            ours = frontmatter.parse(fm_text)
            theirs = yaml.safe_load(fm_text)
            theirs = {k: (str(v) if not isinstance(v, (list, dict)) else v) for k, v in theirs.items()}
            if isinstance(theirs.get("metadata"), dict):
                theirs["metadata"] = {k: str(v) for k, v in theirs["metadata"].items()}
            self.assertEqual(ours, theirs, str(f))


class ValidatorOnRealLibrary(unittest.TestCase):
    def test_library_is_structurally_valid(self):
        rep = validate_library.run(ROOT)
        self.assertEqual(rep.errors, [], "\n".join(rep.errors))
        self.assertEqual(rep.stats["skills"], 45)
        self.assertGreaterEqual(rep.stats["agents"], 14)


class ValidatorMutationTests(unittest.TestCase):
    """Each mutation re-creates a realistic defect; the validator must catch it."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        copy_library(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def errors(self):
        return "\n".join(validate_library.run(self.root).errors)

    def edit(self, rel, old, new):
        p = self.root / rel
        p.write_text(p.read_text(encoding="utf-8").replace(old, new, 1), encoding="utf-8")

    def test_nasa_map_phantom_skill(self):  # the original starter-kit defect
        p = self.root / "sources/nasa-17-processes.json"
        d = json.loads(p.read_text())
        d["processes"][2]["skill_ids"] = ["se-does-not-exist"]
        p.write_text(json.dumps(d))
        self.assertIn("mapped skill 'se-does-not-exist' does not exist", self.errors())

    def test_nasa_map_wrong_count(self):
        p = self.root / "sources/nasa-17-processes.json"
        d = json.loads(p.read_text())
        d["processes"].pop()
        p.write_text(json.dumps(d))
        self.assertIn("expected 17 processes", self.errors())

    def test_skill_name_mismatch_and_bad_name(self):
        self.edit(".claude/skills/se-requirements/SKILL.md", "name: se-requirements", "name: SE--Requirements")
        e = self.errors()
        self.assertIn("invalid name", e)
        self.assertIn("must equal directory name", e)

    def test_non_spec_key_rejected(self):
        self.edit(".claude/skills/se-requirements/SKILL.md", "metadata:", "context: fork\nmetadata:")
        self.assertIn("non-spec frontmatter keys ['context']", self.errors())

    def test_missing_section(self):
        self.edit(".claude/skills/se-requirements/SKILL.md", "## Decision criteria", "## Rules")
        self.assertIn("missing required sections: Decision criteria", self.errors())

    def test_broken_reference(self):
        self.edit(".claude/skills/se-requirements/SKILL.md", "(references/requirements-quality.md)", "(references/missing.md)")
        self.assertIn("referenced file does not exist: references/missing.md", self.errors())

    def test_non_stdlib_import(self):
        p = self.root / ".claude/skills/se-requirements/scripts/req_lint.py"
        p.write_text("import requests\n" + p.read_text())
        self.assertIn("non-stdlib module 'requests'", self.errors())

    def test_unknown_source(self):
        self.edit(".claude/skills/se-requirements/SKILL.md", 'sources: "nasa-se-design', 'sources: "made-up-source nasa-se-design')
        self.assertIn("unknown source 'made-up-source'", self.errors())

    def test_agent_without_tools_inherits_everything(self):
        self.edit(".claude/agents/systems-engineer.md", "tools: Read, Grep, Glob, Bash, Write, Edit\n", "")
        self.assertIn("tools must be an explicit allowlist", self.errors())

    def test_reviewer_with_write(self):
        self.edit(".claude/agents/independent-reviewer.md", "tools: Read, Grep, Glob, Bash", "tools: Read, Grep, Glob, Bash, Write")
        self.assertIn("reviewer agents must not have Write/Edit", self.errors())

    def test_agent_missing_skill(self):
        self.edit(".claude/agents/vv-engineer.md", "- `se-transition`", "- `se-teleportation`")
        self.assertIn("unknown skill 'se-teleportation'", self.errors())

    def test_skill_not_in_pack(self):
        p = self.root / "packs/packs.json"
        d = json.loads(p.read_text())
        d["packs"]["systems-engineering"]["skills"].remove("se-transition")
        p.write_text(json.dumps(d))
        self.assertIn("skill not listed in its pack", self.errors())

    def test_registry_bad_status_and_missing_crosswalk(self):
        p = self.root / "sources/registry.json"
        d = json.loads(p.read_text())
        d[0]["access_status"] = "TRUST_ME"
        p.write_text(json.dumps(d))
        (self.root / "docs/crosswalks/dora.json").unlink()
        e = self.errors()
        self.assertIn("access_status must be one of", e)
        self.assertIn("docs/crosswalks/dora.json: missing crosswalk", e)

    def test_crosswalk_bad_verification_label(self):
        p = self.root / "docs/crosswalks/nasa-se.json"
        d = json.loads(p.read_text())
        d["rows"][0]["source_verification"] = "probably"
        p.write_text(json.dumps(d))
        self.assertIn("source_verification must be", self.errors())


if __name__ == "__main__":
    unittest.main()
