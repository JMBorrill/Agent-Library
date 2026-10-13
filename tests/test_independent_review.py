import unittest

from tests.helpers import load_script, rules, run_cli, run_json, skill_path

SKILL = "independent-review"
mod = load_script(SKILL, "claim_check")
EX = skill_path(SKILL, "assets", "examples")


class ClaimCheckTests(unittest.TestCase):
    def scan(self, text):
        return rules(mod.scan_text(text))

    def test_fixtures(self):
        code, out = run_json(SKILL, "claim_check", EX / "report-pass.md")
        self.assertEqual(code, 0)
        code, out = run_json(SKILL, "claim_check", EX / "report-fail.md")
        self.assertEqual(code, 1)
        errs = [f["rule"] for f in out["findings"] if f["severity"] == "error"]
        self.assertEqual(errs.count("assurance-claim"), 3)
        self.assertEqual(errs.count("unsupported-research"), 2)
        self.assertIn("absolute-claim", errs)

    def test_negation_and_signoff(self):
        self.assertEqual(self.scan("This is not approved until the owner signs."), set())
        self.assertEqual(self.scan("Only the gate authority can mark it approved."), set())
        self.assertEqual(self.scan("Baseline approved [signoff: Jane Owner, 2026-01-02]."), set())
        self.assertIn("assurance-claim", self.scan("Baseline approved."))

    def test_code_blocks_ignored(self):
        self.assertEqual(self.scan("```\nstatus = 'approved'\n```"), set())
        self.assertEqual(self.scan("Use `approved` as a status value is fine"), set())

    def test_research_needs_evidence(self):
        self.assertIn("unsupported-research", self.scan("Customers said they want SMS reminders."))
        self.assertEqual(self.scan("Customers said they want SMS reminders [evidence: INT-04]."), set())
        self.assertEqual(self.scan("We have not interviewed customers; users said nothing yet is NOT evidence."), set())

    def test_precise_citation_marker(self):
        self.assertIn("unverified-citation", self.scan("Follow MCOB 11.6 for affordability."))
        self.assertEqual(self.scan("Follow MCOB 11.6 for affordability (unverified)."), set())

    def test_absolute(self):
        self.assertIn("absolute-claim", self.scan("The model is 100% accurate."))

    def test_directory_scan_and_empty(self):
        code, out = run_json(SKILL, "claim_check", EX)
        self.assertEqual(out["summary"]["files"], 2)
        self.assertEqual(run_cli(SKILL, "claim_check", "no-such-dir").returncode, 2)


class ClaimCheckFalsePositiveTests(unittest.TestCase):
    def test_quote_pairs_not_merged_and_headings_skipped(self):
        self.assertEqual(rules(mod.scan_text('Click "draft reply" then the panel shows a long explanation before "send" is pressed.')), set())
        self.assertEqual(rules(mod.scan_text('## Recommendation on "proceed to building the MVP on synthetic data"')), set())
        self.assertIn("unsupported-research", rules(mod.scan_text('He said "this is exactly what our whole team needs today".')))

    def test_domain_terms_not_flagged(self):
        self.assertEqual(rules(mod.scan_text("Escalate to a qualified human reviewer.")), set())
        self.assertEqual(rules(mod.scan_text("Use the risk-free rate from a cited curve.")), set())
        self.assertIn("assurance-claim", rules(mod.scan_text("The rig is now qualified.")))


if __name__ == "__main__":
    unittest.main()
