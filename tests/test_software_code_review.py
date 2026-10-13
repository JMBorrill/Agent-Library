import unittest

from tests.helpers import assert_schema, load_script, rules, run_cli, run_json, skill_path

SKILL = "software-code-review"
scan_mod = load_script(SKILL, "diff_risk_scan")
rep_mod = load_script(SKILL, "review_report_check")
EX = skill_path(SKILL, "assets", "examples")
FINDINGS_SCHEMA = skill_path(SKILL, "assets", "schemas", "findings-report.schema.json")
REVIEW_SCHEMA = skill_path(SKILL, "assets", "schemas", "review-report.schema.json")


def diff(path, added, start=1, context_before=()):
    lines = [f"diff --git a/{path} b/{path}", f"--- a/{path}", f"+++ b/{path}",
             f"@@ -{start},1 +{start},{len(added) + len(context_before)} @@"]
    lines += [" " + c for c in context_before] + ["+" + a for a in added]
    return "\n".join(lines) + "\n"


class DiffRiskScanTests(unittest.TestCase):
    def test_pass_fixture(self):
        code, out = run_json(SKILL, "diff_risk_scan", EX / "pr-pass.diff")
        self.assertEqual(code, 0)
        self.assertTrue(out["passed"])
        self.assertEqual(out["summary"]["test_files"], 1)
        assert_schema(self, out, FINDINGS_SCHEMA)

    def test_fail_fixture_rules(self):
        code, out = run_json(SKILL, "diff_risk_scan", EX / "pr-fail.diff")
        self.assertEqual(code, 1)
        self.assertEqual(rules(out["findings"], "error"), {"hardcoded-secret", "swallowed-exception"})
        for r in ["no-test-changes", "debug-output", "todo-without-issue", "commented-out-code", "long-function"]:
            self.assertIn(r, rules(out["findings"], "warning"))
        assert_schema(self, out, FINDINGS_SCHEMA)

    def test_secret_value_not_echoed(self):
        _, out = run_json(SKILL, "diff_risk_scan", EX / "pr-fail.diff")
        self.assertNotIn("AKIAFAKEFAKEFAKEFAKE", str(out))

    def test_line_numbers_follow_hunk_header(self):
        res = scan_mod.scan(diff("src/a.py", ["x = 1  # TODO later"], start=40, context_before=["y = 2"]))
        todo = [f for f in res["findings"] if f["rule"] == "todo-without-issue"][0]
        self.assertEqual(todo["line"], 41)

    def test_todo_with_issue_reference_ok(self):
        res = scan_mod.scan(diff("src/a.py", ["x = 1  # TODO(AIOPS-77) handle DST"]))
        self.assertNotIn("todo-without-issue", rules(res["findings"]))

    def test_size_thresholds(self):
        big = scan_mod.scan(diff("src/a.py", [f"v{i} = {i}" for i in range(1001)]))
        self.assertIn("cl-too-large", rules(big["findings"], "error"))
        mid = scan_mod.scan(diff("src/a.py", [f"v{i} = {i}" for i in range(150)]))
        self.assertIn("cl-size-medium", rules(mid["findings"], "info"))
        self.assertEqual(mid["summary"]["size_band"], "medium")
        custom = scan_mod.scan(diff("src/a.py", [f"v{i} = {i}" for i in range(150)]), large=120)
        self.assertIn("cl-too-large", rules(custom["findings"]))

    def test_except_with_handling_not_flagged(self):
        res = scan_mod.scan(diff("src/a.py", ["try:", "    go()", "except ValueError:", "    pass",
                                              "except Exception as exc:", "    log.warning(exc)"]))
        self.assertNotIn("swallowed-exception", rules(res["findings"]))

    def test_env_lookup_not_a_secret(self):
        res = scan_mod.scan(diff("src/a.py", ['api_key = os.environ["CAL_API_KEY"]']))
        self.assertNotIn("hardcoded-secret", rules(res["findings"]))

    def test_print_allowed_in_tests(self):
        res = scan_mod.scan(diff("tests/test_a.py", ["print('debug')"]))
        self.assertNotIn("debug-output", rules(res["findings"]))

    def test_empty_and_malformed(self):
        self.assertIn("empty-diff", rules(scan_mod.scan("")["findings"]))
        with self.assertRaises(ValueError):
            scan_mod.scan("diff --git a/x.py b/x.py\n--- a/x.py\n+++ b/x.py\n@@ bogus @@\n+x\n")
        self.assertEqual(run_cli(SKILL, "diff_risk_scan", "missing.diff").returncode, 2)

    def test_strict_blocks_warnings(self):
        path = skill_path(SKILL, "assets", "examples", "pr-pass.diff")
        self.assertEqual(run_cli(SKILL, "diff_risk_scan", path, "--strict").returncode, 0)


class ReviewReportTests(unittest.TestCase):
    def test_pass_fixtures(self):
        for name in ("review-pass.json", "review-pass.md"):
            code, out = run_json(SKILL, "review_report_check", EX / name)
            self.assertEqual(code, 0, name)
            assert_schema(self, out, FINDINGS_SCHEMA)

    def test_pass_json_matches_input_schema(self):
        import json
        assert_schema(self, json.loads((EX / "review-pass.json").read_text()), REVIEW_SCHEMA)

    def test_fail_fixture(self):
        code, out = run_json(SKILL, "review_report_check", EX / "review-fail.md")
        self.assertEqual(code, 1)
        errs = rules(out["findings"], "error")
        self.assertTrue({"missing-decision", "bad-location", "missing-severity-label"} <= errs)
        self.assertIn("comment-targets-person", rules(out["findings"], "warning"))

    def test_lgtm_with_open_required_is_inconsistent(self):
        res = rep_mod.check({"decision": "LGTM", "findings": [
            {"severity": "Required", "aspect": "tests", "location": "a.py:3",
             "comment": "Add a test for the overlap branch so regressions are caught."}]})
        self.assertIn("decision-inconsistent", rules(res["findings"], "error"))

    def test_unknown_decision(self):
        res = rep_mod.check({"decision": "approved", "findings": []})
        self.assertIn("unknown-decision", rules(res["findings"], "error"))

    def test_findings_not_a_list(self):
        res = rep_mod.check({"decision": "lgtm", "findings": "none"})
        self.assertIn("no-findings-table", rules(res["findings"], "error"))


if __name__ == "__main__":
    unittest.main()
