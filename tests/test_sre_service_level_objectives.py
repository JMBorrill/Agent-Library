import copy
import json
import unittest

from tests.helpers import assert_schema, load_script, rules, run_cli, run_json, skill_path

SKILL = "sre-service-level-objectives"
mod = load_script(SKILL, "slo_calc")
EX = skill_path(SKILL, "assets", "examples")
SCHEMAS = skill_path(SKILL, "assets", "schemas")
TOL = 1e-6


class SloCalcTests(unittest.TestCase):
    def test_known_answer_999_30d(self):
        self.assertAlmostEqual(mod.budget(0.999, 30)["allowed_bad_minutes"], 43.2, delta=TOL)
        self.assertAlmostEqual(mod.budget(99.9, 30)["allowed_bad_minutes"], 43.2, delta=TOL)  # percent form

    def test_more_known_answers(self):
        self.assertAlmostEqual(mod.budget(0.999, 28)["allowed_bad_minutes"], 40.32, delta=TOL)
        self.assertAlmostEqual(mod.budget(0.9995, 30)["allowed_bad_minutes"], 21.6, delta=TOL)
        self.assertAlmostEqual(mod.budget(0.99, 30)["allowed_bad_minutes"], 432.0, delta=TOL)

    def test_event_budget_and_burn(self):
        b = mod.budget(0.999, 30, total_events=2_000_000, bad_events=500, elapsed_days=7.5)
        self.assertAlmostEqual(b["allowed_bad_events"], 2000, delta=TOL)
        self.assertAlmostEqual(b["budget_consumed"], 0.25, delta=TOL)
        self.assertAlmostEqual(b["remaining_bad_events"], 1500, delta=TOL)
        self.assertAlmostEqual(b["average_burn_rate"], 1.0, delta=TOL)
        m = mod.budget(0.999, 30, bad_minutes=43.2)
        self.assertTrue(m["budget_exhausted"])

    def test_sli_and_burn_rate(self):
        self.assertAlmostEqual(mod.sli(999, 1000), 0.999, delta=TOL)
        self.assertAlmostEqual(mod.burn_rate(0.0144, 0.999), 14.4, delta=TOL)

    def test_invalid_inputs(self):
        for call in (lambda: mod.sli(1, 0), lambda: mod.sli(5, 4), lambda: mod.sli(-1, 4),
                     lambda: mod.budget(1.0, 30), lambda: mod.budget(100, 30), lambda: mod.budget(0.999, 0),
                     lambda: mod.budget(0.999, 30, total_events=10, bad_events=11),
                     lambda: mod.budget(0.999, 30, bad_events=1), lambda: mod.minutes("1y")):
            with self.assertRaises(mod.InputError):
                call()
        self.assertEqual(run_cli(SKILL, "slo_calc", "sli", "--good", "1", "--total", "0").returncode, 2)

    def test_budget_spent_at_detection(self):
        policy = json.loads((EX / "alert-policy-example.json").read_text())
        obs = json.loads((EX / "observations-example.json").read_text())
        res = mod.evaluate_alerts(policy, obs)
        spent = {a["name"]: a["budget_spent_at_detection"] for a in res["alerts"]}
        self.assertAlmostEqual(spent["fast-burn-page"], 0.02, delta=TOL)
        self.assertAlmostEqual(spent["slow-burn-page"], 0.05, delta=TOL)
        self.assertAlmostEqual(spent["budget-ticket"], 0.10, delta=TOL)

    def test_alert_example_cli(self):
        code, out = run_json(SKILL, "slo_calc", "alerts", "--policy", EX / "alert-policy-example.json",
                             "--observations", EX / "observations-example.json")
        self.assertEqual(code, 1)
        self.assertEqual(out["firing"], ["fast-burn-page"])
        fast = out["alerts"][0]
        self.assertAlmostEqual(fast["burn_long"], 16.6667, delta=1e-4)  # 2000/120000 / 0.001
        self.assertAlmostEqual(fast["burn_short"], 21.0, delta=1e-4)    # 210/10000 / 0.001
        assert_schema(self, out, SCHEMAS / "alerts.output.schema.json")

    def test_both_windows_required(self):
        policy = {"target": 0.999, "alerts": [{"name": "a", "long_window": "1h", "short_window": "5m", "burn_rate": 10}]}
        quiet = mod.evaluate_alerts(policy, {"1h": {"error_rate": 0.02}, "5m": {"error_rate": 0.001}})
        self.assertEqual(quiet["firing"], [])  # long window hot, short window recovered
        with self.assertRaises(mod.InputError):
            mod.evaluate_alerts(policy, {"1h": {"error_rate": 0.02}})

    def test_spec_pass_and_fail(self):
        code, out = run_json(SKILL, "slo_calc", "validate", EX / "slo-spec-pass.json")
        self.assertEqual(code, 0)
        self.assertAlmostEqual(out["summary"]["allowed_bad_minutes"], 43.2, delta=TOL)
        assert_schema(self, out, SCHEMAS / "findings-report.schema.json")
        assert_schema(self, json.loads((EX / "slo-spec-pass.json").read_text()), SCHEMAS / "slo-spec.schema.json")
        code, out = run_json(SKILL, "slo_calc", "validate", EX / "slo-spec-fail.json")
        self.assertEqual(code, 1)
        self.assertTrue({"missing-field", "sli-incomplete", "target-range", "window-format", "alert-windows"}
                        <= rules(out["findings"], "error"))
        self.assertTrue({"no-paging-alert", "no-error-budget-policy"} <= rules(out["findings"], "warning"))

    def test_alert_after_exhaustion_warning(self):
        spec = json.loads((EX / "slo-spec-pass.json").read_text())
        s2 = copy.deepcopy(spec)
        s2["alerting_policy"]["alerts"].append({"name": "late", "severity": "ticket", "long_window": "30d",
                                                "short_window": "1d", "burn_rate": 2})
        self.assertIn("alert-after-exhaustion", rules(mod.validate_spec(s2)["findings"], "warning"))

    def test_bad_json_exit_2(self):
        self.assertEqual(run_cli(SKILL, "slo_calc", "validate", "nope.json").returncode, 2)


if __name__ == "__main__":
    unittest.main()
