import unittest

from tests.helpers import load_script, rules, run_cli, run_json, skill_path

SKILL = "se-stakeholder-conops"
mod = load_script(SKILL, "conops_check")
EX = skill_path(SKILL, "assets", "examples")


class ConopsTests(unittest.TestCase):
    def test_pass(self):
        code, out = run_json(SKILL, "conops_check", EX / "conops-pass.md", "--stakeholders",
                             EX / "stakeholders-pass.csv", "--needs", EX / "needs-pass.csv")
        self.assertEqual(code, 0)
        self.assertEqual(out["summary"], {"errors": 0, "warnings": 0})

    def test_fail(self):
        code, out = run_json(SKILL, "conops_check", EX / "conops-fail.md", "--stakeholders",
                             EX / "stakeholders-fail.csv", "--needs", EX / "needs-fail.csv")
        self.assertEqual(code, 1)
        self.assertTrue({"missing-section", "no-off-nominal", "unsupported-stakeholder-claim", "need-without-moe",
                         "no-decision-owner", "no-role", "unknown-need"} <= rules(out["findings"], "error"))
        self.assertIn("solution-in-need", rules(out["findings"], "warning"))

    def test_evidence_tag_allows_claim(self):
        md = "## Mission need\nx\n## Operational scenarios\nnominal; off-nominal fault\nUsers said it hurts [evidence: R-12]\n"
        self.assertNotIn("unsupported-stakeholder-claim", rules(mod.check_conops(md)))

    def test_registers_independent(self):
        f = mod.check_registers([{"stakeholder": "A", "role": "r", "decision_rights": "yes", "needs": ""}], None)
        self.assertEqual(f, [])

    def test_unreadable(self):
        self.assertEqual(run_cli(SKILL, "conops_check", "missing.md").returncode, 2)


if __name__ == "__main__":
    unittest.main()
