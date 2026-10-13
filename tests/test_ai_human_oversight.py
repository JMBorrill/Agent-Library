import unittest

from tests.helpers import assert_schema, load_script, rules, run_cli, run_json, skill_path

SKILL = "ai-human-oversight"
ov = load_script(SKILL, "oversight_check")
EX = skill_path(SKILL, "assets", "examples")
SCHEMA = skill_path(SKILL, "assets", "schemas", "findings-report.schema.json")
COLS = ov.REQUIRED + ov.OPTIONAL


def row(**kw):
    base = {c: "" for c in COLS}
    base.update(decision_type="Mortgage affordability assessment", about_individuals="yes", impact="high",
                ai_role="recommend", human_role="Underwriter", approver_role="Senior Underwriter",
                override_logged="yes", explanation_provided="yes", appeal_route="Human review on request",
                monitoring_metric="override rate", rollback_trigger="override rate > 15% for 2 weeks", kill_switch_owner="Platform Owner")
    base.update(kw)
    return base


def check(*rows):
    return ov.check(COLS, list(rows))


class OversightTests(unittest.TestCase):
    def test_pass_fixture(self):
        code, out = run_json(SKILL, "oversight_check", EX / "oversight-matrix-pass.csv")
        self.assertEqual(code, 0)
        self.assertEqual(out["summary"]["errors"], 0)
        self.assertEqual(out["summary"]["warnings"], 0)
        assert_schema(self, out, SCHEMA)

    def test_fail_fixture_rules(self):
        code, out = run_json(SKILL, "oversight_check", EX / "oversight-matrix-fail.csv")
        self.assertEqual(code, 1)
        errs = rules(out["findings"], "error")
        for r in ["ov-act-without-approval", "ov-act-no-rollback", "ov-explanation-required", "ov-appeal-required",
                  "ov-approver-not-human", "ov-no-human-role", "ov-no-monitoring", "ov-override-not-logged", "ov-enum"]:
            self.assertIn(r, errs)
        warns = rules(out["findings"], "warning")
        for r in ["ov-automation-bias", "ov-duplicate-decision", "ov-no-kill-switch"]:
            self.assertIn(r, warns)
        assert_schema(self, out, SCHEMA)

    def test_clean_row(self):
        res = check(row())
        self.assertEqual((res["summary"]["errors"], res["summary"]["warnings"]), (0, 0))

    def test_high_impact_recommend_needs_pause_trigger(self):  # raised by mortgage demo review F-04
        res = check(row(impact="high", ai_role="recommend", rollback_trigger=""))
        self.assertIn("ov-no-rollback-trigger", rules(res["findings"], "warning"))

    def test_act_rules_by_impact(self):
        for impact, expect_err in (("low", False), ("medium", False), ("high", True), ("critical", True)):
            with self.subTest(impact=impact):
                res = check(row(impact=impact, ai_role="act", approver_role="", rollback_trigger="error rate > 2%"))
                self.assertEqual("ov-act-without-approval" in rules(res["findings"], "error"), expect_err)

    def test_act_with_approver_high_ok_critical_warns(self):
        res = check(row(ai_role="act", rollback_trigger="x > 1%"))
        self.assertNotIn("ov-act-without-approval", rules(res["findings"]))
        res = check(row(ai_role="act", impact="critical", rollback_trigger="x > 1%"))
        self.assertIn("ov-critical-act", rules(res["findings"], "warning"))

    def test_act_not_about_individuals(self):
        res = check(row(decision_type="Server log triage", about_individuals="no", impact="high",
                        ai_role="act", approver_role="", rollback_trigger="alert", explanation_provided="no",
                        appeal_route=""))
        self.assertNotIn("ov-act-without-approval", rules(res["findings"]))
        self.assertNotIn("ov-appeal-required", rules(res["findings"]))

    def test_act_requires_rollback(self):
        res = check(row(decision_type="Email triage", about_individuals="no", impact="low", ai_role="act",
                        approver_role="", explanation_provided="no", appeal_route="", rollback_trigger=""))
        self.assertIn("ov-act-no-rollback", rules(res["findings"], "error"))

    def test_credit_keyword_inference_without_flag(self):
        res = check(row(about_individuals="", decision_type="Loan eligibility check", explanation_provided="no",
                        appeal_route="none"))
        errs = rules(res["findings"], "error")
        self.assertTrue({"ov-explanation-required", "ov-appeal-required"} <= errs)

    def test_override_logging_severity(self):
        self.assertIn("ov-override-not-logged", rules(check(row(override_logged="no"))["findings"], "error"))
        low = check(row(decision_type="Queue routing", about_individuals="no", impact="low", override_logged="no"))
        self.assertIn("ov-override-not-logged", rules(low["findings"], "warning"))
        inform = check(row(ai_role="inform", override_logged="no"))
        self.assertNotIn("ov-override-not-logged", rules(inform["findings"]))

    def test_self_approval_critical(self):
        res = check(row(impact="critical", human_role="Underwriter", approver_role="underwriter"))
        self.assertIn("ov-self-approval", rules(res["findings"], "warning"))

    def test_empty_and_missing_columns(self):
        self.assertIn("ov-empty", rules(ov.check(COLS, [])["findings"], "error"))
        self.assertIn("ov-missing-columns", rules(ov.check(["decision_type"], [])["findings"], "error"))
        self.assertEqual(run_cli(SKILL, "oversight_check", "missing.csv").returncode, 2)

    def test_output_never_says_approved_or_compliant(self):
        proc = run_cli(SKILL, "oversight_check", EX / "oversight-matrix-pass.csv")
        self.assertNotRegex(proc.stdout.lower(), r"\bcompliant\b|\bapproved\b")


if __name__ == "__main__":
    unittest.main()
