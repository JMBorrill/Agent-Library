import json
import tempfile
import unittest
from pathlib import Path

from tests.helpers import assert_schema, load_script, rules, run_cli, run_json, skill_path

SKILL = "product-experiment-design"
mod = load_script(SKILL, "experiment_calc")
EX = skill_path(SKILL, "assets", "examples")
SCHEMAS = skill_path(SKILL, "assets", "schemas")


class SampleSizeKnownAnswers(unittest.TestCase):
    """Hand-computed in references/statistics.md (z values to 6 d.p.)."""

    def test_pooled_10_to_12(self):
        exact = mod.n_per_arm_exact(0.10, 0.12)
        self.assertAlmostEqual(exact, 3840.85, delta=0.05)  # tolerance 0.05 units
        self.assertEqual(mod.sample_size(0.10, 0.12), 3841)

    def test_unpooled_10_to_12(self):
        self.assertAlmostEqual(mod.n_per_arm_exact(0.10, 0.12, formula="unpooled"), 3838.10, delta=0.05)
        self.assertEqual(mod.sample_size(0.10, 0.12, formula="unpooled"), 3839)

    def test_symmetric_in_direction(self):
        self.assertEqual(mod.sample_size(0.12, 0.10), mod.sample_size(0.10, 0.12))

    def test_mde_inverts_sample_size(self):
        self.assertAlmostEqual(mod.mde(0.10, 3841), 0.02, delta=1e-4)
        self.assertAlmostEqual(mod.mde(0.10, 3839, formula="unpooled"), 0.02, delta=1e-4)
        self.assertLess(mod.mde(0.30, 1400, direction="decrease"), 0.06)

    def test_mde_unreachable_returns_none(self):
        self.assertIsNone(mod.mde(0.5, 5))

    def test_cli_sample_size_schema(self):
        code, out = run_json(SKILL, "experiment_calc", "sample-size", "--baseline", "0.10", "--mde", "0.02")
        self.assertEqual(code, 0)
        self.assertEqual(out["result"]["n_per_arm"], 3841)
        self.assertEqual(out["formula"], "pooled")
        assert_schema(self, out, SCHEMAS / "calc.output.schema.json")


class ClusterRandomisation(unittest.TestCase):
    """Design effect DE = 1 + (m - 1) * rho applied to n per arm."""

    def test_known_answer(self):
        # n = 1000, m = 20, rho = 0.05 -> DE = 1.95 -> 1950 per arm, ceil(1950/20) = 98 clusters
        r = mod.cluster_adjust(1000, 20, 0.05)
        self.assertAlmostEqual(r["design_effect"], 1.95, places=12)
        self.assertEqual(r["n_per_arm"], 1950)
        self.assertEqual(r["clusters_per_arm"], 98)
        self.assertEqual(r["total"], 3900)
        self.assertEqual(r["individuals_in_whole_clusters_per_arm"], 1960)
        # rho = 0 or m = 1 -> no inflation
        self.assertEqual(mod.cluster_adjust(1000, 20, 0)["n_per_arm"], 1000)
        self.assertEqual(mod.cluster_adjust(1000, 1, 0.3)["clusters_per_arm"], 1000)

    def test_cli_cluster_sample_size(self):
        code, out = run_json(SKILL, "experiment_calc", "sample-size", "--baseline", "0.10", "--mde", "0.02",
                             "--cluster-size", "20", "--icc", "0.05")
        self.assertEqual(code, 0)
        self.assertEqual(out["result"]["n_per_arm_individual"], 3841)
        self.assertEqual(out["result"]["n_per_arm"], 7490)          # ceil(3841 * 1.95 = 7489.95)
        self.assertEqual(out["result"]["clusters_per_arm"], 375)    # ceil(7490 / 20 = 374.5)
        assert_schema(self, out, SCHEMAS / "calc.output.schema.json")

    def test_invalid_cluster_inputs(self):
        for m, rho in ((0.5, 0.05), (20, -0.1), (20, 1.5), (float("nan"), 0.1)):
            with self.assertRaises(mod.InputError):
                mod.cluster_adjust(1000, m, rho)
        base = ["sample-size", "--baseline", "0.10", "--mde", "0.02"]
        for extra in (["--cluster-size", "20"], ["--icc", "0.05"], ["--cluster-size", "0", "--icc", "0.05"],
                      ["--cluster-size", "20", "--icc", "1.2"]):
            self.assertEqual(run_cli(SKILL, "experiment_calc", *base, *extra).returncode, 2, extra)


class EdgeCases(unittest.TestCase):
    def test_invalid_probabilities_and_effects(self):
        for p1, p2 in ((0, 0.1), (1, 0.9), (0.1, 1.0), (-0.1, 0.1), (0.1, 0.1)):
            with self.assertRaises(mod.InputError):
                mod.n_per_arm_exact(p1, p2)
        with self.assertRaises(mod.InputError):
            mod.n_per_arm_exact(0.1, 0.12, alpha=0)
        with self.assertRaises(mod.InputError):
            mod.n_per_arm_exact(0.1, 0.12, power=1.0)
        with self.assertRaises(mod.InputError):
            mod.mde(0.1, 0)

    def test_cli_edge_cases_exit_2(self):
        for args in (["sample-size", "--baseline", "0", "--target", "0.1"],
                     ["sample-size", "--baseline", "1", "--target", "0.9"],
                     ["sample-size", "--baseline", "0.1", "--mde", "0"],
                     ["sample-size", "--baseline", "0.1", "--mde", "-0.02"],
                     ["mde", "--baseline", "0.1", "--n", "-5"],
                     ["evaluate", "--control", "11", "10", "--treatment", "5", "10"],
                     ["evaluate", "--control", "1", "0", "--treatment", "5", "10"],
                     ["plan", "missing.json"]):
            self.assertEqual(run_cli(SKILL, "experiment_calc", *args).returncode, 2, args)

    def test_no_variation_not_computable(self):
        res = mod.two_prop_test(0, 100, 0, 100)
        self.assertIsNone(res["p_value"])
        self.assertFalse(res["significant"])
        res = mod.two_prop_test(100, 100, 100, 100)
        self.assertIsNone(res["p_value"])


class EvaluateKnownAnswers(unittest.TestCase):
    def test_two_prop_test(self):
        res = mod.two_prop_test(100, 1000, 130, 1000)
        self.assertAlmostEqual(res["z"], 2.1027, delta=5e-4)
        self.assertAlmostEqual(res["p_value"], 0.0355, delta=5e-4)
        self.assertAlmostEqual(res["ci"][0], 0.002068, delta=1e-5)
        self.assertAlmostEqual(res["ci"][1], 0.057932, delta=1e-5)
        self.assertTrue(res["significant"])

    def test_evaluate_pass_and_guardrail_breach(self):
        code, out = run_json(SKILL, "experiment_calc", "evaluate", "--plan", EX / "plan-pass.json",
                             "--results", EX / "results-pass.json")
        self.assertEqual(code, 0)
        self.assertEqual(out["summary"]["recommendation"], "RECOMMEND_SHIP")
        self.assertTrue(out["summary"]["requires_human_decision"])
        assert_schema(self, out, SCHEMAS / "report.output.schema.json")
        code, out = run_json(SKILL, "experiment_calc", "evaluate", "--plan", EX / "plan-pass.json",
                             "--results", EX / "results-fail.json")
        self.assertEqual(code, 1)
        self.assertIn("guardrail-breached", rules(out["findings"], "error"))
        self.assertEqual(out["summary"]["recommendation"], "RECOMMEND_DO_NOT_SHIP")

    def test_inconclusive_and_harmful(self):
        plan = json.loads((EX / "plan-pass.json").read_text())
        flat = {"primary": {"control": {"conversions": 420, "n": 1400}, "treatment": {"conversions": 430, "n": 1400}}}
        self.assertEqual(mod.evaluate(plan, flat)["summary"]["recommendation"], "INCONCLUSIVE")
        worse = {"primary": {"control": {"conversions": 420, "n": 1400}, "treatment": {"conversions": 340, "n": 1400}}}
        self.assertEqual(mod.evaluate(plan, worse)["summary"]["recommendation"], "RECOMMEND_DO_NOT_SHIP")


class PlanChecks(unittest.TestCase):
    def test_pass_plan(self):
        code, out = run_json(SKILL, "experiment_calc", "plan", EX / "plan-pass.json")
        self.assertEqual(code, 0)
        self.assertEqual(out["summary"]["required_per_arm"], 1377)
        assert_schema(self, out, SCHEMAS / "report.output.schema.json")
        assert_schema(self, json.loads((EX / "plan-pass.json").read_text()), SCHEMAS / "experiment-plan.schema.json")

    def test_fail_plan_seeded_defects(self):
        code, out = run_json(SKILL, "experiment_calc", "plan", EX / "plan-fail.json")
        self.assertEqual(code, 1)
        errs = rules(out["findings"], "error")
        for expected in ["prediction-not-falsifiable", "multiple-primary-metrics", "baseline-range",
                         "mde-range", "power-range", "optional-stopping", "ethics-no-consent-note",
                         "decision-rule-not-preregistered", "decision-rule-incomplete",
                         "decision-rule-after-launch"]:
            self.assertIn(expected, errs)
        warns = rules(out["findings"], "warning")
        self.assertIn("duration-short", warns)
        self.assertIn("no-guardrails", warns)

    def test_underpowered_and_traffic(self):
        plan = json.loads((EX / "plan-pass.json").read_text())
        plan["sample_size_per_arm"] = 1000
        plan["expected_eligible_per_day"] = 50
        errs = rules(mod.check_plan(plan)["findings"], "error")
        self.assertIn("underpowered", errs)
        self.assertIn("insufficient-traffic", errs)

    def test_sequential_design_allows_interim_looks(self):
        plan = json.loads((EX / "plan-pass.json").read_text())
        plan["stopping_rule"] = "Group-sequential design with O'Brien-Fleming boundaries; stop when significant at an interim look."
        self.assertNotIn("optional-stopping", rules(mod.check_plan(plan)["findings"]))

    def test_missing_fields_and_non_object(self):
        res = mod.check_plan({"id": "X-EXP-001"})
        self.assertIn("plan-missing-field", rules(res["findings"], "error"))
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "list.json"
            p.write_text("[1, 2]", encoding="utf-8")
            self.assertEqual(run_cli(SKILL, "experiment_calc", "plan", p).returncode, 2)
            p.write_text("{not json", encoding="utf-8")
            self.assertEqual(run_cli(SKILL, "experiment_calc", "plan", p).returncode, 2)


if __name__ == "__main__":
    unittest.main()
