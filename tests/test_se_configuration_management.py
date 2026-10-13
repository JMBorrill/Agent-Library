import unittest

from tests.helpers import load_script, rules, run_cli, run_json, skill_path

SKILL = "se-configuration-management"
mod = load_script(SKILL, "baseline_diff")
EX = skill_path(SKILL, "assets", "examples")


class BaselineDiffTests(unittest.TestCase):
    def test_pass(self):
        code, out = run_json(SKILL, "baseline_diff", EX / "baseline-v1.csv", EX / "baseline-v2-pass.csv",
                             "--changes", EX / "change-log.csv")
        self.assertEqual(code, 0)
        self.assertEqual(out["added"], ["DEMO-SYS-006"])
        self.assertIn("DEMO-SYS-001", out["modified"])
        self.assertIn("cr-not-implemented", rules(out["findings"], "warning"))

    def test_fail(self):
        code, out = run_json(SKILL, "baseline_diff", EX / "baseline-v1.csv", EX / "baseline-v2-fail.csv",
                             "--changes", EX / "change-log.csv")
        self.assertEqual(code, 1)
        self.assertTrue({"deleted-not-retired", "rejected-cr-applied", "uncontrolled-change",
                         "retired-id-reused"} <= rules(out["findings"], "error"))

    def test_without_change_log_every_controlled_change_flagged(self):
        old = [{"id": "A", "status": "approved", "statement": "x"}]
        new = [{"id": "A", "status": "approved", "statement": "y"}]
        res = mod.diff(old, new, "id", None)
        self.assertIn("uncontrolled-change", rules(res["findings"], "error"))

    def test_proposed_items_change_freely(self):
        old = [{"id": "A", "status": "proposed", "statement": "x"}]
        new = [{"id": "A", "status": "proposed", "statement": "y"}]
        self.assertEqual(mod.diff(old, new, "id")["summary"]["errors"], 0)

    def test_approved_cr_requires_approver(self):
        res = mod.diff([], [], "id", [{"cr_id": "CR1", "changed_ids": "A", "status": "approved", "approved_by": ""}])
        self.assertIn("cr-without-approver", rules(res["findings"], "error"))

    def test_key_autodetect_icd_and_unreadable(self):
        p = run_cli(SKILL, "baseline_diff", "missing1.csv", "missing2.csv")
        self.assertEqual(p.returncode, 2)


if __name__ == "__main__":
    unittest.main()
