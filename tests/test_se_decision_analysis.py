import unittest

from tests.helpers import assert_schema, load_script, rules, run_cli, run_json, skill_path

SKILL = "se-decision-analysis"
mod = load_script(SKILL, "decision_matrix")
EX = skill_path(SKILL, "assets", "examples")
SCHEMA = skill_path(SKILL, "assets", "schemas", "decision-report.schema.json")


def simple(**settings):
    """Hand-computable case: weights 0.6/0.4; A=(1,0) B=(0,1) C=(0.5,0.5) after min-max."""
    return {
        "decision_id": "T-DEC-001", "question": "q", "decision_owner": "owner",
        "criteria": [{"id": "C1", "weight": 0.6, "direction": "max"},
                     {"id": "C2", "weight": 0.4, "direction": "max"}],
        "alternatives": [
            {"id": "A", "scores": {"C1": {"value": 10, "basis": "measured"}, "C2": {"value": 0, "basis": "measured"}}},
            {"id": "B", "scores": {"C1": {"value": 0, "basis": "measured"}, "C2": {"value": 10, "basis": "measured"}}},
            {"id": "C", "scores": {"C1": {"value": 5, "basis": "measured"}, "C2": {"value": 5, "basis": "measured"}}},
        ],
        "settings": settings,
    }


class DecisionTests(unittest.TestCase):
    def test_known_answer_totals(self):
        res = mod.analyse(simple())
        self.assertEqual([(r["alternative"], r["score"]) for r in res["ranking"]],
                         [("A", 0.6), ("C", 0.5), ("B", 0.4)])
        self.assertAlmostEqual(res["recommendation"]["margin"], 0.1)

    def test_switching_weight_known_answer(self):
        # A total = w1, B = 1 - w1, C = 0.5. Below w1 = 0.5 B overtakes; nearest flip at 0.499 -> B.
        res = mod.analyse(simple())
        sw = next(s for s in res["sensitivity"] if s["criterion"] == "C1")["switching_weight"]
        self.assertEqual(sw, {"weight": 0.499, "winner": "B"})

    def test_rank_sensitive_flag(self):
        res = mod.analyse(simple(sensitivity_pct=20))  # 0.6*0.8 = 0.48 < 0.5 -> flips
        self.assertIn("rank-sensitive", rules(res["findings"], "warning"))
        res = mod.analyse(simple(sensitivity_pct=10))  # 0.54 -> no flip
        self.assertNotIn("rank-sensitive", rules(res["findings"]))

    def test_must_screen(self):
        d = simple()
        d["criteria"][1]["must"] = {"min": 1}
        res = mod.analyse(d)
        self.assertIn("A", res["screened"])
        self.assertEqual(res["recommendation"]["alternative"], "C")

    def test_all_screened_is_error(self):
        d = simple()
        d["criteria"][0]["must"] = {"min": 100}
        self.assertIn("no-feasible-alternative", rules(mod.analyse(d)["findings"], "error"))

    def test_weights_normalised_and_direction_min(self):
        d = simple()
        d["criteria"][0]["weight"], d["criteria"][1]["weight"] = 3, 2
        d["criteria"][1]["direction"] = "min"
        res = mod.analyse(d)
        self.assertIn("weights-normalised", rules(res["findings"], "warning"))
        self.assertAlmostEqual(res["weights"]["C1"], 0.6)
        self.assertEqual(res["ranking"][0]["alternative"], "A")  # A best on both now
        self.assertEqual(res["ranking"][0]["score"], 1.0)

    def test_normalisation_none(self):
        res = mod.analyse(simple(normalisation="none", scale_max=10))
        self.assertEqual(res["ranking"][0]["score"], 0.6)

    def test_weak_evidence(self):
        d = simple()
        for a in d["alternatives"]:
            for s in a["scores"].values():
                s["basis"] = "judgement"
        self.assertIn("weak-evidence", rules(mod.analyse(d)["findings"], "warning"))

    def test_pass_fixture_schema(self):
        code, out = run_json(SKILL, "decision_matrix", EX / "decision-pass.json")
        self.assertEqual(code, 0)
        self.assertEqual(out["recommendation"]["alternative"], "HOP")
        self.assertIn("WHEEL", out["screened"])
        assert_schema(self, out, SCHEMA)

    def test_fail_fixture(self):
        code, out = run_json(SKILL, "decision_matrix", EX / "decision-fail.json")
        self.assertEqual(code, 1)
        self.assertTrue({"no-decision-owner", "direction", "missing-score"} <= rules(out["findings"], "error"))

    def test_too_few_alternatives_and_unreadable(self):
        d = simple()
        d["alternatives"] = d["alternatives"][:1]
        self.assertIn("too-few-alternatives", rules(mod.analyse(d)["findings"], "error"))
        self.assertEqual(run_cli(SKILL, "decision_matrix", "nope.json").returncode, 2)


if __name__ == "__main__":
    unittest.main()
