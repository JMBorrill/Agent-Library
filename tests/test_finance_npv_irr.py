"""Tests for finance-npv-irr/cashflow.py. Known answers hand-computed (see references/dcf-method.md)."""
import json
import tempfile
import unittest
from pathlib import Path

from tests.helpers import assert_schema, load_script, rules, run_cli, run_json, skill_path

SKILL = "finance-npv-irr"
cf = load_script(SKILL, "cashflow")
EX = skill_path(SKILL, "assets", "examples")
OUT_SCHEMA = skill_path(SKILL, "assets", "schemas", "cashflow-output.schema.json")
IN_SCHEMA = skill_path(SKILL, "assets", "schemas", "cashflow-input.schema.json")
FLOWS = [-1000, 300, 400, 500]


class KnownAnswers(unittest.TestCase):
    def test_npv_t0_two_dp(self):
        self.assertEqual(round(cf.npv(0.10, FLOWS), 2), -21.04)

    def test_npv_t1_is_t0_divided_by_one_plus_r(self):
        self.assertAlmostEqual(cf.npv(0.10, FLOWS, "t1"), cf.npv(0.10, FLOWS) / 1.1, places=9)

    def test_irr_unique(self):
        res = cf.irr_analysis(FLOWS)
        self.assertEqual(res["status"], "unique")
        self.assertAlmostEqual(res["irr"], 0.08896, delta=5e-6)  # tolerance 0.0005 pp
        self.assertAlmostEqual(cf.npv(res["irr"], FLOWS), 0.0, delta=1e-6)

    def test_mirr(self):
        self.assertAlmostEqual(cf.mirr(FLOWS, 0.10, 0.10), 1.303 ** (1 / 3) - 1, places=10)

    def test_payback_simple_and_discounted_never(self):
        self.assertAlmostEqual(cf.payback(FLOWS)["period"], 2.6, places=10)
        d = cf.payback(FLOWS, 0.10)
        self.assertTrue(d["never"])
        self.assertIsNone(d["period"])

    def test_discounted_payback_interpolated(self):
        # at 0%: same as simple; at 5% cumulative PV -> -1000, -714.29, -351.47, +80.45
        d = cf.payback(FLOWS, 0.05)
        expected = 2 + 351.4739229 / (500 / 1.05 ** 3)
        self.assertAlmostEqual(d["period"], expected, places=6)

    def test_payback_reversal_flag(self):
        res = cf.payback([-100, 50, 60, -50])
        self.assertAlmostEqual(res["period"], 1 + 50 / 60, places=10)
        self.assertTrue(res["reverses"])

    def test_profitability_index(self):
        self.assertAlmostEqual(cf.profitability_index(0.10, FLOWS), 978.963185574 / 1000, places=8)

    def test_capm_and_wacc(self):
        self.assertAlmostEqual(cf.capm_cost_of_equity(0.04, 1.2, 0.05), 0.10, places=12)
        self.assertAlmostEqual(cf.wacc(600, 400, 0.10, 0.05, 0.25), 0.075, places=12)

    def test_dcf_gordon(self):
        res = cf.dcf_enterprise_value([100, 110, 121], 0.10, 0.02)
        self.assertAlmostEqual(res["terminal_value"], 1542.75, places=8)
        self.assertAlmostEqual(res["enterprise_value"], 1431.818181818, places=6)

    def test_dcf_growth_ge_rate_errors(self):
        with self.assertRaises(ValueError):
            cf.dcf_enterprise_value([100], 0.05, 0.05)

    def test_multiple_irr_roots(self):
        res = cf.irr_analysis([-100, 230, -132])  # (1+r) = 1.1 or 1.2
        self.assertEqual(res["status"], "multiple-possible")
        self.assertEqual(len(res["roots"]), 2)
        self.assertAlmostEqual(res["roots"][0], 0.10, delta=1e-8)
        self.assertAlmostEqual(res["roots"][1], 0.20, delta=1e-8)
        self.assertIsNone(cf.irr([-100, 230, -132]))

    def test_switching_values(self):
        sv = cf.switching_value("inflow_scale", 0.10, FLOWS)
        self.assertAlmostEqual(sv["switching_value"], 1000 / 978.963185574, places=7)
        sv_rate = cf.switching_value("rate", 0.10, FLOWS)
        self.assertAlmostEqual(sv_rate["switching_value"], cf.irr(FLOWS), places=8)

    def test_sensitivity_table(self):
        t = cf.sensitivity_table("rate", [0.0, 0.10], 0.10, FLOWS)
        self.assertAlmostEqual(t[0]["npv"], 200.0, places=9)
        self.assertAlmostEqual(t[1]["npv"], cf.npv(0.10, FLOWS), places=9)


class EdgeCases(unittest.TestCase):
    def test_all_zero_flows(self):
        self.assertEqual(cf.npv(0.1, [0, 0, 0]), 0)
        self.assertEqual(cf.irr_analysis([0, 0, 0])["status"], "none-no-sign-change")
        out = cf.analyse({"rate": 0.1, "flows": [0, 0, 0], "price_basis": "real"})
        self.assertIn("all-zero-flows", rules(out["findings"], "warning"))
        self.assertIn("no-irr", rules(out["findings"], "error"))

    def test_rate_minus_100_percent_rejected(self):
        with self.assertRaises(cf.InputError):
            cf.npv(-1.0, FLOWS)

    def test_empty_list_rejected(self):
        with self.assertRaises(cf.InputError):
            cf.npv(0.1, [])

    def test_non_numeric_rejected(self):
        for bad in (["a", 1], [None, 1], [True, 1], [float("nan")]):
            with self.assertRaises(cf.InputError):
                cf.clean_flows(bad)

    def test_wacc_guards(self):
        with self.assertRaises(cf.InputError):
            cf.wacc(0, 0, 0.1, 0.05, 0.2)
        with self.assertRaises(cf.InputError):
            cf.wacc(1, 1, 0.1, 0.05, 1.5)

    def test_pi_needs_negative_initial(self):
        with self.assertRaises(cf.InputError):
            cf.profitability_index(0.1, [100, 50])


class Cli(unittest.TestCase):
    def test_pass_example(self):
        code, out = run_json(SKILL, "cashflow", EX / "cashflow-pass.json")
        self.assertEqual(code, 0)
        self.assertTrue(out["passed"])
        self.assertAlmostEqual(out["results"]["npv"], -21.0368, delta=1e-4)
        self.assertAlmostEqual(out["results"]["wacc"], 0.075, places=10)
        assert_schema(self, out, OUT_SCHEMA)
        assert_schema(self, json.loads((EX / "cashflow-pass.json").read_text()), IN_SCHEMA)

    def test_fail_example(self):
        code, out = run_json(SKILL, "cashflow", EX / "cashflow-fail.json")
        self.assertEqual(code, 1)
        self.assertEqual(rules(out["findings"], "error"), {"no-irr", "terminal-growth-ge-rate"})
        assert_schema(self, out, OUT_SCHEMA)

    def test_multiple_irr_example_warns(self):
        code, out = run_json(SKILL, "cashflow", EX / "cashflow-multiple-irr.json")
        self.assertEqual(code, 0)
        self.assertIn("multiple-irr", rules(out["findings"], "warning"))
        code, _ = run_json(SKILL, "cashflow", EX / "cashflow-multiple-irr.json", "--strict")
        self.assertEqual(code, 1)

    def test_csv_matches_json(self):
        code, out = run_json(SKILL, "cashflow", EX / "flows-pass.csv", "--rate", "0.10")
        self.assertEqual(code, 0)
        self.assertAlmostEqual(out["results"]["npv"], -21.0368, delta=1e-4)

    def test_csv_period_column_honoured(self):
        """F07 regression: CSV periods 3,4,5 were treated as t0 (NPV 41.3223); now discounted by period."""
        with tempfile.TemporaryDirectory() as td:
            def write(name, body):
                p = Path(td) / name
                p.write_text(body)
                return p
            p3 = write("p3.csv", "period,cash_flow\n3,-1000\n4,600\n5,600\n")
            code, out = run_json(SKILL, "cashflow", p3, "--rate", "0.10")
            self.assertEqual(code, 0)
            # -1000/1.1^3 + 600/1.1^4 + 600/1.1^5 = 41.3223 / 1.1^3 = 31.0461
            self.assertAlmostEqual(out["results"]["npv"], -1000 / 1.1 ** 3 + 600 / 1.1 ** 4 + 600 / 1.1 ** 5,
                                   places=8)
            self.assertIn("csv-leading-periods-zero-filled", rules(out["findings"], "info"))
            # starting at 0 and at 1 (unsorted rows) both index by period
            code, out = run_json(SKILL, "cashflow", write("p0.csv", "period,cash_flow\n1,600\n0,-1000\n2,600\n"),
                                 "--rate", "0.10")
            self.assertAlmostEqual(out["results"]["npv"], -1000 + 600 / 1.1 + 600 / 1.21, places=8)
            code, out = run_json(SKILL, "cashflow", write("p1.csv", "period,cash_flow\n1,-1000\n2,600\n3,600\n"),
                                 "--rate", "0.10")
            self.assertAlmostEqual(out["results"]["npv"], -1000 / 1.1 + 600 / 1.21 + 600 / 1.331, places=8)
            for name, body, msg in (("gap.csv", "period,cash_flow\n0,-1000\n1,600\n3,600\n", "missing periods [2]"),
                                    ("dup.csv", "period,cash_flow\n0,-1000\n1,600\n1,600\n", "duplicate periods [1]"),
                                    ("neg.csv", "period,cash_flow\n-1,-1000\n0,600\n", "period must be >= 0")):
                proc = run_cli(SKILL, "cashflow", write(name, body), "--rate", "0.1")
                self.assertEqual(proc.returncode, 2, name)
                self.assertIn(msg, proc.stderr, name)
            proc = run_cli(SKILL, "cashflow", p3, "--rate", "0.1", "--convention", "t0")
            self.assertEqual(proc.returncode, 2)

    def test_malformed_inputs_exit_2(self):
        with tempfile.TemporaryDirectory() as td:
            cases = {"empty.json": {"rate": 0.1, "flows": []},
                     "text.json": {"rate": 0.1, "flows": [-1, "x"]},
                     "rate.json": {"rate": -1.0, "flows": [-1, 2]}}
            for name, body in cases.items():
                p = Path(td) / name
                p.write_text(json.dumps(body))
                self.assertEqual(run_cli(SKILL, "cashflow", p).returncode, 2, name)
            bad_csv = Path(td) / "bad.csv"
            bad_csv.write_text("period,cash_flow\n0,-100\n1,abc\n")
            self.assertEqual(run_cli(SKILL, "cashflow", bad_csv, "--rate", "0.1").returncode, 2)
        self.assertEqual(run_cli(SKILL, "cashflow", "missing.json").returncode, 2)

    def test_no_approval_language(self):
        proc = run_cli(SKILL, "cashflow", EX / "cashflow-pass.json")
        self.assertNotIn("approved", proc.stdout.lower())


if __name__ == "__main__":
    unittest.main()
