import json
import unittest
from datetime import date

from tests.helpers import assert_schema, load_script, rules, run_cli, run_json, skill_path

SKILL = "sre-incident-response"
mod = load_script(SKILL, "postmortem_check")
EX = skill_path(SKILL, "assets", "examples")
OUT_SCHEMA = skill_path(SKILL, "assets", "schemas", "findings-report.schema.json")
IN_SCHEMA = skill_path(SKILL, "assets", "schemas", "postmortem.schema.json")
PASS_MD = (EX / "postmortem-pass.md").read_text()


def check_md(text, as_of=None):
    return mod.check(mod.parse_markdown(text), as_of)


class PostmortemTests(unittest.TestCase):
    def test_pass_markdown(self):
        code, out = run_json(SKILL, "postmortem_check", EX / "postmortem-pass.md")
        self.assertEqual(code, 0)
        self.assertEqual(out["summary"]["timeline_entries"], 6)
        self.assertEqual(out["summary"]["timeline_span_minutes"], 325.0)  # 08:05 -> 13:30
        self.assertEqual(out["summary"]["warnings"], 0)
        assert_schema(self, out, OUT_SCHEMA)

    def test_pass_json_and_input_schema(self):
        code, out = run_json(SKILL, "postmortem_check", EX / "postmortem-pass.json")
        self.assertEqual(code, 0)
        self.assertEqual(out["summary"]["timeline_span_minutes"], 47.0)
        assert_schema(self, json.loads((EX / "postmortem-pass.json").read_text()), IN_SCHEMA)

    def test_fail_markdown(self):
        code, out = run_json(SKILL, "postmortem_check", EX / "postmortem-fail.md")
        self.assertEqual(code, 1)
        self.assertEqual(rules(out["findings"], "error"),
                         {"missing-section", "impact-not-quantified", "timeline-out-of-order", "action-no-owner",
                          "action-bad-priority", "action-bad-due-date", "action-no-tracking-id"})
        self.assertTrue({"blame-language", "no-severity", "timeline-timezone", "no-contributing-factors"}
                        <= rules(out["findings"], "warning"))
        assert_schema(self, out, OUT_SCHEMA)

    def test_overdue_with_as_of(self):
        res = check_md(PASS_MD, date(2026, 10, 13))
        self.assertEqual([f["id"] for f in res["findings"] if f["rule"] == "action-overdue"], ["action line 59"])
        self.assertEqual(res["summary"]["errors"], 0)

    def test_timezone_offsets_and_order(self):
        text = PASS_MD.replace("| 2026-09-14 08:40 |", "| 2026-09-14 09:40+02:00 |")  # = 07:40Z, before 08:05Z
        res = check_md(text)
        self.assertIn("timeline-out-of-order", rules(res["findings"], "error"))

    def test_time_carries_date_forward(self):
        text = PASS_MD.replace("| 2026-09-14 10:12 |", "| 10:12 |")
        self.assertEqual(check_md(text)["summary"]["errors"], 0)

    def test_blame_heuristic_avoids_system_subjects(self):
        clean = "## Summary\nThe deploy failed to start because the job neglected nothing.\n"
        self.assertNotIn("blame-language", rules(check_md(clean)["findings"]))
        for phrase in ("It was operator error.", "Priya forgot the flag.", "They should have noticed."):
            self.assertIn("blame-language", rules(check_md(f"## Summary\n{phrase}\n")["findings"]), phrase)
        self.assertNotIn("blame-language", rules(check_md("## Summary\nWe run blameless reviews.\n")["findings"]))

    def test_empty_document(self):
        res = check_md("")
        self.assertIn("missing-section", rules(res["findings"], "error"))

    def test_bad_inputs_exit_2(self):
        self.assertEqual(run_cli(SKILL, "postmortem_check", "missing.md").returncode, 2)
        self.assertEqual(run_cli(SKILL, "postmortem_check", EX / "postmortem-pass.md", "--as-of", "soon").returncode, 2)


if __name__ == "__main__":
    unittest.main()
