import csv
import tempfile
import unittest
from pathlib import Path

from tests.helpers import assert_schema, load_script, rules, run_cli, run_json, skill_path

SKILL = "product-requirements-brief"
mod = load_script(SKILL, "prd_check")
req_lint = load_script("se-requirements", "req_lint")
EX = skill_path(SKILL, "assets", "examples")
SCHEMA = skill_path(SKILL, "assets", "schemas", "prd-check.output.schema.json")
COLS = mod.STORY_COLUMNS


def story(**kw):
    base = dict(id="DWS-STY-001", job_story="When I am ill, I want to tell owners at once, so I can rest.",
                acceptance_criteria="Given 3 walks today When I mark a day off Then 3 walks are listed",
                priority="must", evidence_ids="DWS-EV-001", requirement_ids="")
    base.update(kw)
    return base


class PrdCheckTests(unittest.TestCase):
    def test_pass_example_cli_and_schema(self):
        code, out = run_json(SKILL, "prd_check", EX / "prd-pass.md", "--stories", EX / "stories-pass.csv",
                             "--evidence", EX / "evidence-log.csv")
        self.assertEqual(code, 0)
        self.assertEqual(out["summary"]["errors"], 0)
        self.assertEqual(rules(out["findings"], "warning"), {"story-without-gwt"})
        assert_schema(self, out, SCHEMA)

    def test_fail_example_seeded_defects(self):
        code, out = run_json(SKILL, "prd_check", EX / "prd-fail.md", "--stories", EX / "stories-fail.csv",
                             "--evidence", EX / "evidence-log.csv")
        self.assertEqual(code, 1)
        errs = rules(out["findings"], "error")
        for expected in ["placeholder-section", "missing-section", "outcome-unmeasurable", "non-goals-empty",
                         "job-story-format", "unknown-evidence-id", "duplicate-id", "must-without-gwt",
                         "id-format", "requirement-id-format", "priority"]:
            self.assertIn(expected, errs)
        warns = rules(out["findings"], "warning")
        for expected in ["accessibility-unspecific", "solution-in-story", "non-evidence-cited",
                         "ambiguous-acceptance", "must-without-evidence"]:
            self.assertIn(expected, warns)
        assert_schema(self, out, SCHEMA)

    def test_job_story_regex(self):
        self.assertTrue(mod.JOB_STORY.match("When a walk is cancelled, I want to be offered a time, so that I can keep the routine."))
        self.assertFalse(mod.JOB_STORY.match("As a walker, I want X so that Y"))
        self.assertFalse(mod.JOB_STORY.match("When X, I want Y, so I can Z"))

    def test_multiple_scenarios_parsed(self):
        sc = mod.scenarios("Given a When b Then c; Given d When e Then f")
        self.assertEqual([s["then"] for s in sc], ["c", "f"])
        self.assertEqual(sc[1]["given"], "d")

    def test_requirement_id_reuse_across_stories(self):
        f = mod.check_stories(COLS, [story(requirement_ids="DWS-SW-001"),
                                     story(id="DWS-STY-002", requirement_ids="DWS-SW-001")])
        self.assertIn("requirement-id-reused", rules(f, "error"))

    def test_wont_and_could_without_gwt(self):
        f = mod.check_stories(COLS, [story(priority="wont", acceptance_criteria="")])
        self.assertEqual(rules(f, "error"), set())
        f = mod.check_stories(COLS, [story(priority="could", acceptance_criteria="")])
        self.assertIn("story-without-gwt", rules(f, "warning"))

    def test_missing_columns_and_empty(self):
        self.assertIn("missing-columns", rules(mod.check_stories(["id"], []), "error"))
        self.assertIn("no-stories", rules(mod.check_stories(COLS, []), "error"))
        self.assertIn("empty-document", rules(mod.check_prd(""), "error"))

    def test_flow_down_lints_clean_in_se_requirements(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "reqs.csv"
            proc = run_cli(SKILL, "prd_check", EX / "prd-pass.md", "--stories", EX / "stories-pass.csv",
                           "--flow-down", out)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            cols, rows = req_lint.read_rows(out)
            self.assertEqual(cols, mod.OUT_COLUMNS)
            self.assertEqual(len(rows), 7)
            self.assertTrue(all(r["status"] == "proposed" for r in rows))
            res = req_lint.lint(cols, rows)
            self.assertEqual(res["summary"]["errors"], 0, res["findings"])
            self.assertEqual(res["summary"]["warnings"], 0, res["findings"])
            sw = [r for r in rows if r["level"] == "software"]
            self.assertEqual([r["id"] for r in sw], ["DWS-SW-001", "DWS-SW-002", "DWS-SW-003", "DWS-SW-004"])
            self.assertTrue(all(" shall " in r["statement"] for r in sw))
            self.assertEqual(len({r["verification_id"] for r in sw}), 4)

    def test_flow_down_generated_ids_avoid_collisions_and_skip_bad(self):
        rows = [story(requirement_ids="DWS-SW-001"),
                story(id="DWS-STY-002", acceptance_criteria="Given a When b Then c; Given d When e Then f"),
                story(id="DWS-STY-003", acceptance_criteria="")]
        out, info = mod.flow_down(rows, prefix="DWS-SW")
        ids = [r["id"] for r in out if r["level"] == "software"]
        self.assertEqual(ids, ["DWS-SW-001", "DWS-SW-002", "DWS-SW-003"])
        self.assertIn("flow-down-skipped", rules(info))

    def test_flow_down_to_stdout(self):
        proc = run_cli(SKILL, "prd_check", EX / "prd-pass.md", "--stories", EX / "stories-pass.csv", "--flow-down", "-")
        self.assertEqual(proc.returncode, 0)
        reader = list(csv.DictReader(proc.stdout.splitlines()))
        self.assertEqual(len(reader), 7)
        self.assertIn("Scope:", proc.stderr)

    def test_usage_errors_exit_2(self):
        self.assertEqual(run_cli(SKILL, "prd_check", "missing.md").returncode, 2)
        self.assertEqual(run_cli(SKILL, "prd_check", EX / "prd-pass.md", "--flow-down", "-").returncode, 2)
        self.assertEqual(run_cli(SKILL, "prd_check", EX / "prd-pass.md", "--stories", EX / "stories-pass.csv",
                                 "--prefix", "bad prefix").returncode, 2)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.csv"
            p.write_text("id,job_story\nA,b,c,d\n", encoding="utf-8")
            self.assertEqual(run_cli(SKILL, "prd_check", EX / "prd-pass.md", "--stories", p).returncode, 2)


if __name__ == "__main__":
    unittest.main()
