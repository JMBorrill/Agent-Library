import unittest

from tests.helpers import assert_schema, load_script, rules, run_json, skill_path

SKILL = "se-requirements"
lint_mod = load_script(SKILL, "req_lint")
EX = skill_path(SKILL, "assets", "examples")
SCHEMA = skill_path(SKILL, "assets", "schemas", "lint-report.schema.json")
COLS = ["id", "parent", "level", "statement", "rationale", "source", "owner", "status",
        "verification_method", "acceptance_criteria", "verification_id"]


def row(**kw):
    base = {c: "" for c in COLS}
    base.update(id="P-SYS-001", level="system", statement="The unit shall weigh no more than 2.0 kg.",
                rationale="mass budget", source="analysis A1", owner="lead", status="approved",
                verification_method="inspection", acceptance_criteria="Scale reading <= 2.0 kg",
                parent="P-STK-001")
    base.update(kw)
    return base


NEED = row(id="P-STK-001", level="stakeholder", parent="", statement="Users need a portable unit.",
           verification_method="demonstration", acceptance_criteria="User confirms portability")


class ReqLintTests(unittest.TestCase):
    def lint(self, *rows):
        return lint_mod.lint(COLS, list(rows))

    def test_pass_example_cli_and_schema(self):
        code, out = run_json(SKILL, "req_lint", EX / "requirements-pass.csv")
        self.assertEqual(code, 0)
        self.assertTrue(out["passed"])
        self.assertEqual(out["summary"]["errors"], 0)
        assert_schema(self, out, SCHEMA)

    def test_fail_example_detects_all_seeded_defects(self):
        code, out = run_json(SKILL, "req_lint", EX / "requirements-fail.csv")
        self.assertEqual(code, 1)
        errs = rules(out["findings"], "error")
        for expected in ["duplicate-id", "id-format", "tbd-in-approved", "unknown-parent",
                         "trace-cycle", "verification-method", "approved-missing-owner"]:
            self.assertIn(expected, errs)
        warns = rules(out["findings"], "warning")
        for expected in ["not-atomic", "ambiguous-term", "escape-clause", "open-ended", "no-shall"]:
            self.assertIn(expected, warns)

    def test_clean_pair_passes(self):
        res = self.lint(NEED, row())
        self.assertEqual(res["summary"]["errors"], 0)
        self.assertEqual(res["summary"]["warnings"], 0)

    def test_missing_columns_is_error(self):
        res = lint_mod.lint(["id", "statement"], [])
        self.assertIn("missing-columns", rules(res["findings"], "error"))

    def test_tbd_allowed_when_proposed_but_not_approved(self):
        prop = self.lint(NEED, row(status="proposed", statement="The unit shall weigh no more than TBD kg."))
        self.assertIn("tbd-open", rules(prop["findings"], "warning"))
        self.assertEqual(prop["summary"]["errors"], 0)
        appr = self.lint(NEED, row(statement="The unit shall weigh no more than TBD kg."))
        self.assertIn("tbd-in-approved", rules(appr["findings"], "error"))

    def test_self_parent_and_cycle(self):
        res = self.lint(row(id="P-SYS-001", parent="P-SYS-001"))
        self.assertIn("self-parent", rules(res["findings"], "error"))
        res = self.lint(row(id="P-SYS-001", parent="P-SYS-002"), row(id="P-SYS-002", parent="P-SYS-001"))
        self.assertIn("trace-cycle", rules(res["findings"], "error"))

    def test_retired_parent_is_error_and_retired_rows_skipped(self):
        res = self.lint(row(id="P-SYS-002", status="retired", statement=""), row(parent="P-SYS-002"))
        self.assertIn("retired-parent", rules(res["findings"], "error"))
        self.assertNotIn("empty-statement", rules(res["findings"]))

    def test_ambiguity_does_not_match_inside_hyphenated_words(self):
        res = self.lint(NEED, row(statement="The low-gravity rig shall weigh no more than 2.0 kg."))
        self.assertNotIn("ambiguous-term", rules(res["findings"]))

    def test_unmeasurable_acceptance_warning(self):
        res = self.lint(NEED, row(verification_method="test", acceptance_criteria="Works well"))
        self.assertIn("unmeasurable-acceptance", rules(res["findings"], "warning"))

    def test_strict_mode_fails_on_warnings(self):
        code, out = run_json(SKILL, "req_lint", EX / "requirements-pass.csv", "--strict")
        self.assertEqual(code, 0)  # pass example has info only
        self.assertTrue(out["passed"])

    def test_unreadable_input_exit_2(self):
        from tests.helpers import run_cli
        self.assertEqual(run_cli(SKILL, "req_lint", "does-not-exist.csv").returncode, 2)

    def test_tree_handles_multiple_parents(self):
        rows = [NEED, row(id="P-SYS-002", parent="P-STK-001"), row(id="P-SUB-001", parent="P-SYS-001;P-SYS-002", level="subsystem")]
        rows[1:1] = [row()]
        text = lint_mod.tree(rows)
        self.assertEqual(text.count("P-SUB-001"), 2)


if __name__ == "__main__":
    unittest.main()
