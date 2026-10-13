"""Tests for credit-criteria-modelling: criteria_engine.py and affordability_calc.py."""
import copy
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from tests.helpers import assert_schema, load_script, rules, run_cli, run_json, skill_path

SKILL = "credit-criteria-modelling"
ce = load_script(SKILL, "criteria_engine")
af = load_script(SKILL, "affordability_calc")
EX = skill_path(SKILL, "assets", "examples")
SCH = skill_path(SKILL, "assets", "schemas")
CRITERIA = json.loads((EX / "criteria-pass.json").read_text())
CASE = json.loads((EX / "case-pass.json").read_text())
AFF = json.loads((EX / "affordability-pass.json").read_text())


def rule(**kw):
    base = dict(rule_id="R-1", lender="L (synthetic)", product="P", criterion="cltv_pct", operator="lte",
                value=75, unit="percent", effective_from="2026-01-01", effective_to=None,
                source_document="doc v1 p2", last_verified="2026-09-01")
    base.update(kw)
    return base


class Validation(unittest.TestCase):
    def test_pass_criteria_clean(self):
        self.assertEqual(ce.validate(CRITERIA["rules"], date(2026, 10, 1)), [])

    def test_unknown_operator_missing_source_overlap(self):
        f = ce.validate([rule(operator="approx"), rule(rule_id="R-2", source_document=""),
                         rule(rule_id="R-3", effective_from="2026-05-01")], date(2026, 10, 1))
        errs = rules(f, "error")
        self.assertTrue({"unknown-operator", "missing-source", "overlapping-effective-dates"} <= errs)

    def test_adjacent_versions_do_not_overlap(self):
        f = ce.validate([rule(effective_to="2026-03-31"), rule(rule_id="R-2", effective_from="2026-04-01")],
                        date(2026, 10, 1))
        self.assertNotIn("overlapping-effective-dates", rules(f))
        f = ce.validate([rule(effective_to="2026-04-01"), rule(rule_id="R-2", effective_from="2026-04-01")],
                        date(2026, 10, 1))
        self.assertIn("overlapping-effective-dates", rules(f, "error"))

    def test_stale_boundary_and_superseded_skip(self):
        ok = ce.validate([rule(last_verified="2026-07-03")], date(2026, 10, 1), 90)  # 90 days
        self.assertNotIn("stale-criterion", rules(ok))
        stale = ce.validate([rule(last_verified="2026-07-02")], date(2026, 10, 1), 90)
        self.assertIn("stale-criterion", rules(stale, "warning"))
        old = ce.validate([rule(last_verified="2020-01-01", effective_to="2026-06-30")], date(2026, 10, 1))
        self.assertNotIn("stale-criterion", rules(old))

    def test_bad_values_and_dates(self):
        f = ce.validate([rule(operator="between", value=[9, 1]), rule(rule_id="R-2", operator="in", value="x"),
                         rule(rule_id="R-3", operator="gte", value="10"),
                         rule(rule_id="R-4", effective_from="01/01/2026"),
                         rule(rule_id="R-5", criterion="x", effective_from="2026-05-01", effective_to="2026-01-01")])
        errs = rules(f, "error")
        self.assertTrue({"bad-value", "bad-date", "bad-effective-period"} <= errs)


class Evaluation(unittest.TestCase):
    def outcomes(self, case, crit=None, stale=None):
        return {(r["lender"]): r for r in ce.evaluate((crit or CRITERIA)["rules"], case, stale)}

    def test_example_outcomes(self):
        res = self.outcomes(CASE)
        self.assertEqual(res["Northbridge Mutual (synthetic)"]["outcome"], "eligible_indicative")
        self.assertEqual(res["Fernvale Home Finance (synthetic)"]["outcome"], "refer")
        self.assertEqual(res["Kestrel Lending (synthetic)"]["outcome"], "ineligible_indicative")
        # superseded 70% rule must not apply on the 2026 application date
        ids = [x["rule_id"] for x in res["Northbridge Mutual (synthetic)"]["reasons"]]
        self.assertNotIn("NBM-2C-001", ids)

    def test_superseded_rule_applies_on_old_date(self):
        case = copy.deepcopy(CASE)
        case["application_date"] = "2025-06-01"
        res = self.outcomes(case)
        nbm = res["Northbridge Mutual (synthetic)"]
        self.assertEqual(nbm["outcome"], "ineligible_indicative")  # 72.5 > 70
        self.assertEqual(res["Kestrel Lending (synthetic)"]["outcome"], "refer")  # no rules in effect

    def test_missing_data_refers_not_passes(self):
        case = copy.deepcopy(CASE)
        del case["facts"]["cltv_pct"]
        res = self.outcomes(case)
        self.assertEqual(res["Northbridge Mutual (synthetic)"]["outcome"], "refer")
        case["facts"]["cltv_pct"] = None
        self.assertEqual(self.outcomes(case)["Northbridge Mutual (synthetic)"]["outcome"], "refer")

    def test_unit_and_type_mismatch_refer(self):
        case = copy.deepcopy(CASE)
        case["units"]["cltv_pct"] = "fraction"
        self.assertEqual(self.outcomes(case)["Northbridge Mutual (synthetic)"]["outcome"], "refer")
        case = copy.deepcopy(CASE)
        case["facts"]["loan_amount"] = "fifty thousand"
        self.assertEqual(self.outcomes(case)["Northbridge Mutual (synthetic)"]["outcome"], "refer")

    def test_fail_beats_refer(self):
        case = copy.deepcopy(CASE)
        case["facts"]["cltv_pct"] = 90
        self.assertEqual(self.outcomes(case)["Fernvale Home Finance (synthetic)"]["outcome"], "ineligible_indicative")

    def test_stale_passing_rule_refers(self):
        res = self.outcomes(CASE, stale={"NBM-2C-002"})
        self.assertEqual(res["Northbridge Mutual (synthetic)"]["outcome"], "refer")

    def test_operators(self):
        self.assertTrue(ce.apply_operator("between", 5, [1, 5]))
        self.assertTrue(ce.apply_operator("not_in", "flat", ["house"]))
        self.assertTrue(ce.apply_operator("is_false", False, None))
        with self.assertRaises(TypeError):
            ce.apply_operator("is_true", "yes", None)

    def test_case_without_date_rejected(self):
        with self.assertRaises(ce.InputError):
            ce.evaluate(CRITERIA["rules"], {"facts": {}})


class Affordability(unittest.TestCase):
    def test_known_annuity(self):
        self.assertEqual(round(af.monthly_payment(200000, 5.0, 25), 2), 1169.18)

    def test_zero_rate_is_p_over_n(self):
        self.assertAlmostEqual(af.monthly_payment(120000, 0, 10), 1000.0, places=10)

    def test_interest_only(self):
        self.assertAlmostEqual(af.monthly_payment(240000, 5.0, 25, "interest_only"), 1000.0, places=10)

    def test_example_values(self):
        out = af.calculate(AFF)
        r = out["results"]
        self.assertAlmostEqual(r["ltv_pct"], 12.5)
        self.assertAlmostEqual(r["cltv_pct"], 72.5)
        self.assertAlmostEqual(r["stressed_rate_pct"], 9.5)
        self.assertAlmostEqual(r["monthly_payment_stressed"], af.monthly_payment(50000, 9.5, 15), places=10)
        self.assertAlmostEqual(r["dti_pct"], (250 + 1150 + r["monthly_payment_stressed"]) / 5000 * 100, places=10)
        self.assertAlmostEqual(r["net_disposable_income_monthly"],
                               3750 - 1300 - 250 - 1150 - r["monthly_payment_stressed"], places=10)
        self.assertAlmostEqual(r["lti_total_secured"], 290000 / 60000, places=10)
        self.assertEqual(out["summary"]["errors"], 0)

    def test_stress_floor(self):
        case = dict(AFF, product_rate_pct=1.0, stress_margin_pct=1.0, stress_floor_rate_pct=6.0)
        self.assertAlmostEqual(af.calculate(case)["results"]["stressed_rate_pct"], 6.0)

    def test_zero_income(self):
        out = af.calculate(dict(AFF, gross_annual_income=0, net_monthly_income=0))
        self.assertIsNone(out["results"]["lti"])
        self.assertIsNone(out["results"]["dti_pct"])
        self.assertIsNone(out["results"]["payment_to_net_income_pct"])
        self.assertTrue({"income-zero", "net-income-zero"} <= rules(out["findings"], "error"))

    def test_ltv_over_100(self):
        out = af.calculate(dict(AFF, charge="first", loan_amount=420000))
        self.assertIn("ltv-exceeds-100", rules(out["findings"], "error"))

    def test_negative_and_bad_inputs(self):
        for bad in (dict(AFF, loan_amount=-1), dict(AFF, term_years=0), dict(AFF, property_value=0),
                    dict(AFF, product_rate_pct="five"), dict(AFF, charge="third"),
                    {k: v for k, v in AFF.items() if k != "loan_amount"}):
            with self.assertRaises(af.InputError):
                af.calculate(bad)


class AffordabilityReferSignal(unittest.TestCase):
    """F02 regression: no PASS banner; negative NDI / DTI over policy produce a refer signal."""

    # Reviewer case 1: 200,000 over 25 y at 5% + 3% stress; income 40,000; net 2,600/month
    AFF1 = {"property_value": 250000, "loan_amount": 200000, "term_years": 25, "product_rate_pct": 5,
            "stress_margin_pct": 3, "stress_margin_source": "synthetic policy", "gross_annual_income": 40000,
            "net_monthly_income": 2600, "monthly_committed_expenditure": 200, "monthly_essential_expenditure": 1000}
    # Reviewer case 2 (second charge): 50,000 over 10 y at 0%, first-charge payment 900/month
    AFF2 = {"property_value": 300000, "loan_amount": 50000, "term_years": 10, "product_rate_pct": 0,
            "stress_margin_pct": 0, "stress_margin_source": "x", "gross_annual_income": 30000,
            "net_monthly_income": 2000, "monthly_committed_expenditure": 0, "monthly_essential_expenditure": 1500,
            "charge": "second", "existing_first_charge_balance": 200000, "existing_first_charge_payment": 900}

    def test_reviewer_case_1_negative_ndi_refers(self):
        out = af.calculate(self.AFF1)
        r = out["results"]
        # stressed payment at 8%: 1,543.63; NDI 2600-1000-200-1543.63 = -143.63; DTI 1743.63/3333.33 = 52.31%
        self.assertAlmostEqual(r["monthly_payment_stressed"], 1543.63, places=2)
        self.assertAlmostEqual(r["net_disposable_income_monthly"], -143.63, places=2)
        self.assertAlmostEqual(r["dti_pct"], 52.31, places=2)
        self.assertTrue(out["refer"])
        self.assertIn("negative-ndi", rules(out["findings"], "error"))
        self.assertEqual(out["status"], "refer")

    def test_reviewer_case_2_second_charge_refers(self):
        out = af.calculate(self.AFF2)
        # payment 50,000/120 = 416.67; NDI 2000-1500-900-416.67 = -816.67
        self.assertAlmostEqual(out["results"]["net_disposable_income_monthly"], -816.67, places=2)
        self.assertTrue(out["refer"])
        self.assertIn("negative-ndi", rules(out["findings"], "error"))
        self.assertIn("stress-margin-zero", rules(out["findings"], "warning"))

    def test_dti_policy_threshold(self):
        case = dict(self.AFF1, net_monthly_income=4000, dti_policy_max_pct=45, dti_policy_source="synthetic")
        out = af.calculate(case)
        self.assertGreater(out["results"]["net_disposable_income_monthly"], 0)
        self.assertIn("dti-above-policy", rules(out["findings"], "error"))
        self.assertTrue(out["refer"])
        ok = af.calculate(dict(case, dti_policy_max_pct=60))
        self.assertFalse(ok["refer"])
        self.assertEqual(ok["status"], "calculation_complete")

    def test_cli_never_prints_pass(self):
        with tempfile.TemporaryDirectory() as td:
            for name, case in (("a1.json", self.AFF1), ("a2.json", self.AFF2)):
                p = Path(td) / name
                p.write_text(json.dumps(case))
                proc = run_cli(SKILL, "affordability_calc", p)
                self.assertEqual(proc.returncode, 1)
                self.assertNotIn("PASS", proc.stdout)
                self.assertIn("REFER", proc.stdout)
        proc = run_cli(SKILL, "affordability_calc", EX / "affordability-pass.json")
        self.assertEqual(proc.returncode, 0)
        self.assertNotIn("PASS", proc.stdout)
        self.assertIn("CALCULATION COMPLETE (indicative arithmetic, not an affordability decision)", proc.stdout)


class Cli(unittest.TestCase):
    def test_engine_pass(self):
        code, out = run_json(SKILL, "criteria_engine", EX / "criteria-pass.json", "--case", EX / "case-pass.json")
        self.assertEqual(code, 0)
        self.assertEqual(out["summary"]["outcomes"],
                         {"refer": 1, "ineligible_indicative": 1, "eligible_indicative": 1})
        assert_schema(self, out, SCH / "criteria-output.schema.json")
        assert_schema(self, CRITERIA, SCH / "criteria.schema.json")
        assert_schema(self, CASE, SCH / "case.schema.json")

    def test_engine_fail(self):
        code, out = run_json(SKILL, "criteria_engine", EX / "criteria-fail.json", "--as-of", "2026-10-01",
                             "--case", EX / "case-pass.json")
        self.assertEqual(code, 1)
        self.assertEqual(out["results"], [])
        self.assertEqual(rules(out["findings"], "error"),
                         {"unknown-operator", "missing-source", "bad-value", "bad-effective-period",
                          "overlapping-effective-dates"})
        self.assertIn("stale-criterion", rules(out["findings"], "warning"))
        assert_schema(self, out, SCH / "criteria-output.schema.json")

    def test_affordability_cli(self):
        code, out = run_json(SKILL, "affordability_calc", EX / "affordability-pass.json")
        self.assertEqual(code, 0)
        assert_schema(self, out, SCH / "affordability-output.schema.json")
        assert_schema(self, AFF, SCH / "affordability-input.schema.json")
        code, out = run_json(SKILL, "affordability_calc", EX / "affordability-fail.json")
        self.assertEqual(code, 1)
        self.assertEqual(rules(out["findings"], "error"), {"cltv-exceeds-100", "income-zero", "net-income-zero", "negative-ndi"})
        self.assertTrue(out["refer"])

    def test_malformed_exit_2(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "neg.json"
            p.write_text(json.dumps(dict(AFF, net_monthly_income=-5)))
            self.assertEqual(run_cli(SKILL, "affordability_calc", p).returncode, 2)
            q = Path(td) / "crit.json"
            q.write_text(json.dumps({"rules": "nope"}))
            self.assertEqual(run_cli(SKILL, "criteria_engine", q).returncode, 2)
        self.assertEqual(run_cli(SKILL, "criteria_engine", "missing.json").returncode, 2)

    def test_never_says_approved(self):
        for args in (("criteria_engine", EX / "criteria-pass.json", "--case", EX / "case-pass.json"),
                     ("affordability_calc", EX / "affordability-pass.json")):
            proc = run_cli(SKILL, *args)
            self.assertNotIn("approved", proc.stdout.lower())
            proc = run_cli(SKILL, *args, "--json")
            self.assertNotIn("approved", proc.stdout.lower())


if __name__ == "__main__":
    unittest.main()
