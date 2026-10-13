"""Tests for finance-options/options_appraisal.py (declining discount factors hand-computed)."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from tests.helpers import assert_schema, load_script, rules, run_cli, run_json, skill_path

SKILL = "finance-options"
oa = load_script(SKILL, "options_appraisal")
EX = skill_path(SKILL, "assets", "examples")
OUT_SCHEMA = skill_path(SKILL, "assets", "schemas", "options-output.schema.json")
IN_SCHEMA = skill_path(SKILL, "assets", "schemas", "options-input.schema.json")
PASS = json.loads((EX / "options-pass.json").read_text())


class DiscountFactors(unittest.TestCase):
    def setUp(self):
        self.df = oa.discount_factors(130)

    def test_first_band(self):
        self.assertEqual(self.df[0], 1.0)
        self.assertAlmostEqual(self.df[10], 1.035 ** -10, places=12)
        self.assertAlmostEqual(self.df[30], 0.3562784106, places=9)

    def test_band_boundaries_are_products(self):
        self.assertAlmostEqual(self.df[31], 1.035 ** -30 / 1.03, places=12)
        self.assertAlmostEqual(self.df[75], 1.035 ** -30 * 1.03 ** -45, places=12)
        self.assertAlmostEqual(self.df[76], 1.035 ** -30 * 1.03 ** -45 / 1.025, places=12)
        self.assertAlmostEqual(self.df[126], self.df[125] / 1.02, places=14)

    def test_annuity_factor(self):
        self.assertAlmostEqual(sum(self.df[1:11]), (1 - 1.035 ** -10) / 0.035, places=10)

    def test_custom_schedule_and_validation(self):
        df = oa.discount_factors(3, [{"from_year": 0, "to_year": 1, "rate": 0.10},
                                     {"from_year": 2, "to_year": None, "rate": 0.0}])
        self.assertAlmostEqual(df[3], 1 / 1.1, places=12)
        for bad in ([{"from_year": 1, "to_year": None, "rate": 0.03}],
                    [{"from_year": 0, "to_year": 5, "rate": 0.03}, {"from_year": 7, "to_year": None, "rate": 0.03}],
                    [{"from_year": 0, "to_year": None, "rate": -1.0}], []):
            with self.assertRaises(oa.InputError):
                oa.validate_schedule(bad)

    def test_schedule_too_short(self):
        with self.assertRaises(oa.InputError):
            oa.discount_factors(10, [{"from_year": 0, "to_year": 5, "rate": 0.03}])

    def test_to_real(self):
        self.assertAlmostEqual(oa.to_real([100, 102, 104.04], 0.02)[2], 100.0, places=10)


class Appraisal(unittest.TestCase):
    def test_pass_known_answers(self):
        out = oa.appraise(copy.deepcopy(PASS))
        by = {o["id"]: o for o in out["options"]}
        ann = (1 - 1.035 ** -10) / 0.035
        self.assertAlmostEqual(by["OPT-1"]["pv_costs"], 240 + 96 * ann, places=8)
        self.assertAlmostEqual(by["OPT-1"]["pv_benefits"], 135 * ann, places=8)
        self.assertAlmostEqual(by["OPT-0"]["pv_costs"], 120 + 120 * ann, places=8)
        inc = by["OPT-1"]["incremental"]
        self.assertAlmostEqual(inc["npsv"], by["OPT-1"]["npsv"] - by["OPT-0"]["npsv"], places=9)
        self.assertAlmostEqual(inc["switching_value_benefits_pct"], -inc["npsv"] / inc["pv_benefits"], places=12)
        self.assertEqual(out["highest_npsv_option"], "OPT-1")
        self.assertEqual(out["summary"]["errors"], 0)
        self.assertIn("schedule-default-unverified", rules(out["findings"], "info"))
        self.assertTrue(all("non_monetised_effects" in o for o in out["options"]))

    def test_nominal_conversion_applied(self):
        out = oa.appraise(copy.deepcopy(PASS))
        opt2 = next(o for o in out["options"] if o["id"] == "OPT-2")
        dfs = oa.discount_factors(10)
        expected_pvb = sum(160 * 0.9 / 1.02 ** t * dfs[t] for t in range(1, 11))
        self.assertAlmostEqual(opt2["pv_benefits"], expected_pvb, places=8)

    def test_counterfactual_rules(self):
        doc = copy.deepcopy(PASS)
        doc["options"][0]["is_counterfactual"] = False
        self.assertIn("no-counterfactual", rules(oa.appraise(doc)["findings"], "error"))
        doc["options"][0]["is_counterfactual"] = True
        doc["options"][1]["is_counterfactual"] = True
        self.assertIn("multiple-counterfactuals", rules(oa.appraise(doc)["findings"], "error"))

    def test_series_length_and_negative(self):
        doc = copy.deepcopy(PASS)
        doc["options"][1]["costs"] = [1, 2]
        doc["options"][2]["benefits"] = [-1] + [160] * 10
        r = rules(oa.appraise(doc)["findings"], "error")
        self.assertIn("series-length", r)
        self.assertIn("negative-series-value", r)

    def test_optimism_bias_rules(self):
        doc = copy.deepcopy(PASS)
        del doc["options"][1]["optimism_bias"]
        doc["options"][2]["optimism_bias"] = {"costs_pct": 0.3}
        f = oa.appraise(doc)["findings"]
        self.assertIn("optimism-bias-not-considered", rules(f, "warning"))
        self.assertIn("optimism-bias-unsourced", rules(f, "warning"))
        doc["options"][2]["optimism_bias"] = {"costs_pct": 0.3, "benefits_pct": 1.5, "source": "x"}
        self.assertIn("optimism-bias-range", rules(oa.appraise(doc)["findings"], "error"))

    def test_non_monetised_empty_warns(self):
        doc = copy.deepcopy(PASS)
        doc["options"][1]["non_monetised_effects"] = []
        self.assertIn("non-monetised-empty", rules(oa.appraise(doc)["findings"], "warning"))

    def test_non_numeric_raises(self):
        doc = copy.deepcopy(PASS)
        doc["options"][1]["costs"][3] = "lots"
        with self.assertRaises(oa.InputError):
            oa.appraise(doc)


class Cli(unittest.TestCase):
    def test_pass_example(self):
        code, out = run_json(SKILL, "options_appraisal", EX / "options-pass.json")
        self.assertEqual(code, 0)
        self.assertTrue(out["passed"])
        assert_schema(self, out, OUT_SCHEMA)
        assert_schema(self, PASS, IN_SCHEMA)

    def test_fail_example(self):
        code, out = run_json(SKILL, "options_appraisal", EX / "options-fail.json")
        self.assertEqual(code, 1)
        expected = {"no-counterfactual", "csf-missing", "non-monetised-missing", "appraisal-period-mismatch",
                    "price-base-mismatch", "price-basis-unconvertible"}
        self.assertEqual(rules(out["findings"], "error"), expected)
        assert_schema(self, out, OUT_SCHEMA)

    def test_schedule_file_option(self):
        sched = skill_path(SKILL, "assets", "templates", "discount-schedule-default.json")
        code, out = run_json(SKILL, "options_appraisal", EX / "options-pass.json", "--schedule", sched)
        self.assertEqual(code, 0)
        self.assertEqual(out["discount_schedule"]["label"], "user-supplied schedule")
        self.assertAlmostEqual(out["discount_factors"][10], 1.035 ** -10, places=12)

    def test_malformed_exit_2(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "bad.json"
            p.write_text("{not json")
            self.assertEqual(run_cli(SKILL, "options_appraisal", p).returncode, 2)
            p.write_text(json.dumps({"appraisal": {}, "options": []}))
            self.assertEqual(run_cli(SKILL, "options_appraisal", p).returncode, 2)

    def test_no_approval_language_in_output(self):
        proc = run_cli(SKILL, "options_appraisal", EX / "options-pass.json")
        self.assertNotIn("approved", proc.stdout.lower())
        self.assertNotIn("compliant", proc.stdout.lower())


if __name__ == "__main__":
    unittest.main()
