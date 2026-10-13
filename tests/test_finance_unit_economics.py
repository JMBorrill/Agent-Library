"""Tests for finance-unit-economics/unit_economics.py (known answers hand-computed)."""
import json
import tempfile
import unittest
from pathlib import Path

from tests.helpers import assert_schema, load_script, rules, run_cli, run_json, skill_path

SKILL = "finance-unit-economics"
ue = load_script(SKILL, "unit_economics")
EX = skill_path(SKILL, "assets", "examples")
SCHEMA = skill_path(SKILL, "assets", "schemas", "unit-economics-output.schema.json")


def model(**over):
    inputs = {
        "sales_marketing_spend": {"value": 30000, "tag": "measured", "source": "s"},
        "new_customers": {"value": 30, "tag": "measured", "source": "s"},
        "arpa_monthly": {"value": 100, "tag": "measured", "source": "s"},
        "gross_margin_pct": {"value": 0.8, "tag": "measured", "source": "s"},
        "variable_cost_per_account_monthly": {"value": 10, "tag": "estimate", "owner": "fin"},
        "monthly_churn": {"value": 0.02, "tag": "measured", "source": "s"},
    }
    for k, v in over.items():
        if v is None:
            inputs.pop(k, None)
        else:
            inputs[k] = {"value": v, "tag": "estimate", "owner": "fin"}
    return {"name": "t", "inputs": inputs}


class KnownAnswers(unittest.TestCase):
    def test_base_metrics(self):
        m = ue.run_model(model())["base"]
        self.assertAlmostEqual(m["blended_cac"], 1000.0)
        self.assertAlmostEqual(m["contribution_per_account_monthly"], 70.0)
        self.assertAlmostEqual(m["expected_lifetime_months"], 50.0)
        self.assertAlmostEqual(m["ltv"], 3500.0)
        self.assertAlmostEqual(m["ltv_to_cac"], 3.5)
        self.assertAlmostEqual(m["cac_payback_months"], 1000 / 70, places=10)
        self.assertAlmostEqual(m["cac_payback_gross_margin_months"], 12.5)

    def test_paid_cac(self):
        m = ue.run_model(model(paid_spend=18000, paid_new_customers=12))["base"]
        self.assertAlmostEqual(m["paid_cac"], 1500.0)

    def test_discounted_ltv_hand_case(self):
        # churn 50%, rate 0, horizon 2 -> c * (1 + 0.5)
        self.assertAlmostEqual(ue.discounted_ltv(70, 0.5, 0.0, 2), 105.0, places=10)
        # long horizon converges to closed form c / (d + churn) with (1+d) = 1.12^(1/12)
        d = 1.12 ** (1 / 12) - 1
        self.assertAlmostEqual(ue.discounted_ltv(70, 0.02, 0.12, 5000), 70 / (d + 0.02), places=6)

    def test_scenarios_and_sensitivity(self):
        mdl = model()
        mdl["scenarios"] = {"downside": {"monthly_churn": 0.04}}
        mdl["sensitivity"] = {"monthly_churn": [0.01, 0.05]}
        out = ue.run_model(mdl)
        self.assertAlmostEqual(out["scenarios"]["downside"]["ltv"], 70 * 25)
        self.assertAlmostEqual(out["sensitivity"]["monthly_churn"][0]["ltv"], 70 * 60)  # capped at 60
        self.assertAlmostEqual(out["sensitivity"]["monthly_churn"][1]["ltv_to_cac"], 1.4)


class EdgeCases(unittest.TestCase):
    def test_churn_zero_capped_and_flagged(self):
        out = ue.run_model(model(monthly_churn=0, horizon_months=36))
        self.assertTrue(out["base"]["lifetime_capped_at_horizon"])
        self.assertAlmostEqual(out["base"]["ltv"], 70 * 36)
        self.assertIn("churn-zero-capped", rules(out["findings"], "warning"))

    def test_negative_margin_never_pays_back(self):
        out = ue.run_model(model(gross_margin_pct=-0.1))
        self.assertTrue(out["base"]["cac_payback_never"])
        self.assertIsNone(out["base"]["cac_payback_months"])
        self.assertLess(out["base"]["ltv"], 0)
        self.assertIn("negative-gross-margin", rules(out["findings"], "warning"))
        self.assertIn("cac-never-pays-back", rules(out["findings"], "warning"))

    def test_zero_customers_guarded(self):
        out = ue.run_model(model(new_customers=0))
        self.assertIsNone(out["base"]["blended_cac"])
        self.assertIsNone(out["base"]["ltv_to_cac"])
        self.assertIn("cac-undefined", rules(out["findings"], "error"))

    def test_inconsistent_inputs(self):
        out = ue.run_model(model(paid_new_customers=40, paid_spend=40000))
        self.assertTrue({"inconsistent-customers", "inconsistent-spend"} <= rules(out["findings"], "error"))

    def test_out_of_range_blocks_metrics(self):
        for kw, rule in ((dict(monthly_churn=2), "churn-out-of-range"),
                         (dict(gross_margin_pct=80), "margin-out-of-range"),
                         (dict(arpa_monthly=-5), "negative-input"),
                         (dict(arpa_monthly=None), "missing-input")):
            out = ue.run_model(model(**kw))
            self.assertIn(rule, rules(out["findings"], "error"))
            self.assertNotIn("base", out)

    def test_ledger_tag_rules(self):
        mdl = model()
        mdl["inputs"]["arpa_monthly"] = {"value": 100, "tag": "benchmark"}
        mdl["inputs"]["monthly_churn"] = 0.02
        out = ue.run_model(mdl)
        self.assertIn("benchmark-without-source", rules(out["findings"], "error"))
        self.assertIn("assumption-untagged", rules(out["findings"], "warning"))

    def test_non_numeric_raises(self):
        with self.assertRaises(ue.InputError):
            ue.run_model(model(arpa_monthly="lots"))

    def test_cohort_table(self):
        rows = [{"cohort": "A", "month_index": "0", "active_customers": "100"},
                {"cohort": "A", "month_index": "2", "active_customers": "81"}]
        table, findings = ue.cohort_table(rows)
        self.assertEqual(findings, [])
        self.assertAlmostEqual(table["implied_monthly_churn"], 0.1, places=10)  # 0.9^2 = 0.81

    def test_cohort_retention_above_100_warns(self):
        rows = [{"cohort": "A", "month_index": "0", "active_customers": "10"},
                {"cohort": "A", "month_index": "1", "active_customers": "12"}]
        _, findings = ue.cohort_table(rows)
        self.assertIn("retention-above-100", rules(findings, "warning"))


class Cli(unittest.TestCase):
    def test_pass_example(self):
        code, out = run_json(SKILL, "unit_economics", EX / "unit-economics-pass.json",
                             "--cohorts", EX / "cohorts-pass.csv")
        self.assertEqual(code, 0)
        self.assertAlmostEqual(out["base"]["ltv_to_cac"], 3.5)
        self.assertAlmostEqual(out["cohort_retention"]["average_retention"]["3"], 0.9)
        self.assertEqual(len(out["assumption_ledger"]), 10)
        assert_schema(self, out, SCHEMA)

    def test_fail_example(self):
        code, out = run_json(SKILL, "unit_economics", EX / "unit-economics-fail.json",
                             "--cohorts", EX / "cohorts-fail.csv")
        self.assertEqual(code, 1)
        errs = rules(out["findings"], "error")
        for r in ("cac-undefined", "inconsistent-customers", "inconsistent-spend",
                  "benchmark-without-source", "assumption-bad-tag", "cohort-no-month-0",
                  "duplicate-cohort-month"):
            self.assertIn(r, errs)
        for r in ("churn-zero-capped", "non-positive-contribution", "assumption-untagged"):
            self.assertIn(r, rules(out["findings"], "warning"))
        assert_schema(self, out, SCHEMA)

    def test_malformed_exit_2(self):
        with tempfile.TemporaryDirectory() as td:
            bad = Path(td) / "bad.csv"
            bad.write_text("cohort,month_index,active_customers\nA,zero,10\n")
            self.assertEqual(run_cli(SKILL, "unit_economics", "--cohorts", bad).returncode, 2)
            badj = Path(td) / "bad.json"
            badj.write_text(json.dumps(model(arpa_monthly="x")))
            self.assertEqual(run_cli(SKILL, "unit_economics", badj).returncode, 2)
        self.assertEqual(run_cli(SKILL, "unit_economics").returncode, 2)


if __name__ == "__main__":
    unittest.main()
