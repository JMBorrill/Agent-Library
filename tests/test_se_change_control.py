import unittest

from tests.helpers import load_script, run_cli, run_json, skill_path

SKILL = "se-change-control"
mod = load_script(SKILL, "change_impact")
EX = skill_path(SKILL, "assets", "examples")
ARGS = ["--requirements", EX / "requirements.csv", "--vmatrix", EX / "verification-matrix.csv",
        "--icd", EX / "icd.csv", "--risks", EX / "risks.csv"]


class ChangeImpactTests(unittest.TestCase):
    def test_example_cr(self):
        code, out = run_json(SKILL, "change_impact", "--cr", EX / "change-request.json", *ARGS)
        self.assertEqual(code, 0)
        imp = {k: {e["id"] for e in v} for k, v in out["impacted"].items()}
        self.assertEqual(imp["requirement"], {"DEMO-SYS-001", "DEMO-SUB-001"})
        self.assertEqual(imp["verification"], {"DEMO-VER-001", "DEMO-VER-005"})
        self.assertIn("DEMO-IF-003", imp["interface"])
        self.assertIn("DEMO-RSK-002", imp["risk"])
        acts = {(x["action"], x["id"]) for x in out["actions"]}
        self.assertIn(("re-verify", "DEMO-VER-005"), acts)
        self.assertIn(("interface-renegotiation", "DEMO-IF-003"), acts)
        self.assertIn(("baseline-change", "DEMO-SYS-001"), acts)
        self.assertEqual(out["parents_to_check"], ["DEMO-STK-001"])

    def test_unrelated_branch_not_impacted(self):
        code, out = run_json(SKILL, "change_impact", "--changed", "DEMO-SYS-003", *ARGS)
        self.assertEqual(code, 0)
        ids = {e["id"] for v in out["impacted"].values() for e in v}
        self.assertNotIn("DEMO-SYS-001", ids)
        self.assertIn("DEMO-VER-003", ids)
        # not_tested result -> no re-verify action
        self.assertNotIn(("re-verify", "DEMO-VER-003"), {(x["action"], x["id"]) for x in out["actions"]})

    def test_unknown_id_exit_1(self):
        code, out = run_json(SKILL, "change_impact", "--changed", "DEMO-SYS-404", *ARGS)
        self.assertEqual(code, 1)
        self.assertEqual(out["unknown"], ["DEMO-SYS-404"])

    def test_deep_chain_and_cycle_safety(self):
        reqs = [{"id": "A", "parent": ""}, {"id": "B", "parent": "A"}, {"id": "C", "parent": "B"},
                {"id": "D", "parent": "C;A"}]
        g = mod.build(reqs, [], [], [], [{"from_id": "D", "to_id": "X"}])
        res = mod.impact(g, ["A"])
        self.assertEqual({e["id"] for e in res["impacted"]["requirement"]}, {"A", "B", "C", "D"})
        reqs_cycle = [{"id": "A", "parent": "B"}, {"id": "B", "parent": "A"}]
        res = mod.impact(mod.build(reqs_cycle, [], [], [], []), ["A"])
        self.assertEqual(len(res["impacted"]["requirement"]), 2)

    def test_unreadable(self):
        self.assertEqual(run_cli(SKILL, "change_impact", "--cr", "missing.json").returncode, 2)


if __name__ == "__main__":
    unittest.main()
