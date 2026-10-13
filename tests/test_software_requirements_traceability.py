import tempfile
import unittest
from pathlib import Path

from tests.helpers import assert_schema, load_script, rules, run_cli, run_json, skill_path

SKILL = "software-requirements-traceability"
mod = load_script(SKILL, "trace_scan")
EX = skill_path(SKILL, "assets", "examples")
SCHEMA = skill_path(SKILL, "assets", "schemas", "trace-report.schema.json")
HDR = "id,level,statement,status\n"


def project_args(name, junit=True):
    base = EX / name
    args = [base / "requirements.csv", "--src", base / "src", "--tests", base / "tests", "--base", base]
    if junit:
        args += ["--junit", base / "results-junit.xml"]
    return args


class TraceScanTests(unittest.TestCase):
    def make(self, reqs, src=None, tests=None, junit=None):
        d = Path(tempfile.mkdtemp())
        (d / "req.csv").write_text(HDR + "".join(f"{r},software,stmt,{s}\n" for r, s in reqs))
        (d / "src").mkdir()
        (d / "tests").mkdir()
        for name, text in (src or {}).items():
            (d / "src" / name).write_text(text)
        for name, text in (tests or {}).items():
            (d / "tests" / name).write_text(text)
        jpath = None
        if junit is not None:
            jpath = d / "junit.xml"
            jpath.write_text(junit)
        return mod.run(d / "req.csv", [d / "src"], [d / "tests"], jpath, base=d)

    def test_pass_project(self):
        code, out = run_json(SKILL, "trace_scan", *project_args("project-pass"))
        self.assertEqual(code, 0)
        res = {m["id"]: m["result"] for m in out["matrix"]}
        self.assertEqual(res["AIOPS-SW-001"], "pass")
        self.assertEqual(res["AIOPS-SW-003"], "pass")
        self.assertEqual(res["AIOPS-SW-004"], "not_tested")
        assert_schema(self, out, SCHEMA)

    def test_fail_project_has_exactly_one_gap(self):
        code, out = run_json(SKILL, "trace_scan", *project_args("project-fail"))
        self.assertEqual(code, 1)
        errors = [f for f in out["findings"] if f["severity"] == "error"]
        self.assertEqual([(f["id"], f["rule"]) for f in errors], [("AIOPS-SW-003", "approved-untested")])
        assert_schema(self, out, SCHEMA)

    def test_no_junit_means_not_tested_never_pass(self):
        code, out = run_json(SKILL, "trace_scan", *project_args("project-pass", junit=False))
        self.assertEqual(code, 0)
        self.assertTrue(all(m["result"] == "not_tested" for m in out["matrix"]))
        self.assertIn("no-results", rules(out["findings"], "info"))

    def test_partial_results_not_pass(self):
        tests = {"test_a.py": "def test_P_SW_001_a():\n    pass\n\ndef test_P_SW_001_b():\n    pass\n"}
        junit = '<testsuite><testcase name="test_P_SW_001_a"/></testsuite>'
        res = self.make([("P-SW-001", "approved")], tests=tests, junit=junit)
        row = res["matrix"][0]
        self.assertEqual(row["result"], "not_tested")
        self.assertIn("missing-result", rules(res["findings"], "warning"))

    def test_failure_and_skip(self):
        tests = {"test_a.py": "def test_P_SW_001():\n    pass\n\ndef test_P_SW_002():\n    pass\n"}
        junit = ('<testsuite><testcase name="test_P_SW_001"><failure/></testcase>'
                 '<testcase name="test_P_SW_002"><skipped/></testcase></testsuite>')
        res = self.make([("P-SW-001", "approved"), ("P-SW-002", "approved")], tests=tests, junit=junit)
        by = {m["id"]: m["result"] for m in res["matrix"]}
        self.assertEqual(by, {"P-SW-001": "fail", "P-SW-002": "blocked"})
        self.assertIn("test-failed", rules(res["findings"], "error"))

    def test_unknown_and_retired_references(self):
        tests = {"test_a.py": "def test_x():\n    # @req P-SW-009\n    pass\n\ndef test_P_SW_002():\n    pass\n"}
        src = {"m.py": "# P-SW-777 stale tag\nx = 1\n"}
        res = self.make([("P-SW-002", "retired")], src=src, tests=tests)
        self.assertTrue({"test-unknown-requirement", "test-retired-requirement"} <= rules(res["findings"], "error"))
        self.assertIn("code-unknown-requirement", rules(res["findings"], "warning"))

    def test_code_tagged_but_untested_proposed(self):
        res = self.make([("P-SW-003", "proposed")], src={"m.py": "def f():\n    \"\"\"P-SW-003\"\"\"\n"})
        self.assertIn("code-untested", rules(res["findings"], "warning"))

    def test_string_literal_in_code_is_not_a_tag(self):
        res = self.make([("P-SW-004", "proposed")], src={"m.py": "LABEL = 'P-SW-004'\n"})
        self.assertEqual(res["matrix"][0]["code_refs"], [])

    def test_js_comment_block_and_marker(self):
        src = {"a.ts": "/* implements\n * P-SW-005 */\nexport const x = 1;\n"}
        tests = {"a.test.ts": "it('P-SW-005 works', () => {});\n"}
        res = self.make([("P-SW-005", "approved")], src=src, tests=tests)
        row = res["matrix"][0]
        self.assertEqual(row["code_refs"], ["src/a.ts:2"])
        self.assertEqual(len(row["tests"]), 1)

    def test_bad_status_and_custom_pattern(self):
        res = self.make([("P-SW-006", "done")])
        self.assertIn("bad-status", rules(res["findings"], "error"))
        rx_res = mod.build([{"id": "REQ7", "status": "approved", "level": "software"}], {},
                           [{"name": "t", "file": "t.py", "line": 1, "ids": {"REQ7"}}], None)
        self.assertEqual(rx_res["summary"]["errors"], 0)

    def test_usage_errors_exit_2(self):
        self.assertEqual(run_cli(SKILL, "trace_scan", "nope.csv", "--tests", "nope").returncode, 2)
        base = EX / "project-pass"
        self.assertEqual(run_cli(SKILL, "trace_scan", base / "requirements.csv").returncode, 2)
        with tempfile.TemporaryDirectory() as d:
            bad = Path(d) / "r.csv"
            bad.write_text("identifier,state\nX-001,approved\n")
            self.assertEqual(run_cli(SKILL, "trace_scan", bad, "--tests", base / "tests").returncode, 2)


if __name__ == "__main__":
    unittest.main()
