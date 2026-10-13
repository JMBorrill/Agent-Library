import unittest

from tests.helpers import assert_schema, load_script, rules, run_cli, run_json, skill_path

SKILL = "se-verification-validation"
mod = load_script(SKILL, "vmatrix_check")
EX = skill_path(SKILL, "assets", "examples")
COLS = ["activity_id", "type", "requirement_id", "need_id", "method", "level", "configuration",
        "procedure_ref", "acceptance_criteria", "result", "evidence_ref", "run_date", "performed_by",
        "reviewer", "notes"]
REQS = [
    {"id": "P-STK-001", "level": "stakeholder", "status": "approved", "verification_method": "demonstration"},
    {"id": "P-SYS-001", "level": "system", "status": "approved", "verification_method": "test"},
    {"id": "P-SYS-002", "level": "system", "status": "proposed", "verification_method": "analysis"},
]


def act(**kw):
    base = {c: "" for c in COLS}
    base.update(activity_id="P-VER-001", type="verification", requirement_id="P-SYS-001", method="test",
                acceptance_criteria="<= 5 ms", result="not_tested")
    base.update(kw)
    return base


VAL = act(activity_id="P-VAL-001", type="validation", requirement_id="", need_id="P-STK-001",
          method="demonstration", acceptance_criteria="PI confirms")


class VMatrixTests(unittest.TestCase):
    def test_pass_fixture(self):
        code, out = run_json(SKILL, "vmatrix_check", EX / "vmatrix-pass.csv", "--requirements", EX / "requirements.csv")
        self.assertEqual(code, 0)
        self.assertEqual(out["summary"]["planned_coverage_pct"], 100.0)
        self.assertEqual(out["summary"]["failed_or_blocked"], ["DEMO-SYS-002"])
        assert_schema(self, out, skill_path(SKILL, "assets", "schemas", "vmatrix-report.schema.json"))

    def test_fail_fixture_rules(self):
        code, out = run_json(SKILL, "vmatrix_check", EX / "vmatrix-fail.csv", "--requirements", EX / "requirements.csv")
        self.assertEqual(code, 1)
        for r in ["result-without-evidence", "no-configuration", "unknown-requirement",
                  "validation-used-as-verification", "method", "result", "unverified-requirement"]:
            self.assertIn(r, rules(out["findings"], "error"))
        self.assertIn("self-review", rules(out["findings"], "warning"))
        self.assertIn("unvalidated-need", rules(out["findings"], "warning"))

    def test_missing_coverage_detected(self):
        res = mod.check(REQS, COLS, [VAL])
        self.assertIn("unverified-requirement", rules(res["findings"], "error"))
        self.assertEqual(res["summary"]["planned_coverage_pct"], 0.0)

    def test_proposed_excluded_unless_flag(self):
        res = mod.check(REQS, COLS, [act(), VAL])
        self.assertEqual(res["summary"]["errors"], 0)
        res = mod.check(REQS, COLS, [act(), VAL], include_proposed=True)
        self.assertIn("unverified-requirement", rules(res["findings"], "error"))

    def test_pass_requires_evidence_date_configuration(self):
        res = mod.check(REQS, COLS, [act(result="pass"), VAL])
        errs = rules(res["findings"], "error")
        self.assertTrue({"result-without-evidence", "result-without-date", "no-configuration"} <= errs)
        ok = mod.check(REQS, COLS, [act(result="pass", evidence_ref="e.csv", run_date="2026-01-02",
                                        configuration="rev A", performed_by="a", reviewer="b"), VAL])
        self.assertEqual(ok["summary"]["errors"], 0)
        self.assertEqual(ok["summary"]["passed_pct"], 100.0)

    def test_any_fail_dominates_requirement_state(self):
        rows = [act(result="pass", evidence_ref="e", run_date="2026-01-01", configuration="A", reviewer="r"),
                act(activity_id="P-VER-002", result="fail", evidence_ref="e2", run_date="2026-01-02",
                    configuration="A", reviewer="r"), VAL]
        res = mod.check(REQS, COLS, rows)
        self.assertEqual(res["summary"]["requirement_states"], {"fail": 1})

    def test_verifying_need_warns(self):
        res = mod.check(REQS, COLS, [act(), VAL, act(activity_id="P-VER-003", requirement_id="P-STK-001",
                                                       method="demonstration")])
        self.assertIn("verifying-a-need", rules(res["findings"], "warning"))

    def test_method_mismatch_warns(self):
        res = mod.check(REQS, COLS, [act(method="inspection"), VAL])
        self.assertIn("method-mismatch", rules(res["findings"], "warning"))

    def test_missing_columns(self):
        res = mod.check(REQS, ["activity_id"], [])
        self.assertIn("missing-columns", rules(res["findings"], "error"))

    def test_unreadable(self):
        self.assertEqual(run_cli(SKILL, "vmatrix_check", "nope.csv", "--requirements", "nope2.csv").returncode, 2)


if __name__ == "__main__":
    unittest.main()
