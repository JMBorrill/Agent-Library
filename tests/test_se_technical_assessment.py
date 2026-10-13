import unittest
from datetime import date

from tests.helpers import load_script, rules, run_cli, run_json, skill_path

SKILL = "se-technical-assessment"
mod = load_script(SKILL, "tpm_track")
EX = skill_path(SKILL, "assets", "examples")
COLS = ["tpm_id", "parameter", "unit", "direction", "limit", "alert_margin_pct", "date", "value", "basis"]


def r(date_, value, **kw):
    b = dict(tpm_id="T", parameter="p", unit="kg", direction="upper_limit", limit="100", alert_margin_pct="10",
             date=date_, value=str(value), basis="measured")
    b.update(kw)
    return b


class TpmTests(unittest.TestCase):
    def test_margin_known_answers(self):
        self.assertAlmostEqual(mod.margin_pct(80, 100, "upper_limit"), 20.0)
        self.assertAlmostEqual(mod.margin_pct(250, 200, "lower_limit"), 25.0)
        self.assertAlmostEqual(mod.margin_pct(112, 100, "upper_limit"), -12.0)
        with self.assertRaises(ZeroDivisionError):
            mod.margin_pct(1, 0, "upper_limit")

    def test_linear_projection_known_answer(self):
        # values 10, 20, 30 at days 0, 10, 20 -> slope 1/day; projection at day 30 = 40
        d0 = date(2026, 1, 1).toordinal()
        slope, icpt = mod.fit([(d0, 10), (d0 + 10, 20), (d0 + 20, 30)])
        self.assertAlmostEqual(slope, 1.0)
        self.assertAlmostEqual(slope * (d0 + 30) + icpt, 40.0)

    def test_status_bands(self):
        res = mod.assess(COLS, [r("2026-01-01", 95)])
        self.assertEqual(res["tpms"][0]["status"], "alert")
        res = mod.assess(COLS, [r("2026-01-01", 101)])
        self.assertEqual(res["tpms"][0]["status"], "breach")
        self.assertIn("breach", rules(res["findings"], "error"))

    def test_projected_breach(self):
        rows = [r("2026-01-01", 70), r("2026-02-01", 80), r("2026-03-01", 88)]
        res = mod.assess(COLS, rows, date(2026, 6, 1))
        self.assertIn("projected-breach", rules(res["findings"], "warning"))

    def test_negative_projection_flagged(self):  # raised by ASTER demo builder
        rows = [r("2026-01-01", 0.30, direction="lower_limit", limit="0.05"), r("2026-02-01", 0.20, direction="lower_limit", limit="0.05"),
                r("2026-03-01", 0.10, direction="lower_limit", limit="0.05")]
        res = mod.assess(COLS, rows, date(2026, 6, 1))
        self.assertIn("projection-implausible", rules(res["findings"], "warning"))

    def test_fixtures(self):
        code, out = run_json(SKILL, "tpm_track", EX / "tpm-pass.csv", "--milestone", "2027-01-15")
        self.assertEqual(code, 0)
        self.assertIn("projected-breach", rules(out["findings"], "warning"))
        code, out = run_json(SKILL, "tpm_track", EX / "tpm-fail.csv")
        self.assertEqual(code, 1)
        self.assertTrue({"breach", "inconsistent-units", "direction"} <= rules(out["findings"], "error"))

    def test_duplicate_date_and_unreadable(self):
        res = mod.assess(COLS, [r("2026-01-01", 1), r("2026-01-01", 2)])
        self.assertIn("duplicate-date", rules(res["findings"], "error"))
        self.assertEqual(run_cli(SKILL, "tpm_track", "missing.csv").returncode, 2)


if __name__ == "__main__":
    unittest.main()
