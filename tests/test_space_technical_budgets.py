import json
import math
import unittest
from datetime import date

from tests.helpers import assert_schema, load_script, rules, run_cli, run_json, skill_path

SKILL = "space-technical-budgets"
bc = load_script(SKILL, "budget_calc")
lb = load_script(SKILL, "link_budget")
EX = skill_path(SKILL, "assets", "examples")
SCH = skill_path(SKILL, "assets", "schemas")
POLICY = EX / "margin-policy-example.json"
TIGHT = EX / "margin-policy-tight-example.json"
COLS = bc.REQUIRED_COLUMNS

BASE_POLICY = {
    "label": "test policy (synthetic)",
    "contingency_percent": {"estimated": 20, "calculated": 10, "heritage": 5, "measured": 3},
    "required_system_margin_percent": 15,
    "budgets": {"mass": {"unit": "kg", "allocation": 30.0}},
}


def row(**kw):
    base = {c: "" for c in COLS}
    base.update(item_id="X", parent="", budget="mass", unit="kg", cbe="1.0", maturity="measured",
                quantity="1", mode="")
    base.update(kw)
    return base


def hand_rows():
    return [row(item_id="ROOT", budget="", unit="", cbe="", maturity="", quantity=""),
            row(item_id="STR", parent="ROOT", cbe="12.0", maturity="calculated"),
            row(item_id="RW", parent="ROOT", cbe="0.9", maturity="heritage", quantity="4"),
            row(item_id="HAR", parent="ROOT", unit="g", cbe="2500", maturity="estimated"),
            row(item_id="CAM", parent="ROOT", cbe="1.5", maturity="measured")]


def policy(**budget_overrides):
    p = json.loads(json.dumps(BASE_POLICY))
    p["budgets"]["mass"].update(budget_overrides)
    return bc.validate_policy(p)


class BudgetCalcTests(unittest.TestCase):
    def test_known_answer_contingency_rollup(self):
        # Hand computation (tolerance 1e-9): CBE 12 + 3.6 + 2.5 + 1.5 = 19.6 kg;
        # contingency 1.2 + 0.18 + 0.5 + 0.045 = 1.925 kg; predicted 21.525 kg;
        # margin vs 30 kg = 8.475 kg = 28.25 % of allocation.
        res = bc.evaluate(COLS, hand_rows(), policy())
        t = res["totals"][0]
        self.assertAlmostEqual(t["cbe"], 19.6, places=9)
        self.assertAlmostEqual(t["contingency"], 1.925, places=9)
        self.assertAlmostEqual(t["predicted"], 21.525, places=9)
        self.assertAlmostEqual(t["margin"], 8.475, places=9)
        self.assertAlmostEqual(t["margin_percent"], 28.25, places=9)
        self.assertEqual(t["status"], "within-policy")
        root = [r for r in res["rollup"] if r["node"] == "ROOT"][0]
        self.assertAlmostEqual(root["predicted"], 21.525, places=9)
        self.assertEqual(res["summary"]["errors"], 0)

    def test_margin_below_policy_and_predicted_basis(self):
        res = bc.evaluate(COLS, hand_rows(), policy(allocation=25.0))
        self.assertIn("margin-below-policy", rules(res["findings"], "error"))
        self.assertAlmostEqual(res["totals"][0]["margin_percent"], 13.9, places=9)
        p = policy(allocation=25.0)
        p["margin_basis"] = "predicted"
        res = bc.evaluate(COLS, hand_rows(), p)
        # 3.475 / 21.525 * 100 = 16.1440...% -> meets 15 % on predicted basis
        self.assertAlmostEqual(res["totals"][0]["margin_percent"], 3.475 / 21.525 * 100, places=5)
        self.assertEqual(res["summary"]["errors"], 0)

    def test_negative_margin(self):
        res = bc.evaluate(COLS, hand_rows(), policy(allocation=20.0))
        self.assertIn("negative-margin", rules(res["findings"], "error"))

    def test_rss_combination(self):
        rows = [row(item_id="A", cbe="3", maturity="measured"), row(item_id="B", cbe="4", maturity="measured")]
        p = policy(combine="rss")
        p["contingency_percent"]["measured"] = 0
        t = bc.evaluate(COLS, rows, p)["totals"][0]
        self.assertAlmostEqual(t["predicted"], 5.0, places=9)

    def test_modes_with_all_items(self):
        p = bc.validate_policy({**BASE_POLICY, "budgets": {"power": {
            "unit": "W", "allocation_by_mode": {"drive": 50, "safe": 20}}}})
        rows = [row(item_id="OBC", budget="power", unit="W", cbe="10", maturity="measured", mode="all"),
                row(item_id="MOT", budget="power", unit="W", cbe="20", maturity="calculated", mode="drive")]
        res = bc.evaluate(COLS, rows, p)
        by = {t["mode"]: t for t in res["totals"]}
        self.assertAlmostEqual(by["drive"]["predicted"], 10.3 + 22.0, places=9)
        self.assertAlmostEqual(by["safe"]["predicted"], 10.3, places=9)
        rows.append(row(item_id="SCI", budget="power", unit="W", cbe="1", mode="science"))
        self.assertIn("unknown-mode", rules(bc.evaluate(COLS, rows, p)["findings"], "error"))

    def test_row_level_defects(self):
        rows = [row(item_id="A", unit="W"), row(item_id="B", maturity=""), row(item_id="C", quantity=""),
                row(item_id="D", cbe="abc"), row(item_id="E", cbe=""), row(item_id="F", parent="NOPE"),
                row(item_id="G", budget="thermal"), row(item_id="H", maturity="guess"),
                row(item_id="I", cbe="-1"), row(item_id="J", quantity="-2")]
        f = bc.evaluate(COLS, rows, policy())["findings"]
        errs = rules(f, "error")
        for r in ["unit-mismatch", "missing-maturity", "bad-number", "missing-cbe", "unknown-parent",
                  "budget-not-in-policy", "unknown-maturity", "negative-cbe", "bad-quantity"]:
            self.assertIn(r, errs)
        self.assertIn("missing-quantity", rules(f, "warning"))

    def test_cycle_and_header_cbe(self):
        rows = [row(item_id="A", parent="B", cbe=""), row(item_id="B", parent="A", cbe="")]
        self.assertIn("trace-cycle", rules(bc.evaluate(COLS, rows, policy())["findings"], "error"))
        rows = [row(item_id="P", cbe="5"), row(item_id="C", parent="P", cbe="1")]
        res = bc.evaluate(COLS, rows, policy())
        self.assertIn("header-cbe-ignored", rules(res["findings"], "warning"))
        self.assertAlmostEqual(res["totals"][0]["cbe"], 1.0)

    def test_empty_and_missing_columns(self):
        self.assertIn("empty-budget", rules(bc.evaluate(COLS, [], policy())["findings"], "error"))
        self.assertIn("missing-columns", rules(bc.evaluate(["item_id"], [], policy())["findings"], "error"))

    def test_policy_validation(self):
        for bad in [{}, {**BASE_POLICY, "contingency_percent": {"estimated": -1}},
                    {**BASE_POLICY, "budgets": {"mass": {"unit": "kg", "allocation": 0}}},
                    {**BASE_POLICY, "budgets": {"mass": {"unit": "kg", "allocation": 1, "combine": "max"}}},
                    {**BASE_POLICY, "margin_basis": "cbe"}]:
            with self.assertRaises(bc.PolicyError):
                bc.validate_policy(bad)

    def test_unit_factor(self):
        self.assertAlmostEqual(bc.unit_factor("g", "kg"), 1e-3)
        self.assertAlmostEqual(bc.unit_factor("MB", "Mbit"), 8.0)
        self.assertAlmostEqual(bc.unit_factor("J", "Wh"), 1 / 3600)
        self.assertIsNone(bc.unit_factor("W", "kg"))

    def test_trend_projection_known_answer(self):
        # predicted 10, 12, 14 at days 0, 10, 20 -> slope 0.2/day; at day 40 -> 18.
        snaps = []
        for d, v in [(date(2026, 1, 1), 10.0), (date(2026, 1, 11), 12.0), (date(2026, 1, 21), 14.0)]:
            p = policy(allocation=20.0)
            p["contingency_percent"]["measured"] = 0
            snaps.append((d, bc.evaluate(COLS, [row(cbe=str(v))], p)))
        tr, f = bc.trend(snaps, date(2026, 2, 10))
        self.assertAlmostEqual(tr[0]["slope_per_day"], 0.2, places=9)
        self.assertAlmostEqual(tr[0]["projected_predicted"], 18.0, places=9)
        self.assertEqual(tr[0]["projected_breach_date"], "2026-02-20")  # day 50
        self.assertIn("trend-projects-margin-shortfall", rules(f))  # 18 > 20*(1-0.15)=17
        tr, f = bc.trend(snaps, date(2026, 3, 1))
        self.assertIn("trend-projects-breach", rules(f))
        with self.assertRaises(ValueError):
            bc.linear_fit([1, 1], [2, 3])


class BudgetCliTests(unittest.TestCase):
    def test_pass_fixture(self):
        code, out = run_json(SKILL, "budget_calc", EX / "budget-pass.csv", "--policy", POLICY)
        self.assertEqual(code, 0, out["findings"])
        self.assertTrue(out["passed"])
        self.assertIn("example-policy-in-use", rules(out["findings"], "warning"))
        self.assertIn("not from ECSS or NASA", out["policy_label"])
        mass = [t for t in out["totals"] if t["budget"] == "mass"][0]
        self.assertAlmostEqual(mass["predicted"], 21.525, places=6)
        assert_schema(self, out, SCH / "budget-report.schema.json")

    def test_fail_fixture(self):
        code, out = run_json(SKILL, "budget_calc", EX / "budget-fail.csv", "--policy", TIGHT)
        self.assertEqual(code, 1)
        errs = rules(out["findings"], "error")
        for r in ["duplicate-id", "unit-mismatch", "missing-maturity", "budget-not-in-policy",
                  "unknown-mode", "margin-below-policy", "negative-margin"]:
            self.assertIn(r, errs)
        self.assertIn("missing-quantity", rules(out["findings"], "warning"))
        assert_schema(self, out, SCH / "budget-report.schema.json")

    def test_tpm_snapshots_cli(self):
        tpm = EX / "tpm"
        args = []
        for f in sorted(tpm.glob("mass-snapshot-*.csv")):
            args += ["--snapshot", f"{f.stem[-10:]}={f}"]
        code, out = run_json(SKILL, "budget_calc", "--policy", POLICY, *args)
        self.assertEqual(code, 0)
        self.assertEqual(out["summary"]["snapshots"], 3)
        self.assertIn("trend-projects-margin-shortfall", rules(out["findings"], "warning"))
        code, out = run_json(SKILL, "budget_calc", "--policy", POLICY, *args, "--project-to", "2027-09-01")
        self.assertIn("trend-projects-breach", rules(out["findings"], "warning"))
        assert_schema(self, out, SCH / "budget-report.schema.json")

    def test_usage_errors_exit_2(self):
        self.assertEqual(run_cli(SKILL, "budget_calc", "missing.csv", "--policy", POLICY).returncode, 2)
        self.assertEqual(run_cli(SKILL, "budget_calc", EX / "budget-pass.csv", "--policy", "nope.json").returncode, 2)
        self.assertEqual(run_cli(SKILL, "budget_calc", "--policy", POLICY).returncode, 2)
        self.assertEqual(run_cli(SKILL, "budget_calc", "--policy", POLICY, "--snapshot", "bad").returncode, 2)

    def test_policies_match_schema_and_label(self):
        for p in (POLICY, TIGHT):
            data = json.loads(p.read_text(encoding="utf-8"))
            self.assertIn("example values — not from ECSS or NASA", data["label"])
            assert_schema(self, data, SCH / "margin-policy.schema.json")


class LinkBudgetTests(unittest.TestCase):
    def test_fspl_known_answer(self):
        # 20 log10(4 pi * 1000 / (299792458/2.4e9)) = 100.0520 dB (tolerance 0.005 dB)
        self.assertAlmostEqual(lb.fspl_db(2.4e9, 1000.0), 100.052, delta=0.005)
        self.assertAlmostEqual(lb.fspl_db(2.4e9, 2000.0) - lb.fspl_db(2.4e9, 1000.0),
                               20 * math.log10(2), places=9)

    def test_boltzmann_db(self):
        self.assertAlmostEqual(lb.K_DB, -228.5992, delta=1e-3)

    def test_eb_n0_known_answer(self):
        link = json.loads((EX / "link-pass.json").read_text(encoding="utf-8"))
        res = lb.evaluate(link)
        fspl = 20 * math.log10(4 * math.pi * 5000 / (299792458 / 2.4e9))
        cn0 = 2.0 - fspl - 3.0 - 24.0 + 228.59916717
        self.assertAlmostEqual(res["c_n0_dbhz"], cn0, places=4)
        self.assertAlmostEqual(res["eb_n0_margin_db"], cn0 - 60 - 9.6 - 2.0, places=4)
        self.assertAlmostEqual(res["rx_power_dbm"], 2.0 + 30 - fspl - 3.0 + 3 - 1, places=4)

    def test_link_fixtures_cli(self):
        code, out = run_json(SKILL, "link_budget", "evaluate", EX / "link-pass.json")
        self.assertEqual(code, 0)
        assert_schema(self, out, SCH / "link-report.schema.json")
        code, out = run_json(SKILL, "link_budget", "evaluate", EX / "link-fail.json")
        self.assertEqual(code, 1)
        self.assertIn("negative-link-margin", rules(out["findings"], "error"))
        assert_schema(self, out, SCH / "link-report.schema.json")

    def test_margin_below_policy(self):
        link = json.loads((EX / "link-pass.json").read_text(encoding="utf-8"))
        link["required_margin"] = {"value": 15, "unit": "dB"}
        self.assertIn("link-margin-below-policy", rules(lb.evaluate(link)["findings"], "error"))

    def test_unit_validation(self):
        base = json.loads((EX / "link-pass.json").read_text(encoding="utf-8"))
        for key, bad in [("frequency", {"value": 2.4, "unit": "GHZ"}),
                         ("tx_antenna_gain", {"value": 3, "unit": "dB"}),
                         ("tx_losses", {"value": -1, "unit": "dB"}),
                         ("distance", {"value": 0, "unit": "km"}),
                         ("rx_gt", {"value": -24, "unit": "dB"}),
                         ("tx_power", {"value": 0, "unit": "W"}),
                         ("data_rate", {"value": 1, "unit": "baud"})]:
            link = dict(base, **{key: bad})
            with self.assertRaises(lb.InputError, msg=key):
                lb.evaluate(link)
        with self.assertRaises(lb.InputError):
            lb.fspl_db(0, 1)

    def test_cli_fspl_and_bad_input(self):
        code, out = run_json(SKILL, "link_budget", "fspl", "--frequency-hz", "2.4e9", "--distance-m", "1000")
        self.assertEqual(code, 0)
        self.assertAlmostEqual(out["fspl_db"], 100.052, delta=0.005)
        self.assertEqual(run_cli(SKILL, "link_budget", "fspl", "--frequency-hz", "-1",
                                 "--distance-m", "1").returncode, 2)
        self.assertEqual(run_cli(SKILL, "link_budget", "evaluate", "missing.json").returncode, 2)


if __name__ == "__main__":
    unittest.main()
