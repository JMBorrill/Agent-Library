import json
import unittest

from tests.helpers import ROOT, assert_schema, load_script, rules, run_cli, run_json, skill_path

SKILL = "security-asvs-controls"
mod = load_script(SKILL, "asvs_coverage")
EX = skill_path(SKILL, "assets", "examples")
INDEX_PATH = skill_path(SKILL, "assets", "data", "asvs-5.0.0-index.json")
INDEX = mod.load_index(INDEX_PATH)
SCHEMA = skill_path(SKILL, "assets", "schemas", "asvs-coverage.output.schema.json")
COLS = mod.COLUMNS


def row(rid, level="L1", app="yes", just="", impl="x.py", method="automated-test", ev="ci-1", status="pass"):
    return dict(zip(COLS, [rid, level, app, just, impl, method, ev, status]))


class AsvsCoverageTests(unittest.TestCase):
    def test_index_counts_match_audit(self):
        levels = [v["level"] for v in INDEX.values()]
        self.assertEqual((len(levels), levels.count(1), levels.count(2), levels.count(3)), (345, 70, 183, 92))
        bundled = json.loads(INDEX_PATH.read_text())
        extract = json.loads((ROOT / "sources" / "extracts" / "owasp-asvs-5.0.0-index.json").read_text())
        self.assertEqual(bundled["requirements"], extract["requirements"])
        self.assertIn("CC BY-SA 4.0", bundled["licence_notice"])

    def test_scope_sizes_cumulative(self):
        allch = mod.parse_chapters(None, INDEX)
        self.assertEqual(len(mod.in_scope(INDEX, 1, allch)), 70)
        self.assertEqual(len(mod.in_scope(INDEX, 2, allch)), 253)
        self.assertEqual(len(mod.in_scope(INDEX, 3, allch)), 345)
        self.assertEqual(len(mod.in_scope(INDEX, 1, {"V8"})), 4)

    def test_pass_fixture(self):
        code, out = run_json(SKILL, "asvs_coverage", EX / "control-map-pass.csv", "--level", "1", "--chapters", "V7,V8")
        self.assertEqual(code, 0)
        s = out["summary"]
        self.assertEqual((s["in_scope"], s["mapped"], s["applicable"], s["pass"]), (10, 10, 9, 7))
        self.assertAlmostEqual(s["pass_pct_of_applicable"], 77.8, places=1)
        assert_schema(self, out, SCHEMA)

    def test_fail_fixture(self):
        code, out = run_json(SKILL, "asvs_coverage", EX / "control-map-fail.csv", "--level", "1", "--chapters", "V7,V8")
        self.assertEqual(code, 1)
        expected = {"asvs-unversioned", "asvs-version-mismatch", "asvs-unknown-id", "level-mismatch",
                    "na-without-justification", "pass-without-evidence", "control-failed", "duplicate-row"}
        self.assertEqual(expected, rules(out["findings"], "error"))
        self.assertIn("missing-requirements", rules(out["findings"], "warning"))
        assert_schema(self, out, SCHEMA)

    def test_require_complete_and_out_of_scope(self):
        res = mod.check(COLS, [row("v5.0.0-8.1.1")], INDEX, 1, {"V8"}, require_complete=True)
        self.assertIn("missing-requirements", rules(res["findings"], "error"))
        res = mod.check(COLS, [row("v5.0.0-8.1.2", level="L2")], INDEX, 1, {"V8"})
        self.assertIn("out-of-scope-row", rules(res["findings"], "info"))

    def test_library_id_form_accepted(self):
        res = mod.check(COLS, [row("ASVS-v5.0.0-8.1.1")], INDEX, 1, {"V8"})
        self.assertNotIn("asvs-bad-format", rules(res["findings"]))
        self.assertEqual(res["summary"]["mapped"], 1)

    def test_empty_map_and_missing_columns(self):
        res = mod.check(COLS, [], INDEX, 1, {"V8"})
        self.assertEqual(res["summary"]["mapped"], 0)
        self.assertEqual(res["summary"]["pass_pct_of_applicable"], None)
        res = mod.check(["asvs_id"], [], INDEX, 1, {"V8"})
        self.assertIn("missing-columns", rules(res["findings"], "error"))

    def test_generate_template(self):
        proc = run_cli(SKILL, "asvs_coverage", "--generate-template", "--level", "1", "--chapters", "V8")
        self.assertEqual(proc.returncode, 0)
        lines = proc.stdout.strip().splitlines()
        self.assertEqual(lines[0].split(","), COLS)
        self.assertEqual(len(lines), 5)
        self.assertTrue(lines[1].startswith("v5.0.0-8.1.1,L1"))

    def test_usage_errors(self):
        self.assertEqual(run_cli(SKILL, "asvs_coverage", "nope.csv", "--level", "1").returncode, 2)
        self.assertEqual(run_cli(SKILL, "asvs_coverage", EX / "control-map-pass.csv", "--level", "1",
                                 "--chapters", "V99").returncode, 2)
        self.assertEqual(run_cli(SKILL, "asvs_coverage", "--level", "1").returncode, 2)

    def test_output_has_no_assurance_language(self):
        proc = run_cli(SKILL, "asvs_coverage", EX / "control-map-pass.csv", "--level", "1", "--chapters", "V7,V8")
        self.assertNotRegex(proc.stdout.lower().replace("not a compliance", ""), r"\bcompliant\b|\bcertified\b")


if __name__ == "__main__":
    unittest.main()
