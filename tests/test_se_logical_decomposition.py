import unittest

from tests.helpers import load_script, rules, run_cli, run_json, skill_path

SKILL = "se-logical-decomposition"
mod = load_script(SKILL, "function_check")
EX = skill_path(SKILL, "assets", "examples")
REQ = skill_path("se-verification-validation", "assets", "examples", "requirements.csv")


class FunctionTests(unittest.TestCase):
    def test_pass(self):
        code, out = run_json(SKILL, "function_check", EX / "functions-pass.csv", "--components", EX / "components.csv",
                             "--requirements", REQ)
        self.assertEqual(code, 0)
        self.assertIn("requirement-not-allocated", rules(out["findings"], "warning"))  # DEMO-SYS-003 mass

    def test_fail(self):
        code, out = run_json(SKILL, "function_check", EX / "functions-fail.csv", "--components", EX / "components.csv")
        self.assertEqual(code, 1)
        self.assertTrue({"duplicate-id", "unknown-parent", "unallocated-leaf", "unproduced-input", "unknown-element"}
                        <= rules(out["findings"], "error"))
        self.assertIn("not-verb-object", rules(out["findings"], "warning"))

    def test_naming_heuristic(self):
        f = [{"function_id": "F1", "parent_function": "", "name": "Sequence trial", "inputs": "", "outputs": "",
              "allocated_to": "A", "requirement_ids": "R"}]
        self.assertNotIn("not-verb-object", rules(mod.check(f)["findings"]))
        f[0]["name"] = "Navigation subsystem"
        self.assertIn("not-verb-object", rules(mod.check(f)["findings"]))

    def test_cycle(self):
        f = [{"function_id": "A", "parent_function": "B", "name": "Do a", "allocated_to": "x", "requirement_ids": "r"},
             {"function_id": "B", "parent_function": "A", "name": "Do b", "allocated_to": "x", "requirement_ids": "r"}]
        self.assertIn("tree-cycle", rules(mod.check(f)["findings"], "error"))

    def test_unreadable(self):
        self.assertEqual(run_cli(SKILL, "function_check", "missing.csv").returncode, 2)


if __name__ == "__main__":
    unittest.main()
