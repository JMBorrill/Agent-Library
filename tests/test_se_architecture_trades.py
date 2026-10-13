import json
import tempfile
import unittest
from pathlib import Path

from tests.helpers import load_script, rules, run_cli, run_json, skill_path

SKILL = "se-architecture-trades"
mod = load_script(SKILL, "trade_space")
EX = skill_path(SKILL, "assets", "examples")


class TradeSpaceTests(unittest.TestCase):
    def test_example_counts(self):
        code, out = run_json(SKILL, "trade_space", EX / "trade-space.json")
        self.assertEqual(code, 0)
        self.assertEqual(out["summary"]["combinations"], 18)
        # 3x2x3 = 18. Excluded: WHEELS+RW (2), WHEELS+COLDGAS (2), SUPERCAP+COLDGAS not already
        # counted (SPRING, FLYWHEEL: 2), FLYWHEEL without LIION not already counted (NONE, RW: 2) -> 18 - 8 = 10
        self.assertEqual(out["summary"]["feasible"], 10)
        self.assertEqual(out["summary"]["with_immature_options"], 2)
        concepts = {c["concept"] for c in out["concepts"]}
        self.assertNotIn("FLYWHEEL+SUPERCAP+NONE", concepts)
        self.assertNotIn("WHEELS+LIION+RW", concepts)

    def test_fail_fixture(self):
        code, out = run_json(SKILL, "trade_space", EX / "trade-space-fail.json")
        self.assertEqual(code, 1)
        self.assertTrue({"duplicate-function", "duplicate-option", "trl-range", "unknown-option", "bad-requires"}
                        <= rules(out["findings"], "error"))

    def test_no_feasible(self):
        d = {"functions": [{"id": "F1", "options": [{"id": "A"}]}, {"id": "F2", "options": [{"id": "B"}]}],
             "incompatible": [["A", "B"]]}
        self.assertIn("no-feasible-concept", rules(mod.analyse(d)["findings"], "error"))

    def test_export_decision_skeleton(self):
        with tempfile.TemporaryDirectory() as t:
            crit = Path(t) / "c.json"
            crit.write_text(json.dumps([{"id": "C1", "name": "mass", "weight": 1.0, "direction": "min"}]))
            out = Path(t) / "d.json"
            code, _ = run_json(SKILL, "trade_space", EX / "trade-space.json", "--export-decision", out, "--criteria", crit)
            self.assertEqual(code, 0)
            d = json.loads(out.read_text())
            self.assertEqual(len(d["alternatives"]), 10)
            self.assertIn("C1", d["alternatives"][0]["scores"])
            self.assertEqual(d["decision_owner"], "")  # must be filled by a human

    def test_unreadable(self):
        self.assertEqual(run_cli(SKILL, "trade_space", "missing.json").returncode, 2)


if __name__ == "__main__":
    unittest.main()
