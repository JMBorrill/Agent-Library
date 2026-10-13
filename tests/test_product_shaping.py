import tempfile
import unittest
from pathlib import Path

from tests.helpers import assert_schema, load_script, rules, run_cli, run_json, skill_path

SKILL = "product-shaping"
mod = load_script(SKILL, "pitch_check")
EX = skill_path(SKILL, "assets", "examples")
SCHEMA = skill_path(SKILL, "assets", "schemas", "pitch-check.output.schema.json")

GOOD = (EX / "pitch-pass.md").read_text(encoding="utf-8")


def with_appetite(text: str) -> str:
    return GOOD.replace("2 weeks for one designer and one developer.", text)


class PitchCheckTests(unittest.TestCase):
    def test_pass_examples_cli_and_schema(self):
        code, out = run_json(SKILL, "pitch_check", EX / "pitch-pass.md", "--scopes", EX / "scopes-pass.md")
        self.assertEqual(code, 0)
        self.assertEqual(out["summary"]["warnings"], 0)
        self.assertEqual(out["summary"]["pitch"]["appetite_weeks"], 2.0)
        assert_schema(self, out, SCHEMA)

    def test_fail_pitch_seeded_defects(self):
        code, out = run_json(SKILL, "pitch_check", EX / "pitch-fail.md")
        self.assertEqual(code, 1)
        errs = rules(out["findings"], "error")
        for expected in ["appetite-unbounded", "appetite-exceeds-cycle", "rabbit-hole-unresolved",
                         "no-gos-empty", "unbounded-scope"]:
            self.assertIn(expected, errs)
        warns = rules(out["findings"], "warning")
        for expected in ["appetite-after-solution", "problem-without-evidence", "solution-no-elements",
                         "vague-term"]:
            self.assertIn(expected, warns)
        assert_schema(self, out, SCHEMA)

    def test_fail_scopes(self):
        code, out = run_json(SKILL, "pitch_check", "--scopes", EX / "scopes-fail.md")
        self.assertEqual(code, 1)
        self.assertTrue({"duplicate-scope", "scope-no-must-have", "scope-empty"} <= rules(out["findings"], "error"))
        self.assertIn("scope-is-layer", rules(out["findings"], "warning"))

    def test_appetite_cap_is_configurable(self):
        f, s = mod.check_pitch(with_appetite("8 weeks for one designer and one developer."), max_weeks=6)
        self.assertIn("appetite-exceeds-cycle", rules(f, "error"))
        f, s = mod.check_pitch(with_appetite("8 weeks for one designer and one developer."), max_weeks=10)
        self.assertNotIn("appetite-exceeds-cycle", rules(f))

    def test_appetite_units(self):
        self.assertEqual(mod.appetite_weeks("10 working days"), [2.0])
        self.assertEqual(mod.appetite_weeks("1 month"), [4.0])
        self.assertEqual(mod.appetite_weeks("6 weeks"), [6.0])

    def test_missing_and_ambiguous_appetite(self):
        f, _ = mod.check_pitch(with_appetite("Small."))
        self.assertIn("appetite-no-time-budget", rules(f, "error"))
        f, _ = mod.check_pitch(with_appetite("2 weeks, maybe 4 weeks."))
        self.assertIn("appetite-ambiguous", rules(f, "warning"))

    def test_missing_sections(self):
        f, _ = mod.check_pitch("# Pitch\n\n## Problem\nSomething DWS-EV-001.\n")
        missing = [x for x in f if x["rule"] == "missing-section"]
        self.assertEqual(len(missing), 4)

    def test_rabbit_hole_resolution_markers(self):
        for marker in ("-> cut it", "Decision: drop it", "Resolution: patch", "→ out of scope"):
            text = GOOD.replace("- SMS costs for large client lists -> Patch: reuse the existing reminder SMS budget and cap at 40 messages per day off.",
                                f"- SMS costs {marker}")
            self.assertNotIn("rabbit-hole-unresolved", rules(mod.check_pitch(text)[0]), marker)

    def test_hyphenated_words_not_vague(self):
        text = GOOD.replace("no new navigation.", "no new navigation; a well-improved-looking list.")
        self.assertNotIn("vague-term", rules(mod.check_pitch(text)[0]))

    def test_empty_inputs(self):
        f, _ = mod.check_pitch("   ")
        self.assertIn("empty-document", rules(f, "error"))
        f, _ = mod.check_scopes("")
        self.assertIn("no-scopes", rules(f, "error"))

    def test_usage_errors_exit_2(self):
        self.assertEqual(run_cli(SKILL, "pitch_check").returncode, 2)
        self.assertEqual(run_cli(SKILL, "pitch_check", "missing.md").returncode, 2)
        self.assertEqual(run_cli(SKILL, "pitch_check", EX / "pitch-pass.md", "--max-appetite-weeks", "0").returncode, 2)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bin.md"
            p.write_bytes(b"\xff\xfe\x00bad")
            self.assertEqual(run_cli(SKILL, "pitch_check", p).returncode, 2)


if __name__ == "__main__":
    unittest.main()
