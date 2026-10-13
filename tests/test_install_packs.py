import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers import ROOT

SCRIPT = ROOT / "scripts" / "install_packs.py"


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True, timeout=120)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = Path(self.tmp.name)
        (self.t / ".claude").mkdir()
        (self.t / ".claude" / "settings.json").write_text('{"keep": true}')
        (self.t / "CLAUDE.md").write_text("project rules")

    def tearDown(self):
        self.tmp.cleanup()

    def test_dry_run_writes_nothing(self):
        p = run("--target", self.t, "--packs", "systems-engineering", "--json")
        self.assertEqual(p.returncode, 0, p.stderr)
        rep = json.loads(p.stdout)
        self.assertTrue(rep["dry_run"])
        self.assertFalse((self.t / ".claude" / "skills").exists())
        self.assertTrue(all(i["action"] == "CREATE" for i in rep["items"]))

    def test_apply_then_idempotent(self):
        self.assertEqual(run("--target", self.t, "--skills", "se-requirements", "--apply").returncode, 0)
        self.assertTrue((self.t / ".claude/skills/se-requirements/scripts/req_lint.py").is_file())
        rep = json.loads(run("--target", self.t, "--skills", "se-requirements", "--json").stdout)
        self.assertEqual(rep["items"][0]["action"], "SKIP")
        manifest = json.loads((self.t / ".claude/agent-library.lock.json").read_text())
        self.assertIn("skill:se-requirements", manifest["installed"])

    def test_conflict_refused_without_overwrite(self):
        agents = self.t / ".claude" / "agents"
        agents.mkdir()
        (agents / "requirements-engineer.md").write_text("user's own agent")
        p = run("--target", self.t, "--agents", "requirements-engineer", "--apply", "--json")
        self.assertEqual(p.returncode, 1)
        self.assertIn("refused", json.loads(p.stdout))
        self.assertEqual((agents / "requirements-engineer.md").read_text(), "user's own agent")
        self.assertFalse((self.t / ".claude/skills").exists())  # nothing written at all

    def test_overwrite_makes_backup(self):
        agents = self.t / ".claude" / "agents"
        agents.mkdir()
        (agents / "requirements-engineer.md").write_text("user's own agent")
        p = run("--target", self.t, "--agents", "requirements-engineer", "--apply", "--overwrite")
        self.assertEqual(p.returncode, 0, p.stderr)
        backups = list((self.t / ".agent-library-backup").rglob("requirements-engineer.md"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), "user's own agent")
        self.assertIn("name: requirements-engineer", (agents / "requirements-engineer.md").read_text())

    def test_protected_files_untouched_and_dependencies_added(self):
        p = run("--target", self.t, "--agents", "vv-engineer", "--apply", "--json")
        rep = json.loads(p.stdout)
        self.assertTrue(any("required by agent 'vv-engineer'" in n for n in rep["notes"]))
        self.assertEqual((self.t / ".claude/settings.json").read_text(), '{"keep": true}')
        self.assertEqual((self.t / "CLAUDE.md").read_text(), "project rules")

    def test_skills_only_alternate_dir(self):
        p = run("--target", self.t, "--packs", "ai-governance", "--no-agents", "--skills-dir", ".agents/skills", "--apply")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue((self.t / ".agents/skills/ai-eval-harness/SKILL.md").is_file())
        self.assertFalse((self.t / ".claude/agents").exists())

    def test_bad_inputs(self):
        self.assertEqual(run("--target", self.t, "--packs", "nope").returncode, 2)
        self.assertEqual(run("--target", self.t / "missing", "--packs", "ux").returncode, 2)
        self.assertEqual(run("--target", ROOT, "--packs", "ux").returncode, 2)
        self.assertEqual(run("--target", self.t, "--skills-dir", "../escape", "--packs", "ux").returncode, 2)
        self.assertEqual(run("--target", self.t).returncode, 2)

    def test_list(self):
        p = run("--list")
        self.assertEqual(p.returncode, 0)
        self.assertIn("systems-engineering", p.stdout)


if __name__ == "__main__":
    unittest.main()
