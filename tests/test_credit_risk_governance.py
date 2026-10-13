"""Tests for credit-risk-governance/governance_check.py."""
import tempfile
import unittest
from datetime import date
from pathlib import Path

from tests.helpers import assert_schema, load_script, rules, run_cli, run_json, skill_path

SKILL = "credit-risk-governance"
gc = load_script(SKILL, "governance_check")
EX = skill_path(SKILL, "assets", "examples")
SCHEMA = skill_path(SKILL, "assets", "schemas", "gap-report.schema.json")
COLS = gc.REQUIRED_COLUMNS + ["control_type", "model_risk", "last_validated"]
AS_OF = date(2026, 10, 1)


def row(**kw):
    base = dict(control_id="X-001", area="credit_granting", description="d", owner="o", frequency="monthly",
                evidence_ref="E1", last_tested="2026-09-01", status="tested_effective",
                independent_of_origination="yes", control_type="", model_risk="no", last_validated="")
    base.update(kw)
    return base


def full_cover(*extra):
    rows = [row(control_id=f"A-{i}", area=a) for i, a in enumerate(gc.AREAS)]
    return rows + list(extra)


class Checks(unittest.TestCase):
    def run_check(self, rows, cols=COLS, **kw):
        return gc.check(cols, rows, AS_OF, **kw)

    def test_clean_register(self):
        res = self.run_check(full_cover())
        self.assertEqual(res["summary"]["errors"], 0)
        self.assertEqual(res["summary"]["warnings"], 0)

    def test_area_not_covered_and_not_implemented_does_not_count(self):
        rows = full_cover()
        rows[1]["status"] = "not_implemented"
        res = self.run_check(rows)
        self.assertIn("area-not-covered", rules(res["findings"], "error"))
        self.assertIn("control-not-implemented", rules(res["findings"], "warning"))

    def test_area_aliases(self):
        self.assertEqual(gc.normalise_area("Governance"), "credit_risk_environment")
        self.assertEqual(gc.normalise_area("monitoring"), "administration_measurement_monitoring")
        self.assertIsNone(gc.normalise_area("marketing"))

    def test_missing_owner(self):
        res = self.run_check(full_cover(row(control_id="X-9", owner="TBD")))
        self.assertIn("missing-owner", rules(res["findings"], "error"))

    def test_test_age_boundary(self):
        ok = self.run_check(full_cover(row(control_id="X-9", last_tested="2025-10-01")))  # 365 days
        self.assertNotIn("test-overdue", rules(ok["findings"]))
        late = self.run_check(full_cover(row(control_id="X-9", last_tested="2025-09-30")))  # 366 days
        self.assertIn("test-overdue", rules(late["findings"], "error"))
        custom = self.run_check(full_cover(row(control_id="X-9", last_tested="2026-06-01")), max_test_age=90)
        self.assertIn("test-overdue", rules(custom["findings"], "error"))

    def test_never_tested_and_future_and_bad_date(self):
        res = self.run_check(full_cover(row(control_id="X-7", status="operating", last_tested=""),
                                        row(control_id="X-8", last_tested="2027-01-01"),
                                        row(control_id="X-9", last_tested="01/02/2026")))
        errs = rules(res["findings"], "error")
        self.assertTrue({"never-tested", "future-date", "bad-date"} <= errs)

    def test_designed_control_not_flagged_untested(self):
        res = self.run_check(full_cover(row(control_id="X-9", status="designed", last_tested="", evidence_ref="")))
        self.assertNotIn("never-tested", rules(res["findings"]))

    def test_independence(self):
        res = self.run_check(full_cover(row(control_id="X-9", control_type="approval",
                                            independent_of_origination="no")))
        self.assertIn("independence-lacking", rules(res["findings"], "error"))
        res = self.run_check(full_cover(row(control_id="X-9", area="controls", independent_of_origination="no")))
        self.assertIn("independence-lacking", rules(res["findings"], "error"))
        res = self.run_check(full_cover(row(control_id="X-9", independent_of_origination="no")))  # ordinary control
        self.assertNotIn("independence-lacking", rules(res["findings"]))
        res = self.run_check(full_cover(row(control_id="X-9", independent_of_origination="")))
        self.assertIn("independence-unknown", rules(res["findings"], "error"))

    def test_model_validation(self):
        res = self.run_check(full_cover(row(control_id="X-9", model_risk="yes")))
        self.assertIn("model-not-validated", rules(res["findings"], "error"))
        res = self.run_check(full_cover(row(control_id="X-9", control_type="scorecard", last_validated="2024-01-01")))
        self.assertIn("model-validation-overdue", rules(res["findings"], "warning"))

    def test_no_as_of_skips_age(self):
        res = gc.check(COLS, full_cover(row(control_id="X-9", last_tested="2001-01-01")), None)
        self.assertIn("age-check-skipped", rules(res["findings"], "info"))
        self.assertNotIn("test-overdue", rules(res["findings"]))

    def test_missing_columns(self):
        res = gc.check(["control_id", "area"], [], AS_OF)
        self.assertIn("missing-columns", rules(res["findings"], "error"))

    def test_empty_register_reports_all_areas_uncovered(self):
        res = self.run_check([])
        self.assertEqual(sum(1 for f in res["findings"] if f["rule"] == "area-not-covered"), 4)


class Cli(unittest.TestCase):
    def test_pass_example(self):
        code, out = run_json(SKILL, "governance_check", EX / "controls-register-pass.csv", "--as-of", "2026-10-01")
        self.assertEqual(code, 0)
        self.assertEqual(out["report_type"], "gap-report")
        assert_schema(self, out, SCHEMA)

    def test_fail_example(self):
        code, out = run_json(SKILL, "governance_check", EX / "controls-register-fail.csv", "--as-of", "2026-10-01")
        self.assertEqual(code, 1)
        errs = rules(out["findings"], "error")
        for r in ("independence-lacking", "missing-owner", "test-overdue", "model-not-validated", "never-tested",
                  "tested-without-evidence", "duplicate-control-id", "independence-unknown", "area-not-covered"):
            self.assertIn(r, errs)
        assert_schema(self, out, SCHEMA)

    def test_bad_inputs_exit_2(self):
        self.assertEqual(run_cli(SKILL, "governance_check", "nope.csv").returncode, 2)
        self.assertEqual(run_cli(SKILL, "governance_check", EX / "controls-register-pass.csv",
                                 "--as-of", "1 Oct 2026").returncode, 2)
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "ragged.csv"
            p.write_text(",".join(COLS) + "\n" + ",".join(["x"] * (len(COLS) + 2)) + "\n")
            self.assertEqual(run_cli(SKILL, "governance_check", p).returncode, 2)

    def test_output_never_approves(self):
        proc = run_cli(SKILL, "governance_check", EX / "controls-register-pass.csv", "--as-of", "2026-10-01")
        low = proc.stdout.lower()
        self.assertNotIn("approved", low)
        self.assertNotIn("compliant", low)


if __name__ == "__main__":
    unittest.main()
