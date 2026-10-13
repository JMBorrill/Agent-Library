import unittest
from datetime import date

from tests.helpers import load_script, rules, run_cli, run_json, skill_path

trn = load_script("se-transition", "transition_check")
dat = load_script("se-technical-data-management", "data_register_check")
TEX = skill_path("se-transition", "assets", "examples")
DEX = skill_path("se-technical-data-management", "assets", "examples")


class TransitionTests(unittest.TestCase):
    def test_fixtures(self):
        code, out = run_json("se-transition", "transition_check", TEX / "transition-pass.json")
        self.assertEqual((code, out["status"]), (0, "READY_FOR_ACCEPTANCE"))
        self.assertIn("awaiting-receiver", rules(out["findings"], "info"))
        code, out = run_json("se-transition", "transition_check", TEX / "transition-fail.json")
        self.assertEqual((code, out["status"]), (1, "NOT_READY"))
        self.assertTrue({"no-receiver", "missing-version", "open-verification-unwaived", "limitations-undocumented"}
                        <= rules(out["findings"], "error"))

    def test_waiver_needs_approver(self):
        base = {"receiving_organisation": "r", "limitations_documented": True,
                "deliverables": [{"id": "D", "version": "1", "configuration_id": "c", "acceptance_ref": "a",
                                  "documentation": ["m"], "known_issues": []}],
                "open_verification": [{"activity_id": "V", "result": "blocked", "waiver_ref": "W"}]}
        self.assertEqual(trn.check(base)["status"], "NOT_READY")
        base["open_verification"][0]["waiver_approved_by"] = "owner"
        self.assertEqual(trn.check(base)["status"], "READY_FOR_ACCEPTANCE")


class DataRegisterTests(unittest.TestCase):
    def test_fixtures(self):
        code, _ = run_json("se-technical-data-management", "data_register_check", DEX / "data-register-pass.csv",
                           "--as-of", "2026-10-13")
        self.assertEqual(code, 0)
        code, out = run_json("se-technical-data-management", "data_register_check", DEX / "data-register-fail.csv")
        self.assertEqual(code, 1)
        self.assertTrue({"duplicate-id", "missing-owner", "classification", "credential-in-location",
                         "no-access-control", "personal-data-no-basis", "multiple-sources-of-truth"}
                        <= rules(out["findings"], "error"))

    def test_credential_value_not_echoed(self):
        p = run_cli("se-technical-data-management", "data_register_check", DEX / "data-register-fail.csv")
        self.assertNotIn("hunter2", p.stdout)

    def test_stale_and_token_query(self):
        rows = [{"data_id": "D1", "owner": "o", "classification": "internal", "location": "https://x/y?token=abc",
                 "retention": "1y", "last_updated": "2020-01-01"}]
        res = dat.check(rows, date(2026, 1, 1))
        self.assertIn("credential-in-location", rules(res["findings"], "error"))
        self.assertIn("stale", rules(res["findings"], "warning"))


if __name__ == "__main__":
    unittest.main()
