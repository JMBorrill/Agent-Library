import unittest
from datetime import datetime, timezone

from tests.helpers import assert_schema, load_script, rules, run_cli, run_json, skill_path

SKILL = "software-delivery-metrics"
mod = load_script(SKILL, "dora_metrics")
EX = skill_path(SKILL, "assets", "examples")
SCHEMA = skill_path(SKILL, "assets", "schemas", "dora-metrics.output.schema.json")
COLS = ["deploy_id", "service", "deployed_at", "commit_times", "status", "is_rework", "restored_at"]
TOL = 1e-4  # values are rounded to 4 decimal places


def row(i, at, commits, status="success", rework="no", restored="", service="svc"):
    return dict(zip(COLS, [f"D{i}", service, at, commits, status, rework, restored]))


# Hand-computed known-answer dataset (window 2026-09-01 .. 2026-09-08 = 7 days):
#   lead-time samples (successful deployments only): 2 h, 6 h, 1 h, 24 h -> sorted 1,2,6,24
#   median 4; p75 rank 2.25 -> 6 + 0.25*18 = 10.5; p90 rank 2.7 -> 6 + 0.7*18 = 18.6
#   intervals 24 h, 2 h, 68 h (D4 is 08:00Z) -> median 24; CFR 1/4; rework 1/4; recovery 1.5 h
KNOWN = [
    row(1, "2026-09-01T10:00:00Z", "2026-09-01T08:00:00Z"),
    row(2, "2026-09-02T10:00:00Z", "2026-09-01T22:00:00Z", "failed", restored="2026-09-02T11:30:00Z"),
    row(3, "2026-09-02T12:00:00Z", "2026-09-02T06:00:00Z;2026-09-02T11:00:00Z", rework="yes"),
    row(4, "2026-09-05T10:00:00+02:00", "2026-09-04T10:00:00+02:00"),
]
START = datetime(2026, 9, 1, tzinfo=timezone.utc)
END = datetime(2026, 9, 8, tzinfo=timezone.utc)


class DoraMetricsTests(unittest.TestCase):
    def test_known_answers(self):
        res = mod.compute(COLS, KNOWN, start=START, end=END, min_sample=1)
        m = res["metrics"]
        self.assertEqual(res["summary"]["errors"], 0)
        df = m["Deployment frequency"]
        self.assertEqual(df["count"], 4)
        self.assertAlmostEqual(df["per_day"], 4 / 7, delta=TOL)
        self.assertAlmostEqual(df["per_week"], 4.0, delta=TOL)
        self.assertAlmostEqual(df["median_interval_hours"], 24.0, delta=TOL)
        lt = m["Change lead time"]
        self.assertEqual(lt["n"], 4)
        self.assertAlmostEqual(lt["median"], 4.0, delta=TOL)
        self.assertAlmostEqual(lt["p75"], 10.5, delta=TOL)
        self.assertAlmostEqual(lt["p90"], 18.6, delta=TOL)
        self.assertAlmostEqual(m["Change fail rate"]["ratio"], 0.25, delta=TOL)
        self.assertAlmostEqual(m["Deployment rework rate"]["ratio"], 0.25, delta=TOL)
        self.assertAlmostEqual(m["Failed deployment recovery time"]["median"], 1.5, delta=TOL)

    def test_percentile_function(self):
        self.assertIsNone(mod.percentile([], 50))
        self.assertEqual(mod.percentile([5.0], 90), 5.0)
        self.assertAlmostEqual(mod.percentile([1, 2, 3, 4], 50), 2.5)

    def test_pass_fixture_and_schema(self):
        code, out = run_json(SKILL, "dora_metrics", EX / "deployments-pass.csv")
        self.assertEqual(code, 0)
        m = out["metrics"]
        self.assertEqual(m["Deployment frequency"]["count"], 12)
        self.assertAlmostEqual(m["Deployment frequency"]["per_day"], 0.75, delta=TOL)
        self.assertAlmostEqual(m["Change lead time"]["median"], 7.5, delta=TOL)
        self.assertAlmostEqual(m["Change fail rate"]["ratio"], 2 / 12, delta=TOL)
        self.assertEqual(len(out["cautions"]), 7)
        assert_schema(self, out, SCHEMA)

    def test_fail_fixture(self):
        code, out = run_json(SKILL, "dora_metrics", EX / "deployments-fail.csv")
        self.assertEqual(code, 1)
        self.assertEqual(rules(out["findings"], "error"),
                         {"naive-timestamp", "negative-duration", "malformed-row", "duplicate-deploy-id"})
        self.assertTrue({"mixed-services", "small-sample", "unrecovered-failure"} <= rules(out["findings"], "warning"))
        assert_schema(self, out, SCHEMA)

    def test_service_filter_removes_mixed_warning(self):
        code, out = run_json(SKILL, "dora_metrics", EX / "deployments-fail.csv", "--service", "crm-api")
        self.assertNotIn("mixed-services", rules(out["findings"]))

    def test_empty_window_and_no_rows(self):
        res = mod.compute(COLS, KNOWN, start=datetime(2025, 1, 1, tzinfo=timezone.utc),
                          end=datetime(2025, 1, 2, tzinfo=timezone.utc))
        self.assertIn("no-deployments", rules(res["findings"], "warning"))
        self.assertEqual(res["metrics"], {})
        res = mod.compute(COLS, [])
        self.assertIn("no-deployments", rules(res["findings"]))

    def test_missing_columns_and_optional_columns(self):
        res = mod.compute(["deploy_id", "service"], [])
        self.assertIn("missing-columns", rules(res["findings"], "error"))
        cols = ["deploy_id", "service", "deployed_at", "status"]
        res = mod.compute(cols, [{c: v for c, v in KNOWN[0].items() if c in cols}], min_sample=1)
        self.assertTrue({"no-commit-data", "no-rework-data"} <= rules(res["findings"], "warning"))
        self.assertNotIn("Change lead time", res["metrics"])

    def test_bad_window_arguments_exit_2(self):
        p = EX / "deployments-pass.csv"
        self.assertEqual(run_cli(SKILL, "dora_metrics", p, "--start", "2026-09-10", "--end", "2026-09-01").returncode, 2)
        self.assertEqual(run_cli(SKILL, "dora_metrics", p, "--start", "2026-09-01T00:00:00").returncode, 2)
        self.assertEqual(run_cli(SKILL, "dora_metrics", "missing.csv").returncode, 2)

    def test_human_output_prints_cautions(self):
        proc = run_cli(SKILL, "dora_metrics", EX / "deployments-pass.csv")
        self.assertIn("Setting metrics as a goal", proc.stdout)
        self.assertIn("not targets", proc.stdout)


if __name__ == "__main__":
    unittest.main()
