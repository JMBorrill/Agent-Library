import unittest

from tests.helpers import load_script, rules, run_cli, run_json, skill_path

SKILL = "se-implementation-integration"
mod = load_script(SKILL, "integration_check")
EX = skill_path(SKILL, "assets", "examples")


def plan(**kw):
    p = {"final_assembly": "S",
         "components": [{"id": "A", "unit_verified": True}, {"id": "B", "unit_verified": True}, {"id": "C", "unit_verified": True}],
         "steps": [{"step_id": "I1", "integrates": ["A", "B"], "produces": "AB", "prerequisites": [], "checks": ["V1"]},
                   {"step_id": "I2", "integrates": ["AB", "C"], "produces": "S", "prerequisites": ["I1"], "checks": ["V2"]}]}
    p.update(kw)
    return p


class IntegrationTests(unittest.TestCase):
    def test_clean_plan(self):
        res = mod.check(plan())
        self.assertEqual(res["summary"]["errors"], 0)
        self.assertEqual(res["order"], ["I1", "I2"])

    def test_missing_prerequisite_detected(self):
        p = plan()
        p["steps"][1]["prerequisites"] = []
        self.assertIn("assembly-not-ready", rules(mod.check(p)["findings"], "error"))

    def test_transitive_prerequisite_ok(self):
        p = plan()
        p["components"].append({"id": "D", "unit_verified": True})
        p["steps"][1]["produces"] = "ABC"
        p["steps"].append({"step_id": "I3", "integrates": ["AB", "D", "ABC"], "produces": "S",
                           "prerequisites": ["I2"], "checks": ["V3"]})
        p["steps"][1]["integrates"] = ["AB", "C"]
        res = mod.check(p)
        self.assertNotIn("assembly-not-ready", rules(res["findings"]))  # AB reached via I2 -> I1

    def test_icd_interface_coverage(self):
        icd = [{"interface_id": "IF1", "from_component": "A", "to_component": "C"}]
        res = mod.check(plan(), icd)  # A (inside AB) joined with C at I2
        self.assertIn("interface-not-checked", rules(res["findings"], "warning"))
        p = plan()
        p["steps"][1]["interfaces"] = ["IF1"]
        self.assertNotIn("interface-not-checked", rules(mod.check(p, icd)["findings"]))

    def test_fixtures(self):
        code, _ = run_json(SKILL, "integration_check", EX / "integration-pass.json", "--icd", EX / "icd.csv")
        self.assertEqual(code, 0)
        code, out = run_json(SKILL, "integration_check", EX / "integration-fail.json", "--icd", EX / "icd.csv")
        self.assertEqual(code, 1)
        self.assertTrue({"produced-twice", "prerequisite-cycle", "no-checks", "assembly-not-ready", "unknown-item",
                         "no-final-assembly"} <= rules(out["findings"], "error"))

    def test_unreadable(self):
        self.assertEqual(run_cli(SKILL, "integration_check", "missing.json").returncode, 2)


if __name__ == "__main__":
    unittest.main()
